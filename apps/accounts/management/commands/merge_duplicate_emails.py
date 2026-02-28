import logging

from accounts.models import JwtToken
from allauth.account.models import EmailAddress
from challenges.models import (
    ChallengeConfiguration,
    StarChallenge,
    UserInvitation,
)
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam

logger = logging.getLogger(__name__)

FK_MODELS = [
    (ChallengeHost, "user"),
    (ChallengeHostTeam, "created_by"),
    (Participant, "user"),
    (ParticipantTeam, "created_by"),
    (Submission, "created_by"),
    (ChallengeConfiguration, "user"),
    (StarChallenge, "user"),
    (UserInvitation, "user"),
]

ONE_TO_ONE_MODELS = [
    JwtToken,
]


class Command(BaseCommand):
    help = (
        "Find users sharing the same email address, reassign all related "
        "objects to the account with the most submissions (falling back to "
        "newest), and deactivate duplicates. "
        "Dry-run by default; pass --commit to apply."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            default=False,
            help="Actually apply changes. Without this flag, only a dry-run report is printed.",
        )

    def handle(self, *args, **options):
        commit = options["commit"]
        mode = "COMMIT" if commit else "DRY-RUN"
        self.stdout.write(f"\n=== Merge Duplicate Emails ({mode}) ===\n")

        dupes = (
            User.objects.values("email")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("-cnt")
        )

        if not dupes.exists():
            self.stdout.write("No duplicate emails found. Nothing to do.")
            return

        self.stdout.write(f"Found {dupes.count()} email(s) with duplicates:\n")

        total_merged = 0
        for entry in dupes:
            email = entry["email"]
            count = entry["cnt"]
            users = list(
                User.objects.filter(email=email).order_by("date_joined")
            )
            canonical, duplicates = self._pick_canonical(users)

            self.stdout.write(f"\n  Email: {email} ({count} users)")
            self.stdout.write(
                f"  Canonical: id={canonical.id} username={canonical.username} "
                f"joined={canonical.date_joined} "
                f"submissions={Submission.objects.filter(created_by=canonical).count()}"
            )

            for dup in duplicates:
                self.stdout.write(
                    f"  Duplicate: id={dup.id} username={dup.username} "
                    f"joined={dup.date_joined} "
                    f"submissions={Submission.objects.filter(created_by=dup).count()}"
                )
                self._merge_user(canonical, dup, commit=commit)
                total_merged += 1

        self.stdout.write(
            f"\n=== Summary: {total_merged} duplicate user(s) "
            f"{'merged' if commit else 'would be merged'} ===\n"
        )

    def _pick_canonical(self, users):
        """Choose which user to keep from a group sharing the same email.

        Prefers the account with the most submissions.  When counts are tied
        (including zero-zero), falls back to the newest (latest date_joined).
        Returns (canonical, list_of_duplicates).
        """
        canonical = max(
            users,
            key=lambda u: (
                Submission.objects.filter(created_by=u).count(),
                u.date_joined,
            ),
        )
        duplicates = [u for u in users if u.pk != canonical.pk]
        return canonical, duplicates

    def _merge_user(self, canonical, duplicate, commit=False):
        """Reassign all related objects from *duplicate* to *canonical* and deactivate."""
        action = "Reassigning" if commit else "Would reassign"

        try:
            if commit:
                with transaction.atomic():
                    self._do_merge(canonical, duplicate, action)
            else:
                self._do_merge(canonical, duplicate, action)
        except Exception:
            logger.exception(
                "Failed to merge user %s into %s", duplicate.id, canonical.id
            )
            self.stderr.write(
                f"    ERROR merging user {duplicate.id} — see logs"
            )

    def _do_merge(self, canonical, duplicate, action):
        for model, field_name in FK_MODELS:
            qs = model.objects.filter(**{field_name: duplicate})
            count = qs.count()
            if count:
                self.stdout.write(
                    f"    {action} {count} {model.__name__}.{field_name} "
                    f"rows from user {duplicate.id} -> {canonical.id}"
                )
                if action == "Reassigning":
                    qs.update(**{field_name: canonical})

        for model in ONE_TO_ONE_MODELS:
            obj = model.objects.filter(user=duplicate).first()
            if not obj:
                continue
            self.stdout.write(
                f"    {action.replace('Reassigning', 'Deleting').replace('Would reassign', 'Would delete')} "
                f"{model.__name__} for user {duplicate.id}"
            )
            if action == "Reassigning":
                obj.delete()

        tagged_email = self._make_duplicate_email(
            duplicate.email, duplicate.id
        )
        rename_label = (
            "Renaming" if action == "Reassigning" else "Would rename"
        )
        self.stdout.write(
            f"    {rename_label} email for user {duplicate.id}: "
            f"{duplicate.email} -> {tagged_email}"
        )

        email_addrs = EmailAddress.objects.filter(user=duplicate)
        ea_count = email_addrs.count()
        if ea_count:
            self.stdout.write(
                f"    {rename_label} {ea_count} EmailAddress row(s) for user {duplicate.id}"
            )
            if action == "Reassigning":
                email_addrs.update(email=tagged_email)

        try:
            from rest_framework.authtoken.models import Token
        except ImportError:
            # Django REST Framework authtoken app is optional.
            Token = None

        if Token is not None:
            try:
                tokens = Token.objects.filter(user=duplicate)
                t_count = tokens.count()
                if t_count:
                    self.stdout.write(
                        f"    {action.replace('Reassigning', 'Deleting').replace('Would reassign', 'Would delete')} "
                        f"{t_count} auth Token(s) for user {duplicate.id}"
                    )
                    if action == "Reassigning":
                        tokens.delete()
            except Exception:
                logger.exception(
                    "Error while processing auth tokens for duplicate user %s",
                    duplicate.id,
                )

        deactivate_label = (
            "Deactivating" if action == "Reassigning" else "Would deactivate"
        )
        self.stdout.write(
            f"    {deactivate_label} user {duplicate.id} ({duplicate.username})"
        )
        if action == "Reassigning":
            duplicate.email = tagged_email
            duplicate.is_active = False
            duplicate.save(update_fields=["email", "is_active"])

    @staticmethod
    def _make_duplicate_email(email, user_id):
        """Turn 'user@example.com' into 'user+duplicate-{id}@example.com'.

        Appends user_id so each deactivated user gets a unique email,
        avoiding collisions when multiple duplicates share the same address
        (or when the original email is empty).
        """
        email = (email or "").strip()
        local, at, domain = email.rpartition("@")
        if not at or not domain:
            return f"duplicate-{user_id}@deactivated.local"
        return f"{local}+duplicate-{user_id}@{domain}"
