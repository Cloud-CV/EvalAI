from django.contrib.auth import get_user_model

from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Make username as a read_only field.
    """
    class Meta:
        model = get_user_model()
        fields = ('pk', 'email', 'username', 'first_name', 'last_name')
        read_only_fields = ('email', 'username')


class ProfileSerializer(UserDetailsSerializer):
    """
    Serializer to update the user profile.
    """

    affiliation = serializers.CharField(source="profile.affiliation")
    avatar = Base64ImageField(source="profile.avatar")

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('affiliation', 'avatar',)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        affiliation = profile_data.get('affiliation')
        avatar = profile_data.get('avatar')

        instance = super(ProfileSerializer, self).update(instance, validated_data)

        profile = instance.profile
        if profile_data and affiliation:
            profile.affiliation = affiliation
            profile.save()

        if profile_data and avatar:
            profile.avatar = avatar
            profile.save()

        return instance
