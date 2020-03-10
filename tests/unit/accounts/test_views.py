import os
from os.path import join

from rest_framework.authtoken.models import Token

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.conf import settings
from django.db import models


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.client.force_authenticate(user=self.user)


class DisableUserTest(BaseAPITestClass):

    url = reverse_lazy("accounts:disable_user")

    def test_disable_user(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MyImageField(models.ImageField):

    def __init__(self, *args, **kwargs):
        super(MyImageField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(MyImageField, self).clean(*args, **kwargs)
        filename = os.path.splitext(data.name)
        if len(filename[1]):
            data.name += u'.' + filename[1]
        return data


class TestRequestForm(forms.Form):
    username = forms.CharField(label='test', max_length=100)
    affiliation = forms.CharField(label='Your name', max_length=100)
    github_url = forms.CharField(label='Your name', max_length=100)
    google_scholar_url = forms.CharField(label='Your name', max_length=100)
    linkedin_url = forms.CharField(label='Your name', max_length=100)
    password = forms.CharField(label='Your name', max_length=100)
    user_avatar = MyImageField()


class TestUpdateUser(BaseAPITestClass):
    def test_cannot_update_username(self):
        self.url = reverse_lazy("rest_user_details")
        test_image = File(open(join(settings.BASE_DIR, "examples", "example1", "test_image.png")))
        test_image = SimpleUploadedFile("file.png", test_image.read().encode("utf-8", errors='strict'), content_type="multipart/form-data")
        self.data = {
            "username": "anotheruser",
            "affiliation": "some_affiliation",
            "github_url": "https://github.url",
            "google_scholar_url": "https://google-scholar.url",
            "linkedin_url": "https://linkedin.url",
            "password": "secret_password",
            "user_avatar": test_image,
        }
        form = TestRequestForm(self.data)
        response = self.client.put(
            os.path.join("api", "auth", str(self.url)), form
        )
        self.assertNotContains(response, "anotheruser")
        self.assertContains(response, "someuser")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetAuthTokenTest(BaseAPITestClass):

    url = reverse_lazy("accounts:get_auth_token")

    def test_get_auth_token(self):
        response = self.client.get(self.url, {})
        token = Token.objects.get(user=self.user)
        expected_data = {"token": "{}".format(token)}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
