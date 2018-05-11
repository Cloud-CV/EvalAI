import click

from click import echo


@click.command()
def challenges():
    """Example script."""
    echo('Hello Challenges!')
