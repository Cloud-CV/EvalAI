from rest_framework import serializers
from .models import PaymentTier, ChallengePaymentTier


class PaymentTierSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentTier model
    """
    
    class Meta:
        model = PaymentTier
        fields = [
            'id',
            'name',
            'display_name',
            'is_active',
            'is_free_tier',
            'created_at',
            'modified_at'
        ]
        read_only_fields = ['is_free_tier', 'created_at', 'modified_at']


class ChallengePaymentTierSerializer(serializers.ModelSerializer):
    """
    Serializer for ChallengePaymentTier model
    """
    
    payment_tier_details = PaymentTierSerializer(source='payment_tier', read_only=True)
    challenge_title = serializers.CharField(source='challenge.title', read_only=True)
    
    class Meta:
        model = ChallengePaymentTier
        fields = [
            'id',
            'challenge',
            'challenge_title',
            'payment_tier',
            'payment_tier_details',
            'created_at',
            'modified_at'
        ]
        read_only_fields = ['created_at', 'modified_at']