from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Seeds the database with random but sensible values."

    def add_arguments(self, parser):
        parser.add_argument(
            "-nc",
            nargs="?",
            default=500,
            type=int,
            help="Number of challenges. Default: 500 (40% present, 20% future, 40% past)",
        )

    def handle(self, *args, **options):
        nc = options["nc"]
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting the database seeder with {self.nc} challenges. Hang on..."
            )
        )
        call_command("runscript", "seed", "--script-args", nc)
        
