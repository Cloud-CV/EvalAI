import click

from click import echo

from .challenges import challenge, challenges
from .set_host import host
from .add_token import set_token
from .submissions import submission
from .teams import teams
from .get_token import get_token


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """
    Welcome to the EvalAI CLI.
    """
    if ctx.invoked_subcommand is None:
        welcome_text = (
            """
                        #######                  ###      ###    #######
                        ##      ##   ##   #####  ###     #####     ###
                        #####    ## ##   ##  ##  ###    ##   ##    ###
                        ##        ###   ###  ##  #####  #######    ###
                        #######    #     ### ### #####  ##   ##  #######\n\n"""
            "Welcome to the EvalAI CLI. Use evalai --help for viewing all the options\n"
            "CHALLENGE and PHASE placeholders used throughout the CLI are"
            " for challenge_id\nand phase_id of the challenges and phases."
        )
        echo(welcome_text)


main.add_command(challenges)
main.add_command(challenge)
main.add_command(host)
main.add_command(set_token)
main.add_command(submission)
main.add_command(teams)
main.add_command(get_token)
