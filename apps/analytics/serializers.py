from rest_framework import serializers


class SubmissionStats(object):
    def __init__(self, submission_total):
        self.submission_total = submission_total


class SubmissionStatsSerializer(serializers.Serializer):
    submission_total = serializers.IntegerField()
