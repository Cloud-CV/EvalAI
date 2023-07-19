import os
import json
import logging
import random
import string
import uuid

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from moto import mock_ecr, mock_sts

from base.utils import (
    get_model_object,
    get_boto3_client,
    mock_if_non_prod_aws,
    send_email,
)

from .models import (
    Challenge,
    ChallengePhase,
    Leaderboard,
    DatasetSplit,
    ChallengePhaseSplit,
    ParticipantTeam,
)

logger = logging.getLogger(__name__)

get_challenge_model = get_model_object(Challenge)

get_challenge_phase_model = get_model_object(ChallengePhase)

get_leaderboard_model = get_model_object(Leaderboard)

get_dataset_split_model = get_model_object(DatasetSplit)

get_challenge_phase_split_model = get_model_object(ChallengePhaseSplit)

get_participant_model = get_model_object(ParticipantTeam)


def get_missing_keys_from_dict(dictionary, keys):
    """
    Function to get a list of missing keys from a python dict.

    Parameters:
    dict: keys-> 'dictionary': A python dictionary.
                 'keys': List of keys to check for in the dictionary.

    Returns:
    list: A list of keys missing from the dictionary object.
    """
    missing_keys = []
    for key in keys:
        if key not in dictionary.keys():
            missing_keys.append(key)
    return missing_keys


def get_file_content(file_path, mode):
    if os.path.isfile(file_path):
        with open(file_path, mode) as file_content:
            return file_content.read()


def read_file_data_as_content_file(file_path, mode, name):
    content_file = ContentFile(get_file_content(file_path, mode), name)
    return content_file


def convert_to_aws_ecr_compatible_format(string):
    """Make string compatible with AWS ECR repository naming

    Arguments:
        string {string} -- Desired ECR repository name

    Returns:
        string -- Valid ECR repository name
    """
    return string.replace(" ", "-").lower()


def convert_to_aws_federated_user_format(string):
    """Make string compatible with AWS ECR repository naming

    Arguments:
        string {string} -- Desired ECR repository name

    Returns:
        string -- Valid ECR repository name
    """
    string = string.replace(" ", "-")
    result = ""
    for ch in string:
        if ch.isalnum() or ch in ["=", ",", ".", "@", "-"]:
            result += ch
    return result


def get_aws_credentials_for_challenge(challenge_pk):
    """
    Return the AWS credentials for a challenge using challenge pk
    Arguments:
        challenge_pk {int} -- challenge pk for which credentails are to be fetched
    Returns:
        aws_key {dict} -- Dict containing aws keys for a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    if challenge.use_host_credentials:
        # TODO - Add storage bucket name field in django models
        aws_keys = {
            "AWS_ACCOUNT_ID": challenge.aws_account_id,
            "AWS_ACCESS_KEY_ID": challenge.aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": challenge.aws_secret_access_key,
            "AWS_REGION": challenge.aws_region,
            "AWS_STORAGE_BUCKET_NAME": "",
        }
    else:
        aws_keys = {
            "AWS_ACCOUNT_ID": settings.AWS_ACCOUNT_ID,
            "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
            "AWS_REGION": settings.AWS_REGION,
            "AWS_STORAGE_BUCKET_NAME": settings.AWS_STORAGE_BUCKET_NAME,
        }
    return aws_keys


def generate_presigned_url(file_key_on_s3, challenge_pk):
    """
    Function to get the presigned url to upload a file to s3
    Arguments:
        file_key_on_s3 {string} -- The S3 key for the file to be uploaded
        challenge_pk {int} -- challenge pk for which credentails are to be fetched
    Returns:
        response_data {dict} -- Dict containing the presigned_url or the error if request failed
    """
    if settings.DEBUG or settings.TEST:
        return

    try:
        aws_keys = get_aws_credentials_for_challenge(challenge_pk)

        s3 = get_boto3_client("s3", aws_keys)
        response = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": aws_keys["AWS_STORAGE_BUCKET_NAME"],
                "Key": file_key_on_s3,
            },
            ExpiresIn=settings.PRESIGNED_URL_EXPIRY_TIME,
            HttpMethod="PUT",
        )
        response_data = {"presigned_url": response}
        return response_data
    except Exception as e:
        logger.exception(e)
        response_data = {"error": "Could not fetch presigned url."}
        return response_data


def generate_presigned_url_for_multipart_upload(
    file_key_on_s3, challenge_pk, num_parts
):
    """
    Function to get the presigned urls to upload a file to s3 in chunks
    Arguments:
        file_key_on_s3 {string} -- The S3 key for the file to be uploaded
        challenge_pk {int} -- challenge pk for which credentails are to be fetched
    Returns:
        response_data {dict} -- Dict containing the presigned_urls or the error if request failed
    """
    if settings.DEBUG:
        return
    response_data = {}
    try:
        aws_keys = get_aws_credentials_for_challenge(challenge_pk)

        s3 = get_boto3_client("s3", aws_keys)
        response = s3.create_multipart_upload(
            Bucket=aws_keys["AWS_STORAGE_BUCKET_NAME"],
            Key=file_key_on_s3,
            ACL="public-read",
        )

        upload_id = response["UploadId"]
        presigned_urls = []
        for part_number in range(1, num_parts + 1):
            presigned_url = s3.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": aws_keys["AWS_STORAGE_BUCKET_NAME"],
                    "Key": file_key_on_s3,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=settings.PRESIGNED_URL_EXPIRY_TIME,
            )
            presigned_urls.append(
                {"partNumber": part_number, "url": presigned_url}
            )
        response_data = {
            "presigned_urls": presigned_urls,
            "upload_id": upload_id,
        }
    except Exception as e:
        logger.exception(e)
        response_data = {"error": "Could not fetch presigned urls."}
    return response_data


def complete_s3_multipart_file_upload(
    parts, upload_id, file_key_on_s3, challenge_pk
):
    """
    Function to complete the multipart upload of s3 files using presigned urls
    Arguments:
        parts {List} -- List of S3 ETag and PartNumber for each uploaded chunk
        upload_id {string} -- Unique upload id for multipart file upload
        file_key_on_s3 {string} -- The S3 key for the file to be uploaded
        challenge_pk {int} -- challenge pk for which credentails are to be fetched
    Returns:
        response_data {dict} -- Dict containing the presigned_urls or the error if request failed
    """
    if settings.DEBUG:
        return
    response_data = {}
    try:
        aws_keys = get_aws_credentials_for_challenge(challenge_pk)

        s3 = get_boto3_client("s3", aws_keys)
        response_data = s3.complete_multipart_upload(
            Bucket=aws_keys["AWS_STORAGE_BUCKET_NAME"],
            Key=file_key_on_s3,
            MultipartUpload={"Parts": parts},
            UploadId=upload_id,
        )
    except Exception as e:
        logger.exception(e)
        response_data = {"error": "Could not fetch presigned urls."}
    return response_data


def get_or_create_ecr_repository(name, aws_keys):
    """Get or create AWS ECR Repository

    Arguments:
        name {string} -- name of ECR repository

    Keyword Arguments:
        aws_keys {dict} -- AWS keys where the ECR repositories will be created

    Returns:
        tuple -- Contains repository dict and boolean field to represent whether ECR repository was created
        Eg: (
                {
                    'repositoryArn': 'arn:aws:ecr:us-east-1:1234567890:repository/some-repository-name',
                    'registryId': '1234567890',
                    'repositoryName': 'some-repository-name',
                    'repositoryUri': '1234567890.dkr.ecr.us-east-1.amazonaws.com/some-repository-name',
                    'createdAt': datetime.datetime(2019, 2, 6, 9, 12, 5, tzinfo=tzlocal())
                },
                False
            )
    """
    repository, created = None, False
    client = get_boto3_client("ecr", aws_keys)
    try:
        response = client.describe_repositories(
            registryId=aws_keys.get("AWS_ACCOUNT_ID"), repositoryNames=[name]
        )
        repository = response["repositories"][0]
    except ClientError as e:
        if (
            e.response["Error"]["Code"] == "RepositoryNotFoundException"
            or e.response["Error"]["Code"] == "400"
        ):
            response = client.create_repository(repositoryName=name)
            repository = response["repository"]
            created = True
        else:
            logger.exception(e)
    return (repository, created)


def create_federated_user(name, repository, aws_keys):
    """Create AWS federated user

    Arguments:
        name {string} -- Name of participant team for which federated user is to be created
        repository {string} -- Name of the AWS ECR repository to which user should be granted permission

    Returns:
        dict -- Dict containing user related credentials such as access_key_id, access_secret etc.
        Eg:
        {
            'Credentials': {
                'AccessKeyId': 'ABCDEFGHIJKLMNOPQRTUVWXYZ',
                'SecretAccessKey': 'NMgBB75gfVBCDEFGHIJK8g00qVyyzQW+4XjJGQALMNOPQRSTUV',
                'SessionToken': 'FQoGZX.....',
                'Expiration': datetime.datetime(2019, 2, 7, 5, 43, 58, tzinfo=tzutc())
            },
            'FederatedUser': {
                'FederatedUserId': '1234567890:test-user',
                'Arn': 'arn:aws:sts::1234567890:federated-user/test-user'
            },
            'PackedPolicySize': 28,
            'ResponseMetadata': {
                'RequestId': 'fb47f78b-2a92-11e9-84b9-33527429b818',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {
                'x-amzn-requestid': 'fb47f78b-2a92-11e9-84b9-33527429b818',
                'content-type': 'text/xml',
                'content-length': '1245',
                'date': 'Thu, 07 Feb 2019 04:43:57 GMT'
                },
                'RetryAttempts': 0
            }
        }
    """
    AWS_ACCOUNT_ID = aws_keys.get("AWS_ACCOUNT_ID")
    AWS_REGION = aws_keys.get("AWS_REGION")
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ecr:*",
                "Resource": "arn:aws:ecr:{}:{}:repository/{}".format(
                    AWS_REGION, AWS_ACCOUNT_ID, repository
                ),
            },
            {
                "Effect": "Allow",
                "Action": ["ecr:GetAuthorizationToken"],
                "Resource": "*",
            },
        ],
    }
    client = get_boto3_client("sts", aws_keys)
    response = client.get_federation_token(
        Name=convert_to_aws_federated_user_format(name),
        Policy=json.dumps(policy),
        DurationSeconds=43200,
    )
    return response


@mock_if_non_prod_aws(mock_ecr)
@mock_if_non_prod_aws(mock_sts)
def get_aws_credentials_for_submission(challenge, participant_team):
    """
    Method to generate AWS Credentails for CLI's Push
    Wrappers:
        - mock_ecr: To mock ECR requests to generate ecr credemntials
        - mock_sts: To mock STS requests to generated federated user
    Args:
        - challenge: Challenge model
        - participant_team: Participant Team Model
    Returns:
        - dict: {
            "federated_user"
            "docker_repository_uri"
        }
    """
    aws_keys = get_aws_credentials_for_challenge(challenge.pk)
    ecr_repository_name = "{}-participant-team-{}".format(
        challenge.slug, participant_team.pk
    )
    ecr_repository_name = convert_to_aws_ecr_compatible_format(
        ecr_repository_name
    )
    repository, created = get_or_create_ecr_repository(
        ecr_repository_name, aws_keys
    )
    name = str(uuid.uuid4())[:32]
    docker_repository_uri = repository["repositoryUri"]
    federated_user = create_federated_user(name, ecr_repository_name, aws_keys)
    return {
        "federated_user": federated_user,
        "docker_repository_uri": docker_repository_uri,
    }


def is_user_in_allowed_email_domains(email, challenge_pk):
    challenge = get_challenge_model(challenge_pk)
    for domain in challenge.allowed_email_domains:
        if domain.lower() in email.lower():
            return True
    return False


def is_user_in_blocked_email_domains(email, challenge_pk):
    challenge = get_challenge_model(challenge_pk)
    for domain in challenge.blocked_email_domains:
        domain = "@" + domain
        if domain.lower() in email.lower():
            return True
    return False


def get_unique_alpha_numeric_key(length):
    """
    Returns unique alpha numeric key of length
    Arguments:
        length {int} -- length of unique key to generate
    Returns:
        key {string} -- unique alpha numeric key of length
    """
    return "".join(
        [
            random.choice(string.ascii_letters + string.digits)
            for i in range(length)
        ]
    )


def get_challenge_template_data(challenge):
    """
    Returns a dict for sendgrid email template data
    Arguments:
        challenge {Class Object} -- Challenge model object
    Returns:
        template_data {dict} -- a dict for sendgrid email template data
    """
    challenge_url = "{}/web/challenges/challenge-page/{}".format(
        settings.EVALAI_API_SERVER, challenge.id
    )
    challenge_manage_url = "{}/web/challenges/challenge-page/{}/manage".format(
        settings.EVALAI_API_SERVER, challenge.id
    )
    template_data = {
        "CHALLENGE_NAME": challenge.title,
        "CHALLENGE_URL": challenge_url,
        "CHALLENGE_MANAGE_URL": challenge_manage_url,
    }
    return template_data


def send_emails(emails, template_id, template_data):
    """
    Sends email to list of users using provided template
    Arguments:
        emails {list} -- recepient email ids
        template_id {string} -- sendgrid template id
        template_data {dict} -- sendgrid email template data
    """
    for email in emails:
        send_email(
            sender=settings.CLOUDCV_TEAM_EMAIL,
            recipient=email,
            template_id=template_id,
            template_data=template_data,
        )


def parse_submission_meta_attributes(submission):
    """
    Extracts submission attributes into Dict
    Arguments:
        submission {dict} -- Serialized submission object
    Returns:
        submission_meta_attributes {dict} -- a dict of submission meta attributes
    """
    submission_meta_attributes = {}
    if submission["submission_metadata"] is None:
        return {}
    for meta_attribute in submission["submission_metadata"]:
        if meta_attribute["type"] == "checkbox":
            submission_meta_attributes[
                meta_attribute["name"]
            ] = meta_attribute.get("values")
        else:
            submission_meta_attributes[
                meta_attribute["name"]
            ] = meta_attribute.get("value")
    return submission_meta_attributes


def add_tags_to_challenge(yaml_file_data, challenge):
    if "tags" in yaml_file_data:
        tags_data = yaml_file_data["tags"]
        new_tags = set(tags_data)
        # Remove tags not present in the YAML file
        challenge.list_tags = [tag for tag in challenge.list_tags if tag in new_tags]

        # Add new tags to the challenge
        for tag_name in new_tags:
            if tag_name not in challenge.list_tags:
                challenge.list_tags.append(tag_name)
    else:
        # Remove all existing tags if no tags are defined in the YAML file
        challenge.list_tags = []


def add_domain_to_challenge(yaml_file_data, challenge):
    if "domain" in yaml_file_data:
        domain_value = yaml_file_data["domain"]
        valid_domains = [choice[0] for choice in challenge.DOMAIN_OPTIONS]
        if domain_value in valid_domains:
            challenge.domain = domain_value
            challenge.save()
        else:
            message = f"Invalid domain value: {domain_value}, valid values are: {valid_domains}"
            response_data = {"error": message}
            return response_data
    else:
        challenge.domain = None
        challenge.save()
