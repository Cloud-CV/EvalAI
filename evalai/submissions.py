import os

import base64
import boto3
import click
import docker
import json
import requests
import shutil
import sys
import tempfile
import urllib.parse as urlparse
import uuid

from click import echo, style

from evalai.utils.common import notify_user
from evalai.utils.requests import make_request
from evalai.utils.submissions import (
    display_submission_details,
    display_submission_result,
    convert_bytes_to,
)
from evalai.utils.urls import URLS
from evalai.utils.config import EVALAI_HOST_URLS, HOST_URL_FILE_PATH


class Submission(object):

    def __init__(self, submission_id):
        self.submission_id = submission_id


@click.group(invoke_without_command=True)
@click.argument("SUBMISSION_ID", type=int)
@click.pass_context
def submission(ctx, submission_id):
    """
    View submission specific details.
    """
    """
    Invoked by `evalai submission SUBMISSION_ID`.
    """
    ctx.obj = Submission(submission_id=submission_id)
    if ctx.invoked_subcommand is None:
        display_submission_details(submission_id)


@submission.command()
@click.pass_obj
def result(ctx):
    """
    Display the submission result
    """
    """
    Invoked by `evalai submission SUBMISSION_ID result`.
    """
    display_submission_result(ctx.submission_id)


@click.command()
@click.argument("IMAGE", nargs=1)
@click.option(
    "-p",
    "--phase",
    help="challenge-phase-name to which image is to be pushed",
    required=True,
)
def push(image, phase):
    """
    Push docker image to a particular challenge phase.
    """
    """
    Invoked by `evalai push IMAGE:TAG -p PHASE_ID`.
    """
    if len(image.split(":")) != 2:
        message = "\nError: Please enter the tag name with image.\n\nFor eg: `evalai push ubuntu:latest --phase 123`"
        notify_user(message, color="red")
        sys.exit(1)

    tag = str(uuid.uuid4())
    docker_client = docker.from_env()
    try:
        docker_image = docker_client.images.get(image)
    except docker.errors.ImageNotFound:
        message = "\nError: Image not found. Please enter the correct image name and tag."
        notify_user(message, color="red")
        sys.exit(1)

    request_path = URLS.phase_details_using_slug.value
    request_path = request_path.format(phase)
    response = make_request(request_path, "GET")
    challenge_pk = response.get("challenge")
    phase_pk = response.get("id")

    request_path = URLS.challenge_details.value
    request_path = request_path.format(challenge_pk)
    response = make_request(request_path, "GET")
    max_docker_image_size = response.get("max_docker_image_size")

    docker_image_size = docker_image.__dict__.get("attrs").get("VirtualSize")
    if docker_image_size > max_docker_image_size:
        max_docker_image_size = convert_bytes_to(max_docker_image_size, "gb")
        message = "\nError: Image is too large. The maximum image size allowed is {} GB".format(
            max_docker_image_size
        )
        notify_user(message, color="red")
        sys.exit(1)

    request_path = URLS.get_aws_credentials.value
    request_path = request_path.format(phase_pk)

    response = make_request(request_path, "GET")
    federated_user = response["success"]["federated_user"]
    repository_uri = response["success"]["docker_repository_uri"]

    AWS_ACCOUNT_ID = federated_user["FederatedUser"]["FederatedUserId"].split(
        ":"
    )[0]
    AWS_SERVER_PUBLIC_KEY = federated_user["Credentials"]["AccessKeyId"]
    AWS_SERVER_SECRET_KEY = federated_user["Credentials"]["SecretAccessKey"]
    SESSION_TOKEN = federated_user["Credentials"]["SessionToken"]

    ecr_client = boto3.client(
        "ecr",
        region_name="us-east-1",
        aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
        aws_secret_access_key=AWS_SERVER_SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
    )

    token = ecr_client.get_authorization_token(registryIds=[AWS_ACCOUNT_ID])
    ecr_client = boto3.client("ecr", region_name="us-east-1")
    username, password = (
        base64.b64decode(token["authorizationData"][0]["authorizationToken"])
        .decode()
        .split(":")
    )
    registry = token["authorizationData"][0]["proxyEndpoint"]
    docker_client.login(
        username, password, registry=registry, dockercfg_path=os.getcwd()
    )

    # Tag and push docker image and create a submission if successfully pushed
    docker_client.images.get(image).tag("{}:{}".format(repository_uri, tag))
    for line in docker_client.images.push(
        repository_uri, tag, stream=True, decode=True
    ):
        if line.get("status") in ["Pushing", "Pushed"] and line.get(
            "progress"
        ):
            print("{id}: {status} {progress}".format(**line))
        elif line.get("errorDetail"):
            error = line.get("error")
            notify_user(error, color="red")
        elif line.get("aux"):
            aux = line.get("aux")
            pushed_image_tag = aux["Tag"]
            submitted_image_uri = "{}:{}".format(
                repository_uri, pushed_image_tag
            )
            BASE_TEMP_DIR = tempfile.mkdtemp()
            data = {"submitted_image_uri": submitted_image_uri}
            submission_file_path = os.path.join(
                BASE_TEMP_DIR, "submission.json"
            )
            with open(submission_file_path, "w") as outfile:
                json.dump(data, outfile)
            request_path = URLS.make_submission.value
            request_path = request_path.format(challenge_pk, phase_pk)
            response = make_request(request_path, "POST", submission_file_path)
            shutil.rmtree(BASE_TEMP_DIR)
        else:
            print(
                " ".join(
                    "{}: {}".format(k, v)
                    for k, v in line.items()
                    if k != "progressDetail"
                )
            )


@click.command()
@click.argument("URL", nargs=1)
def download_file(url):
    parsed_url = urlparse.urlparse(url)
    parsed_host_url = "{parsed_url.scheme}://{parsed_url.netloc}".format(
        parsed_url=parsed_url
    )
    is_correct_host = False
    # TODO: Replace the hardcoded host url with cli's host url
    with open(HOST_URL_FILE_PATH, "r") as file:
        host_url = file.read()
    if parsed_host_url in EVALAI_HOST_URLS:
        is_correct_host = True
    if parsed_host_url == host_url:
        is_correct_host = True

    if is_correct_host:
        bucket = urlparse.parse_qs(parsed_url.query).get("bucket")
        key = urlparse.parse_qs(parsed_url.query).get("key")
        if not bucket or not key:
            echo(
                style(
                    "\nThe bucket or key is missing in the url.\n",
                    fg="red",
                    bold=True,
                )
            )
            sys.exit(1)
        request_path = URLS.download_file.value
        request_path = request_path.format(bucket[0], key[0])
        response = make_request(request_path, "GET")
        signed_url = response.get("signed_url")
        file_name = key[0].split("/")[-1]
        try:
            response = requests.get(signed_url, stream=True)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            echo(err)
            sys.exit(1)
        except requests.exceptions.RequestException:
            echo(
                style(
                    "\nCould not establish a connection to EvalAI."
                    " Please check the Host URL.\n",
                    bold=True,
                    fg="red",
                )
            )
            sys.exit(1)
        with open(file_name, "wb") as file:
            total_file_length = int(response.headers.get("content-length"))
            chunk_size = 1024
            with click.progressbar(
                length=total_file_length, label="Downloading file"
            ) as bar:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    bar.update(chunk_size)
            echo(
                style(
                    "\nYour file {} is successfully downloaded.\n".format(
                        file_name
                    ),
                    fg="green",
                    bold=True,
                )
            )
    else:
        echo(
            style(
                "\nThe url doesn't match the EvalAI url. Please check the url.\n",
                fg="red",
                bold=True,
            )
        )
        sys.exit(1)
