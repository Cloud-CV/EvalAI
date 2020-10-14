import os
import click
import json

from click import echo, style
from evalai.utils.auth import get_user_auth_token_by_login
from evalai.utils.config import AUTH_TOKEN_PATH, AUTH_TOKEN_DIR


@click.group(invoke_without_command=True)
@click.pass_context
def login(ctx):
    """
    Login to EvalAI and save token.
    """
    username = click.prompt("username", type=str, hide_input=False)
    password = click.prompt("Enter password", type=str, hide_input=True)
    token = get_user_auth_token_by_login(username, password)

    if os.path.exists(AUTH_TOKEN_PATH):
        with open(str(AUTH_TOKEN_PATH), "w") as TokenFile:
            try:
                json.dump(token, TokenFile)
            except (OSError, IOError) as e:
                echo(e)
    else:
        if not os.path.exists(AUTH_TOKEN_DIR):
            os.makedirs(AUTH_TOKEN_DIR)
        with open(str(AUTH_TOKEN_PATH), "w+") as TokenFile:
            try:
                json.dump(token, TokenFile)
            except (OSError, IOError) as e:
                echo(e)

    echo(style("\nLogged in successfully!", bold=True))
