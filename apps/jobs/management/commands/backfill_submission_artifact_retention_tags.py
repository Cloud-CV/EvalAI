from django.core.management.base import BaseCommand, CommandError
from jobs.s3_retention import backfill_submission_artifact_tags


class Command(BaseCommand):
    help = "Backfill S3 retention tags for submission artifacts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--challenge-phase-ids",
            type=int,
            nargs="+",
            default=None,
            help="Only backfill submissions for these challenge phase IDs.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Apply S3 tags. Default mode is dry-run.",
        )
        parser.add_argument(
            "--bucket",
            default=None,
            help="Override the S3 bucket name resolved from Django storage settings.",
        )

    def handle(self, *args, **options):
        dry_run = not options["execute"]
        challenge_phase_ids = options["challenge_phase_ids"]
        bucket_name = options["bucket"]

        if not dry_run and not bucket_name:
            self.stdout.write(
                "No --bucket supplied; using bucket from Django storage settings."
            )

        try:
            summary = backfill_submission_artifact_tags(
                challenge_phase_ids=challenge_phase_ids,
                dry_run=dry_run,
                bucket_name=bucket_name,
            )
        except Exception as exc:
            raise CommandError(str(exc))

        mode = "DRY RUN" if dry_run else "EXECUTE"
        self.stdout.write(f"S3 retention tag backfill complete ({mode})")
        self.stdout.write(f"Submissions seen: {summary['submissions_seen']}")
        self.stdout.write(f"Objects seen: {summary['objects_seen']}")
        self.stdout.write(f"Objects to tag: {summary['objects_to_tag']}")
        self.stdout.write(f"Objects tagged: {summary['objects_tagged']}")
        self.stdout.write(f"Objects failed: {summary['objects_failed']}")
