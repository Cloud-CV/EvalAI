from rest_framework import serializers

from hosts.serializers import ChallengeHostTeamSerializer

from .models import (Challenge,
                     ChallengeConfiguration,
                     ChallengePhase,
                     ChallengePhaseSplit,
                     DatasetSplit,
                     Leaderboard,
                     StarChallenge)


class ChallengeSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengeSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context and context.get('request').method != 'GET':
            challenge_host_team = context.get('challenge_host_team')
            kwargs['data']['creator'] = challenge_host_team.pk
        else:
            self.fields['creator'] = ChallengeHostTeamSerializer()

    class Meta:
        model = Challenge
        fields = ('id', 'title', 'short_description', 'description', 'terms_and_conditions',
                  'submission_guidelines', 'evaluation_details',
                  'image', 'start_date', 'end_date', 'creator',
                  'published', 'enable_forum', 'anonymous_leaderboard', 'is_active',
                  'allowed_email_domains', 'blocked_email_domains',
                  'approved_by_admin', 'forum_url',)


class ChallengePhaseSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengePhaseSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge = context.get('challenge')
            if challenge:
                kwargs['data']['challenge'] = challenge.pk

    class Meta:
        model = ChallengePhase
        fields = ('id', 'name', 'description', 'leaderboard_public', 'start_date',
                  'end_date', 'challenge', 'max_submissions_per_day', 'max_submissions',
                  'is_public', 'is_active', 'codename',)


class DatasetSplitSerializer(serializers.ModelSerializer):

    class Meta:
        model = DatasetSplit
        fields = ('id', 'name', 'codename')


class ChallengePhaseSplitSerializer(serializers.ModelSerializer):
    """Serialize the ChallengePhaseSplits Model"""

    dataset_split_name = serializers.SerializerMethodField()
    challenge_phase_name = serializers.SerializerMethodField()

    class Meta:
        model = ChallengePhaseSplit
        fields = ('id', 'dataset_split', 'challenge_phase', 'challenge_phase_name', 'dataset_split_name', 'visibility')

    def get_dataset_split_name(self, obj):
        return obj.dataset_split.name

    def get_challenge_phase_name(self, obj):
        return obj.challenge_phase.name


class ChallengeConfigSerializer(serializers.ModelSerializer):
    """
    Serialize the ChallengeConfiguration Model.
    """
    def __init__(self, *args, **kwargs):
        super(ChallengeConfigSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            kwargs['data']['user'] = request.user.pk

    class Meta:
        model = ChallengeConfiguration
        fields = ('zip_configuration', 'user',)


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serialize the Leaderboard Model.
    """
    class Meta:
        model = Leaderboard
        fields = ('id', 'schema')


class ZipChallengeSerializer(ChallengeSerializer):
    """
    Serializer used for creating challenge through zip file.
    """
    def __init__(self, *args, **kwargs):
        super(ZipChallengeSerializer, self).__init__(*args, **kwargs)

        context = kwargs.get('context')
        if context:
            image = context.get('image')
            if image:
                kwargs['data']['image'] = image
            evaluation_script = context.get('evaluation_script')
            if evaluation_script:
                kwargs['data']['evaluation_script'] = evaluation_script

    class Meta:
        model = Challenge
        fields = ('id', 'title', 'short_description', 'description', 'terms_and_conditions',
                  'submission_guidelines', 'start_date', 'end_date', 'creator', 'evaluation_details',
                  'published', 'enable_forum', 'anonymous_leaderboard', 'image', 'is_active', 'evaluation_script',
                  'allowed_email_domains', 'blocked_email_domains', 'forum_url',)


class ZipChallengePhaseSplitSerializer(serializers.ModelSerializer):
    """
    Serializer used for creating challenge phase split through zip file.
    """
    class Meta:
        model = ChallengePhaseSplit
        fields = ('id', 'challenge_phase', 'dataset_split', 'leaderboard', 'visibility')


class ChallengePhaseCreateSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengePhaseCreateSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge = context.get('challenge')
            if challenge:
                kwargs['data']['challenge'] = challenge.pk
            test_annotation = context.get('test_annotation')
            if test_annotation:
                kwargs['data']['test_annotation'] = test_annotation

    class Meta:
        model = ChallengePhase
        fields = ('id', 'name', 'description', 'leaderboard_public', 'start_date',
                  'end_date', 'challenge', 'max_submissions_per_day', 'max_submissions',
                  'is_public', 'is_active', 'is_submission_public', 'codename', 'test_annotation')


class StarChallengeSerializer(serializers.ModelSerializer):

    count = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(StarChallengeSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge = context.get('challenge')
            if challenge:
                kwargs['data']['challenge'] = challenge.pk
            request = context.get('request')
            if request:
                kwargs['data']['user'] = request.user.pk
            starred = context.get('is_starred')
            if starred:
                kwargs['data']['is_starred'] = starred

    class Meta:
        model = StarChallenge
        fields = ('user', 'challenge', 'count', 'is_starred')

    def get_count(self, obj):
        count = StarChallenge.objects.filter(challenge=obj.challenge, is_starred=True).count()
        return count
