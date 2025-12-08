"""Unit tests for the IoTService model.

These tests validate the creation of IoTService with required attributes.
IoTService is created FIRST and defines the apikey and entity_type
that devices will inherit.
"""

import pytest
from pydantic import ValidationError

from fiware_actuators_setup.models import IoTService


class TestIoTServiceCreation:
    """Tests for IoTService model creation."""

    def test_create_valid_service(self):
        """Test creating a valid IoTService with all required fields."""
        service = IoTService(
            apikey="my-api-key",
            cbroker="http://orion:1026",
            entity_type="Actuator",
            resource="/iot/d",
        )

        assert service.apikey == "my-api-key"
        assert service.cbroker == "http://orion:1026"
        assert service.entity_type == "Actuator"
        assert service.resource == "/iot/d"

    def test_service_missing_entity_type_raises_error(self):
        """Test that IoTService requires entity_type field."""
        with pytest.raises(ValidationError):
            IoTService(
                apikey="my-api-key",
                cbroker="http://orion:1026",
                resource="/iot/d",
                # entity_type is missing
            )

    def test_service_missing_apikey_raises_error(self):
        """Test that IoTService requires apikey field."""
        with pytest.raises(ValidationError):
            IoTService(
                cbroker="http://orion:1026",
                entity_type="Actuator",
                resource="/iot/d",
                # apikey is missing
            )

    def test_service_empty_apikey_raises_error(self):
        """Test that IoTService rejects empty apikey."""
        with pytest.raises(ValidationError):
            IoTService(
                apikey="",
                cbroker="http://orion:1026",
                entity_type="Actuator",
                resource="/iot/d",
            )
