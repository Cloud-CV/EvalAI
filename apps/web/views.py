import logging
import traceback
from base.utils import send_slack_notification
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import render

from smtplib import SMTPException
from .models import Subscribers, Team
from .serializers import ContactSerializer, SubscribeSerializer, TeamSerializer

from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

logger = logging.getLogger(__name__)


def home(request, template_name="index.html"):
    """
    Home Page View
    """
    return render(request, template_name)


def page_not_found(request, exception):
    response = render(request, "error404.html")
    response.status_code = 404
    return response


def internal_server_error(request):
    response = render(request, "error500.html")
    response.status_code = 500
    return response


def notify_users_about_challenge(request):
    """
    Email New Challenge Details to EvalAI Users
    """
    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "GET":
            template_name = "notification_email_data.html"
            return render(request, template_name)

        elif request.method == "POST":
            users = User.objects.exclude(email__exact="").values_list(
                "email", flat=True
            )
            subject = request.POST.get("subject")
            body_html = request.POST.get("body")

            sender = settings.CLOUDCV_TEAM_EMAIL

            email = EmailMessage(
                subject,
                body_html,
                sender,
                [settings.CLOUDCV_TEAM_EMAIL],
                bcc=users,
            )
            email.content_subtype = "html"

            try:
                email.send()
                return render(
                    request,
                    "notification_email_conformation.html",
                    {"message": "All the emails are sent successfully!"},
                )
            except SMTPException:
                logger.exception(traceback.format_exc())
                return render(
                    request, "notification_email_data.html", {"errors": 1}
                )
        else:
            return render(request, "error404.html")
    else:
        return render(request, "error404.html")


@api_view(["GET", "POST"])
@throttle_classes([AnonRateThrottle])
@permission_classes((permissions.AllowAny,))
def contact_us(request):
    user_does_not_exist = False
    try:
        user = User.objects.get(username=request.user)
        name = user.username
        email = user.email
        request_data = {"name": name, "email": email}
    except User.DoesNotExist:
        request_data = request.data
        user_does_not_exist = True

    if request.method == "POST" or user_does_not_exist:
        if request.data.get("message"):
            request_data["message"] = request.data.get("message")
        serializer = ContactSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
            response_data = {
                "message": "We have received your request and will contact you shortly."
            }

            if not settings.DEBUG:
                message = {
                    "text": "A *contact message* is received!",
                    "fields": [
                        {
                            "title": "Name",
                            "value": request.data["name"],
                            "short": True,
                        },
                        {
                            "title": "Email",
                            "value": request.data["email"],
                            "short": True,
                        },
                        {
                            "title": "Message",
                            "value": request.data["message"],
                            "short": False,
                        },
                    ],
                }
                send_slack_notification(message=message)
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "GET":
        response_data = {"name": name, "email": email}
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@throttle_classes([AnonRateThrottle])
@permission_classes((permissions.AllowAny,))
def subscribe(request):
    if request.method == "GET":
        subscribers = Subscribers.objects.all().order_by("-pk")
        serializer = SubscribeSerializer(
            subscribers, many=True, context={"request": request}
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    elif request.method == "POST":
        email = request.data.get("email")
        # When user has already subscribed
        if Subscribers.objects.filter(email=email).exists():
            response_data = {
                "message": "You have already subscribed to EvalAI"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubscribeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {
                "message",
                "You will be notified about our latest updates at {}.".format(
                    email
                ),
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@throttle_classes([AnonRateThrottle])
@permission_classes((permissions.AllowAny,))
def our_team(request):
    if request.method == "GET":
        teams = Team.objects.all().order_by("position")
        serializer = TeamSerializer(
            teams, many=True, context={"request": request}
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    elif request.method == "POST":
        # team_type is set to Team.CONTRIBUTOR by default and can be overridden by the requester
        request.data["team_type"] = request.data.get(
            "team_type", Team.CONTRIBUTOR
        )
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {"message", "Successfully added the contributor."}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
