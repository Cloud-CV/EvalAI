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

        self.data = {
            'name': 'New Message',
            'email': 'newuser@test.com',
            'message': 'New Message for Conatct'
        }

    def test_create_contact_message_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_contact_message_with_no_data(self):
        del self.data['message']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreateTeamMember(APITestCase):
    def setUp(self):
        self.url = reverse_lazy('web:our_team')
        self.contributor = {
            'name': 'John Snow',
            'email': 'john@snow.com',
            'github_url': 'www.github.com/johnsnow',
            'linkedin_url': 'www.linkedin.com/johnsnow',
            'personal_website': 'www.johnsnow.com',
        }

    def test_add_contributor_test(self):
        # TODO add 'Header' and 'Background image' to testing
        response = self.client.post(self.url, self.contributor)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Team.objects.all()), 1)

        team = Team.objects.all()[0]
        result = {
            'name': team.name,
            'email': team.email,
            'github_url': team.github_url,
            'linkedin_url': team.linkedin_url,
            'personal_website': team.personal_website,
        }
        self.assertEqual(self.contributor, result)
        self.assertEqual(Team.CONTRIBUTOR, team.team_type)


class GetTeamTest(APITestCase):
    def setUp(self):
        self.url = reverse_lazy('web:our_team')
        self.team = Team.objects.create(
            name='John Snow',
            email='john@snow.com',
            description='An awesome description for John Snow',
            headshot=SimpleUploadedFile(
                name='test_headshot.jpg',
                content=open('frontend/src/images/deshraj.png', 'rb').read(),
                content_type='image/png'
            ),
            github_url='www.github.com/johnsnow',
            linkedin_url='www.linkedin.com/johnsnow',
            personal_website='www.johnsnow.com',
            background_image=SimpleUploadedFile(
                name='test_background_image.jpg',
                content=open('frontend/src/images/deshraj-profile.jpg', 'rb').read(),
                content_type='image/jpg'
            ),
            team_type='Core Team',
            visible=True,
        )

    def test_team_get_request(self):
        response = self.client.get(self.url)
        expected = [
            {
                "name": self.team.name,
                "headshot": "http://testserver%s" % self.team.headshot.url,
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
        self.assertIn('Error 404', unicode(response))
        response = internal_server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn('Error 500', unicode(response))
