import boto3

from botocore.exceptions import ClientError

from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.template.loader import get_template
from django.template import Context

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage

from .models import Team
from .serializers import ContactSerializer, TeamSerializer

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle


def home(request, template_name="index.html"):
    """
    Home Page View
    """
    return render(request, template_name)


def page_not_found(request):
    response = render(request, 'error404.html',
                      )
    response.status_code = 404
    return response


def internal_server_error(request):
    response = render(request, 'error500.html',
                      )
    response.status_code = 500
    return response


def notify_users_about_challenge(request):
    """
    Email New Challenge Details to EvalAI Users
    """
    if request.user.is_authenticated() and request.user.is_superuser:
        if request.method == 'GET':
            template_name = 'notification_email_data.html'
            return render(request, template_name)

        elif request.method == 'POST':
            emails = User.objects.all().exclude(email__isnull=True, email__exact='').values_list('email', flat=True)

            SUBJECT = request.POST.get('subject')
            BODY_HTML = request.POST.get('body')

            try:
                challenge_image = request.FILES['challenge_image']
            except:
                challenge_image = None

            if challenge_image:
                image = MIMEImage(challenge_image.read())
                image.add_header('Content-ID', '<{}>'.format(challenge_image))

            AWS_REGION = "us-west-2"
            CHARSET = "utf-8"
            msg = MIMEMultipart('mixed')

            SENDER = settings.EMAIL_HOST_USER
            RECIPIENT = 'rishabhjain2018@gmail.com'


            client = boto3.client('ses', region_name=AWS_REGION)
            msg['subject'] = SUBJECT
            msg['From'] = SENDER
            msg['To'] = RECIPIENT

            msg_body = MIMEMultipart('alternative')
            htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
            msg_body.attach(htmlpart)

            print "222222222"
            if challenge_image:
                msg.attach(image)


            try:
                response = client.send_raw_email(
                    Source=SENDER,
                    Destinations=[
                    RECIPIENT],
                    RawMessage={
                    'Data':msg.as_string(),
                    })
                print "SENT EMAIL"
                return render(request,
                              'notification_email_conformation.html',
                              {'message': 'All the emails are sent successfully!'})
            except ClientError as e:
                print e.response['Error']['Message']
        else:
            return render(request, 'error404.html')
    else:
        return render(request, 'error404.html')


@throttle_classes([AnonRateThrottle, ])
@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def contact_us(request):
    user_does_not_exist = False
    try:
        user = User.objects.get(username=request.user)
        name = user.username
        email = user.email
        request_data = {'name': name, 'email': email}
    except:
        request_data = request.data
        user_does_not_exist = True

    if request.method == 'POST' or user_does_not_exist:
        if request.POST.get('message'):
            request_data['message'] = request.POST.get('message')
        serializer = ContactSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'message': 'We have received your request and will contact you shortly.'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        response_data = {"name": name, "email": email}
        return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([AnonRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def our_team(request):
    if request.method == 'GET':
        teams = Team.objects.all()
        serializer = TeamSerializer(teams, many=True, context={'request': request})
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # team_type is set to Team.CONTRIBUTOR by default and can be overridden by the requester
        request.data['team_type'] = request.data.get('team_type', Team.CONTRIBUTOR)
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'message', 'Successfully added the contributor.'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
