from __future__ import unicode_literals

from django.apps import AppConfig


class ChallengesConfig(AppConfig):
    name = "challenges"

    def ready(self):
        import challenges.signals  # noqa
