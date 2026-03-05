import logging

import dns.resolver
from allauth.account.adapter import DefaultAccountAdapter
from disposable_email_domains import blocklist
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

DISPOSABLE_DOMAINS = frozenset(blocklist)

ROLE_BASED_LOCAL_PARTS = frozenset(
    {
        "abuse",
        "admin",
        "billing",
        "compliance",
        "devnull",
        "ftp",
        "hostmaster",
        "info",
        "mailer-daemon",
        "marketing",
        "no-reply",
        "noc",
        "noreply",
        "postmaster",
        "root",
        "sales",
        "security",
        "support",
        "webmaster",
        "www",
    }
)

DOMAIN_TYPO_MAP = {
    "gamil.com": "gmail.com",
    "gail.com": "gmail.com",
    "gmal.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "gmali.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmil.com": "gmail.com",
    "gnail.com": "gmail.com",
    "gogglemail.com": "googlemail.com",
    "googlmail.com": "googlemail.com",
    "hotamil.com": "hotmail.com",
    "hotmai.com": "hotmail.com",
    "hotmal.com": "hotmail.com",
    "hotmial.com": "hotmail.com",
    "hotmil.com": "hotmail.com",
    "iclod.com": "icloud.com",
    "iclould.com": "icloud.com",
    "outloo.com": "outlook.com",
    "outlok.com": "outlook.com",
    "outlool.com": "outlook.com",
    "outook.com": "outlook.com",
    "protonmal.com": "protonmail.com",
    "protonmaill.com": "protonmail.com",
    "yaho.com": "yahoo.com",
    "yahooo.com": "yahoo.com",
    "yaho.co.in": "yahoo.co.in",
    "yhaoo.com": "yahoo.com",
    "yhoo.com": "yahoo.com",
}


class EvalAIAccountAdapter(DefaultAccountAdapter):
    """
    Custom allauth adapter that:
    1. Rejects duplicate, role-based, typo'd, and disposable email addresses.
    2. Validates email domains have valid MX records at registration time.
    3. Suppresses outgoing allauth emails to addresses flagged as bounced.
    4. Clears the email_bounced flag when a new email address is confirmed.
    """

    def clean_email(self, email):
        email = super().clean_email(email)

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "A user is already registered with this email address."
            )

        local_part, domain = email.rsplit("@", 1)
        domain = domain.lower()

        if local_part.lower() in ROLE_BASED_LOCAL_PARTS:
            raise ValidationError(
                "Role-based email addresses (e.g. noreply@, admin@) are "
                "not accepted. Please use a personal email address."
            )

        # Check typo before disposable so users get helpful suggestions
        # (typo domains may also appear in the disposable blocklist)
        suggested = DOMAIN_TYPO_MAP.get(domain)
        if suggested:
            raise ValidationError(
                "Did you mean {}@{}? The domain '{}' looks like a typo.".format(
                    local_part, suggested, domain
                )
            )

        extra_blocked = set(getattr(settings, "BLOCKED_EMAIL_DOMAINS", []))
        if domain in DISPOSABLE_DOMAINS or domain in extra_blocked:
            raise ValidationError(
                "Disposable email addresses are not allowed. "
                "Please use a permanent email address."
            )

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
            logger.debug(
                "No User found with email %s when checking for bounced "
                "profile; sending via default allauth adapter.",
                email,
            )
        super().send_mail(template_prefix, email, context)

    def confirm_email(self, request, email_address):
        super().confirm_email(request, email_address)
        user = email_address.user
        if hasattr(user, "profile") and user.profile.email_bounced:
            # Lazy import: allauth loads this adapter via the full
            # "apps.accounts.adapter" path.  A top-level import of
            # .serializers would re-import models under that path and
            # conflict with the already-registered "accounts.models".
            from .serializers import EmailBounceSerializer

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
