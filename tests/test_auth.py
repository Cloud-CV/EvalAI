import os
import shutil
from click.testing import CliRunner

from evalai.challenges import challenges
from evalai.utils.config import AUTH_TOKEN_DIR

from tests.base import BaseTestClass


class TestGetUserAuthToken(BaseTestClass):

    def setup(self):
        if os.path.exists(AUTH_TOKEN_DIR):
            shutil.rmtree(AUTH_TOKEN_DIR)

    def test_get_user_auth_token_when_file_does_not_exist(self):
        expected = ("\nYour token file doesn't exists.\n"
                    "\nIt should be present at ~/.evalai/token.json\n\n")
        runner = CliRunner()
        result = runner.invoke(challenges)
        response = result.output
        assert response == expected
