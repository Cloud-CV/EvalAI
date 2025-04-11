#!/usr/bin/env python
"""
manage.py - Entry point to run Django management commands for EvalAI.
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # The above import may fail for some other reason.
        # Ensure that the issue is really that Django is missing
        # to avoid masking other exceptions.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
