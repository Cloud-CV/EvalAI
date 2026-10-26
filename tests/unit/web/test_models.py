from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from web.models import Contact, Subscribers, Team


class ContactTestCase(TestCase):
    def setUp(self):
        super(ContactTestCase, self).setUp()
        self.contact = Contact.objects.create(
            name="user", email="user@domain.com", message="test message"
        )

    def test__str__(self):
        name = self.contact.name
        email = self.contact.email
        message = self.contact.message
        final_string = "{0}: {1}: {2}".format(name, email, message)
        self.assertEqual(final_string, self.contact.__str__())


class TeamTestCase(TestCase):
    def setUp(self):
        super(TeamTestCase, self).setUp()
        self.team = Team.objects.create(
            name="user",
            email="test@user.com",
            description="Description for Test User",
            headshot=SimpleUploadedFile(
                name="test_headshot.jpg",
                content=open("frontend/src/images/logo.png", "rb").read(),
                content_type="image/png",
            ),
            github_url="www.github.com/Cloud-CV",
            linkedin_url="www.linkedin.com/testuser",
            personal_website="CloudCV.org",
            background_image=SimpleUploadedFile(
                name="test_background_image.jpg",
                content=open("frontend/src/images/rocket.png", "rb").read(),
                content_type="image/png",
            ),
            team_type=Team.CORE_TEAM,
            visible=True,
        )

    def test__str__(self):
        self.assertEqual(self.team.name, self.team.__str__())


class SubscribersTestCase(TestCase):
    def setUp(self):
        super(SubscribersTestCase, self).setUp()
        self.subscriber = Subscribers.objects.create(
            email="subscriber@domain.com"
        )

    def test__str__(self):
        self.assertEqual(str(self.subscriber), "subscriber@domain.com")

    def test_email_unique_constraint(self):
        """Test that duplicate email addresses raise IntegrityError"""
        with self.assertRaises(IntegrityError):
            Subscribers.objects.create(email="subscriber@domain.com")
