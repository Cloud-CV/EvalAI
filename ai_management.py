import datetime
import json
import os
import random
import string
import uuid
import yaml

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
    ChallengeTemplate,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from challenges.utils import get_file_content
from hosts.models import ChallengeHostTeam, ChallengeHost
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam

fake = Factory.create()

NUMBER_OF_CHALLENGES = 1
NUMBER_OF_PHASES = 2
NUMBER_OF_DATASET_SPLITS = 2
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

def ai_suggest_challenge_title():
    # Placeholder for AI model integration to suggest challenge titles
    return fake.first_name() + " AI Challenge"

def ai_optimize_challenge_dates():
    # Placeholder for AI model integration to suggest optimal challenge dates
    start_date = timezone.now() - timedelta(days=random.randint(50, 150))
    end_date = timezone.now() + timedelta(days=random.randint(400, 600))
    return start_date, end_date

def ai_recommend_submission_status():
    # Placeholder for AI model integration to recommend submission statuses
    return random.choice([Submission.FINISHED, Submission.FAILED])

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
    # (Database deletion code remains unchanged)
    return True

def create_user(is_admin, username=""):
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
    team_name = "{} Host Team".format(fake.city())
    team = ChallengeHostTeam.objects.create(
        team_name=team_name, created_by=user
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

def create_challenge_host_participant_team(challenge_host_team):
    emails = challenge_host_team.get_all_challenge_host_email()
    team_name = "Host_{}_Team".format(random.randint(1, 100000))
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
    anon_counter = 0  # two private leaderboards
    for i in xrange(number_of_challenges):
        anonymous_leaderboard = False
        is_featured = False
        title = ai_suggest_challenge_title()
        if anon_counter < 2:
            anonymous_leaderboard = True
            anon_counter += 1

        start_date, end_date = ai_optimize_challenge_dates()

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
    uuid_stamp = uuid.uuid4().hex[0:10]
    slug = "{t}-{y}-{z}".format(t=title, y=year, z=uuid_stamp)
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
    )
    challenge.save()

    challenge.slug = slug
    challenge.participant_teams.add(participant_host_team)
    challenge.save()

    print(
        "Challenge created with title: {} creator: {} start_date: {} end_date: {}".format(
            title, host_team.team_name, start_date, end_date
        )
    )

def create_challenge_phases(challenge, number_of_phases=1):
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
    dataset_splits = []
    for split in range(number_of_splits):
        dataset_split = DatasetSplit.objects.create(
            name="Split {}".format(split + 1), split=split
        )
        dataset_splits.append(dataset_split)
    return dataset_splits

def load_challenge_configs():
    for path in CHALLENGE_CONFIG_PATHS:
        print("Loading challenge configs from:", path)
        for filename in os.listdir(path):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                with open(os.path.join(path, filename), "r") as file:
                    challenge_config = yaml.safe_load(file)
                    challenge_name = challenge_config.get("title", "Unnamed Challenge")
                    print(f"Challenge Name: {challenge_name}")
                    # Process challenge_config as needed

def main():
    if not check_database():
        print("Database not reset. Exiting.")
        return

    create_user(is_admin=True)
    create_user(is_admin=False, username="participant1")
    
    host_team = create_challenge_host_team(User.objects.first())
    participant_team = create_challenge_host_participant_team(host_team)

    create_challenges(
        number_of_challenges=NUMBER_OF_CHALLENGES,
        host_team=host_team,
        participant_host_team=participant_team,
    )
    load_challenge_configs()

if __name__ == "__main__":
    main()
