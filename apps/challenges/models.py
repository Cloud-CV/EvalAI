from __future__ import unicode_literals

from base.models import TimeStampedModel, model_field_name
from base.utils import RandomFileName, get_slug, is_model_field_changed
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core import serializers
from django.db import models
from django.db.models import signals
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from hosts.models import ChallengeHost
from participants.models import ParticipantTeam

from .constants import (
    DEFAULT_WORKER_PYTHON_VERSION,
    SUPPORTED_WORKER_PYTHON_VERSIONS,
)


@receiver(pre_save, sender="challenges.Challenge")
def save_challenge_slug(sender, instance, **kwargs):
    title = get_slug(instance.title)
    instance.slug = "{}-{}".format(title, instance.pk)


def get_default_eval_metric():
    return ["Accuracy"]


class Challenge(TimeStampedModel):
    """Model representing a hosted Challenge"""

    def __init__(self, *args, **kwargs):
        super(Challenge, self).__init__(*args, **kwargs)
        self._original_evaluation_script = self.evaluation_script
        self._original_approved_by_admin = self.approved_by_admin
        self._original_sqs_retention_period = self.sqs_retention_period
        self._original_end_date = self.end_date

    title = models.CharField(
        max_length=100,
        db_index=True,
        help_text=(
            "Challenge name shown in listings and on the challenge page."
        ),
    )
    short_description = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "One or two line summary shown on challenge cards and in "
            "listings."
        ),
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Full challenge overview rendered on the challenge landing page."
        ),
    )
    terms_and_conditions = models.TextField(
        null=True,
        blank=True,
        help_text="Terms a participant must accept before submitting.",
    )
    submission_guidelines = models.TextField(
        null=True,
        blank=True,
        help_text="Instructions shown to participants on the submission page.",
    )
    evaluation_details = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Explanation of how submissions are scored, shown to "
            "participants."
        ),
    )
    image = models.ImageField(
        upload_to=RandomFileName("logos"),
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text=(
            "Challenge logo shown in listings and on the challenge page."
        ),
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Start Date (UTC)",
        db_index=True,
        help_text=(
            "When the challenge opens. Submissions are rejected before this "
            "time."
        ),
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End Date (UTC)",
        db_index=True,
        help_text=(
            "When the challenge closes. Also triggers worker and EKS "
            "nodegroup scale-down."
        ),
    )
    creator = models.ForeignKey(
        "hosts.ChallengeHostTeam",
        related_name="challenge_creator",
        on_delete=models.CASCADE,
        help_text=(
            "Challenge host team that owns and administers this challenge."
        ),
    )
    DOMAIN_OPTIONS = (
        ("CV", "Computer Vision"),
        ("NLP", "Natural Language Processing"),
        ("RL", "Reinforcement Learning"),
        ("MM", "Multimodal"),
        ("AUD", "Audio"),
        ("TAB", "Tabular"),
    )
    PAID = "paid"
    INTERNAL = "internal"
    CHALLENGE_USAGE_TYPE_OPTIONS = (
        (PAID, "Paid"),
        (INTERNAL, "Internal"),
    )
    domain = models.CharField(
        max_length=50,
        choices=DOMAIN_OPTIONS,
        null=True,
        blank=True,
        help_text="Research area used to filter and group challenges.",
    )
    challenge_usage_type = models.CharField(
        max_length=20,
        choices=CHALLENGE_USAGE_TYPE_OPTIONS,
        default=PAID,
        db_index=True,
        help_text=(
            "Paid challenges are billed to the host; internal ones are not."
        ),
    )
    list_tags = ArrayField(
        models.TextField(null=True, blank=True),
        default=list,
        blank=True,
        help_text=(
            "Free-form tags shown on the challenge page and used in search."
        ),
    )
    has_prize = models.BooleanField(
        default=False,
        help_text=(
            "Whether a prize is offered. Shows the prize section on the "
            "challenge page."
        ),
    )
    has_sponsors = models.BooleanField(
        default=False,
        help_text=(
            "Whether sponsors are listed. Shows the sponsors section on the "
            "challenge page."
        ),
    )
    published = models.BooleanField(
        default=False,
        verbose_name="Publicly Available",
        db_index=True,
        help_text="Whether the challenge is visible to the public.",
    )
    submission_time_limit = models.PositiveIntegerField(
        default=86400,
        help_text=(
            "Per-submission wall-clock limit in seconds. Default 86400 (24 "
            "hours)."
        ),
    )
    is_registration_open = models.BooleanField(
        default=True,
        help_text="Whether new participant teams may join.",
    )
    enable_forum = models.BooleanField(
        default=True,
        help_text="Show a discussion forum link on the challenge page.",
    )
    forum_url = models.URLField(
        max_length=100,
        blank=True,
        null=True,
        help_text=(
            "External discussion forum URL, used when the forum is enabled."
        ),
    )
    leaderboard_description = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Notes rendered above the leaderboard, e.g. how to read each "
            "metric."
        ),
    )
    anonymous_leaderboard = models.BooleanField(
        default=False,
        help_text="Hide participant team names on the public leaderboard.",
    )
    participant_teams = models.ManyToManyField(
        ParticipantTeam,
        blank=True,
        help_text=(
            "Teams that have joined. Normally managed through registration "
            "rather than edited here."
        ),
    )
    manual_participant_approval = models.BooleanField(
        default=False,
        help_text="Require a host to approve each team before it can submit.",
    )
    require_complete_profile = models.BooleanField(
        default=False,
        verbose_name="Require Complete Profile",
        help_text=(
            "If enabled, participants must have a complete profile (name, "
            "address, city, state, country) before joining this challenge."
        ),
    )
    max_team_members = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maximum Team Members",
        help_text="Maximum number of members allowed per participant team. "
        "Leave blank for no limit.",
    )
    approved_participant_teams = models.ManyToManyField(
        ParticipantTeam,
        blank=True,
        related_name="approved_challenge_participant_teams",
        help_text=(
            "Teams cleared to submit when manual participant approval is "
            "enabled."
        ),
    )
    is_disabled = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "Hide the challenge and reject submissions. Also forces workers "
            "and the EKS nodegroup to zero."
        ),
    )
    evaluation_script = models.FileField(
        default=False,
        upload_to=RandomFileName("evaluation_scripts"),
        help_text=(
            "Zip archive containing the evaluation code run against "
            "submissions."
        ),
    )
    approved_by_admin = models.BooleanField(
        default=False,
        verbose_name="Approved By Admin",
        db_index=True,
        help_text=(
            "EvalAI admin approval. Provisions workers or the EKS cluster the "
            "first time it is set."
        ),
    )
    is_approval_requested = models.BooleanField(
        default=False,
        verbose_name="Is Approval Requested",
        db_index=True,
        help_text="Set to True once a challenge host submits an approval request. "
        "Prevents duplicate subscription plan emails from being sent.",
    )
    uses_ec2_worker = models.BooleanField(
        default=False,
        verbose_name="Uses EC2 worker instance",
        db_index=True,
        help_text=(
            "Run the submission worker on a dedicated EC2 instance instead of "
            "Fargate."
        ),
    )
    ec2_instance_id = models.CharField(
        max_length=200,
        default="",
        null=True,
        blank=True,
        help_text=(
            "Instance ID of the provisioned EC2 worker. Set automatically."
        ),
    )
    ec2_storage = models.PositiveIntegerField(
        default=8,
        verbose_name="EC2 storage (GB)",
        help_text="Root volume size for the EC2 worker, in GB.",
    )
    ephemeral_storage = models.PositiveIntegerField(
        default=21,
        verbose_name="Ephemeral Storage (GB)",
        help_text="Fargate task ephemeral storage in GB. Minimum 21.",
    )
    featured = models.BooleanField(
        default=False,
        verbose_name="Featured",
        db_index=True,
        help_text=(
            "Show this challenge in the featured section of the home page."
        ),
    )
    allowed_email_domains = ArrayField(
        models.CharField(max_length=50, blank=True),
        default=list,
        blank=True,
        help_text=(
            "If non-empty, only these email domains may join, e.g. "
            "example.com."
        ),
    )
    blocked_email_domains = ArrayField(
        models.CharField(max_length=50, blank=True),
        default=list,
        blank=True,
        help_text="Email domains barred from joining this challenge.",
    )
    banned_email_ids = ArrayField(
        models.TextField(null=True, blank=True),
        default=list,
        blank=True,
        null=True,
        help_text=(
            "Individual email addresses barred from joining or submitting."
        ),
    )
    remote_evaluation = models.BooleanField(
        default=False,
        verbose_name="Remote Evaluation",
        db_index=True,
        help_text=(
            "Host runs evaluation on their own infrastructure; EvalAI "
            "provisions no workers."
        ),
    )
    queue = models.CharField(
        max_length=200,
        default="",
        verbose_name="SQS queue name",
        db_index=True,
        help_text=(
            "Name of the SQS queue carrying this challenge's submission "
            "messages. Set automatically."
        ),
    )
    sqs_retention_period = models.PositiveIntegerField(
        default=345600,
        verbose_name="SQS Retention Period",
        help_text=(
            "How long unread SQS messages are kept, in seconds. Default "
            "345600 (4 days)."
        ),
    )
    is_docker_based = models.BooleanField(
        default=False,
        verbose_name="Is Docker Based",
        db_index=True,
        help_text=(
            "Participants submit code or container images rather than "
            "prediction files."
        ),
    )
    is_static_dataset_code_upload = models.BooleanField(
        default=False,
        verbose_name="Is Static Dataset Code Upload Based",
        db_index=True,
        help_text=(
            "Two-stage code upload: participant code runs on EKS, then "
            "evaluation runs on the worker."
        ),
    )
    slug = models.SlugField(
        max_length=200,
        null=True,
        unique=True,
        help_text=(
            "URL identifier for the challenge. Generated from the title."
        ),
    )
    max_docker_image_size = models.BigIntegerField(
        default=42949672960,
        null=True,
        blank=True,
        help_text=(
            "Maximum participant image size in bytes. Default 42949672960 (40 "
            "GB)."
        ),
    )
    max_concurrent_submission_evaluation = models.PositiveIntegerField(
        default=100000,
        help_text=(
            "Maximum submissions evaluated at once across all participants."
        ),
    )
    aws_account_id = models.CharField(
        max_length=200,
        default="",
        null=True,
        blank=True,
        help_text=(
            "Host AWS account ID. Required alongside use host credentials for "
            "cross-account EKS scaling."
        ),
    )
    aws_access_key_id = models.CharField(
        max_length=200,
        default="",
        null=True,
        blank=True,
        help_text=(
            "Host AWS access key. Used only when use host credentials is "
            "enabled."
        ),
    )
    aws_secret_access_key = models.CharField(
        max_length=200,
        default="",
        null=True,
        blank=True,
        help_text=(
            "Host AWS secret key. Used only when use host credentials is "
            "enabled."
        ),
    )
    aws_region = models.CharField(
        max_length=50,
        default="us-east-1",
        null=True,
        blank=True,
        help_text="AWS region holding this challenge's compute resources.",
    )
    queue_aws_region = models.CharField(
        max_length=50,
        default="us-east-1",
        null=True,
        blank=True,
        help_text=(
            "AWS region holding the SQS queue. May differ from the compute "
            "region."
        ),
    )
    use_host_credentials = models.BooleanField(
        default=False,
        help_text=(
            "Provision compute in the host's own AWS account using the "
            "credentials below."
        ),
    )
    use_host_sqs = models.BooleanField(
        default=False,
        help_text="Use the host's own SQS queue instead of EvalAI's.",
    )
    use_fifo_sqs = models.BooleanField(
        default=False,
        help_text=(
            "Use a FIFO SQS queue for ordered per-team evaluation within a "
            "phase. Message groups are phase_pk-participant_team_pk so "
            "different teams can be processed in parallel by ECS workers. "
            "Do not toggle after queue creation; provision a new challenge "
            "instead."
        ),
    )
    allow_resuming_submissions = models.BooleanField(
        default=False,
        help_text="Let hosts re-queue a failed or cancelled submission.",
    )
    allow_host_cancel_submissions = models.BooleanField(
        default=False,
        help_text="Let hosts cancel a participant's queued submission.",
    )
    allow_cancel_running_submissions = models.BooleanField(
        default=False,
        help_text=(
            "Let hosts cancel a submission that has already started running."
        ),
    )
    allow_participants_resubmissions = models.BooleanField(
        default=False,
        help_text="Let participants resubmit without consuming a new attempt.",
    )
    cli_version = models.CharField(
        max_length=20,
        verbose_name="evalai-cli version",
        null=True,
        blank=True,
        help_text="Minimum evalai-cli version required to submit.",
    )
    workers = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        help_text=(
            "ECS service lifecycle state: None = never started, "
            "0 = stopped, N = running N workers."
        ),
    )
    max_ecs_workers = models.IntegerField(
        null=True,
        blank=True,
        default=1,
        help_text=(
            "Autoscaling ceiling: max workers the scale-up policy "
            "can launch when the SQS queue is non-empty."
        ),
    )
    min_ecs_workers = models.IntegerField(
        null=True,
        blank=True,
        default=1,
        help_text=(
            "Autoscaling floor: min workers kept alive when the "
            "SQS queue is empty. 0 allows scale-to-zero."
        ),
    )
    task_def_arn = models.CharField(
        null=True,
        blank=True,
        max_length=2048,
        default="",
        help_text=(
            "ECS task definition ARN for the worker. Set automatically when "
            "the service is created or updated."
        ),
    )
    slack_webhook_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Slack incoming webhook for challenge notifications.",
    )
    github_repository = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        default="",
        help_text=(
            "Source repository as account_name/repository_name, used by the "
            "GitHub sync workflow."
        ),
    )
    github_branch = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        default="",
        help_text=(
            "Branch the GitHub sync workflow reads the challenge "
            "configuration from."
        ),
    )
    worker_cpu_cores = models.IntegerField(
        null=True,
        blank=True,
        default=512,
        help_text="Fargate worker CPU in ECS CPU units (1024 = 1 vCPU).",
    )
    worker_memory = models.IntegerField(
        null=True,
        blank=True,
        default=1024,
        help_text="Fargate worker memory in MiB (1024 = 1 GB).",
    )
    use_fargate_spot = models.BooleanField(
        default=True,
        verbose_name="Use Fargate Spot",
        help_text=(
            "If True, use capacityProviderStrategy (Spot). If False, use "
            "launchType FARGATE."
        ),
    )
    fargate_spot_weight = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Fargate Spot Weight",
        help_text=(
            "Weight for FARGATE_SPOT in capacity provider strategy. 0 "
            "excludes Spot."
        ),
    )
    fargate_spot_base = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Fargate Spot Base",
        help_text=(
            "Minimum number of tasks placed on FARGATE_SPOT before weights "
            "apply."
        ),
    )
    fargate_weight = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Fargate Weight",
        help_text=(
            "Weight for FARGATE in capacity provider strategy. 0 = Spot only."
        ),
    )
    fargate_base = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Fargate Base",
        help_text=(
            "Minimum number of tasks placed on FARGATE before weights apply."
        ),
    )
    inform_hosts = models.BooleanField(
        default=True,
        help_text=(
            "Send email notifications about this challenge to its hosts."
        ),
    )
    vpc_cidr = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        default="",
        help_text=(
            "CIDR block for the VPC created for this code upload challenge."
        ),
    )
    subnet_1_cidr = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        default="",
        help_text=(
            "CIDR block for the first subnet of the code upload challenge "
            "VPC."
        ),
    )
    subnet_2_cidr = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        default="",
        help_text=(
            "CIDR block for the second subnet of the code upload challenge "
            "VPC."
        ),
    )
    worker_instance_type = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        default="g4dn.xlarge",
        help_text=(
            "EC2 instance type for the EKS nodes that run code upload "
            "submissions."
        ),
    )
    worker_ami_type = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        default="AL2_x86_64_GPU",
        help_text=(
            "EKS node AMI type. Use a GPU variant unless CPU only jobs is "
            "enabled."
        ),
    )
    worker_disk_size = models.IntegerField(
        null=True,
        blank=True,
        default=100,
        help_text="Disk size of each EKS node, in GB.",
    )
    max_worker_instance = models.IntegerField(
        null=True,
        blank=True,
        default=10,
        help_text=(
            "EKS nodegroup ceiling, and the cap autoscaling may scale "
            "up to. Distinct from max ecs workers, which sizes Fargate."
        ),
    )
    min_worker_instance = models.IntegerField(
        null=True,
        blank=True,
        default=1,
        help_text=(
            "EKS nodegroup floor. Distinct from min ecs workers, which sizes "
            "Fargate."
        ),
    )
    desired_worker_instance = models.IntegerField(
        null=True,
        blank=True,
        default=1,
        help_text=(
            "EKS nodegroup size at creation. Autoscaling adjusts it "
            "from the pending submission count afterwards."
        ),
    )
    cpu_only_jobs = models.BooleanField(
        default=False,
        help_text="Schedule submission jobs without GPUs.",
    )
    job_cpu_cores = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        default="2000m",
        help_text=(
            "CPU request for a code upload submission's Kubernetes job, e.g. "
            "2000m = 2 vCPU."
        ),
    )
    job_memory = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        default="8Gi",
        help_text=(
            "Memory request for a code upload submission's Kubernetes job, "
            "e.g. 8Gi."
        ),
    )
    worker_image_url = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        default="",
        help_text=(
            "Override the worker container image. Leave blank to use the "
            "EvalAI default."
        ),
    )
    worker_python_version = models.CharField(
        max_length=10,
        blank=True,
        null=False,
        default=DEFAULT_WORKER_PYTHON_VERSION,
        choices=[(v, v) for v in SUPPORTED_WORKER_PYTHON_VERSIONS],
        help_text=(
            "Python version for the Fargate submission worker image "
            f"({', '.join(SUPPORTED_WORKER_PYTHON_VERSIONS)})."
        ),
    )
    evaluation_module_error = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Last error raised while importing the host's evaluation module. "
            "Set automatically."
        ),
    )
    is_frozen = models.BooleanField(
        default=False,
        verbose_name="Is Frozen",
        db_index=True,
        help_text=(
            "When frozen, challenge hosts cannot modify the start and end "
            "dates. Automatically set to True when a challenge is approved by "
            "admin."
        ),
    )
    is_submission_paused = models.BooleanField(
        default=False,
        verbose_name="Submissions Paused",
        db_index=True,
        help_text=(
            "When True, new submissions are rejected for all phases of this "
            "challenge. Already-queued submissions continue processing "
            "normally."
        ),
    )

    class Meta:
        app_label = "challenges"
        db_table = "challenge"
        ordering = ("title",)

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


@receiver(signals.post_save, sender="challenges.Challenge")
def create_eks_cluster_or_ec2_for_challenge(
    sender, instance, created, **kwargs
):
    field_name = "approved_by_admin"
    import challenges.aws_utils as aws

    if not created and is_model_field_changed(instance, field_name):
        if (
            instance.approved_by_admin is True
            and instance.is_docker_based is True
            and instance.remote_evaluation is False
        ):
            serialized_obj = serializers.serialize("json", [instance])
            aws.setup_eks_cluster.delay(serialized_obj)
        elif (
            instance.approved_by_admin is True
            and instance.uses_ec2_worker is True
        ):
            serialized_obj = serializers.serialize("json", [instance])
            aws.setup_ec2.delay(serialized_obj)
    aws.challenge_approval_callback(sender, instance, field_name, **kwargs)


@receiver(signals.post_save, sender="challenges.Challenge")
def update_sqs_retention_period_for_challenge(
    sender, instance, created, **kwargs
):
    field_name = "sqs_retention_period"
    import challenges.aws_utils as aws

    if not created and is_model_field_changed(instance, field_name):
        serialized_obj = serializers.serialize("json", [instance])
        aws.update_sqs_retention_period_task.delay(serialized_obj)
        # Update challenge
        curr = getattr(instance, "{}".format(field_name))
        challenge = instance
        challenge._original_sqs_retention_period = curr
        challenge.save()


@receiver(signals.post_save, sender="challenges.Challenge")
def handle_end_date_change_for_challenge(sender, instance, created, **kwargs):
    """
    When a challenge's end_date changes, update or recreate the EventBridge
    cleanup schedule and, if needed, recreate the full worker infrastructure.
    """
    field_name = "end_date"
    import challenges.aws_utils as aws

    if not created and is_model_field_changed(instance, field_name):
        challenge = instance
        new_end_date = challenge.end_date

        # For docker-based EKS challenges, trigger an autoscale check when
        # end_date changes (for example, if moved into the past).
        if (
            challenge.is_docker_based
            and not challenge.remote_evaluation
            and not challenge.uses_ec2_worker
        ):
            aws.trigger_eks_node_autoscale(
                challenge.pk,
                trigger_source="challenge_end_date_changed",
            )
            challenge._original_end_date = new_end_date
            return

        challenge._original_end_date = new_end_date

        # Skip if not a Fargate-managed challenge
        if (
            challenge.is_docker_based
            or challenge.uses_ec2_worker
            or challenge.remote_evaluation
        ):
            return

        # Skip if the challenge was never approved and has no workers
        # (workers may exist from host testing before approval)
        if not challenge.approved_by_admin and challenge.workers is None:
            return

        if new_end_date and new_end_date > timezone.now():
            if challenge.workers is None:
                # Resources were cleaned up (Lambda already fired).
                # Recreate everything: service + auto-scaling + schedule.
                aws.start_workers([challenge])
            else:
                # Resources still exist; just reschedule the cleanup.
                aws.update_challenge_cleanup_schedule(challenge)
        else:
            # New end_date is in the past; trigger cleanup if resources exist.
            if challenge.workers is not None:
                aws.delete_workers([challenge])


class DatasetSplit(TimeStampedModel):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)
    # Id in the challenge config file. Needed to map the object to the value
    # in the config file while updating through Github
    config_id = models.IntegerField(default=None, blank=True, null=True)

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
    challenge = models.ForeignKey("Challenge", on_delete=models.CASCADE)
    KEEP_FOREVER = "keep_forever"
    DAYS_14 = "days_14"
    DAYS_30 = "days_30"
    MONTHS_3 = "months_3"
    MONTHS_6 = "months_6"
    MONTHS_12 = "months_12"
    SUBMISSION_ARTIFACT_RETENTION_POLICY_OPTIONS = (
        (KEEP_FOREVER, "Keep forever"),
        (DAYS_14, "14 days"),
        (DAYS_30, "30 days"),
        (MONTHS_3, "3 months"),
        (MONTHS_6, "6 months"),
        (MONTHS_12, "12 months"),
    )
    submission_artifact_retention_policy = models.CharField(
        max_length=20,
        choices=SUBMISSION_ARTIFACT_RETENTION_POLICY_OPTIONS,
        default=KEEP_FOREVER,
        db_index=True,
    )
    is_public = models.BooleanField(default=False)
    is_submission_public = models.BooleanField(default=False)
    annotations_uploaded_using_cli = models.BooleanField(default=False)
    test_annotation = models.FileField(
        upload_to=RandomFileName("test_annotations"), null=True, blank=True
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
        default=list,
        blank=True,
        null=True,
    )
    slug = models.SlugField(max_length=200, null=True, unique=True)
    environment_image = models.CharField(
        max_length=2128, null=True, blank=True
    )  # Max length of repository name and tag is 2000 and 128 respectively
    allowed_submission_file_types = models.CharField(
        max_length=200, default=".json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy"
    )
    # Flag to restrict user to select only one submission for leaderboard
    is_restricted_to_select_one_submission = models.BooleanField(default=False)
    # Store the schema for the submission meta attributes of this challenge
    # phase.
    submission_meta_attributes = JSONField(default=None, blank=True, null=True)
    # Flag to allow reporting partial metrics for submission evaluation
    is_partial_submission_evaluation_enabled = models.BooleanField(
        default=False
    )
    # Id in the challenge config file. Needed to map the object to the value
    # in the config file while updating through Github
    config_id = models.IntegerField(default=None, blank=True, null=True)
    # Store the default metadata for a submission meta attributes of a
    # challenge phase.
    default_submission_meta_attributes = JSONField(
        default=None, blank=True, null=True
    )
    disable_logs = models.BooleanField(default=False)
    is_submission_paused = models.BooleanField(
        default=False,
        verbose_name="Submissions Paused",
        db_index=True,
        help_text="When True, new submissions are rejected for this phase. Already-queued submissions continue processing normally.",
    )

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

        # If the max_submissions_per_day is less than the
        # max_concurrent_submissions_allowed.
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


def post_save_connect(field_name, sender):
    import challenges.aws_utils as aws

    signals.post_save.connect(
        model_field_name(field_name=field_name)(
            aws.restart_workers_signal_callback
        ),
        sender=sender,
        weak=False,
    )


post_save_connect("evaluation_script", Challenge)
post_save_connect("test_annotation", ChallengePhase)


class Leaderboard(TimeStampedModel):

    schema = JSONField()
    # Id in the challenge config file. Needed to map the object to the value
    # in the config file while updating through Github
    config_id = models.IntegerField(default=None, blank=True, null=True)

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

    challenge_phase = models.ForeignKey(
        "ChallengePhase", on_delete=models.CASCADE
    )
    dataset_split = models.ForeignKey("DatasetSplit", on_delete=models.CASCADE)
    leaderboard = models.ForeignKey("Leaderboard", on_delete=models.CASCADE)
    visibility = models.PositiveSmallIntegerField(
        choices=VISIBILITY_OPTIONS, default=PUBLIC
    )
    leaderboard_decimal_precision = models.PositiveIntegerField(default=2)
    is_leaderboard_order_descending = models.BooleanField(default=True)
    show_leaderboard_by_latest_submission = models.BooleanField(default=False)
    show_execution_time = models.BooleanField(default=False)
    show_scores_on_leaderboard = models.BooleanField(default=True)
    # Allow ordering leaderboard by all metrics
    is_multi_metric_leaderboard = models.BooleanField(default=True)

    def __str__(self):
        return "{0} : {1}".format(
            self.challenge_phase.name, self.dataset_split.name
        )

    class Meta:
        app_label = "challenges"
        db_table = "challenge_phase_split"


class ChallengeTemplate(TimeStampedModel):
    """
    Model to store challenge templates

    Arguments:
        TimeStampedModel {[model class]} -- An abstract base class model that provides self-managed `created_at` and
                                            `modified_at` fields.
    """

    title = models.CharField(max_length=500)
    # Stores the challenge config zip file
    template_file = models.FileField(upload_to=RandomFileName("templates"))
    is_active = models.BooleanField(default=False, db_index=True)
    image = models.ImageField(
        upload_to=RandomFileName("templates/preview-images/"),
        null=True,
        blank=True,
        verbose_name="Template Preview Image",
    )
    dataset = models.CharField(max_length=200, default="")
    # The metrics on which the submissions are evaluated
    eval_metrics = ArrayField(
        models.CharField(max_length=200, blank=True),
        default=get_default_eval_metric,
        blank=True,
    )
    phases = models.IntegerField(null=True, blank=True, default=None)
    splits = models.IntegerField(null=True, blank=True, default=None)
    slug = models.CharField(max_length=500, default="")

    class Meta:
        app_label = "challenges"
        db_table = "challenge_templates"
        ordering = ("-created_at",)

    def __str__(self):
        """Returns the title of challenge template"""
        return self.title


class LeaderboardData(TimeStampedModel):

    challenge_phase_split = models.ForeignKey(
        "ChallengePhaseSplit", on_delete=models.CASCADE
    )
    submission = models.ForeignKey("jobs.Submission", on_delete=models.CASCADE)
    leaderboard = models.ForeignKey("Leaderboard", on_delete=models.CASCADE)
    result = JSONField()
    is_disabled = models.BooleanField(default=False)
    error = JSONField(null=True, blank=True)

    def __str__(self):
        return "{0} : {1}".format(self.challenge_phase_split, self.submission)

    class Meta:
        app_label = "challenges"
        db_table = "leaderboard_data"
        indexes = [
            models.Index(
                fields=["challenge_phase_split", "is_disabled", "-created_at"],
                name="ld_chphase_isdisc_created_idx",
            ),
        ]


class ChallengeConfiguration(TimeStampedModel):
    """
    Model to store zip file for challenge creation.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.OneToOneField(
        Challenge, null=True, blank=True, on_delete=models.CASCADE
    )
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    is_starred = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = "challenges"
        db_table = "starred_challenge"
        unique_together = (("user", "challenge"),)


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
    challenge = models.ForeignKey(
        Challenge, related_name="challenge", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(ChallengeHost, on_delete=models.CASCADE)

    class Meta:
        app_label = "challenges"
        db_table = "invite_user_to_challenge"

    def __str__(self):
        """Returns the email of the user"""
        return self.email


class ChallengeEvaluationCluster(TimeStampedModel):
    """Model to store the config for Kubernetes cluster for a challenge

    Arguments:
        TimeStampedModel {[model class]} -- An abstract base class model that provides self-managed `created_at` and
                                            `modified_at` fields.
    """

    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    cluster_endpoint = models.URLField(max_length=200, blank=True, null=True)
    cluster_ssl = models.TextField(null=True, blank=True)
    cluster_yaml = models.FileField(
        upload_to=RandomFileName("cluster_yaml"), blank=True, null=True
    )
    kube_config = models.FileField(
        upload_to=RandomFileName("kube_config"), blank=True, null=True
    )
    eks_arn_role = models.CharField(max_length=512, null=True, blank=True)
    node_group_arn_role = models.CharField(
        max_length=512, null=True, blank=True
    )
    # Recorded at nodegroup creation so autoscaling targets an explicit
    # nodegroup instead of guessing the first entry from list_nodegroups.
    nodegroup_name = models.CharField(max_length=512, null=True, blank=True)
    ecr_all_access_policy_arn = models.CharField(
        max_length=512, null=True, blank=True
    )
    vpc_id = models.CharField(max_length=512, null=True, blank=True)
    subnet_1_id = models.CharField(max_length=512, null=True, blank=True)
    subnet_2_id = models.CharField(max_length=512, null=True, blank=True)
    security_group_id = models.CharField(max_length=512, null=True, blank=True)
    internet_gateway_id = models.CharField(
        max_length=512, null=True, blank=True
    )
    route_table_id = models.CharField(max_length=512, null=True, blank=True)
    efs_security_group_id = models.CharField(
        max_length=512, null=True, blank=True
    )
    efs_id = models.CharField(max_length=512, null=True, blank=True)
    efs_creation_token = models.CharField(
        max_length=256, null=True, blank=True
    )
    efs_mount_target_ids = ArrayField(
        models.CharField(max_length=256, blank=True), default=list, blank=True
    )

    class Meta:
        app_label = "challenges"
        db_table = "challenge_evaluation_cluster"


class PWCChallengeLeaderboard(TimeStampedModel):
    """
    Model to store the challenge mapping with area, task and dataset of papers with code (PWC)
    (https://paperswithcode.com/)

    Arguments:
        TimeStampedModel {[model class]} -- An abstract base class model that provides self-managed `created_at` and
                                            `modified_at` fields.
    """

    phase_split = models.OneToOneField(
        "ChallengePhaseSplit", on_delete=models.CASCADE
    )
    area = models.CharField(max_length=200, default="", db_index=True)
    task = models.CharField(max_length=200, default="", db_index=True)
    dataset = models.CharField(max_length=200, default="", db_index=True)
    enable_sync = models.BooleanField(
        default=True,
        verbose_name="Enable leaderboard sync to PWC",
        db_index=True,
    )

    class Meta:
        app_label = "challenges"
        db_table = "pwc_challenge_leaderboard"


class ChallengeSponsor(TimeStampedModel):
    """
    Model to store challenge sponsors
    Arguments:
        TimeStampedModel {[model class]} -- An abstract base class model that provides self-managed `created_at` and
                                            `modified_at` fields.
    """

    challenge = models.ForeignKey("Challenge", on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        app_label = "challenges"
        db_table = "challenge_sponsor"

    def __str__(self):
        return f"Sponsor for {self.challenge}: {self.name}"


class ChallengePrize(TimeStampedModel):
    """
    Model to store challenge prizes
    Arguments:
        TimeStampedModel {[model class]} -- An abstract base class model that provides self-managed `created_at` and
                                            `modified_at` fields.
    """

    challenge = models.ForeignKey("Challenge", on_delete=models.CASCADE)
    amount = models.CharField(max_length=10)
    description = models.CharField(max_length=25, blank=True, null=True)
    rank = models.PositiveIntegerField()

    class Meta:
        app_label = "challenges"
        db_table = "challenge_prize"

    def __str__(self):
        return f"Prize for {self.challenge}: Rank {self.rank}, Amount {self.amount}"
