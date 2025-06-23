import analytics
from analytics.apps import AnalyticsConfig


def test_analytics_app_config_properties():
    config = AnalyticsConfig("analytics", analytics)
    assert config.name == "analytics"
