from django.contrib.auth import get_user_model

from rest_framework import serializers


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Make username as a read_only field.
    """
    class Meta:
        model = get_user_model()
        fields = ('pk', 'email', 'username', 'first_name', 'last_name')
        read_only_fields = ('email', 'username')
