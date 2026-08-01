import botocore
from base.utils import get_sqs_queue
from challenges.models import Challenge
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Purge all messages from a challenge SQS queue.

    Use when changing FIFO MessageGroupId strategy so legacy messages
    (old group ids) do not remain alongside newly enqueued messages.

    Safe deploy order:
    1. Pause enqueueing (stop workers accepting new publishes / freeze
       submissions) so producers cannot add messages during the cutover.
    2. Deploy the new MessageGroupId strategy.
    3. Purge or drain the queue (this command removes pending work).
    4. Requeue any submissions that were still submitted/queued and need
       evaluation (e.g. resume/republish).
    5. Resume enqueueing only after the queue is empty and the new
       grouping strategy is active.

    Amazon SQS purge can take up to 60 seconds; do not enqueue until it
    completes.
    """

    help = (
        "Purge all messages from an existing challenge SQS queue (required "
        "when changing FIFO MessageGroupId strategy). Does not create a "
        "missing queue."
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
                "Pause enqueueing first; purge deletes pending work that "
                "must be requeued afterward. [y/N] ".format(
                    queue_name, challenge_pk
                )
            )
            if confirm.strip().lower() not in ("y", "yes"):
                self.stdout.write("Aborted.")
                return

        try:
            queue = get_sqs_queue(queue_name, challenge)
        except botocore.exceptions.ClientError as ex:
            error_code = ex.response.get("Error", {}).get("Code", "")
            if error_code == "AWS.SimpleQueueService.NonExistentQueue":
                raise CommandError(
                    "SQS queue {!r} for challenge {} does not exist.".format(
                        queue_name, challenge_pk
                    )
                ) from ex
            raise CommandError(
                "Failed to look up SQS queue {!r} for challenge {}: {}".format(
                    queue_name, challenge_pk, ex
                )
            ) from ex

        queue.purge()
        self.stdout.write(
            self.style.SUCCESS(
                "Purged queue {!r} for challenge {}. Wait up to 60s "
                "before enqueueing. Requeue any submitted/queued "
                "submissions that still need evaluation, then resume "
                "producers only after the queue is empty under the new "
                "grouping strategy.".format(queue_name, challenge_pk)
            )
        )
