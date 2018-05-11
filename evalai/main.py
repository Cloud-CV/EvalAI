import click

from click import echo

from .auth import auth
from .challenges import challenges
from .submissions import submissions
from .teams import teams


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        echo('I was invoked without subcommand')
    else:
        echo('I am about to invoke %s' % ctx.invoked_subcommand)

main.add_command(auth)
main.add_command(challenges)
main.add_command(submissions)
main.add_command(teams)
