import click

from evalai.utils.challenges import (
                                    display_all_challenge_list,
                                    display_future_challenge_list,
                                    display_ongoing_challenge_list,
                                    display_past_challenge_list,
                                    display_participated_or_hosted_challenges,)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--participant', is_flag=True,
              help="List the challenges that you've participated")
@click.option('--host', is_flag=True,
              help="List the challenges that you've hosted")
def challenges(ctx, participant, host):
    """
    Lists challenges

    Invoked by running `evalai challenges`
    """
    if participant or host:
        display_participated_or_hosted_challenges(host, participant)
    elif ctx.invoked_subcommand is None:
        display_all_challenge_list()


@challenges.command()
def ongoing():
    """
    List all active challenges

    Invoked by running `evalai challenges ongoing`
    """
    display_ongoing_challenge_list()


@challenges.command()
def past():
    """
    List all past challenges

    Invoked by running `evalai challenges past`
    """
    display_past_challenge_list()


@challenges.command()
def future():
    """
    List all upcoming challenges

    Invoked by running `evalai challenges future`
    """
    display_future_challenge_list()
