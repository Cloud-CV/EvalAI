from rest_framework import serializers

from hosts.serializers import ChallengeHostTeamSerializer

from .models import (Challenge,
                     ChallengeConfiguration,
                     ChallengePhase,
                     ChallengePhaseSplit,
                     DatasetSplit,
                     Leaderboard,)


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
                  'published', 'enable_forum', 'anonymous_leaderboard', 'is_active',)


class ChallengePhaseSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengePhaseSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge = context.get('challenge')
            kwargs['data']['challenge'] = challenge.pk

    class Meta:
        model = ChallengePhase
        fields = ('id', 'name', 'description', 'leaderboard_public', 'start_date',
                  'end_date', 'challenge', 'max_submissions_per_day', 'max_submissions',
                  'is_public', 'is_active', 'codename')


class DatasetSplitSerializer(serializers.ModelSerializer):

    class Meta:
        model = DatasetSplit
        fields = '__all__'


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
        super(ChallengeConfigurationSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            user = context.get('user')
            kwargs['data']['user'] = user.pk

    class Meta:
        model = ChallengeConfiguration
        fields = ('zip_configuration', 'user',)


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serialize the Leaderboard Model.
    """
    class Meta:
        model = Leaderboard
        fields = '__all__'


class ZipChallengeSerializer(ChallengeSerializer):
    """
    Serializer used for creating challenge through zip file.
    """
    class Meta:
        model = Challenge
        fields = ('id', 'title', 'short_description', 'description', 'terms_and_conditions',
                  'submission_guidelines', 'start_date', 'end_date', 'creator',
                  'published', 'enable_forum', 'anonymous_leaderboard', 'is_active',)


class ZipChallengePhaseSplitSerializer(serializers.ModelSerializer):
    """
    Serializer used for creating challenge phase split through zip file.
    """
    class Meta:
        model = ChallengePhaseSplit
        fields = '__all__'
