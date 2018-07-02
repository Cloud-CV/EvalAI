from enum import Enum


class URLS(Enum):
    challenge_list = "/api/challenges/challenge/all"
    past_challenge_list = "/api/challenges/challenge/past"
    future_challenge_list = "/api/challenges/challenge/future"
    participant_teams = "/api/participants/participant_team"
    host_teams = "/api/hosts/challenge_host_team/"
    host_challenges = "/api/challenges/challenge_host_team/{}/challenge"
    participant_challenges = "/api/participants/participant_team/{}/challenge"
    participant_team_list = "/api/participants/participant_team"
    participate_in_a_challenge = "/api/challenges/challenge/{}/participant_team/{}"
    challenge_phase_list = "/api/challenges/challenge/{}/challenge_phase"
    challenge_phase_detail = "/api/challenges/challenge/{}/challenge_phase/{}"
    my_submissions = "/api/jobs/challenge/{}/challenge_phase/{}/submission/"
