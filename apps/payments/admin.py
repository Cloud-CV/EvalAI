from django.contrib import admin
from .models import PaymentTier, ChallengePaymentTier


@admin.register(PaymentTier)
class PaymentTierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'display_name', 
        'is_active'
    ]
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'display_name']
    ordering = ['name']


@admin.register(ChallengePaymentTier)
class ChallengePaymentTierAdmin(admin.ModelAdmin):
    list_display = [
        'challenge',
        'payment_tier',
        'created_at'
    ]
    list_filter = [
        'payment_tier__name',
        'created_at'
    ]
    search_fields = [
        'challenge__title'
    ]
    raw_id_fields = ['challenge']