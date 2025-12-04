# Command to run : python manage.py shell  < scripts/seed.py
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

NUMBER_OF_CHALLENGES = 1
NUMBER_OF_PHASES = 2
NUMBER_OF_DATASET_SPLITS = 2
NUMBER_OF_SUBMISSIONS = 10  # Number of submissions to create for testing
DATASET_SPLIT_ITERATOR = 0
CHALLENGE_IMAGE_PATH = "examples/example1/test_zip_file/logo.png"
CHALLENGE_CONFIG_BASE_PATH = os.path.join(settings.BASE_DIR, "examples")
CHALLENGE_CONFIG_DIRS = ["example1", "example2"]
CHALLENGE_CONFIG_PATHS = [
    os.path.join(CHALLENGE_CONFIG_BASE_PATH, config)
    for config in CHALLENGE_CONFIG_DIRS
]


try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3


def check_database():
    if len(EmailAddress.objects.all()) > 0:
        print(
            "Are you sure you want to wipe the existing development database and reseed it? (Y/N)"
        )
        if True:  # Bypassed interactive prompt for non-interactive environments
            destroy_database()
            return True
        else:
            return False
    else:
        return True


def destroy_database():
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
    print(
        f"{'Super user' if is_admin else 'User'} was created with username: {username} password: password"
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
        f"Challenge Host Team created with team_name: {team_name} created_by: {user.username}"
    )
    ChallengeHost.objects.create(
        user=user,
        team_name=team,
        status=ChallengeHost.SELF,
        permissions=ChallengeHost.ADMIN,
    )
    print(
        f"Challenge Host created with user: {user.username} team_name: {team_name}"
    )
    return team


def create_challenge_host_participant_team(challenge_host_team):
    """
    Creates challenge host participant team and returns it.
    """
    emails = challenge_host_team.get_all_challenge_host_email()
    team_name = f"Host_{random.randint(1, 10)}_Team"
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
    number_of_challenges, host_team=None, participant_host_team=None
):
    """
    Creates past challenge, on-going challenge and upcoming challenge.
    """
    anon_counter = 0  # two private leaderboards
    for i in xrange(number_of_challenges):
        anonymous_leaderboard = False
        is_featured = False
        title = f"{fake.first_name()} Challenge"
        if anon_counter < 2:
            anonymous_leaderboard = True
            anon_counter += 1

        start_date = timezone.now() - timedelta(days=100)
        end_date = timezone.now() + timedelta(days=500)

        if i % 4 == 1:
            start_date = timezone.now() - timedelta(days=100)
            end_date = timezone.now() - timedelta(days=500)
        elif i % 4 == 2:
            start_date = timezone.now() + timedelta(days=100)
            end_date = timezone.now() + timedelta(days=500)
        elif i % 4 == 3:
            is_featured = True

        create_challenge(
            title,
            start_date,
            end_date,
            host_team,
            participant_host_team,
            anonymous_leaderboard,
            is_featured=is_featured,
        )


def create_challenge(
    title,
    start_date,
    end_date,
    host_team,
    participant_host_team,
    anon_leaderboard=False,
    is_featured=False,
):
    """
    Creates a challenge.
    """
    evaluation_script = open(
        os.path.join(
            settings.BASE_DIR,
            "examples",
            "example1",
            "sample_evaluation_script.zip",
        ),
        "rb",
    )
    queue = "".join(random.choice(string.ascii_letters) for _ in range(75))
    year = datetime.date.today().year
    # add UUID here
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
        f"Challenge created with title: {title} creator: {host_team.team_name} start_date: {start_date} end_date: {end_date}"
    )


def create_challenge_phases(challenge, number_of_phases=1):
    """
    Creates challenge phases for the created challenges and returns it.
    """
    challenge_phases = []
    for i in range(number_of_phases):
        name = f"{fake.first_name()} Phase"
        with open(
            os.path.join(
                settings.BASE_DIR,
                "examples",
                "example1",
                "test_annotation.txt",
            ),
            "rb",
        ) as data_file:
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
                f"Challenge Phase created with name: {name} challenge: {challenge.title}"
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


def create_leaderboard_data(challenge_phase_split, submission):
    result = {"score": random.randint(1, 100)}
    leaderboard_data = LeaderboardData.objects.create(
        challenge_phase_split=challenge_phase_split,
        submission=submission,
        leaderboard=challenge_phase_split.leaderboard,
        result=result,
        error=None,
        is_disabled=False,
    )
    return leaderboard_data


def create_dataset_splits(number_of_splits):
    """
    Creates dataset splits and returns it.
    """
    dataset_splits = []
    for split in range(number_of_splits):
        global DATASET_SPLIT_ITERATOR
        name = f"Split {DATASET_SPLIT_ITERATOR + 1}"
        codename = f"split{split + 1}"
        dataset_split = DatasetSplit.objects.create(
            name=name, codename=codename
        )
        dataset_splits.append(dataset_split)
        DATASET_SPLIT_ITERATOR += 1
        print(f"Dataset Split created with name: {name} codename: {codename}")
    return dataset_splits


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
        f"Challenge Phase Split created with challenge_phase: {challenge_phase.name} dataset_split: {dataset_split.name}"
    )
    return challenge_phase_split


def create_participant_team(user):
    """
    Creates participant team and returns it.
    """
    team_name = f"{fake.city()} Participant Team"
    team = ParticipantTeam.objects.create(team_name=team_name, created_by=user)
    print(
        f"Participant Team created with team_name: {team_name} created_by: {user.username}"
    )
    Participant.objects.create(user=user, team=team, status="Self")
    print(
        f"Participant created with user: {user.username} team_name: {team_name}"
    )
    return team


def create_submission(
    participant_user,
    participant_team,
    challenge_phase,
    dataset_splits,
    submission_status,
):
    status = submission_status
    submitted_at = timezone.now()
    started_at = timezone.now()
    completed_at = timezone.now()
    input_file = SimpleUploadedFile(
        "dummy_input.txt", b"file_content", content_type="text/plain"
    )
    output = []
    for dataset_split in dataset_splits:
        split_result = {dataset_split.codename: {"score": 0}}
        output.append(split_result)

    result = ["foo", "bar"]
    submission_result = json.dumps(result)

    submission = Submission.objects.create(
        participant_team=participant_team,
        challenge_phase=challenge_phase,
        created_by=participant_user,
        output=output,
        submitted_at=submitted_at,
        started_at=started_at,
        completed_at=completed_at,
        input_file=input_file,
        method_name=fake.first_name(),
        method_description=fake.paragraph(),
        project_url=fake.uri(),
        publication_url=fake.uri(),
        stdout_file=None,
        stderr_file=None,
        environment_log_file=None,
        submission_result_file=ContentFile(submission_result),
        submission_metadata_file=None,
        is_baseline=True,
        is_public=challenge_phase.is_submission_public,
    )
    submission.status = status
    submission.save()
    print(
        f"Submission created by user {participant_user.username} for phase {challenge_phase.name} of challenge {challenge_phase.challenge.title}."
    )

    return submission


def create_challenge_template(challenge_config_path):
    """
    Creates a challenge template

    Arguments:
        challenge_config_path {str}: path to the challenge config location having the config files and zip
    """
    title = f"{fake.first_name()} template"

    template_file = open(
        os.path.join(challenge_config_path, "test_zip_file.zip"), "rb"
    )

    challenge_config_yaml_file_path = os.path.join(
        challenge_config_path, "test_zip_file", "zip_challenge.yaml"
    )
    with open(challenge_config_yaml_file_path, "r") as stream:
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


def run(*args):
    with transaction.atomic():
        try:
            NUMBER_OF_CHALLENGES = int(args[0])
            status = check_database()
            if status is False:
                print("Seeding aborted.")
                return 0
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
                number_of_challenges=NUMBER_OF_CHALLENGES,
                host_team=challenge_host_team,
                participant_host_team=participant_host_team,
            )
            # Create multiple participant teams with multiple users for realistic testing
            print(
                f"Creating participant teams and users for {NUMBER_OF_SUBMISSIONS} submissions..."
            )
            participant_teams = []
            num_teams = min(
                50, max(10, NUMBER_OF_SUBMISSIONS // 100)
            )  # Create 10-50 teams

            for team_idx in range(num_teams):
                # Create team owner
                team_owner = create_user(
                    is_admin=False, username=f"participant_{team_idx}"
                )
                team = create_participant_team(user=team_owner)

                # Add 2-4 additional members to each team to test team member queries
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

            print(
                f"Created {num_teams} participant teams with multiple members"
            )

            # Fetch all the created challenges
            challenges = Challenge.objects.all()
            for challenge in challenges:
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
                dataset_splits = create_dataset_splits(
                    number_of_splits=NUMBER_OF_DATASET_SPLITS
                )

                # Create Challenge Phase Split for each Phase and Dataset Split
                for challenge_phase in challenge_phases:
                    for dataset_split in dataset_splits:
                        challenge_phase_split = create_challenge_phase_splits(
                            challenge_phase, leaderboard, dataset_split
                        )

                # Create submissions distributed across teams and phases using bulk operations
                print(
                    f"Creating {NUMBER_OF_SUBMISSIONS} submissions for challenge '{challenge.title}' using bulk operations..."
                )
                submissions_per_phase = NUMBER_OF_SUBMISSIONS // len(
                    challenge_phases
                )

                # Prepare dummy files for bulk creation
                result = ["foo", "bar"]
                submission_result = json.dumps(result)

                for phase_idx, challenge_phase in enumerate(challenge_phases):
                    # Determine how many submissions for this phase
                    if phase_idx == len(challenge_phases) - 1:
                        # Last phase gets any remaining submissions
                        num_submissions = NUMBER_OF_SUBMISSIONS - (
                            phase_idx * submissions_per_phase
                        )
                    else:
                        num_submissions = submissions_per_phase

                    print(
                        f"  Preparing {num_submissions} submissions for phase '{challenge_phase.name}'..."
                    )

                    # Build list of submissions to bulk create
                    submissions_to_create = []
                    output = []
                    for dataset_split in dataset_splits:
                        split_result = {dataset_split.codename: {"score": 0}}
                        output.append(split_result)

                    current_time = timezone.now()

                    for i in range(num_submissions):
                        # Distribute submissions across teams
                        team, team_owner = participant_teams[
                            i % len(participant_teams)
                        ]

                        # 80% finished, 20% failed for realistic distribution
                        submission_status = (
                            Submission.FAILED
                            if i % 5 == 0
                            else Submission.FINISHED
                        )

                        # Create submission object (not saved yet)
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

                    # Bulk create all submissions at once (much faster!)
                    print(
                        f"  Bulk creating {len(submissions_to_create)} submissions..."
                    )
                    created_submissions = Submission.objects.bulk_create(
                        submissions_to_create, batch_size=1000
                    )
                    print(
                        f"  ✓ Created {len(created_submissions)} submissions"
                    )

                    # Bulk create leaderboard data for finished submissions
                    print("  Creating leaderboard data...")
                    leaderboard_data_to_create = []

                    for submission in created_submissions:
                        if submission.status == Submission.FINISHED:
                            for dataset_split in dataset_splits:
                                challenge_phase_split = (
                                    ChallengePhaseSplit.objects.get(
                                        challenge_phase=challenge_phase,
                                        dataset_split=dataset_split,
                                        leaderboard=leaderboard,
                                    )
                                )
                                result = {"score": random.randint(1, 100)}
                                leaderboard_data = LeaderboardData(
                                    challenge_phase_split=challenge_phase_split,
                                    submission=submission,
                                    leaderboard=challenge_phase_split.leaderboard,
                                    result=result,
                                    error=None,
                                    is_disabled=False,
                                )
                                leaderboard_data_to_create.append(
                                    leaderboard_data
                                )

                    if leaderboard_data_to_create:
                        LeaderboardData.objects.bulk_create(
                            leaderboard_data_to_create, batch_size=1000
                        )
                        print(
                            f"  ✓ Created {len(leaderboard_data_to_create)} leaderboard entries"
                        )

                    print(f"  ✓ Completed phase '{challenge_phase.name}'")

            for path in CHALLENGE_CONFIG_PATHS:
                create_challenge_template(path)

            print("Database successfully seeded.")
        except Exception as e:
            print(e)
            raise
