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
    password = "password"
    email = "admin@gmail.com"
    User.objects.create_user(
        email=email,
        username=username,
        password=password,
        is_staff=True,
        is_superuser=True,
    )
    print "Super user created with \n username: %s \n password: %s" % (username, password)


def create_user():
    fake = Factory.create()
    username = fake.user_name()
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
    team_name = "%s %ss" % (fake.city(), fake.color_name())
    team = ChallengeHostTeam.objects.create(
        team_name=team_name,
        created_by=user,
    )
    print "Challenge Host Team created with \n team_name: %s \n created_by: %s" % (team_name, user.username)
    ChallengeHost.objects.create(user=user, team_name=team, status="Self", permissions="Admin")
    print "Challenge Host created with \n user: %s \n team_name: %s" % (user.username, team_name)
    return team


def create_challenges(creator_team):
    fake = Factory.create()
    present_challenge = create_challenge_object("%s Challenge" % (fake.first_name()),
                                                timezone.now() - timedelta(days=2),
                                                timezone.now() + timedelta(days=88),
                                                creator_team)
    past_challenge = create_challenge_object("%s Challenge" % (fake.first_name()),
                                             timezone.now() - timedelta(days=50),
                                             timezone.now() - timedelta(days=10),
                                             creator_team)
    future_challenge = create_challenge_object("%s Challenge" % (fake.first_name()),
                                               timezone.now() + timedelta(days=10),
                                               timezone.now() + timedelta(days=50),
                                               creator_team)
    return present_challenge, past_challenge, future_challenge


def create_challenge_object(title, start_date, end_date, creator_team):
    fake = Factory.create()
    created_challenge = Challenge.objects.create(
        title=title,
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
        start_date=start_date,
        end_date=end_date,
    )
    print "Challenge created with \n title: %s \n creator: %s \n start_date: %s \n end_date: %s"\
          % (title, creator_team.team_name, start_date, end_date)
    return created_challenge


def create_challenge_phases(challenge, number_of_phases):
    fake = Factory.create()
    start_date = challenge.start_date
    end_date = challenge.end_date
    total_challenge_time = end_date - start_date
    single_phase_time = total_challenge_time / number_of_phases
    for i in range(number_of_phases):
        name = "%s Phase" % (fake.first_name())
        ChallengePhase.objects.create(
            name=name,
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
        print "Challenge Phase created with \n name: %s \n challenge: %s" % (name, challenge.title)


def create_leaderboard():
    leaderboard = Leaderboard.objects.create(
        schema="Some random JSON"
    )
    print "Leaderboard created"
    return leaderboard


def create_dataset_splits(number_of_splits):
    fake = Factory.create()
    for i in range(number_of_splits):
        name = "%s Split" % (fake.first_name())
        codename = "%s%d" % (fake.random_letter(), fake.random_int(min=0, max=999))
        DatasetSplit.objects.create(
            name=name,
            codename=codename,
        )
        print "Dataset Split created with \n name: %s \n codename: %s" % (name, codename)


def create_challenge_phase_splits(leaderboard):
    challenge_phases = ChallengePhase.objects.all()
    for challenge_phase in challenge_phases:
        dataset_split = random.choice(DatasetSplit.objects.all())
        ChallengePhaseSplit.objects.create(
            challenge_phase=challenge_phase,
            leaderboard=leaderboard,
            dataset_split=dataset_split,
        )
        print "Challenge Phase Split created with \n challenge_phase: %s \n dataset_split: %s" \
              % (challenge_phase.name, dataset_split.name)


def create_participant_team(user):
    fake = Factory.create()
    team_name = "%s %ss" % (fake.city(), fake.color_name())
    team = ParticipantTeam.objects.create(
        team_name=team_name,
        created_by=user,
    )
    print "Participant Team created with \n team_name: %s \n created_by: %s" % (team_name, user.username)
    Participant.objects.create(user=user, team=team, status="Self")
    print "Participant created with \n user: %s \n team_name: %s" % (user.username, team_name)
    return team


print "Starting database seeder, Hang on :)"

create_admin_user()
host_user = create_user()
challenge_host_team = create_challenge_host_team(user=host_user)
present_challenge, past_challenge, future_challenge = create_challenges(creator_team=challenge_host_team)
create_challenge_phases(challenge=present_challenge, number_of_phases=2)
leaderboard = create_leaderboard()
create_dataset_splits(number_of_splits=2)
create_challenge_phase_splits(leaderboard=leaderboard)
participant_user = create_user()
participant_team = create_participant_team(user=participant_user)
