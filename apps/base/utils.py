import base64
import boto3
import botocore
import logging
import os
import uuid

from django.conf import settings
from django.utils.deconstruct import deconstructible

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)


class StandardResultSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


def paginated_queryset(queryset, request, pagination_class=PageNumberPagination()):
    """
        Return a paginated result for a queryset
    """
    paginator = pagination_class
    paginator.page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]
    result_page = paginator.paginate_queryset(queryset, request)
    return (paginator, result_page)


@deconstructible
class RandomFileName(object):
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        extension = os.path.splitext(filename)[1]
        path = self.path
        if "id" in self.path and instance.pk:
            path = self.path.format(id=instance.pk)
        filename = "{}{}".format(uuid.uuid4(), extension)
        filename = os.path.join(path, filename)
        return filename


def get_model_object(model_name):
    def get_model_by_pk(pk):
        try:
            model_object = model_name.objects.get(pk=pk)
            return model_object
        except model_name.DoesNotExist:
            raise NotFound("{} {} does not exist".format(model_name.__name__, pk))

    get_model_by_pk.__name__ = "get_{}_object".format(model_name.__name__.lower())
    return get_model_by_pk


def encode_data(data):
    """
    Turn `data` into a hash and an encoded string, suitable for use with `decode_data`.
    """
    encoded = []
    for i in data:
        encoded.append(base64.encodestring(i).split("=")[0])
    return encoded


def decode_data(data):
    """
    The inverse of `encode_data`.
    """
    decoded = []
    for i in data:
        decoded.append(base64.decodestring(i + "=="))
    return decoded


def get_sqs_queue_object():
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
        if ex.response["Error"]["Code"] != "AWS.SimpleQueueService.NonExistentQueue":
            logger.exception("Cannot get queue: {}".format(queue_name))
        queue = sqs.create_queue(QueueName=queue_name)

    return queue
