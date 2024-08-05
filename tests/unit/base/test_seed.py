import unittest
from unittest.mock import MagicMock
from base.management.commands.seed import Command

class TestSeedCommand(unittest.TestCase):
    def test_add_arguments_adds_nc_argument(self):
        parser = MagicMock()
        command = Command()
        command.add_arguments(parser)
        parser.add_argument.assert_called_once_with(
            '-nc', nargs='?', default=20, type=int, help='Number of challenges.')



if __name__ == '__main__':
    unittest.main()