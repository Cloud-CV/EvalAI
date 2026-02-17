# Command to run : python manage.py shell  < scripts/seed.py
# pylint: disable=too-many-lines
import datetime
import json
import os
import random
import string
import uuid
from datetime import timedelta

import yaml
from allauth.account.models import EmailAddress
from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    ChallengeTemplate,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from challenges.utils import get_file_content
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.utils import timezone
from faker import Factory
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam

fake = Factory.create()

NUMBER_OF_CHALLENGES = 500
# Challenge distribution percentages (calculated dynamically from total)
PRESENT_CHALLENGE_PERCENTAGE = 0.40  # 40%
FUTURE_CHALLENGE_PERCENTAGE = 0.20  # 20%
PAST_CHALLENGE_PERCENTAGE = 0.40  # 40%
NUMBER_OF_PHASES = 2
NUMBER_OF_DATASET_SPLITS = 2
NUMBER_OF_SUBMISSIONS = 2000  # Number of submissions to create for testing
CHALLENGE_IMAGE_PATH = "examples/example1/test_zip_file/logo.png"
CHALLENGE_CONFIG_BASE_PATH = os.path.join(settings.BASE_DIR, "examples")
CHALLENGE_CONFIG_DIRS = ["example1", "example2"]
CHALLENGE_CONFIG_PATHS = [
    os.path.join(CHALLENGE_CONFIG_BASE_PATH, config)
    for config in CHALLENGE_CONFIG_DIRS
]


def check_database():
    """Check if database has data and confirm before wiping."""
    if len(EmailAddress.objects.all()) > 0:
        print(
            "Are you sure you want to wipe the existing "
            "development database and reseed it? (Y/N)"
        )
        try:
            user_confirmed = settings.TEST or input().lower() == "y"
        except EOFError:
            # Non-interactive environment (e.g., Docker), skip seeding if data
            # exists
            print(
                "Database already has data. Skipping seed in non-interactive mode."
            )
            print(
                "To force re-seed, run: python manage.py flush && python manage.py seed"
            )
            return False
        if user_confirmed:
            destroy_database()
            return True
        return False
    return True


def destroy_database():
    """Destroy all existing database objects."""
    print("Destroying existing database...")
    print("Destroying Participant objects...")
    Participant.objects.all().delete()
    print("Destroying ParticipantTeam objects...")
    ParticipantTeam.objects.all().delete()
    print("Destroying ChallengePhaseSplit objects...")
    ChallengePhaseSplit.objects.all().delete()
    print("Destroying DatasetSplit objects...")
    DatasetSplit.objects.all().delete()
    print("Destroying ChallengePhase objects...")
    ChallengePhase.objects.all().delete()
    print("Destroying Leaderboard objects...")
    Leaderboard.objects.all().delete()
    print("Destroying Challenge objects...")
    Challenge.objects.all().delete()
    print("Destroying ChallengeHostTeam objects...")
    ChallengeHostTeam.objects.all().delete()
    print("Destroying ChallengeHost objects...")
    ChallengeHost.objects.all().delete()
    print("Destroying User objects...")
    User.objects.all().delete()
    print("Destroying EmailAddress objects...")
    EmailAddress.objects.all().delete()
    return True


def create_user(is_admin, username=""):
    """
    Creates superuser, participant user, host user and returns it.
    """
    if is_admin:
        username = "admin"
        email = "admin@example.com"
    else:
        email = f"{username}@example.com"
    user = User.objects.create_user(
        email=email,
        username=username,
        password="password",
        is_staff=is_admin,
        is_superuser=is_admin,
    )
    EmailAddress.objects.create(
        user=user, email=email, verified=True, primary=True
    )
    user_type = "Super user" if is_admin else "User"
    print(
        f"{user_type} was created with username: {username} password: password"
    )
    return user


def create_challenge_host_team(user):
    """
    Creates challenge host team and returns it.
    """
    team_name = f"{fake.city()} Host Team"
    team = ChallengeHostTeam.objects.create(
        team_name=team_name, created_by=user
    )
    print(
        f"Challenge Host Team created with team_name: {team_name} "
        f"created_by: {user.username}"
    )
    ChallengeHost.objects.create(
        user=user,
        team_name=team,
        status=ChallengeHost.SELF,
        permissions=ChallengeHost.ADMIN,
    )
    print(
        f"Challenge Host created with user: {user.username} "
        f"team_name: {team_name}"
    )
    return team


def create_challenge_host_participant_team(challenge_host_team):
    """
    Creates challenge host participant team and returns it.
    """
    emails = challenge_host_team.get_all_challenge_host_email()
    team_name = f"Host_{random.randint(1, 100000)}_Team"
    participant_host_team = ParticipantTeam(
        team_name=team_name, created_by=challenge_host_team.created_by
    )
    participant_host_team.save()
    for email in emails:
        user = User.objects.get(email=email)
        host = Participant(
            user=user, status=Participant.ACCEPTED, team=participant_host_team
        )
        host.save()
    return participant_host_team


def create_challenges(
    number_of_challenges,
    host_team=None,
    participant_host_team=None,
    num_present=None,
    num_future=None,
    num_past=None,
):
    """
    Creates past, on-going (present), and upcoming (future) challenges.

    Args:
        number_of_challenges: Total number of challenges to create
        host_team: The challenge host team
        participant_host_team: The participant host team
        num_present: Number of present/ongoing challenges (optional)
        num_future: Number of future/upcoming challenges (optional)
        num_past: Number of past challenges (optional)

    If num_present, num_future, and num_past are not provided, uses percentage
    distribution: 40% present, 20% future, 40% past.
    """
    # Use provided counts or calculate from percentages
    if (
        num_present is not None
        and num_future is not None
        and num_past is not None
    ):
        present_count = num_present
        future_count = num_future
        past_count = num_past
    else:
        # Calculate based on percentages: 40% present, 20% future, 40% past
        present_count = int(
            number_of_challenges * PRESENT_CHALLENGE_PERCENTAGE
        )
        future_count = int(number_of_challenges * FUTURE_CHALLENGE_PERCENTAGE)
        past_count = int(number_of_challenges * PAST_CHALLENGE_PERCENTAGE)
        # Handle rounding to ensure total equals number_of_challenges
        total_calculated = present_count + future_count + past_count
        difference = number_of_challenges - total_calculated
        # Adjust present count to make up any rounding difference
        if difference != 0:
            present_count += difference
            if present_count < 0:
                # If somehow we got negative, distribute the adjustment
                past_count += present_count
                present_count = 0

    anon_counter = 0  # two private leaderboards
    challenge_index = 0

    # Create present/ongoing challenges
    print(f"Creating {present_count} present/ongoing challenges...")
    for i in range(present_count):
        anonymous_leaderboard = anon_counter < 2
        if anonymous_leaderboard:
            anon_counter += 1
        is_featured = i < 5  # First 5 present challenges are featured

        title = f"{fake.first_name()} Challenge"
        start_date = timezone.now() - timedelta(days=random.randint(10, 100))
        end_date = timezone.now() + timedelta(days=random.randint(100, 500))

        challenge_config = {
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "host_team": host_team,
            "participant_host_team": participant_host_team,
            "anon_leaderboard": anonymous_leaderboard,
            "is_featured": is_featured,
        }
        create_challenge(challenge_config)
        challenge_index += 1

    # Create future/upcoming challenges
    print(f"Creating {future_count} future/upcoming challenges...")
    for i in range(future_count):
        title = f"{fake.first_name()} Challenge"
        start_date = timezone.now() + timedelta(days=random.randint(10, 100))
        end_date = timezone.now() + timedelta(days=random.randint(200, 500))

        challenge_config = {
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "host_team": host_team,
            "participant_host_team": participant_host_team,
            "anon_leaderboard": False,
            "is_featured": False,
        }
        create_challenge(challenge_config)
        challenge_index += 1

    # Create past challenges
    print(f"Creating {past_count} past challenges...")
    for i in range(past_count):
        title = f"{fake.first_name()} Challenge"
        start_date = timezone.now() - timedelta(days=random.randint(200, 500))
        end_date = timezone.now() - timedelta(days=random.randint(10, 100))

        challenge_config = {
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "host_team": host_team,
            "participant_host_team": participant_host_team,
            "anon_leaderboard": False,
            "is_featured": False,
        }
        create_challenge(challenge_config)
        challenge_index += 1

    print(
        f"Created {challenge_index} challenges: "
        f"{present_count} present, {future_count} future, {past_count} past"
    )


def create_challenge(config):
    """
    Creates a challenge.

    Args:
        config: Dictionary containing challenge configuration with keys:
            title, start_date, end_date, host_team, participant_host_team,
            anon_leaderboard, is_featured
    """
    title = config["title"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    host_team = config["host_team"]
    participant_host_team = config["participant_host_team"]
    anon_leaderboard = config.get("anon_leaderboard", False)
    is_featured = config.get("is_featured", False)

    eval_script_path = os.path.join(
        settings.BASE_DIR,
        "examples",
        "example1",
        "sample_evaluation_script.zip",
    )
    with open(eval_script_path, "rb") as evaluation_script:
        queue = "".join(random.choice(string.ascii_letters) for _ in range(75))
        year = datetime.date.today().year
        uuid_stamp = uuid.uuid4().hex[0:10]
        slug = f"{title}-{year}-{uuid_stamp}"
        slug = slug.lower().replace(" ", "-")[:198]
        image_file = ContentFile(
            get_file_content(CHALLENGE_IMAGE_PATH, "rb"), "logo.png"
        )
        challenge = Challenge(
            title=title,
            short_description=fake.paragraph(),
            description=fake.paragraph(),
            terms_and_conditions=fake.paragraph(),
            submission_guidelines=fake.paragraph(),
            evaluation_details=fake.paragraph(),
            evaluation_script=SimpleUploadedFile(
                evaluation_script.name, evaluation_script.read()
            ),
            approved_by_admin=True,
            leaderboard_description=fake.paragraph(),
            creator=host_team,
            domain="CV",
            list_tags=["Paper", "Dataset"],
            published=True,
            enable_forum=True,
            anonymous_leaderboard=anon_leaderboard,
            start_date=start_date,
            end_date=end_date,
            queue=queue,
            featured=is_featured,
            image=image_file,
            github_repository=f"evalai-examples/{slug}",
        )
        challenge.save()

        challenge.slug = slug
        challenge.participant_teams.add(participant_host_team)
        challenge.save()

    print(
        f"Challenge created with title: {title} "
        f"creator: {host_team.team_name} "
        f"start_date: {start_date} end_date: {end_date}"
    )


def create_challenge_phases(challenge, number_of_phases=1):
    """
    Creates challenge phases for the created challenges and returns it.
    """
    challenge_phases = []
    for i in range(number_of_phases):
        name = f"{fake.first_name()} Phase"
        annotation_path = os.path.join(
            settings.BASE_DIR,
            "examples",
            "example1",
            "test_annotation.txt",
        )
        with open(annotation_path, "rb") as data_file:
            year = datetime.date.today().year
            uuid_stamp = uuid.uuid4().hex[0:10]
            slug = f"{name}-{year}-{uuid_stamp}"
            slug = slug.lower().replace(" ", "-")
            data = data_file.read()
            data = data or None
            challenge_phase = ChallengePhase.objects.create(
                name=name,
                slug=slug,
                description=fake.paragraph(),
                leaderboard_public=True,
                is_public=True,
                is_submission_public=True,
                start_date=challenge.start_date,
                end_date=challenge.end_date,
                challenge=challenge,
                test_annotation=SimpleUploadedFile(
                    fake.file_name(extension="txt"),
                    data,
                    content_type="text/plain",
                ),
                codename=f"phase{i + 1}",
            )
            challenge_phases.append(challenge_phase)
            print(
                f"Challenge Phase created with name: {name} "
                f"challenge: {challenge.title}"
            )
    return challenge_phases


def create_leaderboard():
    """
    Creates Leaderboard schema and returns it.
    """
    schema = {"labels": ["score"], "default_order_by": "score"}
    leaderboard = Leaderboard.objects.create(schema=schema)
    print("Leaderboard created")
    return leaderboard


def create_dataset_splits(number_of_splits, split_iterator=0):
    """
    Creates dataset splits and returns it.

    Args:
        number_of_splits: Number of splits to create
        split_iterator: Starting iterator value for split naming

    Returns:
        Tuple of (dataset_splits list, updated split_iterator)
    """
    dataset_splits = []
    for split in range(number_of_splits):
        name = f"Split {split_iterator + 1}"
        codename = f"split{split + 1}"
        dataset_split = DatasetSplit.objects.create(
            name=name, codename=codename
        )
        dataset_splits.append(dataset_split)
        split_iterator += 1
        print(f"Dataset Split created with name: {name} codename: {codename}")
    return dataset_splits, split_iterator


def create_challenge_phase_splits(challenge_phase, leaderboard, dataset_split):
    """
    Creates a challenge phase split.
    """
    challenge_phase_split = ChallengePhaseSplit.objects.create(
        challenge_phase=challenge_phase,
        leaderboard=leaderboard,
        dataset_split=dataset_split,
        visibility=ChallengePhaseSplit.PUBLIC,
    )
    print(
        f"Challenge Phase Split created with "
        f"challenge_phase: {challenge_phase.name} "
        f"dataset_split: {dataset_split.name}"
    )
    return challenge_phase_split


def create_participant_team(user, team_idx=None):
    """
    Creates participant team and returns it.
    """
    # Include team_idx in name to ensure uniqueness when creating many teams
    if team_idx is not None:
        team_name = f"{fake.city()} Participant Team {team_idx}"
    else:
        team_name = f"{fake.city()} Participant Team"
    team = ParticipantTeam.objects.create(team_name=team_name, created_by=user)
    print(
        f"Participant Team created with team_name: {team_name} "
        f"created_by: {user.username}"
    )
    Participant.objects.create(user=user, team=team, status="Self")
    print(
        f"Participant created with user: {user.username} "
        f"team_name: {team_name}"
    )
    return team


def create_challenge_template(challenge_config_path):
    """
    Creates a challenge template.

    Args:
        challenge_config_path: path to the challenge config location
    """
    title = f"{fake.first_name()} template"
    template_path = os.path.join(challenge_config_path, "test_zip_file.zip")

    with open(template_path, "rb") as template_file:
        challenge_config_yaml_file_path = os.path.join(
            challenge_config_path, "test_zip_file", "zip_challenge.yaml"
        )
        with open(
            challenge_config_yaml_file_path, "r", encoding="utf-8"
        ) as stream:
            yaml_file_data = yaml.safe_load(stream)

        challenge_image_file_path = os.path.join(
            challenge_config_path, "test_zip_file", yaml_file_data["image"]
        )
        image_file = ContentFile(
            get_file_content(challenge_image_file_path, "rb"), "logo.png"
        )

        dataset = fake.first_name()
        phases = len(yaml_file_data["challenge_phases"])
        splits = len(yaml_file_data["dataset_splits"])

        year = datetime.date.today().year
        uuid_stamp = uuid.uuid4().hex[0:10]
        slug = f"{title}-{year}-{uuid_stamp}"

        challenge_template = ChallengeTemplate.objects.create(
            title=title,
            template_file=SimpleUploadedFile(
                template_file.name, template_file.read()
            ),
            is_active=True,
            image=image_file,
            dataset=dataset,
            eval_metrics=["Accuracy", "F1"],
            phases=phases,
            splits=splits,
            slug=slug,
        )

        challenge_template.save()

    print(f"Challenge template {challenge_template.title} created.")
    return challenge_template


def _create_participant_teams(num_teams):
    """Create participant teams with members."""
    participant_teams = []
    for team_idx in range(num_teams):
        team_owner = create_user(
            is_admin=False, username=f"participant_{team_idx}"
        )
        team = create_participant_team(user=team_owner, team_idx=team_idx)

        # Add 2-4 additional members to each team
        num_members = random.randint(2, 4)
        for member_idx in range(num_members):
            member_user = create_user(
                is_admin=False,
                username=f"participant_{team_idx}_member_{member_idx}",
            )
            Participant.objects.create(
                user=member_user,
                team=team,
                status=Participant.ACCEPTED,
            )

        participant_teams.append((team, team_owner))

    print(f"Created {num_teams} participant teams with multiple members")
    return participant_teams


def _create_bulk_submissions(
    challenge_phase, participant_teams, dataset_splits, num_submissions
):
    """Create submissions in bulk for a challenge phase."""
    result = ["foo", "bar"]
    submission_result = json.dumps(result)

    print(
        f"  Preparing {num_submissions} submissions "
        f"for phase '{challenge_phase.name}'..."
    )

    submissions_to_create = []
    output = []
    for dataset_split in dataset_splits:
        split_result = {dataset_split.codename: {"score": 0}}
        output.append(split_result)

    current_time = timezone.now()

    for i in range(num_submissions):
        team, team_owner = participant_teams[i % len(participant_teams)]

        # 80% finished, 20% failed for realistic distribution
        submission_status = (
            Submission.FAILED if i % 5 == 0 else Submission.FINISHED
        )

        submission = Submission(
            participant_team=team,
            challenge_phase=challenge_phase,
            created_by=team_owner,
            output=output,
            submitted_at=current_time,
            started_at=current_time,
            completed_at=current_time,
            input_file=SimpleUploadedFile(
                f"dummy_input_{i}.txt",
                b"file_content",
                content_type="text/plain",
            ),
            method_name=fake.first_name(),
            method_description=fake.paragraph(),
            project_url=fake.uri(),
            publication_url=fake.uri(),
            submission_result_file=ContentFile(
                submission_result, f"result_{i}.json"
            ),
            is_baseline=True,
            is_public=challenge_phase.is_submission_public,
            status=submission_status,
        )
        submissions_to_create.append(submission)

    print(f"  Bulk creating {len(submissions_to_create)} submissions...")
    created_submissions = Submission.objects.bulk_create(
        submissions_to_create, batch_size=1000
    )
    print(f"  ✓ Created {len(created_submissions)} submissions")

    return created_submissions


def _create_bulk_leaderboard_data(
    created_submissions, challenge_phase, dataset_splits, leaderboard
):
    """Create leaderboard data in bulk for finished submissions."""
    print("  Creating leaderboard data...")
    leaderboard_data_to_create = []

    for submission in created_submissions:
        if submission.status == Submission.FINISHED:
            for dataset_split in dataset_splits:
                cps = ChallengePhaseSplit.objects.get(
                    challenge_phase=challenge_phase,
                    dataset_split=dataset_split,
                    leaderboard=leaderboard,
                )
                result = {"score": random.randint(1, 100)}
                leaderboard_data = LeaderboardData(
                    challenge_phase_split=cps,
                    submission=submission,
                    leaderboard=cps.leaderboard,
                    result=result,
                    error=None,
                    is_disabled=False,
                )
                leaderboard_data_to_create.append(leaderboard_data)

    if leaderboard_data_to_create:
        LeaderboardData.objects.bulk_create(
            leaderboard_data_to_create, batch_size=1000
        )
        print(
            f"  ✓ Created {len(leaderboard_data_to_create)} "
            f"leaderboard entries"
        )


def _process_challenge(challenge, participant_teams, split_iterator):
    """Process a single challenge: create phases, splits, submissions."""
    # Add participant teams to challenge
    for team, _ in participant_teams:
        challenge.participant_teams.add(team)

    # Create a leaderboard object for each challenge
    leaderboard = create_leaderboard()

    # Create Phases for a challenge
    challenge_phases = create_challenge_phases(
        challenge, number_of_phases=NUMBER_OF_PHASES
    )

    # Create Dataset Split for each Challenge
    dataset_splits, split_iterator = create_dataset_splits(
        number_of_splits=NUMBER_OF_DATASET_SPLITS,
        split_iterator=split_iterator,
    )

    # Create Challenge Phase Split for each Phase and Dataset Split
    for challenge_phase in challenge_phases:
        for dataset_split in dataset_splits:
            create_challenge_phase_splits(
                challenge_phase, leaderboard, dataset_split
            )

    # Create submissions
    print(
        f"Creating {NUMBER_OF_SUBMISSIONS} submissions for "
        f"challenge '{challenge.title}' using bulk operations..."
    )
    submissions_per_phase = NUMBER_OF_SUBMISSIONS // len(challenge_phases)

    for phase_idx, challenge_phase in enumerate(challenge_phases):
        if phase_idx == len(challenge_phases) - 1:
            num_submissions = NUMBER_OF_SUBMISSIONS - (
                phase_idx * submissions_per_phase
            )
        else:
            num_submissions = submissions_per_phase

        created_submissions = _create_bulk_submissions(
            challenge_phase, participant_teams, dataset_splits, num_submissions
        )

        _create_bulk_leaderboard_data(
            created_submissions, challenge_phase, dataset_splits, leaderboard
        )

        print(f"  ✓ Completed phase '{challenge_phase.name}'")

    return split_iterator


def run(*args):
    """Main entry point for the seed script."""
    with transaction.atomic():
        try:
            # Use command line arg if provided, otherwise use default constant
            num_challenges = int(args[0]) if args else NUMBER_OF_CHALLENGES
            status = check_database()
            if status is False:
                print("Seeding aborted.")
                return None
            print("Seeding...")

            # Create superuser
            create_user(is_admin=True)

            # Create host user
            host_user = create_user(is_admin=False, username="host")

            # Create challenge host team with challenge host
            challenge_host_team = create_challenge_host_team(user=host_user)

            # Create challenge participant team for challenge host
            participant_host_team = create_challenge_host_participant_team(
                challenge_host_team
            )

            # Create challenge
            create_challenges(
                number_of_challenges=num_challenges,
                host_team=challenge_host_team,
                participant_host_team=participant_host_team,
            )

            # Create participant teams
            print(
                f"Creating participant teams and users for "
                f"{NUMBER_OF_SUBMISSIONS} submissions..."
            )
            num_teams = min(50, max(10, NUMBER_OF_SUBMISSIONS // 100))
            participant_teams = _create_participant_teams(num_teams)

            # Process all challenges
            split_iterator = 0
            challenges = Challenge.objects.all()
            for challenge in challenges:
                split_iterator = _process_challenge(
                    challenge, participant_teams, split_iterator
                )

            # Create challenge templates
            for path in CHALLENGE_CONFIG_PATHS:
                create_challenge_template(path)

            print("Database successfully seeded.")
            return None
        except Exception as exc:
            print(exc)
            raise
