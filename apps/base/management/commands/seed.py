from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    help = "Seeds the database with random but sensible values."

    def add_arguments(self, parser):
        parser.add_argument(

            '--nc', dest='nc', nargs='?',default=3,
            help = 'no.of challenges',
        )

    def handle(self, *args, **options):
        self.nc = options['nc']
        self.stdout.write(self.style.SUCCESS('Starting the database seeder. Hang on...'))
        self.stdout.write(self.style.SUCCESS('no of challenges required'.join(options['nc'])))
        call_command('runscript', 'seed', '--settings', 'settings.dev')
        self.stdout.write(self.style.SUCCESS('Database successfully seeded.'))
