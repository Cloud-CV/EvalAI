"""
AWS Lambda function to auto-scale EKS nodegroups for EvalAI challenges.

This function is triggered asynchronously from submission lifecycle events.
It fetches challenge metadata and pending submission counts from internal
EvalAI APIs authenticated via LAMBDA_AUTH_TOKEN, then updates the challenge
EKS nodegroup scaling config accordingly.

Environment variables required:
- EVALAI_API_SERVER: EvalAI API server URL (e.g. https://eval.ai)
- LAMBDA_AUTH_TOKEN: shared secret for internal Lambda-auth APIs
- AWS_REGION: AWS region (optional, defaults to us-east-1)
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


def _get_nodegroup_name(eks_client, cluster_name):
    nodegroups = eks_client.list_nodegroups(clusterName=cluster_name).get(
        "nodegroups", []
    )
    if not nodegroups:
        raise ValueError(
            "No nodegroups found for cluster '{0}'".format(cluster_name)
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


def handler(event, context):
    """
    Lambda handler for EKS nodegroup autoscaling.

    Event payload:
    {
      "challenge_pk": 123,
      "trigger_source": "submission_created|submission_status_changed|manual"
    }
    """
    try:
        _validate_env()
    except RuntimeError as err:
        logger.error("Environment validation failed: %s", err)
        return {"statusCode": 500, "body": str(err)}

    challenge_pk = event.get("challenge_pk")
    if not challenge_pk:
        logger.error("Missing challenge_pk in event: %s", event)
        return {"statusCode": 400, "body": "Missing challenge_pk"}

    logger.info(
        "Starting EKS autoscale for challenge_pk=%s trigger=%s",
        challenge_pk,
        event.get("trigger_source", "unknown"),
    )

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
        return {"statusCode": 502, "body": "Failed to fetch autoscale data"}

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
        eks_client = boto3.client("eks", region_name=aws_region)
        nodegroup_name = _get_nodegroup_name(eks_client, cluster_name)
        current = _get_scaling_config(eks_client, cluster_name, nodegroup_name)
        current_desired = int(current.get("desiredSize", 0))
    except (ClientError, ValueError) as err:
        logger.error(
            "Failed to fetch EKS nodegroup details for challenge %s: %s",
            challenge_pk,
            err,
        )
        return {"statusCode": 500, "body": "Failed to fetch EKS nodegroup"}

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
        scaling_config = {
            "minSize": 1,
            "desiredSize": target_desired_size,
            "maxSize": max(target_desired_size, pending_submissions),
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
        return {"statusCode": 500, "body": "Failed to update EKS nodegroup"}

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
