from unittest import TestCase
from unittest.mock import MagicMock

from challenges.permissions import IsChallengeCreator


class TestIsChallengeCreator(TestCase):
    def setUp(self):
        self.permission = IsChallengeCreator()
        self.request = MagicMock()
        self.view = MagicMock()

    def test_has_permission_unsupported_method(self):
        self.request.method = "TRACE"
        result = self.permission.has_permission(self.request, self.view)
        assert result is False
