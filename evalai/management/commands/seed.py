from django.core.management import BaseCommand


class Command(BaseCommand):

    help = "My custom django command"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting the database seeder. Hang on :)'))
