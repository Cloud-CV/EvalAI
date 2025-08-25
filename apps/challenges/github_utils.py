import logging
import threading
from .models import Challenge, ChallengePhase
from .github_interface import GithubInterface

logger = logging.getLogger(__name__)

# Thread-local storage to prevent recursive GitHub sync calls
_github_sync_context = threading.local()


def github_challenge_sync(challenge_id, changed_field):
    """
    Simple sync from EvalAI to GitHub
    This is the core function that keeps GitHub in sync with EvalAI
    """
    try:
        # Set flag to prevent recursive calls
        _github_sync_context.skip_github_sync = True
        _github_sync_context.change_source = 'github'
        
        # Ensure changed_field is a string
        if not isinstance(changed_field, str):
            logger.error(f"Invalid changed_field type: {type(changed_field)}, expected string")
            return False
        
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
        
        # Update challenge config in GitHub with the specific changed field
        success = github_interface.update_challenge_config(challenge, changed_field)
        
        if success:
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
        # Always clean up the flags
        if hasattr(_github_sync_context, 'skip_github_sync'):
            delattr(_github_sync_context, 'skip_github_sync')
        if hasattr(_github_sync_context, 'change_source'):
            delattr(_github_sync_context, 'change_source')


def github_challenge_phase_sync(challenge_phase_id, changed_field):
    """
    Sync challenge phase from EvalAI to GitHub
    """
    try:
        # Set flag to prevent recursive calls
        _github_sync_context.skip_github_sync = True
        _github_sync_context.change_source = 'github'
        
        # Ensure changed_field is a string
        if not isinstance(changed_field, str):
            logger.error(f"Invalid changed_field type: {type(changed_field)}, expected string")
            return False
        
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
        
        # Update challenge phase config in GitHub with the specific changed field
        success = github_interface.update_challenge_phase_config(challenge_phase, changed_field)
        
        if success:
            return True
        else:
            logger.error(f"Failed to sync challenge phase {challenge_phase_id} to GitHub")
            return False
            
    except ChallengePhase.DoesNotExist:
        logger.error(f"Challenge phase {challenge_phase_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error syncing challenge phase {challenge_phase_id} to GitHub")
        return False
    finally:
        # Always clean up the flags
        if hasattr(_github_sync_context, 'skip_github_sync'):
            delattr(_github_sync_context, 'skip_github_sync')
        if hasattr(_github_sync_context, 'change_source'):
            delattr(_github_sync_context, 'change_source')