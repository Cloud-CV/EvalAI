from accounts.validators import MaximumLengthValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase


class MaximumLengthValidatorTest(SimpleTestCase):
    def test_accepts_password_within_limit(self):
        validator = MaximumLengthValidator(
            max_length=settings.PASSWORD_MAX_LENGTH
        )
        validator.validate("a" * settings.PASSWORD_MAX_LENGTH)

    def test_rejects_password_over_limit(self):
        validator = MaximumLengthValidator(
            max_length=settings.PASSWORD_MAX_LENGTH
        )
        with self.assertRaises(ValidationError) as context:
            validator.validate("a" * (settings.PASSWORD_MAX_LENGTH + 1))
        self.assertEqual(context.exception.code, "password_too_long")

    def test_default_max_length_uses_settings(self):
        validator = MaximumLengthValidator()
        self.assertEqual(validator.max_length, settings.PASSWORD_MAX_LENGTH)

    def test_get_help_text_includes_max_length(self):
        validator = MaximumLengthValidator(max_length=128)
        self.assertIn("128", validator.get_help_text())
