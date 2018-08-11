import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser


class User(AbstractBaseUser):
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

    email = models.EmailField(unique=True, verbose_name='email address', max_length=255)
    full_name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'full_name']


class Organisation(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    name = models.CharField(unique=True, max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    members = models.ManyToManyField(User, through='Membership', through_fields=('organisation', 'user'))

    is_active = models.BooleanField(default=False)


class Membership(models.Model):

    class Meta:
        unique_together = ("organisation", "user")

    MEMBER_ROLES = (
        ("ADMIN", "Admin"),
        ("USER", "User")
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    joined = models.DateTimeField(auto_now_add=True)

    organisation = models.ForeignKey(Organisation)
    user = models.ForeignKey(User)
    role = models.CharField(choices=MEMBER_ROLES, max_length=20, default="USER")
    is_owner = models.BooleanField(default=False)
