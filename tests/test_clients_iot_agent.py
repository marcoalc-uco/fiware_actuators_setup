"""Unit tests for the IoT Agent Client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from fiware_actuators_setup.clients.iot_agent import IoTAgentClient
from fiware_actuators_setup.exceptions import (
    IoTAgentClientError,
    IoTAgentNotFoundError,
    IoTAgentServerError,
)
from fiware_actuators_setup.models.device import Command, Device
from fiware_actuators_setup.models.service import IoTService

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_requests():
    """Mock the requests module for all HTTP operations."""
    with patch("fiware_actuators_setup.clients.iot_agent.requests") as mock:
        yield mock


@pytest.fixture
def client():
    """Create a test IoTAgentClient instance."""
    return IoTAgentClient(
        base_url="http://iot-agent:4041",
        fiware_service="openiot",
        fiware_servicepath="/",
        request_timeout=5,
    )


@pytest.fixture
def sample_service_group():
    """Create a sample IoTService for testing."""
    return IoTService(
        apikey="test-apikey",
        cbroker="http://orion:1026",
        entity_type="Device",
        resource="/iot/d",
    )


@pytest.fixture
def sample_device():
    """Create a sample Device for testing."""
    return Device(
        device_id="dev1",
        entity_name="urn:ngsi-ld:Device:001",
        entity_type="Device",
        transport="HTTP",
        protocol="PDI-IoTA-UltraLight",
        apikey="test-apikey",
        commands=[Command(name="on", type="command")],
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestClientInitialization:
    """Tests for IoTAgentClient initialization."""

    def test_client_from_settings(self):
        """Test IoTAgentClient.from_settings loads configuration from Settings."""

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


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Tests for IoT Agent health check."""

    def test_check_status_ok(self, client, mock_requests):
        """Test check_status returns True when API is healthy."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        assert client.check_status() is True
        mock_requests.get.assert_called_once_with(
            "http://iot-agent:4041/iot/about", timeout=5
        )

    def test_check_status_fail(self, client, mock_requests):
        """Test check_status returns False when API fails."""
        mock_requests.get.side_effect = ConnectionError("Connection error")
        assert client.check_status() is False


# =============================================================================
# Service Group CRUD Tests
# =============================================================================


class TestCreateServiceGroup:
    """Tests for create_service_group method."""

    def test_create_service_group_success(
        self, client, mock_requests, sample_service_group
    ):
        """Test create_service_group sends correct POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        client.create_service_group(sample_service_group)

        mock_requests.post.assert_called_once()
        args, kwargs = mock_requests.post.call_args

        assert args[0] == "http://iot-agent:4041/iot/services"
        assert kwargs["headers"] == {
            "fiware-service": "openiot",
            "fiware-servicepath": "/",
            "Content-Type": "application/json",
        }
        assert kwargs["json"]["services"][0]["apikey"] == "test-apikey"

    def test_create_service_group_raises_client_error_on_400(
        self, client, mock_requests, sample_service_group
    ):
        """Test create_service_group raises IoTAgentClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentClientError) as exc_info:
            client.create_service_group(sample_service_group)

        assert exc_info.value.status_code == 400

    def test_create_service_group_raises_client_error_on_409(
        self, client, mock_requests, sample_service_group
    ):
        """Test create_service_group raises IoTAgentClientError on HTTP 409 Conflict."""
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.text = '{"error": "Conflict - Service group already exists"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentClientError) as exc_info:
            client.create_service_group(sample_service_group)

        assert exc_info.value.status_code == 409

    def test_create_service_group_raises_server_error_on_500(
        self, client, mock_requests, sample_service_group
    ):
        """Test create_service_group raises IoTAgentServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "Internal Server Error"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentServerError) as exc_info:
            client.create_service_group(sample_service_group)

        assert exc_info.value.status_code == 500

    def test_create_service_group_raises_server_error_on_503(
        self, client, mock_requests, sample_service_group
    ):
        """Test create_service_group raises IoTAgentServerError on HTTP 503."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = '{"error": "Service Unavailable"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentServerError) as exc_info:
            client.create_service_group(sample_service_group)

        assert exc_info.value.status_code == 503


class TestGetServiceGroups:
    """Tests for get_service_groups method."""

    def test_get_service_groups_success(self, client, mock_requests):
        """Test get_service_groups returns list of service groups."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "services": [
                {
                    "apikey": "test-apikey",
                    "cbroker": "http://orion:1026",
                    "entity_type": "Device",
                    "resource": "/iot/d",
                }
            ]
        }
        mock_requests.get.return_value = mock_response

        result = client.get_service_groups()

        assert len(result) == 1
        assert result[0]["apikey"] == "test-apikey"
        mock_requests.get.assert_called_once()

    def test_get_service_groups_returns_empty_list(self, client, mock_requests):
        """Test get_service_groups returns empty list when no services exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"services": []}
        mock_requests.get.return_value = mock_response

        result = client.get_service_groups()

        assert result == []

    def test_get_service_groups_raises_server_error_on_500(self, client, mock_requests):
        """Test get_service_groups raises IoTAgentServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "Internal Server Error"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(IoTAgentServerError) as exc_info:
            client.get_service_groups()

        assert exc_info.value.status_code == 500


class TestUpdateServiceGroup:
    """Tests for update_service_group method."""

    def test_update_service_group_success(self, client, mock_requests):
        """Test update_service_group sends correct PUT request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.put.return_value = mock_response

        client.update_service_group(
            resource="/iot/d",
            apikey="test-apikey",
            updates={"entity_type": "UpdatedDevice"},
        )

        mock_requests.put.assert_called_once()
        args, kwargs = mock_requests.put.call_args
        assert "resource=%2Fiot%2Fd" in args[0] or "resource=/iot/d" in args[0]
        assert "apikey=test-apikey" in args[0]

    def test_update_service_group_raises_not_found_on_404(self, client, mock_requests):
        """Test update_service_group raises IoTAgentNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Service group not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.put.return_value = mock_response

        with pytest.raises(IoTAgentNotFoundError) as exc_info:
            client.update_service_group(
                resource="/iot/d",
                apikey="nonexistent-key",
                updates={"entity_type": "Device"},
            )

        assert exc_info.value.status_code == 404

    def test_update_service_group_raises_client_error_on_400(
        self, client, mock_requests
    ):
        """Test update_service_group raises IoTAgentClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.put.return_value = mock_response

        with pytest.raises(IoTAgentClientError) as exc_info:
            client.update_service_group(
                resource="/iot/d",
                apikey="test-apikey",
                updates={"invalid_field": "value"},
            )

        assert exc_info.value.status_code == 400


class TestDeleteServiceGroup:
    """Tests for delete_service_group method."""

    def test_delete_service_group_success(self, client, mock_requests):
        """Test delete_service_group sends correct DELETE request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response

        client.delete_service_group(resource="/iot/d", apikey="test-apikey")

        mock_requests.delete.assert_called_once()
        args, _ = mock_requests.delete.call_args
        assert "resource=%2Fiot%2Fd" in args[0] or "resource=/iot/d" in args[0]
        assert "apikey=test-apikey" in args[0]

    def test_delete_service_group_raises_not_found_on_404(self, client, mock_requests):
        """Test delete_service_group raises IoTAgentNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Service group not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(IoTAgentNotFoundError) as exc_info:
            client.delete_service_group(resource="/iot/d", apikey="nonexistent-key")

        assert exc_info.value.status_code == 404


# =============================================================================
# Device CRUD Tests
# =============================================================================


class TestCreateDevice:
    """Tests for create_device method."""

    def test_create_device_success(self, client, mock_requests, sample_device):
        """Test create_device sends correct POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        client.create_device(sample_device)

        mock_requests.post.assert_called_once()
        args, kwargs = mock_requests.post.call_args
        assert args[0] == "http://iot-agent:4041/iot/devices"
        assert kwargs["json"]["devices"][0]["device_id"] == "dev1"

    def test_create_device_raises_client_error_on_400(
        self, client, mock_requests, sample_device
    ):
        """Test create_device raises IoTAgentClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request - Invalid device"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentClientError) as exc_info:
            client.create_device(sample_device)

        assert exc_info.value.status_code == 400

    def test_create_device_raises_client_error_on_422(
        self, client, mock_requests, sample_device
    ):
        """Test create_device raises IoTAgentClientError on HTTP 422."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = '{"error": "Unprocessable Entity"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentClientError) as exc_info:
            client.create_device(sample_device)

        assert exc_info.value.status_code == 422

    def test_create_device_raises_server_error_on_500(
        self, client, mock_requests, sample_device
    ):
        """Test create_device raises IoTAgentServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "Internal Server Error"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(IoTAgentServerError) as exc_info:
            client.create_device(sample_device)

        assert exc_info.value.status_code == 500


class TestGetDevice:
    """Tests for get_device method."""

    def test_get_device_success(self, client, mock_requests):
        """Test get_device returns device data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "device_id": "dev1",
            "entity_name": "urn:ngsi-ld:Device:001",
            "entity_type": "Device",
            "transport": "HTTP",
            "protocol": "PDI-IoTA-UltraLight",
        }
        mock_requests.get.return_value = mock_response

        result = client.get_device("dev1")

        assert result["device_id"] == "dev1"
        mock_requests.get.assert_called_once()
        args, _ = mock_requests.get.call_args
        assert "dev1" in args[0]

    def test_get_device_raises_not_found_on_404(self, client, mock_requests):
        """Test get_device raises IoTAgentNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Device not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(IoTAgentNotFoundError) as exc_info:
            client.get_device("nonexistent-device")

        assert exc_info.value.status_code == 404


class TestListDevices:
    """Tests for list_devices method."""

    def test_list_devices_success(self, client, mock_requests):
        """Test list_devices returns list of devices."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "devices": [
                {"device_id": "dev1", "entity_name": "urn:ngsi-ld:Device:001"},
                {"device_id": "dev2", "entity_name": "urn:ngsi-ld:Device:002"},
            ]
        }
        mock_requests.get.return_value = mock_response

        result = client.list_devices()

        assert len(result) == 2
        assert result[0]["device_id"] == "dev1"

    def test_list_devices_returns_empty_list(self, client, mock_requests):
        """Test list_devices returns empty list when no devices exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"devices": []}
        mock_requests.get.return_value = mock_response

        result = client.list_devices()

        assert result == []


class TestUpdateDevice:
    """Tests for update_device method."""

    def test_update_device_success(self, client, mock_requests):
        """Test update_device sends correct PUT request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.put.return_value = mock_response

        client.update_device("dev1", updates={"entity_type": "UpdatedDevice"})

        mock_requests.put.assert_called_once()
        args, _ = mock_requests.put.call_args
        assert "dev1" in args[0]

    def test_update_device_raises_not_found_on_404(self, client, mock_requests):
        """Test update_device raises IoTAgentNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Device not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.put.return_value = mock_response

        with pytest.raises(IoTAgentNotFoundError) as exc_info:
            client.update_device(
                "nonexistent-device", updates={"entity_type": "Device"}
            )

        assert exc_info.value.status_code == 404

    def test_update_device_raises_client_error_on_400(self, client, mock_requests):
        """Test update_device raises IoTAgentClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.put.return_value = mock_response

        with pytest.raises(IoTAgentClientError) as exc_info:
            client.update_device("dev1", updates={"invalid_field": "value"})

        assert exc_info.value.status_code == 400


class TestDeleteDevice:
    """Tests for delete_device method."""

    def test_delete_device_success(self, client, mock_requests):
        """Test delete_device sends correct DELETE request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response

        client.delete_device("dev1")

        mock_requests.delete.assert_called_once()
        args, _ = mock_requests.delete.call_args
        assert "dev1" in args[0]

    def test_delete_device_raises_not_found_on_404(self, client, mock_requests):
        """Test delete_device raises IoTAgentNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Device not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(IoTAgentNotFoundError) as exc_info:
            client.delete_device("nonexistent-device")

        assert exc_info.value.status_code == 404
