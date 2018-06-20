# Store all the varibales here
import os

from os.path import expanduser


AUTH_TOKEN = 'token.json'
AUTH_TOKEN_PATH = "{}/.evalai/{}".format(expanduser('~'), AUTH_TOKEN)

API_HOST_URL = os.environ.get("EVALAI_API_URL", 'http://localhost:8000')
