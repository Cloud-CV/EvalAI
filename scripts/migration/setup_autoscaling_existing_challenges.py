"""
One-time migration script to set up auto-scaling and EventBridge cleanup
schedules for all existing active challenges that have workers.

Run this after deploying the event-driven worker scaling changes:

    python manage.py shell < scripts/migration/setup_autoscaling_existing_challenges.py

Prerequisites:
- CHALLENGE_CLEANUP_LAMBDA_ARN environment variable must be set
- EVENTBRIDGE_SCHEDULER_ROLE_ARN environment variable must be set
- IAM permissions for application-autoscaling, cloudwatch, and scheduler
"""

from challenges.aws_utils import (
    schedule_challenge_cleanup,
    setup_auto_scaling_for_service,
)
from challenges.models import Challenge
from django.utils import timezone

# Only process active, Fargate-managed challenges that have workers
challenges = Challenge.objects.filter(
    workers__isnull=False,
    end_date__gt=timezone.now(),
    approved_by_admin=True,
    is_docker_based=False,
    uses_ec2_worker=False,
    remote_evaluation=False,
)

total = challenges.count()
success = 0
failures = []

print(f"Found {total} active challenges to migrate.")

for challenge in challenges:
    try:
        print(
            f"Setting up auto-scaling for challenge {challenge.pk} "
            f"({challenge.title})..."
        )
        setup_auto_scaling_for_service(challenge)
        schedule_challenge_cleanup(challenge)
        success += 1
        print("  -> Success")
    except Exception as e:
        failures.append({"challenge_pk": challenge.pk, "error": str(e)})
        print(f"  -> Failed: {e}")

print(f"\nMigration complete: {success}/{total} succeeded.")
if failures:
    print(f"Failures ({len(failures)}):")
    for f in failures:
        print(f"  Challenge {f['challenge_pk']}: {f['error']}")
