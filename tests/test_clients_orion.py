"""Unit tests for the Orion Context Broker Client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from fiware_actuators_setup.clients import OrionClient
from fiware_actuators_setup.exceptions import (
    OrionClientError,
    OrionNotFoundError,
    OrionServerError,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_requests():
    """Mock the requests module for all HTTP operations."""
    with patch("fiware_actuators_setup.clients.orion.requests") as mock:
        yield mock


@pytest.fixture
def client():
    """Create a test OrionClient instance."""
    return OrionClient(
        base_url="http://orion:1026",
        fiware_service="openiot",
        fiware_servicepath="/",
        request_timeout=5,
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestClientInitialization:
    """Tests for OrionClient initialization."""

    def test_client_initialization(self):
        """Test OrionClient is properly initialized with provided parameters."""
        client = OrionClient(
            base_url="http://orion:1026",
            fiware_service="openiot",
            fiware_servicepath="/",
            request_timeout=5,
        )

        assert client._base_url == "http://orion:1026"
        assert client._service == "openiot"
        assert client._servicepath == "/"
        assert client._request_timeout == 5

    def test_client_strips_trailing_slash_from_base_url(self):
        """Test OrionClient strips trailing slash from base URL."""
        client = OrionClient(
            base_url="http://orion:1026/",
            fiware_service="openiot",
            fiware_servicepath="/",
            request_timeout=5,
        )

        assert client._base_url == "http://orion:1026"

    def test_client_from_settings(self):
        """Test OrionClient.from_settings loads configuration from Settings."""

        class FakeSettings:
            orion_base_url = "http://orion:1026"
            fiware_service = "openiot"
            fiware_servicepath = "/"
            request_timeout = 5

        client = OrionClient.from_settings(FakeSettings)

        assert client._base_url == "http://orion:1026"
        assert client._service == "openiot"
        assert client._servicepath == "/"
        assert client._request_timeout == 5


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Tests for Orion Context Broker health check."""

    def test_check_status_ok(self, client, mock_requests):
        """Test check_status returns True when API is healthy."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        assert client.check_status() is True
        mock_requests.get.assert_called_once_with(
            "http://orion:1026/version", timeout=5
        )

    def test_check_status_fail(self, client, mock_requests):
        """Test check_status returns False when API fails."""
        mock_requests.get.side_effect = ConnectionError("Connection error")
        assert client.check_status() is False

    def test_check_status_returns_false_on_non_200(self, client, mock_requests):
        """Test check_status returns False when API returns non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_requests.get.return_value = mock_response

        assert client.check_status() is False


# =============================================================================
# Get Entity Tests
# =============================================================================


class TestGetEntity:
    """Tests for get_entity method."""

    def test_get_entity_success(self, client, mock_requests):
        """Test get_entity returns entity data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "urn:ngsi-ld:Device:001",
            "type": "Device",
            "status": {"type": "Text", "value": "OK"},
        }
        mock_requests.get.return_value = mock_response

        result = client.get_entity("urn:ngsi-ld:Device:001")

        assert result["id"] == "urn:ngsi-ld:Device:001"
        assert result["type"] == "Device"
        mock_requests.get.assert_called_once()
        args, kwargs = mock_requests.get.call_args
        assert "urn:ngsi-ld:Device:001" in args[0]

    def test_get_entity_raises_not_found_on_404(self, client, mock_requests):
        """Test get_entity raises OrionNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "NotFound", "description": "Entity not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionNotFoundError) as exc_info:
            client.get_entity("nonexistent-entity")

        assert exc_info.value.status_code == 404
        assert exc_info.value.entity_id == "nonexistent-entity"

    def test_get_entity_raises_client_error_on_400(self, client, mock_requests):
        """Test get_entity raises OrionClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "BadRequest"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionClientError) as exc_info:
            client.get_entity("invalid-entity-id")

        assert exc_info.value.status_code == 400

    def test_get_entity_raises_server_error_on_500(self, client, mock_requests):
        """Test get_entity raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.get_entity("urn:ngsi-ld:Device:001")

        assert exc_info.value.status_code == 500

    def test_get_entity_raises_server_error_on_503(self, client, mock_requests):
        """Test get_entity raises OrionServerError on HTTP 503."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = '{"error": "ServiceUnavailable"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.get_entity("urn:ngsi-ld:Device:001")

        assert exc_info.value.status_code == 503


# =============================================================================
# Delete Entity Tests
# =============================================================================


class TestDeleteEntity:
    """Tests for delete_entity method."""

    def test_delete_entity_success(self, client, mock_requests):
        """Test delete_entity sends correct DELETE request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response

        client.delete_entity("urn:ngsi-ld:Device:001")

        mock_requests.delete.assert_called_once()
        args, _ = mock_requests.delete.call_args
        assert "urn:ngsi-ld:Device:001" in args[0]

    def test_delete_entity_raises_not_found_on_404(self, client, mock_requests):
        """Test delete_entity raises OrionNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "NotFound", "description": "Entity not found"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(OrionNotFoundError) as exc_info:
            client.delete_entity("nonexistent-entity")

        assert exc_info.value.status_code == 404
        assert exc_info.value.entity_id == "nonexistent-entity"

    def test_delete_entity_raises_client_error_on_400(self, client, mock_requests):
        """Test delete_entity raises OrionClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "BadRequest"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(OrionClientError) as exc_info:
            client.delete_entity("invalid-entity-id")

        assert exc_info.value.status_code == 400

    def test_delete_entity_raises_server_error_on_500(self, client, mock_requests):
        """Test delete_entity raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.delete_entity("urn:ngsi-ld:Device:001")

        assert exc_info.value.status_code == 500
