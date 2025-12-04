"""Unit tests for the FIWARE Actuator microservice configuration.

These tests validate the creation of valid service with minimum attributes.
"""

import pytest
from pydantic import ValidationError

from fiware_actuators_setup.models import Command, Device, IoTService


def test_create_valid_Service():
    """Test that created service contains de same apikey and entity_type as device"""

    cmd = Command(name="on", type="command")
    device = Device(
        device_id="dev001",
        entity_name="Actuator:001",
        entity_type="Actuator",
        transport="HTTP",
        protocol="PDI-IoTA-UltraLight",
        apikey="mqtt0001",
        commands=[cmd],
    )

    service = IoTService(
        apikey=device.apikey,
        cbroker="http://orion:1026",
        entity_type=device.entity_type,
        resource="/iot/d",
    )

    assert service.apikey == device.apikey
    assert service.cbroker == "http://orion:1026"
    assert service.entity_type == device.entity_type
    assert service.resource == "/iot/d"


def test_service_missing_required_fields():
    """Test creating a valid Service with minimum attributes"""
    with pytest.raises(ValidationError):
        IoTService(
            apikey="mqtt0001",
            cbroker="http://orion:1026",
            resource="/iot/d",
        )
