from .models import PaymentTier, ChallengePaymentTier


def get_challenge_payment_tier(challenge):
    """
    Get the payment tier for a challenge
    
    Args:
        challenge: Challenge instance
        
    Returns:
        ChallengePaymentTier instance or None
    """
    try:
        return ChallengePaymentTier.objects.select_related('payment_tier').get(
            challenge=challenge
        )
    except ChallengePaymentTier.DoesNotExist:
        return None


def set_challenge_payment_tier(challenge, payment_tier_name):
    """
    Set or update the payment tier for a challenge
    
    Args:
        challenge: Challenge instance
        payment_tier_name: Name of the payment tier (e.g., 'free', 'essentials')
        
    Returns:
        ChallengePaymentTier instance
    """
    try:
        payment_tier = PaymentTier.objects.get(name=payment_tier_name, is_active=True)
        
        challenge_payment_tier, created = ChallengePaymentTier.objects.get_or_create(
            challenge=challenge,
            defaults={'payment_tier': payment_tier}
        )
        
        if not created and challenge_payment_tier.payment_tier != payment_tier:
            challenge_payment_tier.payment_tier = payment_tier
            challenge_payment_tier.save()
        
        return challenge_payment_tier
        
    except PaymentTier.DoesNotExist:
        raise ValueError(f"Payment tier '{payment_tier_name}' does not exist or is not active")


def get_default_payment_tier():
    """
    Get the default payment tier (free tier)
    
    Returns:
        PaymentTier instance
    """
    return PaymentTier.objects.get(name='free', is_active=True)


def create_default_payment_tiers():
    """
    Create default payment tiers if they don't exist
    """
    default_tiers = [
        {
            'name': 'free',
            'display_name': 'Free',
        },
        {
            'name': 'essentials',
            'display_name': 'Essentials',
        },
        {
            'name': 'core',
            'display_name': 'Core',
        },
        {
            'name': 'advanced',
            'display_name': 'Advanced',
        },
        {
            'name': 'remote',
            'display_name': 'Remote',
        },
    ]
    
    created_tiers = []
    for tier_data in default_tiers:
        tier, created = PaymentTier.objects.get_or_create(
            name=tier_data['name'],
            defaults=tier_data
        )
        if created:
            created_tiers.append(tier)
    
    return created_tiers


def ensure_challenge_has_payment_tier(challenge):
    """
    Ensure a challenge has a payment tier assigned (defaults to free)
    
    Args:
        challenge: Challenge instance
        
    Returns:
        ChallengePaymentTier instance
    """
    challenge_payment_tier = get_challenge_payment_tier(challenge)
    
    if not challenge_payment_tier:
        # If challenge has the old payment_tier field, use that
        if hasattr(challenge, 'payment_tier') and challenge.payment_tier:
            return set_challenge_payment_tier(challenge, challenge.payment_tier)
        else:
            # Default to free tier
            return set_challenge_payment_tier(challenge, 'free')
    
    return challenge_payment_tier