"""Unit tests for the FIWARE Actuator microservice configuration.

These tests validate the creation of valid device with minimum attributes
and commands.
"""

import pytest

from fiware_actuators_setup.models import Command, Device


def test_create_valid_device():
    """Test creating a valid device with minimum attributes"""

    cmd = Command(name="switch_on", type="command")

    device = Device(
        device_id="dev001",
        entity_name="Actuator:001",
        entity_type="Actuator",
        transport="HTTP",
        protocol="PDI-IoTA-UltraLight",
        apikey="mqtt0001",
        commands=[cmd],
    )

    assert device.device_id == "dev001"
    assert device.commands[0].name == "switch_on"


def test_device_requires_at_least_one_command():
    """Test that device contains at least one commad"""
    with pytest.raises(ValueError):
        Device(
            device_id="dev001",
            entity_name="Actuator:001",
            entity_type="Actuator",
            transport="HTTP",
            protocol="PDI-IoTA-UltraLight",
            commands=[],
        )
