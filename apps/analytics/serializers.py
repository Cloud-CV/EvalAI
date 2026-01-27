from rest_framework import serializers


class ChallengePhaseSubmissionAnalytics:
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        total_submissions,
        participant_team_count,
        flagged_submissions_count,
        public_submissions_count,
        challenge_phase_pk,
    ):
        self.total_submissions = total_submissions
        self.participant_team_count = participant_team_count
        self.flagged_submissions_count = flagged_submissions_count
        self.public_submissions_count = public_submissions_count
        self.challenge_phase = challenge_phase_pk


class ChallengePhaseSubmissionAnalyticsSerializer(serializers.Serializer):
    total_submissions = serializers.IntegerField()
    participant_team_count = serializers.IntegerField()
    flagged_submissions_count = serializers.IntegerField()
    public_submissions_count = serializers.IntegerField()
    challenge_phase = serializers.IntegerField()


class ChallengePhaseSubmissionCount:
    def __init__(self, participant_team_submission_count, challenge_phase_pk):
        self.participant_team_submission_count = (
            participant_team_submission_count
        )
        self.challenge_phase = challenge_phase_pk


class ChallengePhaseSubmissionCountSerializer(serializers.Serializer):
    participant_team_submission_count = serializers.IntegerField()
    challenge_phase = serializers.IntegerField()


class LastSubmissionTimestamp:
    def __init__(
        self,
        last_submission_timestamp_in_challenge,
        last_submission_timestamp_in_challenge_phase,
        challenge_phase_pk,
    ):
        self.last_submission_timestamp_in_challenge = (
            last_submission_timestamp_in_challenge
        )
        self.last_submission_timestamp_in_challenge_phase = (
            last_submission_timestamp_in_challenge_phase
        )
        self.challenge_phase = challenge_phase_pk


class LastSubmissionTimestampSerializer(serializers.Serializer):
    last_submission_timestamp_in_challenge = serializers.DateTimeField(
        format=None
    )
    last_submission_timestamp_in_challenge_phase = serializers.DateTimeField(
        format=None
    )
    challenge_phase = serializers.IntegerField()


# Enhanced Analytics Serializers


class SubmissionSuccessRate:
    """Data class for submission success/failure rates per phase."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        phase_id,
        phase_name,
        total_submissions,
        successful,
        failed,
        success_rate,
        failure_breakdown,
    ):
        self.phase_id = phase_id
        self.phase_name = phase_name
        self.total_submissions = total_submissions
        self.successful = successful
        self.failed = failed
        self.success_rate = success_rate
        self.failure_breakdown = failure_breakdown


class SubmissionSuccessRateSerializer(serializers.Serializer):
    phase_id = serializers.IntegerField()
    phase_name = serializers.CharField()
    total_submissions = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    success_rate = serializers.FloatField()
    failure_breakdown = serializers.DictField(child=serializers.IntegerField())


class EvaluationTimeMetrics:
    """Data class for evaluation time metrics per phase."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        phase_id,
        phase_name,
        avg_evaluation_time_seconds,
        p50,
        p90,
        p99,
        trend,
    ):
        self.phase_id = phase_id
        self.phase_name = phase_name
        self.avg_evaluation_time_seconds = avg_evaluation_time_seconds
        self.p50 = p50
        self.p90 = p90
        self.p99 = p99
        self.trend = trend


class EvaluationTimeTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    avg_time = serializers.FloatField()


class EvaluationTimeMetricsSerializer(serializers.Serializer):
    phase_id = serializers.IntegerField()
    phase_name = serializers.CharField()
    avg_evaluation_time_seconds = serializers.FloatField(allow_null=True)
    p50 = serializers.FloatField(allow_null=True)
    p90 = serializers.FloatField(allow_null=True)
    p99 = serializers.FloatField(allow_null=True)
    trend = EvaluationTimeTrendSerializer(many=True)


class ActivityHeatmap:
    """Data class for participant activity heatmap."""

    def __init__(
        self,
        challenge_id,
        heatmap,
        peak_hours,
        most_active_day,
    ):
        self.challenge_id = challenge_id
        self.heatmap = heatmap
        self.peak_hours = peak_hours
        self.most_active_day = most_active_day


class ActivityHeatmapSerializer(serializers.Serializer):
    challenge_id = serializers.IntegerField()
    heatmap = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField())
    )
    peak_hours = serializers.ListField(child=serializers.CharField())
    most_active_day = serializers.CharField(allow_null=True)


class TeamProgression:
    """Data class for a single team's progression."""

    def __init__(self, team_name, progression):
        self.team_name = team_name
        self.progression = progression


class TeamProgressionEntrySerializer(serializers.Serializer):
    date = serializers.DateField()
    score = serializers.FloatField()
    rank = serializers.IntegerField()


class TeamProgressionSerializer(serializers.Serializer):
    team_name = serializers.CharField()
    progression = TeamProgressionEntrySerializer(many=True)


class ScoreImprovements:
    """Data class for score improvement statistics."""

    def __init__(self, biggest_jump, avg_improvement):
        self.biggest_jump = biggest_jump
        self.avg_improvement = avg_improvement


class BiggestJumpSerializer(serializers.Serializer):
    team = serializers.CharField()
    improvement = serializers.FloatField()


class ScoreImprovementsSerializer(serializers.Serializer):
    biggest_jump = BiggestJumpSerializer(allow_null=True)
    avg_improvement = serializers.FloatField()


class LeaderboardProgression:
    """Data class for leaderboard progression data."""

    def __init__(self, phase_id, top_teams_progression, score_improvements):
        self.phase_id = phase_id
        self.top_teams_progression = top_teams_progression
        self.score_improvements = score_improvements


class LeaderboardProgressionSerializer(serializers.Serializer):
    phase_id = serializers.IntegerField()
    top_teams_progression = TeamProgressionSerializer(many=True)
    score_improvements = ScoreImprovementsSerializer()
