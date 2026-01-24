from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tiers', views.PaymentTierViewSet, basename='payment-tier')
router.register(r'challenge-tiers', views.ChallengePaymentTierViewSet, basename='challenge-payment-tier')

app_name = 'payments'

urlpatterns = [
    path('api/', include(router.urls)),
]