# Command to run : python manage.py shell --settings=settings.dev  < scripts/seed.py

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress

from datetime import timedelta
from faker import Factory

import random
import os

from challenges.models import Challenge, ChallengePhase, DatasetSplit, Leaderboard, ChallengePhaseSplit
from hosts.models import ChallengeHostTeam, ChallengeHost
from participants.models import Participant, ParticipantTeam


def create_admin_user():
    username = "admin"
    password = "password"
    email = "admin@gmail.com"
    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
        is_staff=True,
        is_superuser=True,
    )
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    print "Super user created with \n username: %s \n password: %s" % (username, password)


def create_user(username=""):
    fake = Factory.create()
    password = "password"
    email = "%s@gmail.com" % (username)
    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
    )
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    print "User created with \n username: %s \n email: %s \n password: %s" % (username, email, password)
    return user


def create_challenge_host_team(user):
    fake = Factory.create()
    team_name = "%s Host Team" % (fake.city())
    team = ChallengeHostTeam.objects.create(
        team_name=team_name,
        created_by=user,
    )
    print "Challenge Host Team created with \n team_name: %s \n created_by: %s" % (team_name, user.username)
    ChallengeHost.objects.create(user=user, team_name=team, status="Self", permissions="Admin")
    print "Challenge Host created with \n user: %s \n team_name: %s" % (user.username, team_name)
    return team


def create_challenges(number_of_challenges=3, host_team=None):
    fake = Factory.create()
    for i in xrange(number_of_challenges):
        if (i%3 == 0):
            create_challenge_object("%s Challenge" % (
                fake.first_name()),
                timezone.now() - timedelta(days=100),
                timezone.now() + timedelta(days=500),
                host_team
            )
        elif (i%3 == 1):
            create_challenge_object("%s Challenge" % (
                fake.first_name()),
                timezone.now() - timedelta(days=500),
                timezone.now() - timedelta(days=100),
                host_team
            )
        elif (i%3 == 2):
            create_challenge_object("%s Challenge" % (
                fake.first_name()),
                timezone.now() + timedelta(days=100),
                timezone.now() + timedelta(days=500),
                host_team
            )


def create_challenge_object(title, start_date, end_date, host_team):
    fake = Factory.create()
    evaluation_script = open(os.path.join(settings.BASE_DIR, 'examples', 'example1', 'string_matching.zip'), 'rb')
    created_challenge = Challenge.objects.create(
        title=title,
        short_description=fake.paragraph(),
        description=fake.paragraph(),
        terms_and_conditions=fake.paragraph(),
        submission_guidelines=fake.paragraph(),
        evaluation_details=fake.paragraph(),
        evaluation_script=SimpleUploadedFile(evaluation_script.name, evaluation_script.read()),
        creator=host_team,
        published=True,
        enable_forum=True,
        anonymous_leaderboard=False,
        start_date=start_date,
        end_date=end_date,
    )
    print "Challenge created with \n title: %s \n creator: %s \n start_date: %s \n end_date: %s"\
          % (title, host_team.team_name, start_date, end_date)


def create_challenge_phases(number_of_phases=1):
    fake = Factory.create()
    for i in range(number_of_phases):
        name = "%s Phase" % (fake.first_name())
        ChallengePhase.objects.create(
            name=name,
            description=fake.paragraph(),
            leaderboard_public=True,
            is_public=True,
            start_date=challenge.start_date,
            end_date=challenge.end_date,
            challenge=challenge,
            test_annotation=SimpleUploadedFile(fake.file_name(extension="txt"),
                                               "1\n2\n3\n4\n5\n6\n7\n8\n9\n10", content_type="text/plain"),
            codename="%s%d" % ("phase", i+1),
        )
        print "Challenge Phase created with \n name: %s \n challenge: %s" % (name, challenge.title)


def create_leaderboard():
    import json
    schema = {
        'labels': ['score',],
        'default_order_by': 'score',
    }
    leaderboard = Leaderboard.objects.create(
        schema=schema
    )
    print "Leaderboard created"
    return leaderboard


def create_dataset_splits(number_of_splits):
    for i in range(number_of_splits):
        name = "Split %d" % (DATASET_SPLIT_ITERATOR+1)
        codename = "%s%d" % ('split', DATASET_SPLIT_ITERATOR+1)
        DatasetSplit.objects.create(
            name=name,
            codename=codename,
        )
        DATASET_SPLIT_ITERATOR += 1
        print "Dataset Split created with \n name: %s \n codename: %s" % (name, codename)


def create_challenge_phase_splits(challenge_phase, leaderboard, dataset_split):
    ChallengePhaseSplit.objects.create(
        challenge_phase=challenge_phase,
        leaderboard=leaderboard,
        dataset_split=dataset_split,
        visibility=ChallengePhaseSplit.PUBLIC
    )
    print "Challenge Phase Split created with \n challenge_phase: %s \n dataset_split: %s" \
          % (challenge_phase.name, dataset_split.name)


def create_participant_team(user):
    fake = Factory.create()
    team_name = "%s Participant Team" % (fake.city())
    team = ParticipantTeam.objects.create(
        team_name=team_name,
        created_by=user,
    )
    print "Participant Team created with \n team_name: %s \n created_by: %s" % (team_name, user.username)
    Participant.objects.create(user=user, team=team, status="Self")
    print "Participant created with \n user: %s \n team_name: %s" % (user.username, team_name)
    return team


print "Starting database seeder, Hang on :)"

NUMBER_OF_CHALLENGES = 1
NUMBER_OF_PHASES = 2
NUMBER_OF_DATASET_SPLITS = 2
DATASET_SPLIT_ITERATOR = 0

create_admin_user()
host_user = create_user(username="host")
challenge_host_team = create_challenge_host_team(user=host_user)
create_challenges(number_of_challenges=NUMBER_OF_CHALLENGES, host_team=challenge_host_team)

challenges = Challenge.objects.all()
for challenge in challenges:

    # Create a leaderboard object for each challenge
    leaderboard = create_leaderboard()

    # Create Phases for a challenge
    create_challenge_phases(number_of_phases=NUMBER_OF_PHASES)

    # Create Dataset Split for each Challenge
    create_dataset_splits(number_of_splits=NUMBER_OF_DATASET_SPLITS)
    dataset_splits = DatasetSplit.objects.all().order_by('-created_at')[:NUMBER_OF_DATASET_SPLITS]

    # Create Challenge Phase Split for each Phase and Dataset Split
    challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
    for challenge_phase in challenge_phases:
        for dataset_split in dataset_splits:
            create_challenge_phase_splits(challenge_phase, leaderboard, dataset_split)

participant_user = create_user(username="participant")
participant_team = create_participant_team(user=participant_user)
