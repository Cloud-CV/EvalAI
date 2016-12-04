from django.contrib.auth.models import User

from rest_framework import serializers

from .models import (Participant, ParticipantTeam)


class ParticipantTeamSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ParticipantTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            kwargs['data']['created_by'] = request.user.pk

    class Meta:
        model = ParticipantTeam
        fields = ('id', 'team_name', 'created_by')


class InviteParticipantToTeamSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super(InviteParticipantToTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            self.participant_team = context.get('participant_team')
            self.user = context.get('request').user

    def validate_email(self, value):
        if value == self.user.email:
            raise serializers.ValidationError('A participant cannot invite himself')
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist')
        return value

    def save(self):
        email = self.validated_data.get('email')
        return Participant.objects.create(user=User.objects.get(email=email),
                                          status=Participant.ACCEPTED,
                                          team=self.participant_team)
