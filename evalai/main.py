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
        welcome_text = (r"]]]]]]]                  lll      /+\    (0) "
                     "\n"
                    r"]]      db   db   d880b  lll     +++++       "
                     "\n"
                    r"]]]]]    db db   d.  0b  lll    ++   ++  /#\ "
                     "\n"
                    r"]]        dvb   d8.  0b  lllll  +++++++  |#| "
                     "\n"
                    r"]]]]]]]    V     d8o o8b lllll  ++   ++  \#/ "
                     "\n"
                    r"                                ### ###      "
                     "\n"
                    r"                                 #   #       "
                     "\n\n"

                        "Welcome to the EvalAI CLI. Use evalai --help for viewing all the options\n"
                        "CHALLENGE and PHASE placeholders used throughout the CLI are"
                        " for challenge_id\nand phase_id of the challenges and phases.")
        echo(welcome_text)


main.add_command(challenges)
main.add_command(challenge)
main.add_command(host)
main.add_command(submission)
main.add_command(teams)
