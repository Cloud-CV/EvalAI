#!/usr/bin/env python
"""
Set end date for specified challenges and their phases.

Usage:
    # Dry run (default) - show what would be updated
    python scripts/tools/cleanup_data/set_challenge_end_date.py \
        --challenge-ids 1 2 3 --end-date "2026-01-16"

    # Execute - actually update the database
    python scripts/tools/cleanup_data/set_challenge_end_date.py \
        --challenge-ids 1 2 3 --end-date "2026-01-16" --execute

Run from project root in an environment with database access.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import pytz

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))

# Print early to show script is starting
print("Initializing script...", flush=True)
print(f"Project root: {PROJECT_ROOT}", flush=True)

# Setup Django - uses DJANGO_SETTINGS_MODULE from environment if set
print("Setting up Django...", flush=True)
import django  # noqa: E402

django.setup()
print("Django setup complete.", flush=True)

print("Importing models...", flush=True)
from challenges.models import Challenge, ChallengePhase  # noqa: E402

print("Models imported.", flush=True)


def parse_end_date(date_string: str) -> datetime:
    """
    Parse end date string and return datetime at 11:59:59 PM UTC.

    Args:
        date_string: Date string in format YYYY-MM-DD

    Returns:
        datetime object at 23:59:59 UTC
    """
    try:
        # Parse the date
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        # Set time to 23:59:59 UTC
        end_datetime = datetime.combine(
            date_obj.date(), datetime.max.time().replace(microsecond=0)
        )
        # Localize to UTC
        utc = pytz.UTC
        return utc.localize(end_datetime)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_string}. Expected format: YYYY-MM-DD"
        ) from e


def setup_logging(log_file_path: str) -> None:
    """
    Set up logging to write to both file and console.

    Args:
        log_file_path: Path to the log file
    """
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(
        log_file_path, mode="w", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main():
    parser = argparse.ArgumentParser(
        description="Set end date for specified challenges and their phases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--challenge-ids",
        type=int,
        nargs="+",
        required=True,
        help="List of challenge IDs to update (e.g., --challenge-ids 1 2 3)",
    )
    parser.add_argument(
        "--end-date",
        type=parse_end_date,
        required=True,
        help="End date in YYYY-MM-DD format (will be set to 11:59:59 PM UTC)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually update the database (default is dry run)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (default: auto-generated with timestamp)",
    )
    args = parser.parse_args()

    dry_run = not args.execute
    challenge_ids = args.challenge_ids
    target_end_date = args.end_date

    # Set up log file path
    if args.log_file:
        log_file_path = args.log_file
    else:
        # Generate log file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_str = "dryrun" if dry_run else "execute"
        log_file_path = os.path.join(
            SCRIPT_DIR, f"set_challenge_end_date_{mode_str}_{timestamp}.log"
        )

    # Set up logging
    print(f"Setting up logging to: {log_file_path}", flush=True)
    setup_logging(log_file_path)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info(
        f"Set End Date for Challenges - {'DRY RUN' if dry_run else 'EXECUTE'}"
    )
    logger.info(f"Challenge IDs: {challenge_ids}")
    logger.info(f"Target end date: {target_end_date} (11:59:59 PM UTC)")
    logger.info(f"Log file: {log_file_path}")
    logger.info("=" * 60)

    if dry_run:
        logger.info("")
        logger.info("*** DRY RUN - No changes will be made ***")
        logger.info("*** Use --execute to actually update ***")
        logger.info("")

    # Process challenges one at a time to minimize memory usage
    # Check each challenge ID individually instead of loading all into memory
    logger.info("Validating challenge IDs...")
    valid_challenge_ids = []
    missing_ids = []

    # Check each ID individually to avoid loading all at once
    for challenge_id in challenge_ids:
        if Challenge.objects.filter(id=challenge_id).exists():
            valid_challenge_ids.append(challenge_id)
        else:
            missing_ids.append(challenge_id)

    if missing_ids:
        logger.warning("")
        logger.warning(
            f"⚠️  WARNING: The following challenge IDs were not found: {missing_ids}"
        )
        if not valid_challenge_ids:
            logger.error("")
            logger.error("❌ No valid challenge IDs provided. Exiting.")
            return

    challenge_count = len(valid_challenge_ids)
    logger.info(f"Found {challenge_count} valid challenge(s)")

    if dry_run:
        # Dry run: use .values() to avoid model __init__ issues with .only()
        logger.info("")
        logger.info("Challenges to update:")
        total_phases = 0

        # Use .values() to get dictionaries instead of model instances
        # This avoids the __init__ recursion issue when using .only()
        logger.info("Fetching challenge details...")
        for challenge_data in (
            Challenge.objects.filter(id__in=valid_challenge_ids)
            .values("id", "title", "end_date")
            .order_by("id")
            .iterator(chunk_size=10)
        ):
            challenge_id_val = challenge_data["id"]
            logger.info(
                f"  Challenge {challenge_id_val}: {challenge_data['title']}"
            )
            logger.info(f"    Current end_date: {challenge_data['end_date']}")
            logger.info(f"    New end_date: {target_end_date}")

            # Count and process phases for this challenge
            logger.info(
                f"    Processing phases for challenge {challenge_id_val}..."
            )
            phase_count = ChallengePhase.objects.filter(
                challenge_id=challenge_id_val
            ).count()
            total_phases += phase_count

            if phase_count > 0:
                logger.info(f"    Phases for this challenge ({phase_count}):")
                # Process phases using .values() to avoid similar issues
                for phase_data in (
                    ChallengePhase.objects.filter(
                        challenge_id=challenge_id_val
                    )
                    .values("id", "name", "end_date")
                    .order_by("id")
                    .iterator(chunk_size=10)
                ):
                    logger.info(
                        f"      Phase {phase_data['id']}: {phase_data['name']}"
                    )
                    logger.info(
                        f"        Current end_date: {phase_data['end_date']}"
                    )
                    logger.info(f"        New end_date: {target_end_date}")

        logger.info("")
        logger.info(f"Total phases to update: {total_phases}")
        phase_count = total_phases
    else:
        # Execute: process one challenge at a time to minimize memory
        challenges_updated = 0
        phases_updated = 0

        logger.info("")
        logger.info("Updating challenges and phases...")

        for challenge_id in valid_challenge_ids:
            # Update challenge
            updated = Challenge.objects.filter(id=challenge_id).update(
                end_date=target_end_date
            )
            if updated:
                challenges_updated += 1
                logger.info(f"  Updated challenge {challenge_id}")

            # Update phases for this challenge
            phase_count_for_challenge = ChallengePhase.objects.filter(
                challenge_id=challenge_id
            ).update(end_date=target_end_date)
            phases_updated += phase_count_for_challenge

            if phase_count_for_challenge > 0:
                logger.info(
                    f"    Updated {phase_count_for_challenge} phase(s) for challenge {challenge_id}"
                )

        logger.info("")
        logger.info(f"Updated {challenges_updated} challenge(s)")
        logger.info(f"Updated {phases_updated} phase(s)")
        phase_count = phases_updated

    # Summary (avoid sorted() to save memory - just show lists)
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.info(f"Challenge IDs requested: {challenge_ids}")
    logger.info(f"Valid challenge IDs found: {valid_challenge_ids}")
    if missing_ids:
        logger.info(f"Missing challenge IDs: {missing_ids}")
    logger.info(f"Target end date: {target_end_date} (11:59:59 PM UTC)")
    logger.info(
        f"Challenges {'to update' if dry_run else 'updated'}: {challenge_count}"
    )
    logger.info(
        f"Phases {'to update' if dry_run else 'updated'}: {phase_count}"
    )
    logger.info("=" * 60)
    logger.info("Script completed successfully.")

    # Clean up references to free memory
    del valid_challenge_ids
    if missing_ids:
        del missing_ids


if __name__ == "__main__":
    main()
