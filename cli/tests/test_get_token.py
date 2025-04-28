from click.testing import CliRunner
from unittest.mock import patch, mock_open

from evalai.get_token import get_token


class TestGetToken:
    def test_get_token(self):
        expected_token = "test"
        expected_json = """{"token": "%s"}""" % expected_token
        expected = "Current token is {}".format(expected_token)

        mock_file = mock_open(read_data=expected_json)
        with patch("evalai.get_token.open", mock_file):
            runner = CliRunner()
            result = runner.invoke(get_token)
        response = result.output.rstrip()
        assert response == expected

    @patch("evalai.get_token.os.path.exists", return_value=False)
    def test_get_token_when_auth_token_file_doesnt_exist(self, mock_exists):
        expected = (
            "\nThe authentication token json file doesn't exist at the required path. "
            "Please download the file from the Profile section of the EvalAI webapp and "
            "place it at ~/.evalai/token.json or use evalai -t <token> to add it."
        )
        runner = CliRunner()
        result = runner.invoke(get_token)
        response = result.output.rstrip()
        assert response == expected
