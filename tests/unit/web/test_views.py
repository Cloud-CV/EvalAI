from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from web.models import Contact, Team

from django.test import Client
from django.test import TestCase

from web.views import page_not_found, internal_server_error
from evalai.urls import handler404, handler500


class BaseAPITestCase(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.message = Contact.objects.create(
            name='someuser',
            email='user@test.com',
            message='Message for Contact')


class CreateContactMessage(BaseAPITestCase):

    def setUp(self):
        super(CreateContactMessage, self).setUp()
        self.url = reverse_lazy('web:contact_us')

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        self.data = {
            'name': self.user.username,
            'email': self.user.email,
            'message': 'Sample contact message'
        }

    def test_get_user_data(self):
        expected = {
            'name': self.user.username,
            'email': self.user.email,
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(expected, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_contact_message_with_all_data(self):
        if self.data['message']:
            response = self.client.post(self.url, self.data)
            expected = {'message': 'We have received your request and will contact you shortly.'}
            self.assertEqual(response.data, expected)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_contact_message_with_no_data(self):
        del self.data['message']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreateTeamMember(APITestCase):
    def setUp(self):
        self.url = reverse_lazy('web:our_team')
        self.data = {
            'name': 'Test User',
            'email': 'test@user.com',
            'github_url': 'www.github.com/testuser',
            'linkedin_url': 'www.linkedin.com/testuser',
            'personal_website': 'www.testuser.com',
        }

    def test_create_team_member_default_team_type(self):
        # TODO add 'Header' and 'Background image' to testing
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.all().count(), 1)

        team = Team.objects.get(name=self.data['name'])
        result = {
            'name': team.name,
            'email': team.email,
            'github_url': team.github_url,
            'linkedin_url': team.linkedin_url,
            'personal_website': team.personal_website,
        }
        self.assertEqual(self.data, result)
        self.assertEqual(Team.CONTRIBUTOR, team.team_type)

    def test_create_team_member_custom_team_type(self):
        # TODO add 'Header' and 'Background image' to testing
        self.data['team_type'] = Team.CORE_TEAM
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.all().count(), 1)

        team = Team.objects.get(name=self.data['name'])
        result = {
            'name': team.name,
            'email': team.email,
            'github_url': team.github_url,
            'linkedin_url': team.linkedin_url,
            'personal_website': team.personal_website,
            'team_type': team.team_type
        }
        self.assertEqual(self.data, result)


class GetTeamTest(APITestCase):
    def setUp(self):
        self.url = reverse_lazy('web:our_team')
        self.team = Team.objects.create(
            name='Test User',
            email='test@user.com',
            description='An awesome description for Test User',
            headshot=SimpleUploadedFile(
                name='test_headshot.jpg',
                content=open('frontend/src/images/rocket.png', 'rb').read(),
                content_type='image/png'
            ),
            github_url='www.github.com/testuser',
            linkedin_url='www.linkedin.com/testuser',
            personal_website='www.testuser.com',
            background_image=SimpleUploadedFile(
                name='test_background_image.jpg',
                content=open('frontend/src/images/rocket.png', 'rb').read(),
                content_type='image/jpg'
            ),
            team_type=Team.CORE_TEAM,
            visible=True,
        )

    def test_team_get_request(self):
        response = self.client.get(self.url)
        expected = [
            {
                "name": self.team.name,
                "headshot": "http://testserver%s" % self.team.headshot.url,
                "email": self.team.email,
                "background_image": "http://testserver%s" % self.team.background_image.url,
                "github_url": self.team.github_url,
                "linkedin_url": self.team.linkedin_url,
                "personal_website": self.team.personal_website,
                "description": self.team.description,
                "team_type": self.team.team_type,
            }
        ]
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestErrorPages(TestCase):

    def test_error_handlers(self):
        self.assertTrue(handler404.endswith('.page_not_found'))
        self.assertTrue(handler500.endswith('.internal_server_error'))
        c = Client()
        request = c.get("/abc")
        response = page_not_found(request)
        self.assertEqual(response.status_code, 404)
        response = internal_server_error(request)
        self.assertEqual(response.status_code, 500)


class TestNotifyUsersAboutChallenge(TestCase):

    def setUp(self):
        self.client = Client()

        self.superuser = User.objects.create_superuser(
            'superuser',
            "superuser@test.com",
            'secret_password')

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        self.url = reverse_lazy('web:notify_users_about_challenge')

        self.email_data = {'subject': 'Subject of the Email',
                           'body': 'Body of the Email'}

    def test_if_user_isnt_authenticated(self):
        response = self.client.get(self.url)
        html = response.content.decode('utf8')
        self.assertTrue(html.startswith('<!DOCTYPE html>'))
        self.assertTrue(html.endswith(''))
        self.assertEqual(response.status_code, 200)

    def test_if_user_is_authenticated_but_not_superuser(self):
        self.data = {'username': self.user.username, 'password': self.user.password}
        response = self.client.post(self.url, self.data)
        html = response.content.decode('utf8')
        self.assertTrue(html.startswith('<!DOCTYPE html>'))
        self.assertTrue(html.endswith(''))
        self.assertEqual(response.status_code, 200)

    def test_if_user_is_authenticated_and_superuser(self):
        request = self.client.get('/admin/', follow=True)
        response = self.client.login(username='superuser', password='secret_password')
        self.assertEqual(request.status_code, 200)
        self.assertTrue(response)

    def test_notification_email_data_page(self):
        request = self.client.get('/admin/', follow=True)
        response = self.client.login(username='superuser', password='secret_password', follow=True)
        request = self.client.get(self.url)
        html = request.content.decode('utf8')
        self.assertTrue(html.startswith(''))
        self.assertTrue(html.endswith(''))
        self.assertEqual(request.status_code, 200)
        self.assertTrue(response)

    def test_notification_email_without_challenge_image(self):
        request = self.client.get('/admin/', follow=True)
        response = self.client.login(username='superuser', password='secret_password', follow=True)
        request = self.client.post(self.url, self.email_data)
        html = request.content.decode('utf8')
        self.assertTrue(html.startswith(''))
        self.assertTrue(html.endswith(''))
        self.assertEqual(request.status_code, 200)
        self.assertTrue(response)

    def test_notification_email_with_challenge_image(self):
        request = self.client.get('/admin/', follow=True)
        response = self.client.login(username='superuser', password='secret_password', follow=True)
        self.email_data['challenge_image'] = SimpleUploadedFile(
                                                name='test_background_image.jpg',
                                                content=open('frontend/src/images/rocket.png', 'rb').read(),
                                                content_type='image/jpg'
            )
        request = self.client.post(self.url, self.email_data)
        html = request.content.decode('utf8')
        self.assertTrue(html.startswith(''))
        self.assertTrue(html.endswith(''))
        self.assertTrue(response)
        self.assertEqual(request.status_code, 200)

    def test_notification_with_put_request(self):
        request = self.client.get('/admin/', follow=True)
        response = self.client.login(username='superuser', password='secret_password', follow=True)
        request = self.client.put(self.url, self.email_data)
        html = request.content.decode('utf8')
        self.assertTrue(html.startswith('<!DOCTYPE html>'))
        self.assertTrue(html.endswith(''))
        self.assertTrue(response)
        self.assertEqual(request.status_code, 200)
