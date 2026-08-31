import os
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


def test_add_arguments_defaults_to_the_full_dataset():
    parser_mock = MagicMock()
    command = Command()

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("SEED_CHALLENGES", None)
        command.add_arguments(parser_mock)

    assert parser_mock.add_argument.call_args.kwargs["default"] == 500


def test_add_arguments_honours_seed_challenges_env():
    # The dev container sets this. Without it a fresh database spends over
    # twenty minutes generating 500 challenges x 2000 submissions before
    # Django will serve a single request, which is a load-testing dataset
    # rather than a development one.
    parser_mock = MagicMock()
    command = Command()

    with patch.dict(os.environ, {"SEED_CHALLENGES": "10"}, clear=False):
        command.add_arguments(parser_mock)

    assert parser_mock.add_argument.call_args.kwargs["default"] == 10
