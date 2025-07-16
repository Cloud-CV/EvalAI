#!/usr/bin/env python
# Command to run: python manage.py shell < scripts/migration/populate_github_branch.py
"""
Populate existing challenges with github_branch="challenge" for backward compatibility.

This script should be run after the migration to ensure all existing challenges
have the github_branch field populated with the default value.
"""

import traceback

from challenges.models import Challenge
from django.db import models


def populate_github_branch_fields():
    """
    Populate existing challenges with empty github_branch fields to use "challenge" as default.
    """
    print("Starting github_branch field population...")

    challenges_to_update = (
        Challenge.objects.filter(github_repository__isnull=False)
        .exclude(github_repository="")
        .filter(
            models.Q(github_branch__isnull=True) | models.Q(github_branch="")
        )
    )

    count = challenges_to_update.count()

    if count == 0:
        print("No challenges found that need github_branch population.")
        return

    print(f"Found {count} challenges that need github_branch population.")

    updated_count = challenges_to_update.update(github_branch="challenge")

    print(
        f"Successfully updated {updated_count} challenges with github_branch='challenge'"
    )

    remaining_empty = (
        Challenge.objects.filter(github_repository__isnull=False)
        .exclude(github_repository="")
        .filter(
            models.Q(github_branch__isnull=True) | models.Q(github_branch="")
        )
        .count()
    )

    if remaining_empty == 0:
        print("✅ All challenges now have github_branch populated!")
    else:
        print(
            f"⚠️  Warning: {remaining_empty} challenges still have empty github_branch fields"
        )

    sample_challenges = (
        Challenge.objects.filter(github_repository__isnull=False)
        .exclude(github_repository="")
        .values("id", "title", "github_repository", "github_branch")[:5]
    )

    print("\nSample updated challenges:")
    for challenge in sample_challenges:
        print(
            f"  ID: {challenge['id']}, Title: {challenge['title']}, "
            f"Repo: {challenge['github_repository']}, Branch: {challenge['github_branch']}"
        )


try:
    populate_github_branch_fields()
    print("\n✅ Script completed successfully!")
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    print(traceback.print_exc())
