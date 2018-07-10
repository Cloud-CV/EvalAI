import click
import os
import validators

from click import echo, style

from evalai.utils.config import (AUTH_TOKEN_DIR,
                                 HOST_URL_FILE_PATH,)


@click.group(invoke_without_command=True)
@click.option('-sh', '--set-host',
              help="Set the Host URL of the EvalAI Instance.")
def host(set_host):
    """
    View and configure the Host URL.
    """
    if set_host is not None:
        if validators.url(set_host):
            if not os.path.exists(AUTH_TOKEN_DIR):
                os.makedirs(AUTH_TOKEN_DIR)
            with open(HOST_URL_FILE_PATH, 'w+') as fw:
                try:
                    fw.write(set_host)
                except (OSError, IOError) as e:
                    echo(e)
                echo(style("{} is set as the host url!".format(set_host), bold=True))
        else:
            echo(style("Sorry, please enter a valid url.\n"
                       "Example: https://evalapi.cloudcv.org", bold=True))
    else:
        if not os.path.exists(HOST_URL_FILE_PATH):
            echo(style("You haven't configured a Host URL for the CLI.\n"
                       "The CLI would be using http://localhost:8000 as the default url.", bold=True))
        else:
            with open(HOST_URL_FILE_PATH, 'r') as fr:
                try:
                    data = fr.read()
                    echo(style("{} is the Host URL of EvalAI.".format(data), bold=True))
                except (OSError, IOError) as e:
                    echo(e)
