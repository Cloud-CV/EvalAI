from rest_framework import serializers
from scout.models import ScoutChallenge


class OrganizerSerializer(serializers.Serializer):
    name = serializers.CharField()
    role = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    affiliation = serializers.CharField(required=False, allow_blank=True)


class ScoutChallengePayloadSerializer(serializers.ModelSerializer):
    organizers = OrganizerSerializer(many=True)

    class Meta:
        model = ScoutChallenge
        fields = (
            "benchmark_name",
            "task_area",
            "conference",
            "year",
            "official_url",
            "dataset_url",
            "organizers",
            "evalai_suitable",
            "evalai_reasoning",
        )
        extra_kwargs = {
            "task_area": {"required": True, "allow_blank": False},
            "evalai_reasoning": {"required": True, "allow_blank": True},
            "dataset_url": {"required": False, "allow_blank": True},
        }
