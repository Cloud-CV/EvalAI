from challenges.aws_utils import refresh_worker_task_definitions
from challenges.models import Challenge
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Refresh ECS worker task definitions for active Fargate-managed "
        "challenges so they use current ECR images."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit-id",
            dest="commit_id",
            help=(
                "Git commit SHA to pin worker images to. Recommended for "
                "production deploys."
            ),
        )
        parser.add_argument(
            "--challenge-pk",
            dest="challenge_pk",
            type=int,
            help="Refresh only the specified challenge.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Count matching challenges without updating ECS.",
        )

    def handle(self, *args, **options):
        commit_id = options.get("commit_id")
        challenge_pk = options.get("challenge_pk")
        dry_run = options.get("dry_run", False)

        queryset = None
        if challenge_pk is not None:
            queryset = Challenge.objects.filter(pk=challenge_pk)
            if not queryset.exists():
                raise CommandError(f"Challenge {challenge_pk} does not exist.")

        response = refresh_worker_task_definitions(
            queryset=queryset,
            commit_id=commit_id,
            dry_run=dry_run,
        )
        count = response["count"]
        failures = response["failures"]

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run: {count} challenge(s) would be refreshed."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Refreshed worker task definitions for {count} challenge(s)."
            )
        )
        for failure in failures:
            self.stdout.write(
                self.style.ERROR(
                    "Challenge {}: {}".format(
                        failure["challenge_pk"], failure["message"]
                    )
                )
            )

        if failures:
            raise CommandError(
                "Failed to refresh worker task definitions for "
                f"{len(failures)} challenge(s)."
            )
