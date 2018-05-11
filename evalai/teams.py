import click

from click import echo


@click.command()
def teams():
    """Example script."""
    echo('Hello Teams!')
