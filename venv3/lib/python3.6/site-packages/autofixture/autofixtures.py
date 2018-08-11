# -*- coding: utf-8 -*-
import autofixture
import string
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.utils import timezone
from autofixture import AutoFixture
from autofixture import generators
from .compat import get_field


class UserFixture(AutoFixture):
    '''
    :class:`UserFixture` is automatically used by default to create new
    ``User`` instances. It uses the following values to assure that you can
    use the generated instances without any modification:

    * ``username`` only contains chars that are allowed by django's auth forms.
    * ``email`` is unique.
    * ``first_name`` and ``last_name`` are single, random words of the lorem
      ipsum text.
    * ``is_staff`` and ``is_superuser`` are always ``False``.
    * ``is_active`` is always ``True``.
    * ``date_joined`` and ``last_login`` are always in the past and it is
      assured that ``date_joined`` will be lower than ``last_login``.
    '''
    class Values(object):
        username = generators.StringGenerator(
            max_length=30,
            chars=string.ascii_letters + string.digits + '_')
        first_name = generators.LoremWordGenerator(1)
        last_name = generators.LoremWordGenerator(1)
        password = staticmethod(lambda: make_password(None))
        is_active = True
        # don't generate admin users
        is_staff = False
        is_superuser = False
        date_joined = generators.DateTimeGenerator(max_date=timezone.now())
        last_login = generators.DateTimeGenerator(max_date=timezone.now())

    # don't follow permissions and groups
    follow_m2m = False

    def __init__(self, *args, **kwargs):
        '''
        By default the password is set to an unusable value, this makes it
        impossible to login with the generated users. If you want to use for
        example ``autofixture.create_one('auth.User')`` in your unittests to have
        a user instance which you can use to login with the testing client you
        can provide a ``username`` and a ``password`` argument. Then you can do
        something like::

            autofixture.create_one('auth.User', username='foo', password='bar`)
            self.client.login(username='foo', password='bar')
        '''
        self.username = kwargs.pop('username', None)
        self.password = kwargs.pop('password', None)
        super(UserFixture, self).__init__(*args, **kwargs)
        if self.username:
            self.field_values['username'] = generators.StaticGenerator(
                self.username)

    def unique_email(self, model, instance):
        if User.objects.filter(email=instance.email).exists():
            raise autofixture.InvalidConstraint((get_field(model,'email'),))

    def prepare_class(self):
        self.add_constraint(self.unique_email)

    def post_process_instance(self, instance, commit):
        # make sure user's last login was not before he joined
        changed = False
        if instance.last_login < instance.date_joined:
            instance.last_login = instance.date_joined
            changed = True
        if self.password:
            instance.set_password(self.password)
            changed = True
        if changed and commit:
            instance.save()
        return instance


autofixture.register(User, UserFixture, fail_silently=True)
