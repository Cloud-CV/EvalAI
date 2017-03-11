# Command to run : python manage.py shell --settings=settings.dev  < scripts/seed.py

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress

from datetime import timedelta
from faker import Factory
import random

from challenges.models import Challenge, ChallengePhase, DatasetSplit, Leaderboard, ChallengePhaseSplit
from hosts.models import ChallengeHostTeam, ChallengeHost
from participants.models import Participant, ParticipantTeam


def create_admin_user():
    username = "admin"
    email = "admin@gmail.com"
    User.objects.create_user(
        email=email,
        username=username,
        password="password",
        is_staff=True,
        is_superuser=True,
    )
    print "Super user made with Username: admin and Password: password"


def create_user():
    fake = Factory.create()
    username = fake.user_name()
    email = "%s@gmail.com" % (username)
    user = User.objects.create_user(
        email=email,
        username=username,
        password="password",
    )
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    return user


def create_challenge_host_team(user):
    fake = Factory.create()
    team_name = "%s %ss" % (fake.city(), fake.color_name())
    team = ChallengeHostTeam.objects.create(
        team_name=team_name,
        created_by=user,
    )
    print "Challenge Host Team created"
    return team


def create_challenge_host(user, team):
    ChallengeHost.objects.create(user=user, team_name=team, status="Self", permissions="Admin")
    print "Challenge Host created"


def create_challenge(creator_team):
    fake = Factory.create()
    created_challenge = Challenge.objects.create(
        title="%s Challenge" % (fake.first_name()),
        description=fake.paragraph(),
        terms_and_conditions=fake.paragraph(),
        submission_guidelines=fake.paragraph(),
        evaluation_details=fake.paragraph(),
        evaluation_script=SimpleUploadedFile(fake.file_name(extension="txt"),
                                             'Dummy file content', content_type='text/plain'),
        creator=creator_team,
        published=True,
        enable_forum=True,
        anonymous_leaderboard=False,
        start_date=timezone.now() - timedelta(days=2),
        end_date=timezone.now() + timedelta(days=1),
    )
    print "Challenge created"
    return created_challenge


def create_challenge_phases(challenge, number_of_phases):
    fake = Factory.create()
    start_date = challenge.start_date
    end_date = challenge.end_date
    total_challenge_time = end_date - start_date
    single_phase_time = total_challenge_time / number_of_phases
    for i in range(number_of_phases):
        ChallengePhase.objects.create(
            name="%s Phase" % (fake.first_name()),
            description=fake.paragraph(),
            leaderboard_public=True,
            is_public=True,
            start_date=start_date + (single_phase_time * i),
            end_date=start_date + (single_phase_time * (i + 1)),
            challenge=challenge,
            test_annotation=SimpleUploadedFile(fake.file_name(extension="txt"),
                                               'Dummy file content', content_type='text/plain'),
            codename="%s%d" % (fake.random_letter(), fake.random_int(min=0, max=999)),
        )
    print "Challenge Phases created"


def create_leaderboard():
    fake = Factory.create()
    leaderboard = Leaderboard.objects.create(
        schema="Some random JSON"
    )
    print "Leaderboard created"
    return leaderboard


def create_dataset_splits(number_of_splits):
    fake = Factory.create()
    for i in range(number_of_splits):
        DatasetSplit.objects.create(
            name="%s Split" % (fake.first_name()),
            codename="%s%d" % (fake.random_letter(), fake.random_int(min=0, max=999)),
        )
    print "Dataset Splits created"


def create_challenge_phase_splits(leaderboard):
    challenge_phases = ChallengePhase.objects.all()
    for challenge_phase in challenge_phases:
        dataset_split = random.choice(DatasetSplit.objects.all())
        ChallengePhaseSplit.objects.create(
            challenge_phase=challenge_phase,
            leaderboard=leaderboard,
            dataset_split=dataset_split,
        )
    print "Challenge Phase Splits created"


def create_participant_team(user):
    fake = Factory.create()
    team_name = "%s %ss" % (fake.city(), fake.color_name())
    team = ParticipantTeam.objects.create(
        team_name=team_name,
        created_by=user,
    )
    print "Participant Team created"
    return team


def create_participant(user, team):
    Participant.objects.create(user=user, team=team, status="Self")
    print "Participant created"


print "Starting database seeder, Hang on :)"

create_admin_user()
host_user = create_user()
challenge_host_team = create_challenge_host_team(user=host_user)
create_challenge_host(user=host_user, team=challenge_host_team)
challenge = create_challenge(creator_team=challenge_host_team)
create_challenge_phases(challenge=challenge, number_of_phases=2)
leaderboard = create_leaderboard()
create_dataset_splits(number_of_splits=2)
create_challenge_phase_splits(leaderboard=leaderboard)
participant_user = create_user()
participant_team = create_participant_team(user=participant_user)
create_participant(user=participant_user, team=participant_team)
