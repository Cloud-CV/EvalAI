import unittest
from unittest.mock import patch, MagicMock
from apps.base.management.commands.seed import Command


class TestSeedCommand(unittest.TestCase):

    @patch("apps.base.management.commands.seed.call_command")
    def test_handle_default_nc(self, mock_call_command):
        """
        Test that the handle() method uses the default value 20
        when -nc is not provided.
        """
        command = Command()
        command.stdout = MagicMock()
        command.handle(**{"nc": 20})  

        expected_msg = command.style.SUCCESS("Starting the database seeder. Hang on...")
        command.stdout.write.assert_called_with(expected_msg)

        mock_call_command.assert_called_with("runscript", "seed", "--script-args", 20)

    @patch("apps.base.management.commands.seed.call_command")
    def test_handle_custom_nc(self, mock_call_command):
        """
        Test that the handle() method uses the value of nc
        provided as a command-line argument.
        """
        command = Command()
        command.stdout = MagicMock()
        command.handle(**{"nc": 5}) 

        expected_msg = command.style.SUCCESS("Starting the database seeder. Hang on...")
        command.stdout.write.assert_called_with(expected_msg)

        mock_call_command.assert_called_with("runscript", "seed", "--script-args", 5)

    def test_add_arguments(self):
        """
        Test that the -nc argument is added to the parser correctly.
        """
        parser_mock = MagicMock()
        command = Command()
        command.add_arguments(parser_mock)

        parser_mock.add_argument.assert_called_with(
            "-nc",
            nargs="?",
            default=20,
            type=int,
            help="Number of challenges.",
        )