import os

from django.core.management import BaseCommand, call_command

# The full dataset is a load-testing corpus: 500 challenges times
# NUMBER_OF_SUBMISSIONS submissions each, which takes tens of minutes to
# generate. The dev container overrides SEED_CHALLENGES so a fresh database
# does not block Django from serving for that long.
DEFAULT_NUMBER_OF_CHALLENGES = 500


class Command(BaseCommand):

    help = "Seeds the database with random but sensible values."

    def add_arguments(self, parser):
        default_challenges = int(
            os.environ.get("SEED_CHALLENGES", DEFAULT_NUMBER_OF_CHALLENGES)
        )
        parser.add_argument(
            "-nc",
            nargs="?",
            default=default_challenges,
            type=int,
            help=(
                "Number of challenges. Default: {} "
                "(40% present, 20% future, 40% past). "
                "Override with the SEED_CHALLENGES environment variable."
            ).format(default_challenges),
        )

    def handle(self, *args, **options):
        self.nc = options["nc"]
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting the database seeder with {self.nc} challenges. Hang on..."
            )
        )
        call_command("runscript", "seed", "--script-args", self.nc)
