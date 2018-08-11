from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.

        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """
        if (settings.FRONTEND_URL):
            path = settings.FRONTEND_URL
        else:
            path = 'https://evalai.cloudcv.org/'
        return  str(path) + 'auth/verify-email/' + str(emailconfirmation.key)
