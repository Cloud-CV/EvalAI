#!/usr/bin/env python3
"""
Simplified retention management script.

Usage:
  docker-compose exec django python scripts/manage_retention.py cleanup [--dry-run]
  docker-compose exec django python scripts/manage_retention.py status [--challenge-id <id>]
  docker-compose exec django python scripts/manage_retention.py set-retention <challenge_id> [--days <days>]
  docker-compose exec django python scripts/manage_retention.py consent <challenge_id> <username>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.common")
import django

django.setup()

from datetime import timedelta

from challenges.aws_utils import (
    cleanup_expired_submission_artifacts,
    record_host_retention_consent,
    set_cloudwatch_log_retention,
    update_submission_retention_dates,
)
from challenges.models import Challenge
from django.contrib.auth import get_user_model
from django.utils import timezone
from jobs.models import Submission


def cleanup(dry_run=False):
    """Clean up expired submission artifacts."""
    if dry_run:
        print("DRY RUN: Would clean up expired submissions")
        return

    result = cleanup_expired_submission_artifacts.delay()
    print(f"Cleanup task started: {result.id}")


def status(challenge_id=None):
    """Show retention status."""
    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            print(f"\nChallenge: {challenge.title} (ID: {challenge.pk})")
            print(
                f"Consent: {'Yes' if challenge.retention_policy_consent else 'No'}"
            )
            if challenge.retention_policy_consent:
                print(
                    f"Consent by: {challenge.retention_policy_consent_by.username if challenge.retention_policy_consent_by else 'Unknown'}"
                )
                print(
                    f"Consent date: {challenge.retention_policy_consent_date}"
                )

            submissions = Submission.objects.filter(
                challenge_phase__challenge=challenge
            )
            eligible = submissions.filter(
                retention_eligible_date__lte=timezone.now(),
                is_artifact_deleted=False,
            )
            print(
                f"Submissions: {submissions.count()} total, {eligible.count()} eligible for cleanup"
            )
        except Challenge.DoesNotExist:
            print(f"Challenge {challenge_id} not found")
    else:
        challenges = Challenge.objects.all()
        consented = challenges.filter(retention_policy_consent=True).count()
        total_submissions = Submission.objects.count()
        eligible_submissions = Submission.objects.filter(
            retention_eligible_date__lte=timezone.now(),
            is_artifact_deleted=False,
        ).count()

        print(f"\nOverall Status:")
        print(f"Challenges with consent: {consented}/{challenges.count()}")
        print(f"Total submissions: {total_submissions}")
        print(f"Eligible for cleanup: {eligible_submissions}")


def set_retention(challenge_id, days=None):
    """Set log retention for a challenge."""
    try:
        result = set_cloudwatch_log_retention(challenge_id, days)
        if result.get("success"):
            print(f"Success: Retention set to {result['retention_days']} days")
        else:
            print(f"Error: {result.get('error')}")
    except Exception as e:
        print(f"Error: {e}")


def consent(challenge_id, username):
    """Record consent for a challenge."""
    try:
        user = get_user_model().objects.get(username=username)
        result = record_host_retention_consent(challenge_id, user)
        if result.get("success"):
            print("Consent recorded successfully")
        else:
            print(f"Error: {result.get('error')}")
    except get_user_model().DoesNotExist:
        print(f"User {username} not found")
    except Exception as e:
        print(f"Error: {e}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    action = sys.argv[1]

    if action == "cleanup":
        dry_run = "--dry-run" in sys.argv
        cleanup(dry_run)

    elif action == "status":
        challenge_id = None
        if "--challenge-id" in sys.argv:
            idx = sys.argv.index("--challenge-id")
            if idx + 1 < len(sys.argv):
                challenge_id = int(sys.argv[idx + 1])
        status(challenge_id)

    elif action == "set-retention":
        if len(sys.argv) < 3:
            print("Usage: set-retention <challenge_id> [--days <days>]")
            return
        challenge_id = int(sys.argv[2])
        days = None
        if "--days" in sys.argv:
            idx = sys.argv.index("--days")
            if idx + 1 < len(sys.argv):
                days = int(sys.argv[idx + 1])
        set_retention(challenge_id, days)

    elif action == "consent":
        if len(sys.argv) < 4:
            print("Usage: consent <challenge_id> <username>")
            return
        challenge_id = int(sys.argv[2])
        username = sys.argv[3]
        consent(challenge_id, username)

    else:
        print(f"Unknown action: {action}")
        print(__doc__)


if __name__ == "__main__":
    main()
