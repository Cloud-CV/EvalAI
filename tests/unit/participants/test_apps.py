import participants
from participants.apps import ParticipantsConfig


def test_participants_config_direct_import():
    config = ParticipantsConfig("participants", participants)
    assert config.name == "participants"
