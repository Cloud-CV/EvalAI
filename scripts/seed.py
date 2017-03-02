# Command to run : python manage.py shell --settings=settings.dev  < scripts/seed.py

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress

from datetime import timedelta
from faker import Factory
import random

from challenges.models import Challenge, ChallengePhase, DatasetSplit
from hosts.models import ChallengeHostTeam, ChallengeHost
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam
from web.models import Team, Contact


def seed_user_and_mail():
    fake = Factory.create()
    for i in range(20):
        username = fake.user_name()
        email = "%s@gmail.com" % (username)
        user = User.objects.create_user(
                email=email,
                username=username,
                password="password",
        )
        EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    print "User and Email model seeded."


def seed_challenge_host_team():
    fake = Factory.create()
    for i in range(20):
        user = random.choice(User.objects.filter(is_staff=False))
        team_name = "%s %ss" % (fake.city(), fake.color_name())
        team = ChallengeHostTeam.objects.create(
            team_name=team_name,
            created_by=user,
        )
        ChallengeHost.objects.create(user=user, team_name=team, status="Self", permissions="Admin")
    print "Challenge Host Team Model seeded."


def seed_participant_team():
    fake = Factory.create()
    for i in range(20):
        user = random.choice(User.objects.filter(is_staff=False))
        team_name = "%s %ss" % (fake.city(), fake.color_name())
        team = ParticipantTeam.objects.create(
            team_name=team_name,
            created_by=user,
        )
        Participant.objects.create(user=user, team=team, status="Self")
        number_of_participants = random.choice(range(1, 4))
        partcipants_to_be = User.objects.exclude(username=user.username, is_staff=True).all().order_by('?')[:number_of_participants]
        for partcipant in partcipants_to_be:
            Participant.objects.create(user=partcipant, team=team, status="Accepted")
    print "Participant Team Model seeded."


def seed_challenge():
    fake = Factory.create()
    for i in range(10):
        Challenge.objects.create(
            title="%s Challenge" % (fake.first_name()),
            description=fake.paragraph(),
            terms_and_conditions=fake.paragraph(),
            submission_guidelines=fake.paragraph(),
            evaluation_details=fake.paragraph(),
            creator=random.choice(ChallengeHostTeam.objects.all()),
            published=fake.boolean(chance_of_getting_true=70),
            enable_forum=fake.boolean(chance_of_getting_true=70),
            anonymous_leaderboard=fake.boolean(chance_of_getting_true=70),
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
    challenges = Challenge.objects.all()
    for challenge in challenges:
        participant_teams = ParticipantTeam.objects.order_by('?')[:random.choice(range(1,10))]
        for participant_team in participant_teams:
            challenge.participant_teams.add(participant_team)
            challenge.save()
    print "Challenge model seeded"


def seed_challenge_phase():
    fake = Factory.create()
    challenges = Challenge.objects.all()
    for challenge in challenges:
        start_date = challenge.start_date
        end_date = challenge.end_date
        number_of_phases = random.choice([1, 2, 3, 4])
        total_challenge_time = end_date - start_date
        single_phase_time = total_challenge_time / number_of_phases
        for i in range(number_of_phases):
            ChallengePhase.objects.create(
                name="%s Phase" % (fake.first_name()),
                description=fake.paragraph(),
                leaderboard_public=fake.boolean(chance_of_getting_true=70),
                is_public=fake.boolean(chance_of_getting_true=70),
                start_date=start_date + (single_phase_time * i),
                end_date=start_date + (single_phase_time * (i + 1)),
                challenge=challenge,
                test_annotation=SimpleUploadedFile(fake.file_name(extension="txt"),
                                                   'Dummy file content', content_type='text/plain'),
                codename="%s%d" % (fake.random_letter(), fake.random_int(min=0, max=999)),
            )
    print "Challenge Phase model seeded."


def seed_dataset_splits():
    fake = Factory.create()
    for i in range(10):
        DatasetSplit.objects.create(
            name="%s Split" % (fake.first_name()),
            codename="%s%d" % (fake.random_letter(), fake.random_int(min=0, max=999)),
        )
    print "Dataset Split model seeded."


def seed_submission():
    fake = Factory.create()
    challenge_phases = ChallengePhase.objects.all()
    for challenge_phase in challenge_phases:
        challenge_participant_teams = challenge_phase.challenge.participant_teams.all()
        for challenge_participant_team in challenge_participant_teams:
            participants = Participant.objects.filter(team=challenge_participant_team)
            for participant in participants:
                Submission.objects.create(
                    participant_team=challenge_participant_team,
                    challenge_phase=challenge_phase,
                    created_by=participant.user,
                    input_file=SimpleUploadedFile(fake.file_name(extension="txt"),
                                                  'Dummy File content', content_type='text/plain'),
                    status="submitting",
                )
    print "Submission model seeded."


def seed_team():
    fake = Factory.create()
    for i in range(10):
        Team.objects.create(
                name=fake.name(),
                email=fake.email(),
                description=fake.sentence(),
                headshot=SimpleUploadedFile(
                    name=fake.file_name(extension="png"),
                    content=open('frontend/src/images/deshraj.png', 'rb').read(),
                    content_type='image/png'
                ),
                github_url="www.github.com/%s" % (fake.user_name()),
                linkedin_url="www.linkedin.com/%s" % (fake.user_name()),
                personal_website=fake.url(),
                background_image=SimpleUploadedFile(
                    name=fake.file_name(extension="jpg"),
                    content=open('frontend/src/images/deshraj-profile.jpg', 'rb').read(),
                    content_type='image/jpg'
                ),
                team_type=random.choice(['Core Team', 'Contributor',]),
                visible=fake.boolean(chance_of_getting_true=70),
        )
    print "Team model seeded."


print "Starting database seeder, Hang on :)"

seed_user_and_mail()
seed_challenge_host_team()
seed_participant_team()
seed_challenge()
seed_challenge_phase()
seed_submission()
seed_dataset_splits()
seed_team()
