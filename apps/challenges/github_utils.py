import logging
import yaml
from django.utils import timezone
from .models import Challenge, ChallengePhase
from .github_interface import GithubInterface

logger = logging.getLogger(__name__)


# Global set to track challenges currently being synced
_sync_in_progress = set()

def github_challenge_sync(challenge_id):
    """
    Simple sync from EvalAI to GitHub
    This is the core function that keeps GitHub in sync with EvalAI
    """
    # Prevent multiple simultaneous syncs for the same challenge
    if challenge_id in _sync_in_progress:
        logger.info(f"Challenge {challenge_id} sync already in progress, skipping")
        return False
    
    try:
        # Mark this challenge as being synced
        _sync_in_progress.add(challenge_id)
        
        challenge = Challenge.objects.get(id=challenge_id)
        
        if not challenge.github_repository or not challenge.github_token:
            logger.warning(f"Challenge {challenge_id} missing GitHub configuration")
            return False
        
        # Initialize GitHub interface
        github_interface = GithubInterface(
            challenge.github_repository,
            challenge.github_branch or 'challenge',  # Default to 'challenge' branch
            challenge.github_token
        )
        
        # Update challenge config in GitHub
        success = github_interface.update_challenge_config(challenge)
        
        if success:
            logger.info(f"Successfully synced challenge {challenge_id} to GitHub")
            return True
        else:
            logger.error(f"Failed to sync challenge {challenge_id} to GitHub")
            return False
            
    except Challenge.DoesNotExist:
        logger.error(f"Challenge {challenge_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error syncing challenge {challenge_id} to GitHub: {str(e)}")
        return False
    finally:
        # Always remove from in-progress set
        _sync_in_progress.discard(challenge_id)


def github_challenge_phase_sync(challenge_phase_id):
    """
    Sync challenge phase from EvalAI to GitHub
    """
    try:
        challenge_phase = ChallengePhase.objects.get(id=challenge_phase_id)
        challenge = challenge_phase.challenge
        
        if not challenge.github_repository or not challenge.github_token:
            logger.warning(f"Challenge {challenge.id} missing GitHub configuration")
            return False
        
        # Initialize GitHub interface
        github_interface = GithubInterface(
            challenge.github_repository,
            challenge.github_branch or 'challenge',  # Default to 'challenge' branch
            challenge.github_token
        )
        
        # Update challenge phase config in GitHub
        success = github_interface.update_challenge_phase_config(challenge_phase)
        
        if success:
            logger.info(f"Successfully synced challenge phase {challenge_phase_id} to GitHub")
            return True
        else:
            logger.error(f"Failed to sync challenge phase {challenge_phase_id} to GitHub")
            return False
            
    except ChallengePhase.DoesNotExist:
        logger.error(f"Challenge phase {challenge_phase_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error syncing challenge phase {challenge_phase_id} to GitHub: {str(e)}")
        return False