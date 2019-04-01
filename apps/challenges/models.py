from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import signals

from base.models import (
    TimeStampedModel,
    model_field_name,
    create_post_model_field,
)
from base.utils import RandomFileName
from participants.models import ParticipantTeam
from hosts.models import ChallengeHost


class Challenge(TimeStampedModel):

    """Model representing a hosted Challenge"""

    def __init__(self, *args, **kwargs):
        super(Challenge, self).__init__(*args, **kwargs)
        self._original_evaluation_script = self.evaluation_script

    title = models.CharField(max_length=100, db_index=True)
    short_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField(null=True, blank=True)
    submission_guidelines = models.TextField(null=True, blank=True)
    evaluation_details = models.TextField(null=True, blank=True)
    image = models.ImageField(
        upload_to=RandomFileName("logos"),
        null=True,
        blank=True,
        verbose_name="Logo",
    )
    start_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Start Date (UTC)", db_index=True
    )
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date (UTC)", db_index=True
    )
    creator = models.ForeignKey(
        "hosts.ChallengeHostTeam", related_name="challenge_creator"
    )
    published = models.BooleanField(
        default=False, verbose_name="Publicly Available", db_index=True
    )
    enable_forum = models.BooleanField(default=True)
    forum_url = models.URLField(max_length=100, blank=True, null=True)
    leaderboard_description = models.TextField(null=True, blank=True)
    anonymous_leaderboard = models.BooleanField(default=False)
    participant_teams = models.ManyToManyField(ParticipantTeam, blank=True)
    is_disabled = models.BooleanField(default=False, db_index=True)
    evaluation_script = models.FileField(
        default=False, upload_to=RandomFileName("evaluation_scripts")
    )  # should be zip format
    approved_by_admin = models.BooleanField(
        default=False, verbose_name="Approved By Admin", db_index=True
    )
    featured = models.BooleanField(
        default=False, verbose_name="Featured", db_index=True
    )
    allowed_email_domains = ArrayField(
        models.CharField(max_length=50, blank=True), default=[], blank=True
    )
    blocked_email_domains = ArrayField(
        models.CharField(max_length=50, blank=True), default=[], blank=True
    )
    remote_evaluation = models.BooleanField(
        default=False, verbose_name="Remote Evaluation", db_index=True
    )
    queue = models.CharField(
        max_length=200,
        default="",
        verbose_name="SQS queue name",
        db_index=True,
    )
    is_docker_based = models.BooleanField(
        default=False, verbose_name="Is Docker Based", db_index=True
    )
    slug = models.CharField(max_length=200, db_index=True, default="")
    max_docker_image_size = models.BigIntegerField(
        default=42949672960, null=True, blank=True
    )  # Default is 40 GB
    max_concurrent_submission_evaluation = models.PositiveIntegerField(
        default=100000
    )
    aws_account_id = models.CharField(
        max_length=200, default="", null=True, blank=True
    )
    aws_access_key_id = models.CharField(
        max_length=200, default="", null=True, blank=True
    )
    aws_secret_access_key = models.CharField(
        max_length=200, default="", null=True, blank=True
    )
    aws_region = models.CharField(
        max_length=50, default="us-east-1", null=True, blank=True
    )
    use_host_credentials = models.BooleanField(default=False)

    class Meta:
        app_label = "challenges"
        db_table = "challenge"

    def __str__(self):
        """Returns the title of Challenge"""
        return self.title

    def get_image_url(self):
        """Returns the url of logo of Challenge"""
        if self.image:
            return self.image.url
        return None

    def get_evaluation_script_path(self):
        """Returns the path of evaluation script"""
        if self.evaluation_script:
            return self.evaluation_script.url
        return None

    def get_start_date(self):
        """Returns the start date of Challenge"""
        return self.start_date

    def get_end_date(self):
        """Returns the end date of Challenge"""
        return self.end_date

    @property
    def is_active(self):
        """Returns if the challenge is active or not"""
        if self.start_date < timezone.now() and self.end_date > timezone.now():
            return True
        return False


signals.post_save.connect(
    model_field_name(field_name="evaluation_script")(create_post_model_field),
    sender=Challenge,
    weak=False,
)


class DatasetSplit(TimeStampedModel):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        app_label = "challenges"
        db_table = "dataset_split"


class ChallengePhase(TimeStampedModel):

    """Model representing a Challenge Phase"""

    def __init__(self, *args, **kwargs):
        super(ChallengePhase, self).__init__(*args, **kwargs)
        self._original_test_annotation = self.test_annotation

    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    leaderboard_public = models.BooleanField(default=False)
    start_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Start Date (UTC)", db_index=True
    )
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date (UTC)", db_index=True
    )
    challenge = models.ForeignKey("Challenge")
    is_public = models.BooleanField(default=False)
    is_submission_public = models.BooleanField(default=False)
    test_annotation = models.FileField(
        upload_to=RandomFileName("test_annotations"), default=False
    )
    max_submissions_per_day = models.PositiveIntegerField(
        default=100000, db_index=True
    )
    max_submissions_per_month = models.PositiveIntegerField(
        default=100000, db_index=True
    )
    max_submissions = models.PositiveIntegerField(
        default=100000, db_index=True
    )
    max_concurrent_submissions_allowed = models.PositiveIntegerField(default=3)
    codename = models.CharField(max_length=100, default="Phase Code Name")
    dataset_split = models.ManyToManyField(
        DatasetSplit, blank=True, through="ChallengePhaseSplit"
    )
    allowed_email_ids = ArrayField(
        models.TextField(null=True, blank=True),
        default=[],
        blank=True,
        null=True,
    )
    slug = models.SlugField(max_length=200, null=True, unique=True)

    class Meta:
        app_label = "challenges"
        db_table = "challenge_phase"
        unique_together = (("codename", "challenge"),)

    def __str__(self):
        """Returns the name of Phase"""
        return self.name

    def get_start_date(self):
        """Returns the start date of Phase"""
        return self.start_date

    def get_end_date(self):
        """Returns the end date of Challenge"""
        return self.end_date

    @property
    def is_active(self):
        """Returns if the challenge is active or not"""
        if self.start_date < timezone.now() and self.end_date > timezone.now():
            return True
        return False

    def save(self, *args, **kwargs):

        # If the max_submissions_per_day is less than the max_concurrent_submissions_allowed.
        if (
            self.max_submissions_per_day
            < self.max_concurrent_submissions_allowed
        ):
            self.max_concurrent_submissions_allowed = (
                self.max_submissions_per_day
            )

        challenge_phase_instance = super(ChallengePhase, self).save(
            *args, **kwargs
        )
        return challenge_phase_instance


signals.post_save.connect(
    model_field_name(field_name="test_annotation")(create_post_model_field),
    sender=ChallengePhase,
    weak=False,
)


class Leaderboard(TimeStampedModel):

    schema = JSONField()

    def __str__(self):
        return "{}".format(self.id)

    class Meta:
        app_label = "challenges"
        db_table = "leaderboard"


class ChallengePhaseSplit(TimeStampedModel):

    # visibility options
    HOST = 1
    OWNER_AND_HOST = 2
    PUBLIC = 3

    VISIBILITY_OPTIONS = (
        (HOST, "host"),
        (OWNER_AND_HOST, "owner and host"),
        (PUBLIC, "public"),
    )

    challenge_phase = models.ForeignKey("ChallengePhase")
    dataset_split = models.ForeignKey("DatasetSplit")
    leaderboard = models.ForeignKey("Leaderboard")
    visibility = models.PositiveSmallIntegerField(
        choices=VISIBILITY_OPTIONS, default=PUBLIC
    )

    def __str__(self):
        return "{0} : {1}".format(
            self.challenge_phase.name, self.dataset_split.name
        )

    class Meta:
        app_label = "challenges"
        db_table = "challenge_phase_split"


class LeaderboardData(TimeStampedModel):

    challenge_phase_split = models.ForeignKey("ChallengePhaseSplit")
    submission = models.ForeignKey("jobs.Submission")
    leaderboard = models.ForeignKey("Leaderboard")
    result = JSONField()

    def __str__(self):
        return "{0} : {1}".format(self.challenge_phase_split, self.submission)

    class Meta:
        app_label = "challenges"
        db_table = "leaderboard_data"


class ChallengeConfiguration(TimeStampedModel):
    """
    Model to store zip file for challenge creation.
    """

    user = models.ForeignKey(User)
    challenge = models.OneToOneField(Challenge, null=True, blank=True)
    zip_configuration = models.FileField(
        upload_to=RandomFileName("zip_configuration_files/challenge_zip")
    )
    is_created = models.BooleanField(default=False, db_index=True)
    stdout_file = models.FileField(
        upload_to=RandomFileName("zip_configuration_files/challenge_zip"),
        null=True,
        blank=True,
    )
    stderr_file = models.FileField(
        upload_to=RandomFileName("zip_configuration_files/challenge_zip"),
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "challenges"
        db_table = "challenge_zip_configuration"


class StarChallenge(TimeStampedModel):
    """
    Model to star a challenge
    """

    user = models.ForeignKey(User)
    challenge = models.ForeignKey(Challenge)
    is_starred = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = "challenges"
        db_table = "starred_challenge"


class UserInvitation(TimeStampedModel):
    """
    Model to store invitation status
    """

    ACCEPTED = "accepted"
    PENDING = "pending"

    STATUS_OPTIONS = ((ACCEPTED, ACCEPTED), (PENDING, PENDING))
    email = models.EmailField(max_length=200)
    invitation_key = models.CharField(max_length=200)
    status = models.CharField(
        max_length=30, choices=STATUS_OPTIONS, db_index=True
    )
    challenge = models.ForeignKey(Challenge, related_name="challenge")
    user = models.ForeignKey(User)
    invited_by = models.ForeignKey(ChallengeHost)

    class Meta:
        app_label = "challenges"
        db_table = "invite_user_to_challenge"

    def __str__(self):
        """Returns the email of the user"""
        return self.email
