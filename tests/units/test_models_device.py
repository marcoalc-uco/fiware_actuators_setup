"""Unit tests for the Device model.

These tests validate the creation of Device with required attributes.
Device should use the same apikey and entity_type as its parent IoTService.
"""

import pytest
from pydantic import ValidationError

from fiware_actuators_setup.models import Command, Device, IoTService


class TestDeviceCreation:
    """Tests for Device model creation."""

    def test_create_valid_device(self):
        """Test creating a valid Device with all required fields."""
        cmd = Command(name="switch", type="command")

        device = Device(
            device_id="dev001",
            entity_name="urn:ngsi-ld:Actuator:001",
            entity_type="Actuator",
            transport="MQTT",
            protocol="PDI-IoTA-UltraLight",
            apikey="my-api-key",
            commands=[cmd],
        )

        assert device.device_id == "dev001"
        assert device.entity_type == "Actuator"
        assert device.apikey == "my-api-key"
        assert len(device.commands) == 1

    def test_device_requires_at_least_one_command(self):
        """Test that Device requires at least one command."""
        with pytest.raises(ValueError, match="at least one command"):
            Device(
                device_id="dev001",
                entity_name="urn:ngsi-ld:Actuator:001",
                entity_type="Actuator",
                transport="MQTT",
                protocol="PDI-IoTA-UltraLight",
                apikey="my-api-key",
                commands=[],
            )

    def test_device_missing_apikey_raises_error(self):
        """Test that Device requires apikey field."""
        cmd = Command(name="switch", type="command")

        with pytest.raises(ValidationError):
            Device(
                device_id="dev001",
                entity_name="urn:ngsi-ld:Actuator:001",
                entity_type="Actuator",
                transport="MQTT",
                protocol="PDI-IoTA-UltraLight",
                # apikey is missing
                commands=[cmd],
            )

    def test_device_missing_entity_type_raises_error(self):
        """Test that Device requires entity type field."""
        cmd = Command(name="switch", type="command")

        with pytest.raises(ValidationError):
            Device(
                device_id="dev001",
                entity_name="urn:ngsi-ld:Actuator:001",
                # entity_type is missing
                transport="MQTT",
                protocol="PDI-IoTA-UltraLight",
                apikey="my-api-key",
                commands=[cmd],
            )


class TestDeviceServiceRelationship:
    """Tests for Device and IoTService relationship.

    In FIWARE, IoTService is created FIRST and defines the apikey.
    Devices inherit the apikey to link to their service group.
    """

    def test_device_inherits_apikey_from_service(self):
        """Test that Device uses the same apikey as its parent IoTService."""
        # 1. Create Service FIRST
        service = IoTService(
            apikey="shared-api-key",
            cbroker="http://orion:1026",
            entity_type="Actuator",
            resource="/iot/d",
        )

        # 2. Create Device that inherits from Service
        cmd = Command(name="switch", type="command")
        device = Device(
            device_id="dev001",
            entity_name="urn:ngsi-ld:Actuator:001",
            entity_type=service.entity_type,  # Inherit from service
            transport="MQTT",
            protocol="PDI-IoTA-UltraLight",
            apikey=service.apikey,  # Inherit from service
            commands=[cmd],
        )

        # Verify they share the same values
        assert device.apikey == service.apikey
        assert device.entity_type == service.entity_type

    def test_multiple_devices_share_same_service(self):
        """Test that multiple devices can share the same service apikey."""
        # 1. Create Service FIRST
        service = IoTService(
            apikey="shared-api-key",
            cbroker="http://orion:1026",
            entity_type="Actuator",
            resource="/iot/d",
        )

        # 2. Create multiple Devices
        cmd = Command(name="switch", type="command")
        device1 = Device(
            device_id="dev001",
            entity_name="urn:ngsi-ld:Actuator:001",
            entity_type=service.entity_type,
            transport="MQTT",
            protocol="PDI-IoTA-UltraLight",
            apikey=service.apikey,
            commands=[cmd],
        )
        device2 = Device(
            device_id="dev002",
            entity_name="urn:ngsi-ld:Actuator:002",
            entity_type=service.entity_type,
            transport="MQTT",
            protocol="PDI-IoTA-UltraLight",
            apikey=service.apikey,
            commands=[cmd],
        )

        # All share the same service apikey
        assert device1.apikey == service.apikey
        assert device2.apikey == service.apikey
        assert device1.apikey == device2.apikey
