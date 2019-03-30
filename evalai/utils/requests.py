import json
import requests
import sys

from click import echo, style

from evalai.utils.config import EVALAI_ERROR_CODES
from evalai.utils.common import validate_token

from .auth import get_request_header, get_host_url


def make_request(path, method, files=None, data=None):
    url = "{}{}".format(get_host_url(), path)
    headers = get_request_header()

    if method == "GET":
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if response.status_code in EVALAI_ERROR_CODES:
                validate_token(response.json())
                echo(
                    style(
                        "\nError: {}\n".format(response.json().get("error")),
                        fg="red",
                        bold=True,
                    )
                )
            else:
                echo(err)
            sys.exit(1)
        except requests.exceptions.RequestException:
            echo(
                style(
                    "\nCould not establish a connection to EvalAI."
                    " Please check the Host URL.\n",
                    bold=True,
                    fg="red",
                )
            )
            sys.exit(1)
        return response.json()
    elif method == "POST":
        if files:
            files = {"input_file": open(files, "rb")}
        else:
            files = None
        data = {"status": "submitting"}
        try:
            response = requests.post(
                url, headers=headers, files=files, data=data
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if response.status_code in EVALAI_ERROR_CODES:
                validate_token(response.json())
                echo(
                    style(
                        "\nError: {}\n"
                        "\nUse `evalai challenges` to fetch the active challenges.\n"
                        "\nUse `evalai challenge CHALLENGE phases` to fetch the "
                        "active phases.\n".format(response.json()["error"]),
                        fg="red",
                        bold=True,
                    )
                )
            else:
                echo(err)
            sys.exit(1)
        except requests.exceptions.RequestException:
            echo(
                style(
                    "\nCould not establish a connection to EvalAI."
                    " Please check the Host URL.\n",
                    bold=True,
                    fg="red",
                )
            )
            sys.exit(1)
        response = json.loads(response.text)
        echo(
            style(
                "\nYour docker file is successfully submitted.\n",
                fg="green",
                bold=True,
            )
        )
        echo(
            style(
                "You can use `evalai submission {}` to view this submission's status.\n".format(
                    response.get("id")
                ),
                bold=True,
            )
        )
        return response
    elif method == "PUT":
        # TODO: Add support for PUT request
        pass
    elif method == "PATCH":
        # TODO: Add support for PATCH request
        pass
    elif method == "DELETE":
        # TODO: Add support for DELETE request
        pass
