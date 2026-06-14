from __future__ import unicode_literals

from base.models import TimeStampedModel
from django.contrib.postgres.fields import JSONField
from django.db import models


class Scout(TimeStampedModel):
    """One registered Yutori scout. The schema supports N rows;
    additional scouts are registered via ``scout_create --name <name>``
    with no migration required.

    Inherits ``created_at`` and ``modified_at`` from
    ``base.models.TimeStampedModel`` (the EvalAI convention also used by
    ``jobs.Submission``).
    """

    name = models.CharField(max_length=64, unique=True, db_index=True)
    webhook_token = models.CharField(max_length=128)
    scout_id = models.CharField(max_length=64, unique=True)
    query_hash = models.CharField(max_length=64)
    webhook_url = models.URLField(max_length=512)
    yutori_view_url = models.URLField(max_length=512, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "scout"

    def __str__(self):
        return "Scout(name={}, scout_id={}, paused={})".format(
            self.name, self.scout_id, self.paused_at is not None
        )


class ScoutRun(models.Model):
    """One row per webhook delivery — audit trail of raw Yutori payloads."""

    scout = models.ForeignKey(
        Scout, on_delete=models.CASCADE, related_name="runs"
    )
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    raw_payload = JSONField()
    new_challenge_count = models.IntegerField(default=0)
    parse_warnings = JSONField(default=list, blank=True)

    class Meta:
        ordering = ("-received_at",)

    def __str__(self):
        return "ScoutRun(received_at={}, new={})".format(
            self.received_at, self.new_challenge_count
        )


class ScoutChallenge(models.Model):
    """A deduped benchmark/challenge discovered by the scout."""

    benchmark_name = models.CharField(max_length=512)
    conference = models.CharField(max_length=128)
    year = models.IntegerField()
    canonical_key = models.CharField(
        max_length=768, unique=True, db_index=True
    )

    task_area = models.CharField(max_length=128, blank=True)
    official_url = models.URLField(max_length=1024)
    dataset_url = models.URLField(max_length=1024, blank=True)
    organizers = JSONField(default=list)
    evalai_suitable = models.BooleanField()
    evalai_reasoning = models.TextField(blank=True)

    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    outreach_sent_at = models.DateTimeField(
        null=True, blank=True, db_index=True
    )
    source_run = models.ForeignKey(
        ScoutRun,
        on_delete=models.SET_NULL,
        null=True,
        related_name="challenges",
    )

    class Meta:
        ordering = ("-first_seen",)

    def __str__(self):
        return "{} @ {} {}".format(
            self.benchmark_name, self.conference, self.year
        )
