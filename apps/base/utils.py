import base64
import boto3
import logging
import os
import sendgrid
import uuid

from django.conf import settings
from django.utils.deconstruct import deconstructible

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

from sendgrid.helpers.mail import Email, Mail, Personalization

logger = logging.getLogger(__name__)


class StandardResultSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


def paginated_queryset(
    queryset, request, pagination_class=PageNumberPagination()
):
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
            raise NotFound(
                "{} {} does not exist".format(model_name.__name__, pk)
            )

    get_model_by_pk.__name__ = "get_{}_object".format(
        model_name.__name__.lower()
    )
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


def send_email(
    sender=settings.CLOUDCV_TEAM_EMAIL,
    recepient=None,
    template_id=None,
    template_data={},
):
    """Function to send email

    Keyword Arguments:
        sender {string} -- Email of sender (default: {settings.TEAM_EMAIL})
        recepient {string} -- Recepient email address
        template_id {string} -- Sendgrid template id
        template_data {dict} -- Dictionary to substitute values in subject and email body
    """
    try:
        sg = sendgrid.SendGridAPIClient(
            apikey=os.environ.get("SENDGRID_API_KEY")
        )
        sender = Email(sender)
        mail = Mail()
        mail.from_email = sender
        mail.template_id = template_id
        to_list = Personalization()
        to_list.dynamic_template_data = template_data
        to_email = Email(recepient)
        to_list.add_to(to_email)
        mail.add_personalization(to_list)
        sg.client.mail.send.post(request_body=mail.get())
    except Exception:
        logger.warning(
            "Cannot make sendgrid call. Please check if SENDGRID_API_KEY is present."
        )
    return


def get_url_from_hostname(hostname):
    if settings.DEBUG or settings.TEST:
        scheme = "http"
    else:
        scheme = "https"
    url = "{}://{}".format(scheme, hostname)
    return url


def get_boto3_client(resource, aws_keys):
    """
    Returns the boto3 client for a resource in AWS
    Arguments:
        resource {str} -- Name of the resource for which client is to be created
        aws_keys {dict} -- AWS keys which are to be used
    Returns:
        Boto3 client object for the resource
    """
    try:
        client = boto3.client(
            resource,
            region_name=aws_keys["AWS_REGION"],
            aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
        )
        return client
    except Exception as e:
        logger.exception(e)
