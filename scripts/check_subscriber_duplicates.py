#!/usr/bin/env python
"""
Script to check for duplicate email addresses in the Subscribers model
Run this before applying the unique constraint migration to ensure
there are no existing duplicates in the database.

Usage:
    python scripts/check_subscriber_duplicates.py
"""
import os
import sys

import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")
django.setup()

from django.db.models import Count

from apps.web.models import Subscribers


def check_duplicates():
    """Check for duplicate email addresses in Subscribers model"""
    duplicates = (
        Subscribers.objects.values("email")
        .annotate(count=Count("email"))
        .filter(count__gt=1)
        .order_by("-count")
    )

    if duplicates.exists():
        print(
            "⚠️  WARNING: Found duplicate email addresses in Subscribers table!"
        )
        print("\nDuplicates found:")
        print("-" * 50)
        for item in duplicates:
            print(f"Email: {item['email']}")
            print(f"Count: {item['count']}")
            print("-" * 50)

        print(
            "\n❌ You must resolve these duplicates before applying the "
            "unique constraint migration."
        )
        print("\nTo resolve duplicates, you can:")
        print("1. Keep the most recent subscriber and delete the rest")
        print("2. Manually review each duplicate in the Django admin panel")
        return False
    else:
        print("✅ No duplicate email addresses found!")
        print("It is safe to apply the unique constraint migration.")
        return True


if __name__ == "__main__":
    success = check_duplicates()
    sys.exit(0 if success else 1)
