from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MaximumLengthValidator:
    """
    Reject passwords longer than PASSWORD_MAX_LENGTH to prevent resource
    exhaustion from oversized password payloads.
    """

    def __init__(self, max_length=None):
        self.max_length = max_length or getattr(
            settings, "PASSWORD_MAX_LENGTH", 128
        )

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _(
                    "This password is longer than the maximum of "
                    "%(max_length)d characters."
                ),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return _(
            "Your password must be at most %(max_length)d characters."
            % {"max_length": self.max_length}
        )
