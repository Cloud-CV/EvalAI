from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.template.loader import get_template
from django.template import Context

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
            template_name = 'notification_email.html'
            emails = User.objects.all().exclude(email__isnull=True, email__exact='').values_list('email', flat=True)
            htmly = get_template('notification_email.html')

            subject = request.POST.get('subject')
            body = request.POST.get('body')

            try:
                challenge_image = request.FILES['challenge_image']
            except:
                challenge_image = None

            if challenge_image:
                image = MIMEImage(challenge_image.read())
                image.add_header('Content-ID', '<{}>'.format(challenge_image))

            context = Context({'body': body,
                               'image': challenge_image})

            for email in emails:
                from_email = settings.EMAIL_HOST_USER
                to = [email]
                html_content = htmly.render(context)

                msg = EmailMultiAlternatives(subject, html_content, from_email, to)
                msg.attach_alternative(html_content, "text/html")
                msg.mixed_subtype = 'related'

                if challenge_image:
                    msg.attach(image)

                msg.send()
            return render(request,
                          'notification_email_conformation.html',
                          {'message': 'All the emails are sent successfully!'})
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
