from base.utils import SubmissionArtifactFileName
from django.core.management.base import BaseCommand, CommandError
from jobs.models import Submission


class Command(BaseCommand):
    """Print FK + revision context and a sample upload_to path for a submission.

    Matches Phase 1 of the staging artifact-prefix checklist: confirms
    ``challenge_phase_id`` and predicts nested vs flat prefixes from Django code.
    """

    help = (
        "Show challenge_phase linkage and sample SubmissionArtifactFileName path "
        "for a submission (operational RCA)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_pk",
            type=int,
            help="Submission primary key.",
        )

    def handle(self, *args, **options):
        pk = options["submission_pk"]
        try:
            submission = Submission.objects.select_related(
                "challenge_phase",
                "challenge_phase__challenge",
            ).get(pk=pk)
        except Submission.DoesNotExist:
            raise CommandError(
                "Submission {} does not exist.".format(pk)
            ) from None

        ch = submission.challenge_phase.challenge
        naming = SubmissionArtifactFileName()
        sample = naming(submission, "submission_result.json")
        nested = "/challenge_" in sample and "/phase_" in sample

        self.stdout.write(
            "submission_pk={pk}\n"
            "challenge_phase_id={phase}\n"
            "challenge_pk={chid}\n"
            "remote_evaluation={remote}\n"
            "sample_upload_to_relative_path={sample!r}\n"
            "appears_nested={nested}\n".format(
                pk=submission.pk,
                phase=submission.challenge_phase_id,
                chid=ch.pk,
                remote=ch.remote_evaluation,
                sample=sample,
                nested=nested,
            )
        )
