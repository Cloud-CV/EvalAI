from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user_data, timestamp):
        '''
            Custom Token Generator for Host Invitations
        '''
        user = user_data['user']
        challenge_host_team = user_data['challenge_host_team']
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(
                user.is_user_host) + six.text_type(challenge_host_team.pk)
        )


host_invitations_token_generator = TokenGenerator()
