import os
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from scripts.seed import resolve_submissions_per_challenge


def _resolve(value=None):
    environment = (
        {} if value is None else {"SEED_SUBMISSIONS_PER_CHALLENGE": value}
    )
    with patch.dict(os.environ, environment, clear=False):
        if value is None:
            os.environ.pop("SEED_SUBMISSIONS_PER_CHALLENGE", None)
        return resolve_submissions_per_challenge()


def test_defaults_when_unset():
    assert _resolve() == 2000


def test_reads_a_configured_value():
    assert _resolve("50") == 50


def test_allows_zero_for_challenges_without_submissions():
    assert _resolve("0") == 0


def test_rejects_a_non_integer_with_a_named_error():
    # Without this the seed dies at import with a bare ValueError traceback
    # that never mentions which variable was wrong.
    with pytest.raises(ImproperlyConfigured) as error:
        _resolve("lots")

    assert "SEED_SUBMISSIONS_PER_CHALLENGE" in str(error.value)
    assert "lots" in str(error.value)


def test_rejects_a_negative_value():
    # This is the quiet one. int("-5") succeeds, and the seed loop then
    # iterates range() over a negative count, so the database comes up with
    # zero submissions and no error to explain why.
    with pytest.raises(ImproperlyConfigured) as error:
        _resolve("-5")

    assert "SEED_SUBMISSIONS_PER_CHALLENGE" in str(error.value)
