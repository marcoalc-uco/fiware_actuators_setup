"""Unit tests for the IoT Agent Client."""

from unittest.mock import MagicMock, patch

import pytest

from fiware_actuators_setup.clients.iot_agent import IoTAgentClient
from fiware_actuators_setup.models.device import Command, Device
from fiware_actuators_setup.models.service import IoTService


@pytest.fixture
def mock_requests():
    with patch("fiware_actuators_setup.clients.iot_agent.requests") as mock:
        yield mock


@pytest.fixture
def client():
    return IoTAgentClient(
        base_url="http://iot-agent:4041",
        fiware_service="openiot",
        fiware_servicepath="/",
        request_timeout=5,
    )


def test_check_status_ok(client, mock_requests):
    """Test check_status returns True when API is healthy."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    assert client.check_status() is True
    mock_requests.get.assert_called_once_with(
        "http://iot-agent:4041/iot/about", timeout=5
    )


def test_check_status_fail(client, mock_requests):
    """Test check_status returns False when API fails."""
    mock_requests.get.side_effect = ConnectionError("Connection error")
    assert client.check_status() is False


def test_create_service_group_success(client, mock_requests):
    """Test create_service_group sends correct POST request."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_requests.post.return_value = mock_response

    service_group = IoTService(
        apikey="test-apikey",
        cbroker="http://orion:1026",
        entity_type="Device",
        resource="/iot/d",
    )

    client.create_service_group(service_group)

    mock_requests.post.assert_called_once()
    args, kwargs = mock_requests.post.call_args

    assert args[0] == "http://iot-agent:4041/iot/services"
    assert kwargs["headers"] == {
        "fiware-service": "openiot",
        "fiware-servicepath": "/",
        "Content-Type": "application/json",
    }
    assert kwargs["json"]["services"][0]["apikey"] == "test-apikey"


def test_provision_device_success(client, mock_requests):
    """Test provision_device sends correct POST request."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_requests.post.return_value = mock_response

    device = Device(
        device_id="dev1",
        entity_name="urn:ngsi-ld:Device:001",
        entity_type="Device",
        transport="HTTP",
        protocol="PDI-IoTA-UltraLight",
        apikey="test-apikey",
        commands=[Command(name="on", type="command")],
    )

    client.provision_device(device)

    mock_requests.post.assert_called_once()
    args, kwargs = mock_requests.post.call_args
    assert args[0] == "http://iot-agent:4041/iot/devices"
    assert kwargs["headers"] == {
        "fiware-service": "openiot",
        "fiware-servicepath": "/",
        "Content-Type": "application/json",
    }
    assert kwargs["json"]["devices"][0]["device_id"] == "dev1"


def test_client_from_settings():
    """Test IoTAgentClient.from_settings loads configuration from Settings."""

    # mock Settings instance
    class FakeSettings:
        iota_base_url = "http://iot-agent:4041"
        fiware_service = "openiot"
        fiware_servicepath = "/"
        request_timeout = 5

    client = IoTAgentClient.from_settings(FakeSettings)

    assert client._base_url == "http://iot-agent:4041"
    assert client._service == "openiot"
    assert client._servicepath == "/"
    assert client._request_timeout == 5
