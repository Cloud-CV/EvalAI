from django.core.management.base import BaseCommand

from jobs.queue_timeout import fail_stuck_submissions


class Command(BaseCommand):
    help = (
        "Fail submissions that have remained in a pre-running queue state "
        "(submitted, submitting, queued, resuming) longer than the "
        "challenge's submission_queue_time_limit."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--challenge-pk",
            type=int,
            default=None,
            help="Only process submissions for this challenge.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report submissions that would be failed without updating them.",
        )

    def handle(self, *args, **options):
        failed_count = fail_stuck_submissions(
            challenge_pk=options["challenge_pk"],
            dry_run=options["dry_run"],
        )
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run: {} submission(s) would be failed.".format(
                        failed_count
                    )
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Failed {} queue-stuck submission(s).".format(failed_count)
                )
            )
