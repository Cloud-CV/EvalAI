from __future__ import unicode_literals

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self):
        from .bounce_handler import connect_signals

        connect_signals()
