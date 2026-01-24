from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PaymentTier, ChallengePaymentTier
from .serializers import (
    PaymentTierSerializer,
    ChallengePaymentTierSerializer
)


class PaymentTierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payment tiers
    """
    queryset = PaymentTier.objects.filter(is_active=True)
    serializer_class = PaymentTierSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only admin users can see all tiers
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset


class ChallengePaymentTierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing challenge payment tier mappings
    """
    serializer_class = ChallengePaymentTierSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ChallengePaymentTier.objects.select_related(
            'challenge', 'payment_tier'
        )
        
        # Filter by user's challenges
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                challenge__creator__created_by=self.request.user
            )
        
        # Filter by challenge if provided
        challenge_id = self.request.query_params.get('challenge_id')
        if challenge_id:
            queryset = queryset.filter(challenge_id=challenge_id)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def change_tier(self, request, pk=None):
        """
        Change payment tier for a challenge
        """
        challenge_payment_tier = self.get_object()
        new_tier_id = request.data.get('tier_id')
        
        try:
            new_tier = PaymentTier.objects.get(id=new_tier_id, is_active=True)
            old_tier = challenge_payment_tier.payment_tier
            
            # Update payment tier
            challenge_payment_tier.payment_tier = new_tier
            challenge_payment_tier.save()
            
            return Response({
                'message': f'Tier changed from {old_tier.display_name} to {new_tier.display_name}',
                'old_tier': old_tier.name,
                'new_tier': new_tier.name
            })
            
        except PaymentTier.DoesNotExist:
            return Response(
                {'error': 'Invalid tier selected'},
                status=status.HTTP_400_BAD_REQUEST
            )