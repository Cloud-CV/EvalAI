import sys
from click import echo, style


def validate_token(response):
    """
    Function to check if the authentication token provided by user is valid or not.
    """
    if('detail' in response):
        if (response['detail'] == 'Invalid token'):
            echo(style("\nThe authentication token you are using isn't valid."
                       " Please generate it again.\n", bold=True, bg="red"))
            sys.exit(1)
        if (response['detail'] == 'Token has expired'):
            echo(style("\nSorry, the token has expired. Please generate it again.\n", bold=True, bg="red"))
            sys.exit(1)
