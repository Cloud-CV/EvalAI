import web
from web.apps import WebConfig


def test_web_config_direct_import():
    config = WebConfig("web", web)
    assert config.name == "web"
