from __future__ import unicode_literals

from base.models import TimeStampedModel
from django.db import models


class PaymentTier(TimeStampedModel):
    """
    Model to define different payment tiers
    """
    
    TIER_CHOICES = (
        ("free", "Free"),
        ("essentials", "Essentials"),
        ("core", "Core"),
        ("advanced", "Advanced"),
        ("remote", "Remote"),
    )
    
    name = models.CharField(
        max_length=50, 
        choices=TIER_CHOICES, 
        unique=True,
        db_index=True
    )
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "payments"
        db_table = "payment_tier"
        ordering = ("name",)

    def __str__(self):
        return self.display_name

    @property
    def is_free_tier(self):
        return self.name == "free"


class ChallengePaymentTier(TimeStampedModel):
    """
    Model to map challenges to payment tiers
    """
    
    challenge = models.OneToOneField(
        "challenges.Challenge", 
        on_delete=models.CASCADE,
        related_name="payment_tier_mapping"
    )
    payment_tier = models.ForeignKey(
        PaymentTier, 
        on_delete=models.PROTECT,
        related_name="challenge_mappings"
    )

    class Meta:
        app_label = "payments"
        db_table = "challenge_payment_tier"

    def __str__(self):
        return f"{self.challenge.title} - {self.payment_tier.display_name}"