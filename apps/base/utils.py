import base64
import os
import sendgrid
import uuid

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.deconstruct import deconstructible

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

from sendgrid.helpers.mail import Email, Content, Mail


class StandardResultSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


<<<<<<< HEAD
def paginated_queryset(
    queryset, request, pagination_class=PageNumberPagination()
):
=======
def paginated_queryset(queryset, request, pagination_class=PageNumberPagination()):
>>>>>>> Add feature to invite users via email by challenge host
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


def send_email(subject, template, sender_email, to_email, context):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get("SENDGRID_API_KEY"))
    sender_email = Email(sender_email)
    to_email = Email(to_email)
    subject = subject
    body = render_to_string(template, context)
    content = Content("text/html", body)
    mail = Mail(sender_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    if response.status_code == 202 or response.status_code == 200:
        return response.status_code
    return response
