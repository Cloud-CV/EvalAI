from unittest.mock import MagicMock, patch

from apps.base.management.commands.seed import Command


@patch("apps.base.management.commands.seed.call_command")
def test_handle_default_nc(mock_call_command):
    command = Command()
    command.stdout = MagicMock()
    command.handle(**{"nc": 500})

    expected_msg = command.style.SUCCESS(
        "Starting the database seeder with 500 challenges. Hang on..."
    )
    command.stdout.write.assert_called_with(expected_msg)

    mock_call_command.assert_called_with(
        "runscript", "seed", "--script-args", 500
    )


@patch("apps.base.management.commands.seed.call_command")
def test_handle_custom_nc(mock_call_command):
    command = Command()
    command.stdout = MagicMock()
    command.handle(**{"nc": 5})

    expected_msg = command.style.SUCCESS(
        "Starting the database seeder with 5 challenges. Hang on..."
    )
    command.stdout.write.assert_called_with(expected_msg)

    mock_call_command.assert_called_with(
        "runscript", "seed", "--script-args", 5
    )


def test_add_arguments():
    parser_mock = MagicMock()
    command = Command()
    command.add_arguments(parser_mock)

    parser_mock.add_argument.assert_called_with(
        "-nc",
        nargs="?",
        default=500,
        type=int,
        help="Number of challenges. Default: 500 (40% present, 20% future, 40% past)",
    )
