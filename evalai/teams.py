import click

from evalai.utils.teams import (
                                create_participant_team,
                                display_participant_teams,
                               )


@click.group(invoke_without_command=True)
@click.pass_context
def teams(ctx):
    """
    List all the participant teams of a user.

    Invoked by running `evalai teams`
    """
    if ctx.invoked_subcommand is None:
        display_participant_teams()


@teams.command()
def create():
    """
    Create a participant team.

    Invoked by running `evalai teams create`
    """
    team_name = click.prompt("Enter team name: ", type=str)
    if click.confirm("Please confirm the team name - %s" % (team_name), abort=True):
        create_participant_team(team_name)
