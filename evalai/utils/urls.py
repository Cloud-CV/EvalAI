from enum import Enum


class URLS(Enum):
    login = "/api/auth/login"
    challenge_list = "/api/challenges/challenge/all"
    past_challenge_list = "/api/challenges/challenge/past"
    future_challenge_list = "/api/challenges/challenge/future"
    challenge_details = "/api/challenges/challenge/{}"
    challenge_phase_details = "/api/challenges/challenge/phase/{}/"
    participant_teams = "/api/participants/participant_team"
    host_teams = "/api/hosts/challenge_host_team/"
    host_challenges = "/api/challenges/challenge_host_team/{}/challenge"
    challenge_phase_split_detail = "/api/challenges/{}/challenge_phase_split"
    create_host_team = "/api/hosts/create_challenge_host_team"
    host_team_list = "/api/hosts/challenge_host_team/"
    participant_challenges = "/api/participants/participant_team/{}/challenge"
    participant_team_list = "/api/participants/participant_team"
    participate_in_a_challenge = (
        "/api/challenges/challenge/{}/participant_team/{}"
    )
    challenge_phase_list = "/api/challenges/challenge/{}/challenge_phase"
    challenge_phase_detail = "/api/challenges/challenge/{}/challenge_phase/{}"
    my_submissions = "/api/jobs/challenge/{}/challenge_phase/{}/submission/"
    make_submission = "/api/jobs/challenge/{}/challenge_phase/{}/submission/"
    get_submission = "/api/jobs/submission/{}"
    leaderboard = "/api/jobs/challenge_phase_split/{}/leaderboard/"
    get_aws_credentials = (
        "/api/challenges/phases/{}/participant_team/aws/credentials/"
    )
