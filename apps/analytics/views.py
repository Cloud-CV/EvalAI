import csv
from collections import defaultdict
from datetime import timedelta

from accounts.permissions import HasVerifiedEmail
from challenges.models import LeaderboardData
from challenges.permissions import IsChallengeCreator
from challenges.utils import get_challenge_model, get_challenge_phase_model
from django.http import HttpResponse
from django.utils import timezone
from hosts.utils import is_user_a_host_of_challenge
from jobs.models import Submission
from jobs.serializers import (
    LastSubmissionDateTime,
    LastSubmissionDateTimeSerializer,
    SubmissionCount,
    SubmissionCountSerializer,
)
from participants.models import Participant
from participants.serializers import (
    ChallengeParticipantSerializer,
    ParticipantCount,
    ParticipantCountSerializer,
    ParticipantTeamCount,
    ParticipantTeamCountSerializer,
)
from participants.utils import get_participant_team_id_of_user_for_a_challenge
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import (
    ActivityHeatmap,
    ActivityHeatmapSerializer,
    ChallengePhaseSubmissionAnalytics,
    ChallengePhaseSubmissionAnalyticsSerializer,
    ChallengePhaseSubmissionCount,
    ChallengePhaseSubmissionCountSerializer,
    EvaluationTimeMetrics,
    EvaluationTimeMetricsSerializer,
    LastSubmissionTimestamp,
    LastSubmissionTimestampSerializer,
    LeaderboardProgression,
    LeaderboardProgressionSerializer,
    ScoreImprovements,
    SubmissionSuccessRate,
    SubmissionSuccessRateSerializer,
    TeamProgression,
)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_participant_team_count(request, challenge_pk):
    """
    Returns the number of participant teams in a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    participant_team_count = challenge.participant_teams.count()
    participant_team_count = ParticipantTeamCount(participant_team_count)
    serializer = ParticipantTeamCountSerializer(participant_team_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_participant_count(request, challenge_pk):
    """
    Returns the number of participants in a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    participant_teams = challenge.participant_teams.all()
    participant_count = Participant.objects.filter(
        team__in=participant_teams
    ).count()
    participant_count = ParticipantCount(participant_count)
    serializer = ParticipantCountSerializer(participant_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_submission_count(request, challenge_pk, duration):
    """
    Returns submission count for a challenge according to the duration
    Valid values for duration are all, daily, weekly and monthly.
    """
    # make sure that a valid url is requested.
    if duration.lower() not in ("all", "daily", "weekly", "monthly"):
        response_data = {"error": "Wrong URL pattern!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge = get_challenge_model(challenge_pk)

    challenge_phase_ids = challenge.challengephase_set.all().values_list(
        "id", flat=True
    )

    q_params = {"challenge_phase__id__in": challenge_phase_ids}
    since_date = None
    if duration.lower() == "daily":
        # Get the midnight time of the day
        since_date = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    elif duration.lower() == "weekly":
        since_date = (timezone.now() - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    elif duration.lower() == "monthly":
        since_date = (timezone.now() - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    # for `all` we dont need any condition in `q_params`
    if since_date:
        q_params["submitted_at__gte"] = since_date

    submission_count = Submission.objects.filter(**q_params).count()
    submission_count = SubmissionCount(submission_count)
    serializer = SubmissionCountSerializer(submission_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_challenge_phase_submission_count_by_team(
    request, challenge_pk, challenge_phase_pk
):
    """
    Returns submissions done by a participant team in a challenge phase.
    """
    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    participant_team = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )

    submissions = Submission.objects.filter(
        challenge_phase=challenge_phase,
        challenge_phase__challenge=challenge,
        participant_team=participant_team,
        ignore_submission=False,
    )
    participant_team_submissions = submissions.count()

    challenge_phase_submission_count = ChallengePhaseSubmissionCount(
        participant_team_submissions, challenge_phase.pk
    )
    try:
        serializer = ChallengePhaseSubmissionCountSerializer(
            challenge_phase_submission_count
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except:  # noqa: E722
        response_data = {"error": "Bad request. Please try again later!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_last_submission_time(
    request, challenge_pk, challenge_phase_pk, submission_by
):
    """
    Returns the last submission time for a particular challenge phase
    """
    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    # To get the last submission time by a user in a challenge phase.
    if submission_by == "user":
        last_submitted_at = Submission.objects.filter(
            created_by=request.user.pk,
            challenge_phase=challenge_phase,
            challenge_phase__challenge=challenge,
        )
        last_submitted_at = last_submitted_at.order_by("-submitted_at")[
            0
        ].created_at
        last_submitted_at = LastSubmissionDateTime(last_submitted_at)
        serializer = LastSubmissionDateTimeSerializer(last_submitted_at)
        return Response(serializer.data, status=status.HTTP_200_OK)

    response_data = {"error": "Page not found!"}
    return Response(response_data, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_last_submission_datetime_analysis(
    request, challenge_pk, challenge_phase_pk
):
    """
    API to fetch
    1. To get the last submission time in a challenge phase.
    2. To get the last submission time in a challenge.
    """

    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    submissions = Submission.objects.filter(
        challenge_phase__challenge=challenge
    )

    if not submissions:
        response_data = {
            "message": "You dont have any submissions in this challenge!"
        }
        return Response(response_data, status.HTTP_200_OK)

    last_submission_timestamp_in_challenge = submissions.order_by(
        "-submitted_at"
    )[0].created_at

    submissions_in_a_phase = submissions.filter(
        challenge_phase=challenge_phase
    )

    if not submissions_in_a_phase:
        last_submission_timestamp_in_challenge_phase = (
            "You dont have any submissions in this challenge phase!"
        )
    else:
        last_submission_timestamp_in_challenge_phase = (
            submissions_in_a_phase.order_by("-submitted_at")[0].created_at
        )

    last_submission_timestamp = LastSubmissionTimestamp(
        last_submission_timestamp_in_challenge,
        last_submission_timestamp_in_challenge_phase,
        challenge_phase.pk,
    )

    try:
        serializer = LastSubmissionTimestampSerializer(
            last_submission_timestamp
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except:  # noqa: E722
        response_data = {"error": "Bad request. Please try again later!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_challenge_phase_submission_analysis(
    request, challenge_pk, challenge_phase_pk
):
    """
    Returns:
    1. Total number of submissions in a challenge phase
    2. Number of teams which made submissions in a challenge phase
    3. Number of submissions with various status codes
    4. Number of flagged & public submissions in challenge phase
    """

    challenge = get_challenge_model(challenge_pk)
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)
    # Get the total submissions in a challenge phase
    submissions = Submission.objects.filter(
        challenge_phase=challenge_phase, challenge_phase__challenge=challenge
    )
    total_submissions = submissions.count()
    # Get the total participant teams in a challenge phase
    participant_team_count = (
        submissions.values("participant_team").distinct().count()
    )
    # Get flagged submission count
    flagged_submissions_count = submissions.filter(is_flagged=True).count()
    # Get public submission count
    public_submissions_count = submissions.filter(is_public=True).count()
    challenge_phase_submission_count = ChallengePhaseSubmissionAnalytics(
        total_submissions,
        participant_team_count,
        flagged_submissions_count,
        public_submissions_count,
        challenge_phase.pk,
    )
    try:
        serializer = ChallengePhaseSubmissionAnalyticsSerializer(
            challenge_phase_submission_count
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except ValueError:
        response_data = {"error": "Bad request. Please try again later!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def download_all_participants(request, challenge_pk):
    """
    Returns the List of Participant Teams and its details in csv format
    """
    if is_user_a_host_of_challenge(
        user=request.user, challenge_pk=challenge_pk
    ):
        challenge = get_challenge_model(challenge_pk)
        participant_teams = challenge.participant_teams.all().order_by(
            "-team_name"
        )
        teams = ChallengeParticipantSerializer(
            participant_teams, many=True, context={"request": request}
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            "attachment; filename=participant_teams_{0}.csv".format(
                challenge_pk
            )
        )
        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(["Team Name", "Team Members", "Email Id"])
        for team in teams.data:
            writer.writerow(
                [
                    team["team_name"],
                    ",".join(team["team_members"]),
                    ",".join(team["team_members_email_ids"]),
                ]
            )
        return response

    response_data = {
        "error": "Sorry, you are not authorized to make this request"
    }
    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


# Enhanced Analytics Views


def calculate_percentile(values, percentile):
    """Calculate the given percentile of a list of values."""
    if not values:
        return None
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_submission_success_rates(request, challenge_pk, challenge_phase_pk):
    """
    Returns submission success/failure rates and breakdown by status.
    """
    challenge = get_challenge_model(challenge_pk)
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    submissions = Submission.objects.filter(
        challenge_phase=challenge_phase,
        challenge_phase__challenge=challenge,
    )

    total_submissions = submissions.count()

    # Successful submissions are those with FINISHED status
    successful = submissions.filter(status=Submission.FINISHED).count()

    # Failed submissions include FAILED, CANCELLED statuses
    failed_statuses = [Submission.FAILED, Submission.CANCELLED]
    failed = submissions.filter(status__in=failed_statuses).count()

    # Calculate success rate
    success_rate = (
        round((successful / total_submissions) * 100, 2)
        if total_submissions > 0
        else 0.0
    )

    # Breakdown by failure type
    failure_breakdown = {}
    for status_choice in failed_statuses:
        count = submissions.filter(status=status_choice).count()
        if count > 0:
            failure_breakdown[status_choice] = count

    # Also include other non-success statuses
    other_statuses = [
        Submission.SUBMITTED,
        Submission.RUNNING,
        Submission.SUBMITTING,
        Submission.QUEUED,
    ]
    other_count = submissions.filter(status__in=other_statuses).count()
    if other_count > 0:
        failure_breakdown["pending"] = other_count

    submission_rate = SubmissionSuccessRate(
        phase_id=challenge_phase.pk,
        phase_name=challenge_phase.name,
        total_submissions=total_submissions,
        successful=successful,
        failed=failed,
        success_rate=success_rate,
        failure_breakdown=failure_breakdown,
    )

    serializer = SubmissionSuccessRateSerializer(submission_rate)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_evaluation_time_metrics(request, challenge_pk):
    """
    Returns average and percentile evaluation times for all phases.
    """
    challenge = get_challenge_model(challenge_pk)

    phases_data = []
    challenge_phases = challenge.challengephase_set.all()

    for phase in challenge_phases:
        # Get completed submissions with valid execution times
        submissions = Submission.objects.filter(
            challenge_phase=phase,
            challenge_phase__challenge=challenge,
            status=Submission.FINISHED,
            started_at__isnull=False,
            completed_at__isnull=False,
        )

        execution_times = []
        for sub in submissions:
            exec_time = sub.execution_time
            if exec_time != "None" and exec_time is not None:
                execution_times.append(float(exec_time))

        avg_time = (
            sum(execution_times) / len(execution_times)
            if execution_times
            else None
        )
        p50 = calculate_percentile(execution_times, 50)
        p90 = calculate_percentile(execution_times, 90)
        p99 = calculate_percentile(execution_times, 99)

        # Calculate trend for last 7 days
        trend = []
        for i in range(7):
            date = (timezone.now() - timedelta(days=i)).date()
            day_submissions = submissions.filter(
                completed_at__date=date, started_at__isnull=False
            )
            day_times = []
            for sub in day_submissions:
                exec_time = sub.execution_time
                if exec_time != "None" and exec_time is not None:
                    day_times.append(float(exec_time))
            if day_times:
                trend.append(
                    {"date": date, "avg_time": sum(day_times) / len(day_times)}
                )

        trend.reverse()  # Oldest first

        avg_time_rounded = round(avg_time, 2) if avg_time else None
        phase_metrics = EvaluationTimeMetrics(
            phase_id=phase.pk,
            phase_name=phase.name,
            avg_evaluation_time_seconds=avg_time_rounded,
            p50=round(p50, 2) if p50 else None,
            p90=round(p90, 2) if p90 else None,
            p99=round(p99, 2) if p99 else None,
            trend=trend,
        )
        phases_data.append(phase_metrics)

    serializer = EvaluationTimeMetricsSerializer(phases_data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_participant_activity_heatmap(request, challenge_pk):
    """
    Returns submission activity by hour of day and day of week.
    """
    challenge = get_challenge_model(challenge_pk)

    challenge_phase_ids = challenge.challengephase_set.all().values_list(
        "id", flat=True
    )

    submissions = Submission.objects.filter(
        challenge_phase__id__in=challenge_phase_ids
    )

    # Initialize heatmap with all days and hours
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    heatmap = {
        day: {str(hour).zfill(2): 0 for hour in range(24)} for day in days
    }

    # Count submissions by day and hour
    day_counts = defaultdict(int)
    hour_counts = defaultdict(int)

    for submission in submissions:
        submitted_at = submission.submitted_at
        day_name = days[submitted_at.weekday()]
        hour = str(submitted_at.hour).zfill(2)
        heatmap[day_name][hour] += 1
        day_counts[day_name] += 1
        hour_counts[hour] += 1

    # Find peak hours (top 3)
    sorted_hours = sorted(
        hour_counts.items(), key=lambda x: x[1], reverse=True
    )
    peak_hours = [
        f"{h}:00-{str(int(h)+1).zfill(2)}:00 UTC"
        for h, _ in sorted_hours[:3]
        if _ > 0
    ]

    # Find most active day
    most_active_day = (
        max(day_counts.items(), key=lambda x: x[1])[0]
        if day_counts
        else None
    )

    activity = ActivityHeatmap(
        challenge_id=challenge.pk,
        heatmap=heatmap,
        peak_hours=peak_hours,
        most_active_day=most_active_day,
    )

    serializer = ActivityHeatmapSerializer(activity)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_leaderboard_progression(request, challenge_pk, challenge_phase_pk):
    """
    Returns top teams' score progression over time.
    """
    get_challenge_model(challenge_pk)  # Validate challenge exists
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    # Get the challenge phase split for this phase
    phase_splits = challenge_phase.challengephasesplit_set.all()

    if not phase_splits.exists():
        response_data = {
            "message": "No leaderboard configuration found for this phase"
        }
        return Response(response_data, status=status.HTTP_200_OK)

    # Use the first phase split
    phase_split = phase_splits.first()

    # Get leaderboard data ordered by creation time
    leaderboard_entries = LeaderboardData.objects.filter(
        challenge_phase_split=phase_split,
        is_disabled=False,
    ).select_related(
        "submission__participant_team"
    ).order_by("created_at")

    # Track team progression
    team_progression = defaultdict(list)
    team_best_scores = {}

    for entry in leaderboard_entries:
        team_name = entry.submission.participant_team.team_name
        date = entry.created_at.date()

        # Get the score from result (assumes first metric in schema)
        result = entry.result
        if result and isinstance(result, dict):
            # Get first available score
            score = list(result.values())[0] if result else 0
        else:
            continue

        # Track best score per team
        if team_name not in team_best_scores:
            team_best_scores[team_name] = score
        else:
            if score > team_best_scores[team_name]:
                team_best_scores[team_name] = score

        team_progression[team_name].append({
            "date": date,
            "score": score,
        })

    # Get top 10 teams by best score
    sorted_teams = sorted(
        team_best_scores.items(), key=lambda x: x[1], reverse=True
    )[:10]

    # Build progression data with ranks
    top_teams_progression = []
    for rank, (team_name, _) in enumerate(sorted_teams, 1):
        progression_entries = []
        for entry in team_progression[team_name]:
            progression_entries.append({
                "date": entry["date"],
                "score": entry["score"],
                "rank": rank,
            })
        team_prog = TeamProgression(
            team_name=team_name,
            progression=progression_entries,
        )
        top_teams_progression.append(team_prog)

    # Calculate score improvements
    improvements = []
    for team_name, entries in team_progression.items():
        if len(entries) >= 2:
            first_score = entries[0]["score"]
            last_score = entries[-1]["score"]
            improvement = last_score - first_score
            improvements.append(
                {"team": team_name, "improvement": improvement}
            )

    biggest_jump = (
        max(improvements, key=lambda x: x["improvement"])
        if improvements
        else None
    )
    avg_improvement = (
        sum(i["improvement"] for i in improvements) / len(improvements)
        if improvements
        else 0.0
    )

    score_improvements = ScoreImprovements(
        biggest_jump=biggest_jump,
        avg_improvement=avg_improvement,
    )

    progression = LeaderboardProgression(
        phase_id=challenge_phase.pk,
        top_teams_progression=top_teams_progression,
        score_improvements=score_improvements,
    )

    serializer = LeaderboardProgressionSerializer(progression)
    return Response(serializer.data, status=status.HTTP_200_OK)
