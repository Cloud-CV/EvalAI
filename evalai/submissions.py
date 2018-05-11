import click

from click import echo


@click.command()
def submissions():
    """Example script."""
    echo('Hello Submissions!')
