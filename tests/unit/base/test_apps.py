import base
from base.apps import BaseConfig


def test_base_app_config_properties():
    config = BaseConfig("base", base)
    assert config.name == "base"
