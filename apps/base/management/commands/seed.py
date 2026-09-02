from django.core.management import BaseCommand, call_command

# Sized for development. Generating hundreds of challenges at
# NUMBER_OF_SUBMISSIONS submissions each takes tens of minutes and blocks
# Django from serving until it finishes, which made a first `docker compose
# up` look like a hang. Pass `-nc 500` when a load-testing corpus is wanted.
DEFAULT_NUMBER_OF_CHALLENGES = 10


class Command(BaseCommand):
    help = "Seeds the database with random but sensible values."

    def add_arguments(self, parser):
        parser.add_argument(
            "-nc",
            nargs="?",
            default=DEFAULT_NUMBER_OF_CHALLENGES,
            type=int,
            help=(
                "Number of challenges. Default: {} "
                "(40% present, 20% future, 40% past)."
            ).format(DEFAULT_NUMBER_OF_CHALLENGES),
        )

    def handle(self, *args, **options):
        self.nc = options["nc"]
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting the database seeder with {self.nc} challenges. Hang on..."
            )
        )
        call_command("runscript", "seed", "--script-args", self.nc)
