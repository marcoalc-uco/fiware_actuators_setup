"""Integration tests for IoTAgentClient against real IoT Agent.

These tests require FIWARE services running via docker-compose.
Run: docker-compose up -d
Then: pytest -m integration
"""

import uuid

import pytest

from fiware_actuators_setup.clients import IoTAgentClient
from fiware_actuators_setup.exceptions import IoTAgentNotFoundError
from fiware_actuators_setup.models import Command, Device, IoTService

pytestmark = pytest.mark.integration


class TestIoTAgentHealthCheck:
    """Integration tests for IoT Agent health check."""

    def test_check_status_returns_true(self, iot_agent_client: IoTAgentClient):
        """Test check_status returns True when IoT Agent is running."""
        assert iot_agent_client.check_status() is True


class TestIoTAgentServiceGroups:
    """Integration tests for IoT Agent service group operations."""

    def test_service_group_crud_lifecycle(self, iot_agent_client: IoTAgentClient):
        """Test full CRUD lifecycle for service groups."""
        # Generate unique apikey to avoid conflicts
        unique_apikey = f"test_{uuid.uuid4().hex[:8]}"

        service_group = IoTService(
            apikey=unique_apikey,
            cbroker="http://orion:1026",
            entity_type="TestSensor",
            resource="/iot/d",
        )

        # CREATE
        iot_agent_client.create_service_group(service_group)

        try:
            # LIST
            service_groups = iot_agent_client.get_service_groups()
            assert any(sg.get("apikey") == unique_apikey for sg in service_groups)

            # UPDATE
            iot_agent_client.update_service_group(
                resource="/iot/d",
                apikey=unique_apikey,
                updates={"entity_type": "UpdatedSensor"},
            )

        finally:
            # DELETE (cleanup)
            iot_agent_client.delete_service_group(
                resource="/iot/d", apikey=unique_apikey
            )


class TestIoTAgentDevices:
    """Integration tests for IoT Agent device operations."""

    @pytest.fixture
    def service_group_for_device(self, iot_agent_client: IoTAgentClient):
        """Create a service group for device tests."""
        unique_apikey = f"dev_{uuid.uuid4().hex[:8]}"

        service_group = IoTService(
            apikey=unique_apikey,
            cbroker="http://orion:1026",
            entity_type="TestDevice",
            resource="/iot/d",
        )

        iot_agent_client.create_service_group(service_group)

        yield unique_apikey

        try:
            iot_agent_client.delete_service_group(
                resource="/iot/d", apikey=unique_apikey
            )
        except Exception:
            pass

    def test_device_crud_lifecycle(
        self, iot_agent_client: IoTAgentClient, service_group_for_device: str
    ):
        """Test full CRUD lifecycle for devices."""
        device_id = f"test_device_{uuid.uuid4().hex[:8]}"

        device = Device(
            device_id=device_id,
            entity_name=f"urn:ngsi-ld:TestDevice:{device_id}",
            entity_type="TestDevice",
            transport="MQTT",
            protocol="IoTA-UL",
            apikey=service_group_for_device,  # Use the apikey from service group
            commands=[
                Command(name="switch", type="command"),
            ],
        )

        # CREATE
        iot_agent_client.create_device(device)

        try:
            # READ
            retrieved = iot_agent_client.get_device(device_id)
            assert retrieved["device_id"] == device_id

            # LIST
            devices = iot_agent_client.list_devices()
            assert any(d.get("device_id") == device_id for d in devices)

            # UPDATE
            iot_agent_client.update_device(
                device_id, updates={"entity_type": "UpdatedDevice"}
            )

        finally:
            # DELETE (cleanup)
            iot_agent_client.delete_device(device_id)

        # Verify deletion
        with pytest.raises(IoTAgentNotFoundError):
            iot_agent_client.get_device(device_id)
