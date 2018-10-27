import click

from click import echo

from .challenges import challenge, challenges
from .set_host import host
from .submissions import submission
from .teams import teams


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """
    Welcome to the EvalAI CLI.
    """
    if ctx.invoked_subcommand is None:
        welcome_text = ("""
                                      d888888b
                                 d88888888888888b
                         d88888888b+++++++++++++8b
                    d8888+++++++++++++++++++++++++8b
                  d88++++++++++++*$$$$$$$*++++++++8888b
                  d8+++++++++++$$$"  0  "$$$+++++++++++8b
                   d8++++++++++++*$$$$$$$*+++++++++++++8b
                    d8888880+++++++++++++++++++++++++88b
                            d88888888888888888888888b
            .o88b. db       .d88b.  db    db d8888b.  .o88b. db    db
           d8P  Y8 88      .8P  Y8. 88    88 88  `8D d8P  Y8 88    88
           8P      88      88    88 88    88 88   88 8P      Y8    8P
           8b      88      88    88 88    88 88   88 8b      `8b  d8'
           Y8b  d8 88booo. `8b  d8' 88b  d88 88  .8D Y8b  d8  `8bd8'
            `Y88P' Y88888P  `Y88P'  ~Y8888P' Y8888D'  `Y88P'    YP"""
        "Welcome to the EvalAI CLI. Use evalai --help for viewing all the options\n"
                        "CHALLENGE and PHASE placeholders used throughout the CLI are"
                        " for challenge_id\nand phase_id of the challenges and phases.")
        echo(welcome_text)


main.add_command(challenges)
main.add_command(challenge)
main.add_command(host)
main.add_command(submission)
main.add_command(teams)
