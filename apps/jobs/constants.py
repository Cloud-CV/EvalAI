from .models import Submission


submission_status_to_exclude = [Submission.FAILED, Submission.CANCELLED]
