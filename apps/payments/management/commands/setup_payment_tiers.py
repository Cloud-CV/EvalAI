from django.core.management.base import BaseCommand
from payments.utils import create_default_payment_tiers, ensure_challenge_has_payment_tier
from challenges.models import Challenge


class Command(BaseCommand):
    help = 'Create default payment tiers and migrate existing challenges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-challenges',
            action='store_true',
            help='Migrate existing challenges to use the new payment tier system',
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating default payment tiers...')
        
        created_tiers = create_default_payment_tiers()
        
        if created_tiers:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {len(created_tiers)} payment tiers: '
                    f'{", ".join([tier.display_name for tier in created_tiers])}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Payment tiers already exist, no new tiers created.')
            )

        if options['migrate_challenges']:
            self.stdout.write('Migrating existing challenges...')
            
            challenges = Challenge.objects.all()
            migrated_count = 0
            
            for challenge in challenges:
                try:
                    ensure_challenge_has_payment_tier(challenge)
                    migrated_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error migrating challenge {challenge.id} ({challenge.title}): {e}'
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully migrated {migrated_count} out of {challenges.count()} challenges'
                )
            )