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


@pytest.fixture
def sample_subscription():
    """Create a sample Subscription for testing."""
    from fiware_actuators_setup.models import (
        EntityRef,
        Notification,
        NotificationHttp,
        Subject,
        Subscription,
    )

    return Subscription(
        description="Notify QuantumLeap of all changes",
        subject=Subject(
            entities=[EntityRef(idPattern=".*", type="Device")],
            condition={"attrs": ["temperature"]},
        ),
        notification=Notification(
            http=NotificationHttp(url="http://quantumleap:8668/v2/notify"),
            attrs=["temperature"],
        ),
        throttling=1,
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
# List Entities Tests
# =============================================================================


class TestListEntities:
    """Tests for list_entities method."""

    def test_list_entities_success(self, client, mock_requests):
        """Test list_entities returns list of entities."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "urn:ngsi-ld:Device:001", "type": "Device"},
            {"id": "urn:ngsi-ld:Device:002", "type": "Device"},
        ]
        mock_requests.get.return_value = mock_response

        result = client.list_entities()

        assert len(result) == 2
        assert result[0]["id"] == "urn:ngsi-ld:Device:001"
        mock_requests.get.assert_called_once()
        args, _ = mock_requests.get.call_args
        assert args[0] == "http://orion:1026/v2/entities"

    def test_list_entities_returns_empty_list(self, client, mock_requests):
        """Test list_entities returns empty list when no entities exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_requests.get.return_value = mock_response

        result = client.list_entities()

        assert result == []

    def test_list_entities_raises_server_error_on_500(self, client, mock_requests):
        """Test list_entities raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.list_entities()

        assert exc_info.value.status_code == 500


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


# =============================================================================
# Create Subscription Tests
# =============================================================================


class TestCreateSubscription:
    """Tests for create_subscription method."""

    def test_create_subscription_success(
        self, client, mock_requests, sample_subscription
    ):
        """Test create_subscription sends correct POST request and returns ID."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"Location": "/v2/subscriptions/sub123"}
        mock_requests.post.return_value = mock_response

        subscription_id = client.create_subscription(sample_subscription)

        assert subscription_id == "sub123"
        mock_requests.post.assert_called_once()
        args, kwargs = mock_requests.post.call_args
        assert args[0] == "http://orion:1026/v2/subscriptions"

    def test_create_subscription_raises_client_error_on_400(
        self, client, mock_requests, sample_subscription
    ):
        """Test create_subscription raises OrionClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "BadRequest"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(OrionClientError) as exc_info:
            client.create_subscription(sample_subscription)

        assert exc_info.value.status_code == 400

    def test_create_subscription_raises_server_error_on_500(
        self, client, mock_requests, sample_subscription
    ):
        """Test create_subscription raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.post.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.create_subscription(sample_subscription)

        assert exc_info.value.status_code == 500


# =============================================================================
# Get Subscription Tests
# =============================================================================


class TestGetSubscription:
    """Tests for get_subscription method."""

    def test_get_subscription_success(self, client, mock_requests):
        """Test get_subscription returns subscription data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "sub123",
            "description": "Test subscription",
            "status": "active",
        }
        mock_requests.get.return_value = mock_response

        result = client.get_subscription("sub123")

        assert result["id"] == "sub123"
        mock_requests.get.assert_called_once()
        args, _ = mock_requests.get.call_args
        assert "sub123" in args[0]

    def test_get_subscription_raises_not_found_on_404(self, client, mock_requests):
        """Test get_subscription raises OrionNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "NotFound"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionNotFoundError) as exc_info:
            client.get_subscription("nonexistent-sub")

        assert exc_info.value.status_code == 404

    def test_get_subscription_raises_server_error_on_500(self, client, mock_requests):
        """Test get_subscription raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.get_subscription("sub123")

        assert exc_info.value.status_code == 500


# =============================================================================
# List Subscriptions Tests
# =============================================================================


class TestListSubscriptions:
    """Tests for list_subscriptions method."""

    def test_list_subscriptions_success(self, client, mock_requests):
        """Test list_subscriptions returns list of subscriptions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "sub1", "description": "Sub 1"},
            {"id": "sub2", "description": "Sub 2"},
        ]
        mock_requests.get.return_value = mock_response

        result = client.list_subscriptions()

        assert len(result) == 2
        assert result[0]["id"] == "sub1"

    def test_list_subscriptions_returns_empty_list(self, client, mock_requests):
        """Test list_subscriptions returns empty list when no subscriptions exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_requests.get.return_value = mock_response

        result = client.list_subscriptions()

        assert result == []

    def test_list_subscriptions_raises_server_error_on_500(self, client, mock_requests):
        """Test list_subscriptions raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.get.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.list_subscriptions()

        assert exc_info.value.status_code == 500


# =============================================================================
# Update Subscription Tests
# =============================================================================


class TestUpdateSubscription:
    """Tests for update_subscription method."""

    def test_update_subscription_success(self, client, mock_requests):
        """Test update_subscription sends correct PATCH request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.patch.return_value = mock_response

        client.update_subscription("sub123", updates={"throttling": 5})

        mock_requests.patch.assert_called_once()
        args, kwargs = mock_requests.patch.call_args
        assert "sub123" in args[0]
        assert kwargs["json"] == {"throttling": 5}

    def test_update_subscription_raises_not_found_on_404(self, client, mock_requests):
        """Test update_subscription raises OrionNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "NotFound"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.patch.return_value = mock_response

        with pytest.raises(OrionNotFoundError) as exc_info:
            client.update_subscription("nonexistent-sub", updates={"throttling": 5})

        assert exc_info.value.status_code == 404

    def test_update_subscription_raises_client_error_on_400(
        self, client, mock_requests
    ):
        """Test update_subscription raises OrionClientError on HTTP 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "BadRequest"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.patch.return_value = mock_response

        with pytest.raises(OrionClientError) as exc_info:
            client.update_subscription("sub123", updates={"invalid": "field"})

        assert exc_info.value.status_code == 400

    def test_update_subscription_raises_server_error_on_500(
        self, client, mock_requests
    ):
        """Test update_subscription raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.patch.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.update_subscription("sub123", updates={"throttling": 5})

        assert exc_info.value.status_code == 500


# =============================================================================
# Delete Subscription Tests
# =============================================================================


class TestDeleteSubscription:
    """Tests for delete_subscription method."""

    def test_delete_subscription_success(self, client, mock_requests):
        """Test delete_subscription sends correct DELETE request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response

        client.delete_subscription("sub123")

        mock_requests.delete.assert_called_once()
        args, _ = mock_requests.delete.call_args
        assert "sub123" in args[0]

    def test_delete_subscription_raises_not_found_on_404(self, client, mock_requests):
        """Test delete_subscription raises OrionNotFoundError on HTTP 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "NotFound"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(OrionNotFoundError) as exc_info:
            client.delete_subscription("nonexistent-sub")

        assert exc_info.value.status_code == 404

    def test_delete_subscription_raises_server_error_on_500(
        self, client, mock_requests
    ):
        """Test delete_subscription raises OrionServerError on HTTP 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "InternalServerError"}'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_requests.delete.return_value = mock_response

        with pytest.raises(OrionServerError) as exc_info:
            client.delete_subscription("sub123")

        assert exc_info.value.status_code == 500
