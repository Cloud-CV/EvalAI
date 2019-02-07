import click
import os
import validators

from click import echo, style

from evalai.utils.config import (AUTH_TOKEN_DIR,
                                 AUTH_TOKEN_PATH,
                                 LEN_OF_TOKEN,)


@click.group(invoke_without_command=True)
@click.argument('add_token')
def token(add_token):
    """
    View and configure the EvalAI Token.
    """
    """
    Invoked by `evalai token <your_token_here>`.
    """
    if add_token is not None:
        if validators.length(add_token, min=LEN_OF_TOKEN, max=LEN_OF_TOKEN):
            if not os.path.exists(AUTH_TOKEN_DIR):
                os.makedirs(AUTH_TOKEN_DIR)
            with open(AUTH_TOKEN_PATH, 'w+') as fw:
                try:
                    fw.write(add_token)
                except (OSError, IOError) as e:
                    echo(e)
                echo(style("Token successfully set!", bold=True))
        else:
            echo(style("Error: Invalid Length. Enter a valid token of length: {}".format(LEN_OF_TOKEN), bold=True))
    else:
        if not os.path.exists(AUTH_TOKEN_PATH):
            echo(style("\nThe authentication token json file doesn't exist at the required path. "
                       "Please download the file from the Profile section of the EvalAI webapp and "
                       "place it at ~/.evalai/token.json or use evalai -t <token> to add it.\n\n", bold=True))
        else:
            with open(AUTH_TOKEN_PATH, 'r') as fr:
                try:
                    data = fr.read()
                    echo(style("Current token: {}".format(data), bold=True))
                except (OSError, IOError) as e:
                    echo(e)
