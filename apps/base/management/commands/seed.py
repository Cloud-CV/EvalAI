from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    help = "Seeds the database with random but sensible values."

    def add_arguments(self, parser):
        parser.add_argument(
            "-nc",
            nargs="?",
            default=20,
            type=int,
            help="Number of challenges.",
        )

    def handle(self, *args, **options):
        self.nc = options["nc"]
        self.stdout.write(
            self.style.SUCCESS("Starting the database seeder. Hang on...")
        )
        call_command("runscript", "seed", "--script-args", self.nc)
