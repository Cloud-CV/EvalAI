from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.

        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """
        print('lol')
        # url = reverse(
        #     "account_confirm_email",
        #     args=[emailconfirmation.key])
        # ret = build_absolute_uri(
        #     request,
        #     url)
        return 'http://localhost:4200/auth/verify-email/' + str(emailconfirmation.key)