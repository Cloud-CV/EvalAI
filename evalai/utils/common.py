from click import echo


def valid_token(response):
    """
    Checks if token is valid.
    """

    if ('detail' in response):
        if (response['detail'] == 'Invalid token'):
            echo("The authentication token you are using isn't valid."
                 " Please try again.")
            return False
        if (response['detail'] == 'Token has expired'):
            echo("Sorry, the token has expired.")
            return False
    return True
