import base64
import json
import logging
import os
import re
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import boto3
import botocore
import requests
import sendgrid
from django.conf import settings
from django.db import models
from django.utils.deconstruct import deconstructible
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from sendgrid.helpers.mail import Email, Mail, Personalization

from settings.common import SQS_RETENTION_PERIOD

logger = logging.getLogger(__name__)


class StandardResultSetPagination(PageNumberPagination):
    """Standard pagination class for API results."""
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


def paginated_queryset(
        queryset: models.QuerySet,
        request: Request,
        pagination_class: PageNumberPagination = PageNumberPagination()
) -> Tuple[PageNumberPagination, List[Any]]:
    """
    Return a paginated result for a queryset.

    Args:
        queryset (models.QuerySet): The queryset to paginate
        request (Request): The request object
        pagination_class (PageNumberPagination): The pagination class to use

    Returns:
        Tuple[PageNumberPagination, List[Any]]: (paginator, result_page)
    """
    paginator = pagination_class
    paginator.page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]
    result_page = paginator.paginate_queryset(queryset, request)
    return (paginator, result_page)


def team_paginated_queryset(
        queryset: models.QuerySet,
        request: Request,
        pagination_class: PageNumberPagination = PageNumberPagination()
) -> Tuple[PageNumberPagination, List[Any]]:
    """
    Return a paginated result for a team queryset.

    Args:
        queryset (models.QuerySet): The queryset to paginate
        request (Request): The request object
        pagination_class (PageNumberPagination): The pagination class to use

    Returns:
        Tuple[PageNumberPagination, List[Any]]: (paginator, result_page)
    """
    paginator = pagination_class
    paginator.page_size = settings.REST_FRAMEWORK["TEAM_PAGE_SIZE"]
    result_page = paginator.paginate_queryset(queryset, request)
    return (paginator, result_page)


@deconstructible
class RandomFileName:
    """Generate a random filename for uploaded files."""

    def __init__(self, path: str) -> None:
        """
        Initialize with the path pattern.

        Args:
            path (str): Path pattern to use
        """
        self.path = path

    def __call__(self, instance: models.Model, filename: str) -> str:
        """
        Generate a random filename.

        Args:
            instance (models.Model): The model instance
            filename (str): Original filename

        Returns:
            str: Generated filename
        """
        extension = os.path.splitext(filename)[1]
        path = self.path
        if "id" in self.path and instance.pk:
            path = self.path.format(id=instance.pk)
        filename = f"{uuid.uuid4()}{extension}"
        filename = os.path.join(path, filename)
        return filename


def get_model_object(model_name: models.Model):
    """
    Return a function that gets a model object by its primary key.

    Args:
        model_name (models.Model): The model class

    Returns:
        function: Function to get model object by pk
    """

    def get_model_by_pk(pk):
        try:
            model_object = model_name.objects.get(pk=pk)
            return model_object
        except model_name.DoesNotExist as exc:
            raise NotFound(
                f"{model_name.__name__} {pk} does not exist"
            ) from exc

    get_model_by_pk.__name__ = f"get_{model_name.__name__.lower()}_object"
    return get_model_by_pk


def encode_data(data: List[bytes]) -> List[str]:
    """
    Turn `data` into a hash and an encoded string,
    suitable for use with `decode_data`.

    Args:
        data (List[bytes]): Data to encode

    Returns:
        List[str]: Encoded data
    """
    encoded = []
    for i in data:
        encoded.append(base64.encodestring(i).split("=")[0])
    return encoded


def decode_data(data: List[str]) -> List[bytes]:
    """
    The inverse of `encode_data`.

    Args:
        data (List[str]): Data to decode

    Returns:
        List[bytes]: Decoded data
    """
    decoded = []
    for i in data:
        decoded.append(base64.decodestring(i + "=="))
    return decoded


def send_email(
        sender: str = settings.CLOUDCV_TEAM_EMAIL,
        recipient: Optional[str] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Function to send email.

    Args:
        sender (str): Email of sender (default: settings.TEAM_EMAIL)
        recipient (Optional[str]): Recipient email address
        template_id (Optional[str]): Sendgrid template id
        template_data (Optional[Dict[str, Any]]):
         Dictionary to substitute values in subject and email body
    """
    if template_data is None:
        template_data = {}

    try:
        sg = sendgrid.SendGridAPIClient(
            api_key=os.environ.get("SENDGRID_API_KEY")
        )
        sender = Email(sender)
        mail = Mail()
        mail.from_email = sender
        mail.template_id = template_id
        to_list = Personalization()
        to_list.dynamic_template_data = template_data
        to_email = Email(recipient)
        to_list.add_to(to_email)
        mail.add_personalization(to_list)
        sg.client.mail.send.post(request_body=mail.get())
    except Exception:
        logger.warning(
            "Cannot make sendgrid call. "
            "Please check if SENDGRID_API_KEY is present."
        )


def get_url_from_hostname(hostname: str) -> str:
    """
    Generate URL from hostname based on environment.

    Args:
        hostname (str): The hostname

    Returns:
        str: Complete URL
    """
    if settings.DEBUG or settings.TEST:
        scheme = "http"
    else:
        scheme = "https"
    return f"{scheme}://{hostname}"


def get_boto3_client(resource: str, aws_keys: Dict[str, str]):
    """
    Returns the boto3 client for a resource in AWS.

    Args:
        resource (str): Name of the resource for which client is to be created
        aws_keys (Dict[str, str]): AWS keys which are to be used

    Returns:
        Optional[boto3.client]:
        Boto3 client object for the resource or None if exception occurs
    """
    try:
        client = boto3.client(
            resource,
            region_name=aws_keys["AWS_REGION"],
            aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
        )
        return client
    except Exception as exc:
        logger.exception(exc)
        return None


def get_or_create_sqs_queue(queue_name: str, challenge: Optional[Any] = None):
    """
    Get or create SQS queue.

    Args:
        queue_name (str): Name of the queue
        challenge (Optional[Any]): 
        Challenge object if queue is challenge-specific

    Returns:
        boto3.resources.factory.sqs.Queue: SQS queue object
    """
    if settings.DEBUG or settings.TEST:
        queue_name = "evalai_submission_queue"
        sqs = boto3.resource(
            "sqs",
            endpoint_url=os.environ.get("AWS_SQS_ENDPOINT", "http://sqs:9324"),
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "x"),
        )
    else:
        if challenge and challenge.use_host_sqs:
            sqs = boto3.resource(
                "sqs",
                region_name=challenge.queue_aws_region,
                aws_secret_access_key=challenge.aws_secret_access_key,
                aws_access_key_id=challenge.aws_access_key_id,
            )
        else:
            sqs = boto3.resource(
                "sqs",
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            )
    # Check if the queue exists. If no, then create one
    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as ex:
        if (
                ex.response["Error"]["Code"]
                != "AWS.SimpleQueueService.NonExistentQueue"
        ):
            logger.exception("Cannot get queue: %s", queue_name)
        sqs_retention_period = (
            SQS_RETENTION_PERIOD
            if challenge is None
            else str(challenge.sqs_retention_period)
        )
        queue = sqs.create_queue(
            QueueName=queue_name,
            Attributes={"MessageRetentionPeriod": sqs_retention_period},
        )
    return queue


def get_slug(param: str) -> str:
    """
    Generate a slug from a string.

    Args:
        param (str): String to convert to slug

    Returns:
        str: Generated slug
    """
    slug = param.replace(" ", "-").lower()
    slug = re.sub(r"\W+", "-", slug)
    slug = slug[:180]
    # Max-length for slug is 200, but 180 is used to append pk
    return slug


def get_queue_name(param: str, challenge_pk: int) -> str:
    """
    Generate unique SQS queue name of max length 80 for a challenge.

    Args:
        param (str): Challenge title
        challenge_pk (int): Challenge primary key

    Returns:
        str: Unique queue name
    """
    # The max-length for queue-name is 80 in SQS
    max_len = 80
    max_challenge_title_len = 50

    env = settings.ENVIRONMENT
    queue_name = param.replace(" ", "-").lower()[:max_challenge_title_len]
    queue_name = re.sub(r"\W+", "-", queue_name)

    queue_name = f"{queue_name}-{challenge_pk}-{env}-{uuid.uuid4()}"[:max_len]
    return queue_name


def send_slack_notification(webhook: str = settings.SLACK_WEB_HOOK_URL,
                            message: Dict[str, Any] = "") -> Optional[
                                requests.Response]:
    """
    Send slack notification to any workspace.

    Args:
        webhook (str): Slack webhook URL
        message (Dict[str, Any]): JSON/Text message to be sent to slack

    Returns:
        Optional[requests.Response]:
        Response object from request or None on error
    """
    try:
        data = {
            "attachments":
                [{"color": "ffaf4b", "fields": message["fields"]}],
            "icon_url":
                "https://eval.ai/dist/images/evalai-logo-single.png",
            "text": message["text"],
            "username": "EvalAI",
        }
        return requests.post(
            webhook,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
    except Exception as exc:
        logger.exception("Exception raised while "
                         "sending slack notification. "
                         "\n Exception message: %s", exc)
        return None


def mock_if_non_prod_aws(aws_mocker: callable):
    """
    Decorator to mock AWS in non-production environments.

    Args:
        aws_mocker (callable): Function to use as a mocker

    Returns:
        Function: Original or mocked function
    """

    def decorator(func):
        if not (settings.DEBUG or settings.TEST):
            return func
        return aws_mocker(func)

    return decorator


@contextmanager
def suppress_autotime(model: models.Model, fields: List[str]):
    """
    Context manager to temporarily disable auto_now and auto_now_add.

    Args:
        model (models.Model): Model class
        fields (List[str]): Fields to modify

    Note:
        This function accesses protected members (_meta) of Django models
        which is necessary for this functionality.
    """
    _original_values = {}
    for field in model._meta.local_fields:
        if field.name in fields:
            _original_values[field.name] = {
                "auto_now": field.auto_now,
                "auto_now_add": field.auto_now_add,
            }
            field.auto_now = False
            field.auto_now_add = False
    try:
        yield
    finally:
        for field in model._meta.local_fields:
            if field.name in fields:
                field.auto_now = _original_values[field.name]["auto_now"]
                field.auto_now_add = _original_values[field.name][
                    "auto_now_add"
                ]


def is_model_field_changed(model_obj: models.Model, field_name: str) -> bool:
    """
    Function to check if a model field is changed or not.

    Args:
        model_obj (models.Model): Models.model class object
        field_name (str): Field which needs to be checked

    Returns:
        bool: True/False if the model is changed or not
    """
    prev = getattr(model_obj, f"_original_{field_name}")
    curr = getattr(model_obj, f"{field_name}")
    if prev != curr:
        return True
    return False


def is_user_a_staff(user: models.Model) -> bool:
    """
    Function to check if a user is staff or not.

    Args:
        user (models.Model): User model class object

    Returns:
        bool: True/False if the user is staff or not
    """
    return user.is_staff
