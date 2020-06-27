# Command to run: python manage.py shell < scripts/migration/set_team_name_unique.py

from participants.models import ParticipantTeam
from hosts.models import ChallengeHostTeam


def make_team_name_unique():
    participant_team_list = []
    host_team_list = []
    participant_team_iter = 1

    participant_teams = ParticipantTeam.objects.all()
    try:
        for participant_team in participant_teams:
            if participant_team.team_name in participant_team_list:
                participant_team.team_name = "{0}_{1}".format(
                    participant_team.team_name, participant_team_iter
                )
                participant_team.save()
                participant_team_iter = participant_team_iter + 1
            else:
                participant_team_list.append(participant_team.team_name)
    except Exception as e:
        print(e)

    host_team_iter = 1
    host_teams = ChallengeHostTeam.objects.all()
    try:
        for host_team in host_teams:
            if host_team.team_name in host_team_list:
                host_team.team_name = "{0}_{1}".format(
                    host_team.team_name, host_team_iter
                )
                host_team.save()
                host_team_iter = host_team_iter + 1
            else:
                host_team_list.append(host_team.team_name)
    except Exception as e:
        print(e)


make_team_name_unique()
