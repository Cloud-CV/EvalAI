from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        '''
            Custom Token Generator for Host Invitations
        '''
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_user_host)
        )
host_invitations_token_generator = TokenGenerator()
