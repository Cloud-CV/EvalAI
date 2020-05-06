import base64
import boto3
import re
from botocore.signers import RequestSigner

from challenges.utils import get_aws_credentials_for_challenge


def generate_aws_eks_bearer_token(cluster_name, challenge):
    """Function to generate the AWS EKS bearer Token

    Arguments:
        cluster_name {string} -- Cluster name for which the object is generated
        challenge {Object} -- Challenge Object

    Returns:
        {string} -- Generated bearer token
    """
    challenge_pk = challenge.id
    aws_keys = get_aws_credentials_for_challenge(challenge_pk)
    session = boto3.Session(
        aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
    )
    region = aws_keys["AWS_REGION"]
    client = session.client("sts", region_name=region)
    service_id = client.meta.service_model.service_id
    signer = RequestSigner(
        service_id,
        region,
        "sts",
        "v4",
        session.get_credentials(),
        session.events,
    )
    params = {
        "method": "GET",
        "url": "https://sts.{}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15".format(
            region
        ),
        "body": {},
        "headers": {"x-k8s-aws-id": cluster_name},
        "context": {},
    }
    signed_url = signer.generate_presigned_url(
        params, region_name=region, expires_in=60, operation_name=""
    )
    base64_url = base64.urlsafe_b64encode(signed_url.encode("utf-8")).decode(
        "utf-8"
    )
    # remove any base64 encoding padding
    bearer_token = "k8s-aws-v1." + re.sub(r"=*", "", base64_url)
    return bearer_token
