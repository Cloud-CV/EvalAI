import os
import json
import logging
import random
import zipfile
import string
import uuid

import yaml
from botocore.exceptions import ClientError
from moto import mock_ecr, mock_sts
from os.path import basename, isfile, join

from base.utils import get_model_object, get_boto3_client, mock_if_non_prod_aws

from .models import (
    Challenge,
    ChallengePhase,
    Leaderboard,
    DatasetSplit,
    ChallengePhaseSplit,
)

logger = logging.getLogger(__name__)

get_challenge_model = get_model_object(Challenge)

get_challenge_phase_model = get_model_object(ChallengePhase)

get_leaderboard_model = get_model_object(Leaderboard)

get_dataset_split_model = get_model_object(DatasetSplit)

get_challenge_phase_split_model = get_model_object(ChallengePhaseSplit)


def get_file_content(file_path, mode):
    if os.path.isfile(file_path):
        with open(file_path, mode) as file_content:
            return file_content.read()


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
        aws_keys = {
            "AWS_ACCOUNT_ID": challenge.aws_account_id,
            "AWS_ACCESS_KEY_ID": challenge.aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": challenge.aws_secret_access_key,
            "AWS_REGION": challenge.aws_region,
        }
    else:
        aws_keys = {
            "AWS_ACCOUNT_ID": os.environ.get(
                "AWS_ACCOUNT_ID", "aws_account_id"
            ),
            "AWS_ACCESS_KEY_ID": os.environ.get(
                "AWS_ACCESS_KEY_ID", "aws_access_key_id"
            ),
            "AWS_SECRET_ACCESS_KEY": os.environ.get(
                "AWS_SECRET_ACCESS_KEY", "aws_secret_access_key"
            ),
            "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        }
    return aws_keys


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


def get_unique_key(length):
    return "".join([random.choice(string.ascii_letters + string.digits) for i in range(length)])


def write_file(output_path, mode, file_content):
    with open(output_path, mode) as file:
        file.write(file_content)


def extract_zip_file(file_path, mode, output_path):
    zip_ref = zipfile.ZipFile(file_path, mode)
    zip_ref.extractall(output_path)
    zip_ref.close()
    return zip_ref


def get_yaml_files_from_challenge_config(zip_ref):
    yaml_file_count = 0
    for name in zip_ref.namelist():
        if (name.endswith(".yaml") or name.endswith(".yml")) and (
                not name.startswith("__MACOSX")
        ):
            yaml_file_name = name
            extracted_folder_name = yaml_file_name.split(basename(yaml_file_name))[0]
            yaml_file_count += 1

    if not yaml_file_count:
        return yaml_file_count, None, None
    return yaml_file_count, yaml_file_name, extracted_folder_name


def read_yaml_file(file_path, mode):
    with open(file_path, mode) as stream:
        yaml_file_data = yaml.safe_load(stream)
    return yaml_file_data


def get_yaml_read_error_description(exc):
    # To get the problem description
    if hasattr(exc, "problem"):
        error_description = exc.problem
        # To capitalize the first alphabet of the problem description as default is in lowercase
        error_description = error_description[0:].capitalize()
    # To get the error line and column number
    if hasattr(exc, "problem_mark"):
        mark = exc.problem_mark
        line_number = mark.line + 1
        column_number = mark.column + 1
    return error_description, line_number, column_number


def is_valid_challenge_config_yaml_field(yaml_file_data, key, base_location):
    value = yaml_file_data.get(key)
    message = ""
    is_valid = False
    is_error = False
    if value:
        file_path = join(base_location, value)
        if file_path.endswith(".html") and isfile(file_path):
            is_valid = True
        else:
            message = "WARNING: No {}.html file is present in the zip file.".format(key)
    else:
        message = "ERROR: There is no key for {} in YAML file".format(key)
        is_error = True
    return is_valid, message, is_error


def is_valid_challenge_phase_config_yaml_field(yaml_file_data, key, base_location):
    value = yaml_file_data.get(key)
    message = ""
    is_valid = False
    if value:
        file_path = join(base_location, value)
        if file_path.endswith(".html") and isfile(file_path):
            is_valid = True
        else:
            message = (" WARNING: There is no file for phase "
                       " {} in phase {}.".format(key, yaml_file_data["name"]))
    else:
        message = " ERROR: There is no key for phase {} in phase {}.".format(key, yaml_file_data["name"])
    return is_valid, message
