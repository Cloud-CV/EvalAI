from click import echo


def validate_token(response):
    """
    Function to check if the authentication token provided by user is valid or not.
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
