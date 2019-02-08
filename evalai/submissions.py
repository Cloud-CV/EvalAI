import click

from evalai.utils.submissions import display_submission_details


@click.group(invoke_without_command=True)
@click.argument("SUBMISSION", type=int)
def submission(submission):
    """
    View submission specific details.
    """
    """
    Invoked by `evalai submission SUBMISSION`.
    """
    display_submission_details(submission)
