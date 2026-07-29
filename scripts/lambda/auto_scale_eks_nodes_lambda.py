"""
AWS Lambda function to auto-scale EKS nodegroups for EvalAI challenges.

This function is triggered asynchronously from submission lifecycle events.
It fetches challenge metadata and pending submission counts from internal
EvalAI APIs authenticated via LAMBDA_AUTH_TOKEN, then updates the challenge
EKS nodegroup scaling config accordingly.

It also supports a scheduled sweep mode (``{"sweep": true}``) that reconciles
every autoscale-eligible challenge. Event-driven invocations are best-effort,
so a single dropped invoke can otherwise leave a nodegroup stuck at zero nodes
with submissions pending indefinitely.

Unrecoverable errors are raised rather than returned as an error status code,
so that asynchronous invocations surface in the Lambda ``Errors`` metric and
are routed to the configured dead-letter queue / on-failure destination.
Returning a 5xx body would be recorded as a successful invocation and fail
silently.

Environment variables required:
- EVALAI_API_SERVER: EvalAI API server URL (e.g. https://eval.ai)
- LAMBDA_AUTH_TOKEN: shared secret for internal Lambda-auth APIs
- AWS_REGION: AWS region (optional, defaults to us-east-1)
- EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME: name of the IAM role assumed in a
  challenge's host AWS account for cross-account nodegroup scaling
  (optional, defaults to "evalai-autoscale-crossaccount")
"""

import json
import logging
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

EVALAI_API_SERVER = os.environ.get("EVALAI_API_SERVER")
LAMBDA_AUTH_TOKEN = os.environ.get("LAMBDA_AUTH_TOKEN")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
CROSS_ACCOUNT_ROLE_NAME = os.environ.get(
    "EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME", "evalai-autoscale-crossaccount"
)


class AutoscaleError(Exception):
    """Raised for unrecoverable autoscale failures worth retrying/alarming."""


def _validate_env():
    if not EVALAI_API_SERVER:
        raise RuntimeError("Missing EVALAI_API_SERVER")
    if not LAMBDA_AUTH_TOKEN:
        raise RuntimeError("Missing LAMBDA_AUTH_TOKEN")


def _call_evalai_api(path):
    url = "{0}{1}".format(EVALAI_API_SERVER.rstrip("/"), path)
    headers = {"Authorization": "Bearer {0}".format(LAMBDA_AUTH_TOKEN)}
    request = Request(url=url, headers=headers, method="GET")
    with urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _get_nodegroup_name(eks_client, cluster_name, configured_nodegroup=None):
    """
    Resolve the nodegroup to scale.

    Prefers the name recorded on the challenge at nodegroup creation. Falling
    back to the first entry of list_nodegroups is non-deterministic once a
    cluster has more than one nodegroup, so it is only a last resort.
    """
    if configured_nodegroup:
        return configured_nodegroup

    nodegroups = eks_client.list_nodegroups(clusterName=cluster_name).get(
        "nodegroups", []
    )
    if not nodegroups:
        raise ValueError(
            "No nodegroups found for cluster '{0}'".format(cluster_name)
        )
    if len(nodegroups) > 1:
        logger.warning(
            "Cluster '%s' has %s nodegroups and no recorded nodegroup_name. "
            "Defaulting to '%s'.",
            cluster_name,
            len(nodegroups),
            nodegroups[0],
        )
    return nodegroups[0]


def _get_scaling_config(eks_client, cluster_name, nodegroup_name):
    response = eks_client.describe_nodegroup(
        clusterName=cluster_name,
        nodegroupName=nodegroup_name,
    )
    return response["nodegroup"]["scalingConfig"]


def _desired_size_for_pending(pending_submissions, scale_up_cap):
    if pending_submissions <= 0:
        return 0
    return min(pending_submissions, scale_up_cap)


def _should_force_scale_down(challenge_meta):
    """
    Return True when the challenge should hold zero nodes regardless of its
    pending submission count.

    A disabled challenge is treated like an ended one. Excluding disabled
    challenges from the sweep entirely would be worse: one disabled while its
    nodegroup is scaled up would keep those nodes running with nothing left to
    reconcile it back down.
    """
    if challenge_meta.get("is_disabled"):
        return True

    end_date = challenge_meta.get("end_date")
    if not end_date:
        return False
    try:
        # ISO 8601 from DRF can end with "Z"
        challenge_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Invalid end_date format: %s", end_date)
        return False
    return challenge_end <= datetime.now(challenge_end.tzinfo)


def _build_eks_client(aws_region, challenge_meta):
    """
    Build an EKS client for the challenge's nodegroup.

    Challenges that run in a host-provided AWS account (use_host_credentials)
    have their EKS cluster in a different account than this Lambda. For those
    we assume a cross-account role in the challenge's account; otherwise we use
    the Lambda's own execution role (same-account behaviour, unchanged).
    """
    account_id = challenge_meta.get("aws_account_id")
    use_host_credentials = challenge_meta.get("use_host_credentials")

    if use_host_credentials and not account_id:
        # Falling back to the Lambda's own account here produces a confusing
        # AccessDeniedException against a cluster that lives elsewhere.
        logger.warning(
            "Challenge %s has use_host_credentials=True but no "
            "aws_account_id. Cannot assume the cross-account autoscale role; "
            "falling back to this Lambda's own account, which will fail if "
            "the cluster lives in the host's account. Set aws_account_id on "
            "the challenge.",
            challenge_meta.get("challenge_pk"),
        )

    if use_host_credentials and account_id:
        role_arn = "arn:aws:iam::{0}:role/{1}".format(
            account_id, CROSS_ACCOUNT_ROLE_NAME
        )
        credentials = boto3.client("sts").assume_role(
            RoleArn=role_arn,
            RoleSessionName="evalai-eks-autoscale",
        )["Credentials"]
        return boto3.client(
            "eks",
            region_name=aws_region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )
    return boto3.client("eks", region_name=aws_region)


def _scale_challenge(challenge_pk):
    """
    Reconcile one challenge's nodegroup against its pending submission count.

    Raises:
        AutoscaleError: on failures that should be retried and alarmed on.
    """
    try:
        challenge_meta = _call_evalai_api(
            "/api/challenges/challenge/{0}/autoscale_meta/".format(
                challenge_pk
            )
        )
        pending_data = _call_evalai_api(
            "/api/challenges/challenge/{0}/pending_submission_count/".format(
                challenge_pk
            )
        )
    except (HTTPError, URLError, TimeoutError) as err:
        logger.error(
            "Failed to fetch autoscale data for challenge %s: %s",
            challenge_pk,
            err,
        )
        raise AutoscaleError(
            "Failed to fetch autoscale data for challenge {0}".format(
                challenge_pk
            )
        ) from err

    if not challenge_meta.get("is_docker_based") or challenge_meta.get(
        "remote_evaluation"
    ):
        logger.info(
            "Skipping challenge %s (is_docker_based=%s, remote_evaluation=%s)",
            challenge_pk,
            challenge_meta.get("is_docker_based"),
            challenge_meta.get("remote_evaluation"),
        )
        return {"statusCode": 200, "body": "Skipped non-target challenge"}

    cluster_name = challenge_meta.get("cluster_name")
    if not cluster_name:
        logger.warning("No cluster_name for challenge %s", challenge_pk)
        return {"statusCode": 200, "body": "No cluster configured"}

    pending_submissions = int(pending_data.get("pending_submissions", 0))
    scale_up_cap = int(challenge_meta.get("scale_up_cap", 1))
    aws_region = challenge_meta.get("aws_region") or AWS_REGION
    force_scale_down = _should_force_scale_down(challenge_meta)

    try:
        eks_client = _build_eks_client(aws_region, challenge_meta)
        nodegroup_name = _get_nodegroup_name(
            eks_client,
            cluster_name,
            challenge_meta.get("nodegroup_name"),
        )
        current = _get_scaling_config(eks_client, cluster_name, nodegroup_name)
        current_desired = int(current.get("desiredSize", 0))
    except (ClientError, ValueError) as err:
        logger.error(
            "Failed to fetch EKS nodegroup details for challenge %s: %s",
            challenge_pk,
            err,
        )
        raise AutoscaleError(
            "Failed to fetch EKS nodegroup for challenge {0}".format(
                challenge_pk
            )
        ) from err

    if force_scale_down or pending_submissions == 0:
        target_desired_size = 0
    elif pending_submissions > current_desired:
        target_desired_size = _desired_size_for_pending(
            pending_submissions, scale_up_cap
        )
        if target_desired_size <= current_desired:
            logger.info(
                "No scale-up needed for challenge %s (current=%s pending=%s cap=%s)",
                challenge_pk,
                current_desired,
                pending_submissions,
                scale_up_cap,
            )
            return {"statusCode": 200, "body": "No change"}
    else:
        logger.info(
            "No scale-up needed for challenge %s (current=%s pending=%s)",
            challenge_pk,
            current_desired,
            pending_submissions,
        )
        return {"statusCode": 200, "body": "No change"}

    if target_desired_size == 0:
        scaling_config = {"minSize": 0, "desiredSize": 0, "maxSize": 1}
    else:
        # maxSize must stay within the challenge's configured cap. Deriving it
        # from the raw pending count would let a submission burst raise the
        # ceiling above what the challenge host provisioned for.
        scaling_config = {
            "minSize": 1,
            "desiredSize": target_desired_size,
            "maxSize": max(target_desired_size, scale_up_cap),
        }

    if (
        current.get("minSize") == scaling_config["minSize"]
        and current.get("desiredSize") == scaling_config["desiredSize"]
        and current.get("maxSize") == scaling_config["maxSize"]
    ):
        logger.info(
            "No scaling change needed for challenge %s (desired=%s)",
            challenge_pk,
            current_desired,
        )
        return {"statusCode": 200, "body": "No change"}

    try:
        response = eks_client.update_nodegroup_config(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name,
            scalingConfig=scaling_config,
        )
    except ClientError as err:
        logger.error(
            "Failed to update EKS nodegroup for challenge %s: %s",
            challenge_pk,
            err,
        )
        raise AutoscaleError(
            "Failed to update EKS nodegroup for challenge {0}".format(
                challenge_pk
            )
        ) from err

    logger.info(
        "Updated nodegroup scaling for challenge %s from %s to %s",
        challenge_pk,
        current_desired,
        scaling_config["desiredSize"],
    )
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "challenge_pk": challenge_pk,
                "cluster_name": cluster_name,
                "nodegroup_name": nodegroup_name,
                "aws_region": aws_region,
                "pending_submissions": pending_submissions,
                "scaling_config": scaling_config,
                "update_id": response.get("update", {}).get("id"),
            }
        ),
    }


def _sweep():
    """
    Reconcile every autoscale-eligible challenge.

    One challenge failing must not stop the sweep, so per-challenge errors are
    collected and re-raised together once every challenge has been attempted.
    """
    try:
        eligible = _call_evalai_api(
            "/api/challenges/challenge/autoscale_eligible_challenges/"
        )
    except (HTTPError, URLError, TimeoutError) as err:
        logger.error("Failed to fetch autoscale-eligible challenges: %s", err)
        raise AutoscaleError(
            "Failed to fetch autoscale-eligible challenges"
        ) from err

    challenge_pks = eligible.get("challenge_pks", [])
    logger.info("Sweeping %s challenges", len(challenge_pks))

    succeeded, failed = [], []
    for challenge_pk in challenge_pks:
        try:
            _scale_challenge(challenge_pk)
            succeeded.append(challenge_pk)
        except Exception as err:
            # Deliberately broad. _scale_challenge also raises bare ValueError
            # on malformed API data (a non-numeric pending count, invalid
            # JSON), and catching only AutoscaleError would let one bad
            # challenge skip every challenge after it. logger.exception keeps
            # the traceback, which matters most for the unanticipated types
            # this catch exists to absorb.
            logger.exception(
                "Sweep failed for challenge %s: %s", challenge_pk, err
            )
            failed.append(challenge_pk)

    if failed:
        raise AutoscaleError(
            "Sweep failed for challenges: {0}".format(
                ", ".join(str(pk) for pk in failed)
            )
        )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"swept": len(succeeded), "challenge_pks": succeeded}
        ),
    }


def handler(event, context):
    """
    Lambda handler for EKS nodegroup autoscaling.

    Event payload, either a single challenge:
    {
      "challenge_pk": 123,
      "trigger_source": "submission_created|submission_status_changed|manual"
    }

    or a scheduled reconciliation sweep across all eligible challenges:
    {
      "sweep": true
    }
    """
    _validate_env()

    if event.get("sweep"):
        logger.info("Starting EKS autoscale sweep")
        return _sweep()

    challenge_pk = event.get("challenge_pk")
    if not challenge_pk:
        # A malformed payload is not retryable, so return rather than raise.
        logger.error("Missing challenge_pk in event: %s", event)
        return {"statusCode": 400, "body": "Missing challenge_pk"}

    logger.info(
        "Starting EKS autoscale for challenge_pk=%s trigger=%s",
        challenge_pk,
        event.get("trigger_source", "unknown"),
    )
    return _scale_challenge(challenge_pk)
