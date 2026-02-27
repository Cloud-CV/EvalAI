import logging

import dns.resolver
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class EvalAIAccountAdapter(DefaultAccountAdapter):
    """
    Custom allauth adapter that validates email domains have valid MX records
    before allowing registration, reducing SES bounces from non-existent
    addresses.
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

    def _domain_has_mx_records(self, domain):
        try:
            answers = dns.resolver.resolve(domain, "MX")
            return len(answers) > 0
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            return False
        except Exception:
            logger.warning(
                "Unexpected error during MX lookup for domain: %s",
                domain,
                exc_info=True,
            )
            # Allow registration on unexpected DNS errors to avoid
            # blocking legitimate users due to transient issues.
            return True
