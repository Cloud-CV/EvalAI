from base.utils import get_or_create_sqs_queue
from challenges.models import Challenge
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Purge all messages from a challenge SQS queue.

    Use when changing FIFO MessageGroupId strategy so legacy messages
    (old group ids) do not remain alongside newly enqueued messages.
    Amazon SQS purge can take up to 60 seconds; do not enqueue until it
    completes.
    """

    help = (
        "Purge all messages from a challenge SQS queue (required when "
        "changing FIFO MessageGroupId strategy)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "challenge_pk",
            type=int,
            help="Challenge primary key whose queue should be purged.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip interactive confirmation.",
        )

    def handle(self, *args, **options):
        challenge_pk = options["challenge_pk"]
        try:
            challenge = Challenge.objects.get(pk=challenge_pk)
        except Challenge.DoesNotExist:
            raise CommandError(
                "Challenge {} does not exist.".format(challenge_pk)
            ) from None

        queue_name = challenge.queue
        if not queue_name:
            raise CommandError(
                "Challenge {} has no queue name configured.".format(
                    challenge_pk
                )
            )

        if not options["yes"]:
            confirm = input(
                "Purge ALL messages from queue {!r} for challenge {}? "
                "[y/N] ".format(queue_name, challenge_pk)
            )
            if confirm.strip().lower() not in ("y", "yes"):
                self.stdout.write("Aborted.")
                return

        queue = get_or_create_sqs_queue(queue_name, challenge)
        queue.purge()
        self.stdout.write(
            self.style.SUCCESS(
                "Purged queue {!r} for challenge {}. Wait up to 60s "
                "before enqueueing new messages.".format(
                    queue_name, challenge_pk
                )
            )
        )
