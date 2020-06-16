# Command to run : python manage.py shell  < scripts/seed.py
import datetime
import json
import os
import random
import string
import uuid

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from allauth.account.models import EmailAddress
from faker import Factory

from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from hosts.models import ChallengeHostTeam, ChallengeHost
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam

fake = Factory.create()

NUMBER_OF_CHALLENGES = 1
NUMBER_OF_PHASES = 2
NUMBER_OF_DATASET_SPLITS = 2
DATASET_SPLIT_ITERATOR = 0

try:
    xrange   # Python 2
except NameError:
    xrange = range  # Python 3


def check_database():
    if len(EmailAddress.objects.all()) > 0:
        print(
            "Are you sure you want to wipe the existing development database and reseed it? (Y/N)"
        )
        if settings.TEST or input().lower() == "y":
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
        email = "%s@example.com" % (username)
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
        "{} was created with username: {} password: password".format(
            "Super user" if is_admin else "User", username
        )
    )
    return user


def create_challenge_host_team(user):
    """
    Creates challenge host team and returns it.
    """
    team_name = "{} Host Team".format(fake.city())
    team = ChallengeHostTeam.objects.create(
        team_name=team_name, created_by=user,
    )
    print(
        "Challenge Host Team created with team_name: {} created_by: {}".format(
            team_name, user.username
        )
    )
    ChallengeHost.objects.create(
        user=user,
        team_name=team,
        status=ChallengeHost.SELF,
        permissions=ChallengeHost.ADMIN,
    )
    print(
        "Challenge Host created with user: {} team_name: {}".format(
            user.username, team_name
        )
    )
    return team


def create_challenges(number_of_challenges, host_team=None):
    """
    Creates past challenge, on-going challenge and upcoming challenge.
    """
    anon_counter = 0  # two private leaderboards
    for i in xrange(number_of_challenges):
        is_leaderboard_anon = False
        if anon_counter < 2:
            is_leaderboard_anon = True
            anon_counter += 1
        else:
            is_leaderboard_anon = False

        if i % 3 == 0:
            create_challenge(
                "{} Challenge".format(fake.first_name()),
                timezone.now() - timedelta(days=100),
                timezone.now() + timedelta(days=500),
                host_team,
                is_leaderboard_anon,
            )
        elif i % 3 == 1:
            create_challenge(
                "{} Challenge".format(fake.first_name()),
                timezone.now() - timedelta(days=500),
                timezone.now() - timedelta(days=100),
                host_team,
                is_leaderboard_anon,
            )
        elif i % 3 == 2:
            create_challenge(
                "{} Challenge".format(fake.first_name()),
                timezone.now() + timedelta(days=100),
                timezone.now() + timedelta(days=500),
                host_team,
                is_leaderboard_anon,
            )


def create_challenge(title, start_date, end_date, host_team, anon_leaderboard):
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
    slug = "{t}-{y}-{z}".format(t=title, y=year, z=uuid_stamp)
    slug = slug.lower().replace(" ", "-")[:198]
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
        published=True,
        enable_forum=True,
        anonymous_leaderboard=anon_leaderboard,
        start_date=start_date,
        end_date=end_date,
        queue=queue,
    )
    challenge.save()

    challenge.slug = slug
    challenge.save()

    print(
        "Challenge created with title: {} creator: {} start_date: {} end_date: {}".format(
            title, host_team.team_name, start_date, end_date
        )
    )


def create_challenge_phases(challenge, number_of_phases=1):
    """
    Creates challenge phases for the created challenges and returns it.
    """
    challenge_phases = []
    for i in range(number_of_phases):
        name = "{} Phase".format(fake.first_name())
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
            slug = "{t}-{y}-{z}".format(t=name, y=year, z=uuid_stamp)
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
                codename="{}{}".format("phase", i + 1),
            )
            challenge_phases.append(challenge_phase)
            print(
                "Challenge Phase created with name: {} challenge: {}".format(
                    name, challenge.title
                )
            )
    return challenge_phases


def create_leaderboard():
    """
    Creates Leaderboard schema and returns it.
    """
    schema = {
        "labels": ["score", ],
        "default_order_by": "score",
    }
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
    )
    return leaderboard_data


def create_dataset_splits(number_of_splits):
    """
    Creates dataset splits and returns it.
    """
    dataset_splits = []
    for i in range(number_of_splits):
        global DATASET_SPLIT_ITERATOR
        name = "Split {}".format(DATASET_SPLIT_ITERATOR + 1)
        codename = "{}{}".format("split", DATASET_SPLIT_ITERATOR + 1)
        dataset_split = DatasetSplit.objects.create(
            name=name, codename=codename,
        )
        dataset_splits.append(dataset_split)
        DATASET_SPLIT_ITERATOR += 1
        print(
            "Dataset Split created with name: {} codename: {}".format(
                name, codename
            )
        )
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
        "Challenge Phase Split created with challenge_phase: {} dataset_split: {}".format(
            challenge_phase.name, dataset_split.name
        )
    )
    return challenge_phase_split


def create_participant_team(user):
    """
    Creates participant team and returns it.
    """
    team_name = "{} Participant Team".format(fake.city())
    team = ParticipantTeam.objects.create(
        team_name=team_name, created_by=user,
    )
    print(
        "Participant Team created with team_name: {} created_by: {}".format(
            team_name, user.username
        )
    )
    Participant.objects.create(user=user, team=team, status="Self")
    print(
        "Participant created with user: {} team_name: {}".format(
            user.username, team_name
        )
    )
    return team


def create_submission(participant_user, participant_team, challenge_phase,
                      dataset_splits, submission_status):
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
        submission_result_file=ContentFile(submission_result),
        submission_metadata_file=None,
        is_baseline=True,
    )
    submission.status = status
    submission.save()
    print(
        "Submission created by user {} for phase {} of challenge {}.".format(
            participant_user.username,
            challenge_phase.name,
            challenge_phase.challenge.title,
        )
    )

    return submission


def run(*args):
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
        # Create challenge
        create_challenges(
            number_of_challenges=NUMBER_OF_CHALLENGES,
            host_team=challenge_host_team,
        )
        participant_user = create_user(is_admin=False, username="participant")
        participant_team = create_participant_team(user=participant_user)

        # Fetch all the created challenges
        challenges = Challenge.objects.all()
        for challenge in challenges:
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
                for i in range(10):
                    if i < 5:  # ADDED: two failed submissions
                        submission = create_submission(
                            participant_user,
                            participant_team,
                            challenge_phase,
                            dataset_splits,
                            Submission.FAILED,
                        )
                    else:
                        submission = create_submission(
                            participant_user,
                            participant_team,
                            challenge_phase,
                            dataset_splits,
                            Submission.FINISHED,
                        )
                for dataset_split in dataset_splits:
                    challenge_phase_split = create_challenge_phase_splits(
                        challenge_phase, leaderboard, dataset_split
                    )
                    create_leaderboard_data(challenge_phase_split, submission)

        print("Database successfully seeded.")
    except Exception as e:
        print(e)
