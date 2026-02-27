import logging

import dns.resolver
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .serializers import EmailBounceSerializer

logger = logging.getLogger(__name__)


class EvalAIAccountAdapter(DefaultAccountAdapter):
    """
    Custom allauth adapter that:
    1. Validates email domains have valid MX records at registration time.
    2. Suppresses outgoing allauth emails to addresses flagged as bounced.
    3. Clears the email_bounced flag when a new email address is confirmed.
    """

    def clean_email(self, email):
        email = super().clean_email(email)
        domain = email.rsplit("@", 1)[-1]

        if not self._domain_has_mx_records(domain):
            raise ValidationError(
                "The email domain '{}' does not appear to accept email. "
                "Please check for typos.".format(domain)
            )

        return email

    def send_mail(self, template_prefix, email, context):
        try:
            user = User.objects.get(email__iexact=email)
            if hasattr(user, "profile") and user.profile.email_bounced:
                logger.info(
                    "Suppressed allauth email to bounced address %s "
                    "(template=%s).",
                    email,
                    template_prefix,
                )
                return
        except User.DoesNotExist:
            pass
        super().send_mail(template_prefix, email, context)

    def confirm_email(self, request, email_address):
        super().confirm_email(request, email_address)
        user = email_address.user
        if hasattr(user, "profile") and user.profile.email_bounced:
            serializer = EmailBounceSerializer(user.profile)
            serializer.clear_bounce()
            logger.info(
                "Cleared email_bounced flag for user %s after confirming %s.",
                user.username,
                email_address.email,
            )

    def _domain_has_mx_records(self, domain):
        try:
            answers = dns.resolver.resolve(domain, "MX")
            return len(answers) > 0
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
        ):
            return False
        except dns.exception.Timeout:
            logger.warning(
                "DNS timeout during MX lookup for domain: %s", domain
            )
            return True
        except Exception:
            logger.warning(
                "Unexpected error during MX lookup for domain: %s",
                domain,
                exc_info=True,
            )
            return True
