import hosts
from hosts.apps import HostsConfig

def test_hosts_app_config_properties():
    config = HostsConfig("hosts", hosts)
    assert config.name == "hosts"
