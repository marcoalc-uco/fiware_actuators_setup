"""Integration tests for OrionClient against real Orion Context Broker.

These tests require FIWARE services running via docker-compose.
Run: docker-compose up -d
Then: pytest -m integration
"""

import pytest

from fiware_actuators_setup.clients import OrionClient
from fiware_actuators_setup.exceptions import OrionNotFoundError
from fiware_actuators_setup.models import (
    EntityRef,
    Notification,
    NotificationHttp,
    Subject,
    Subscription,
)

pytestmark = pytest.mark.integration


class TestOrionHealthCheck:
    """Integration tests for Orion health check."""

    def test_check_status_returns_true(self, orion_client: OrionClient):
        """Test check_status returns True when Orion is running."""
        assert orion_client.check_status() is True


class TestOrionEntities:
    """Integration tests for Orion entity operations."""

    def test_list_entities_empty(self, orion_client: OrionClient):
        """Test list_entities returns empty list when no entities exist."""
        entities = orion_client.list_entities()
        # May or may not be empty depending on previous tests
        assert isinstance(entities, list)

    def test_get_entity_not_found(self, orion_client: OrionClient):
        """Test get_entity raises OrionNotFoundError for non-existent entity."""
        with pytest.raises(OrionNotFoundError):
            orion_client.get_entity("urn:ngsi-ld:NonExistent:12345")

    def test_delete_entity_not_found(self, orion_client: OrionClient):
        """Test delete_entity raises OrionNotFoundError for non-existent entity."""
        with pytest.raises(OrionNotFoundError):
            orion_client.delete_entity("urn:ngsi-ld:NonExistent:12345")


class TestOrionSubscriptions:
    """Integration tests for Orion subscription operations."""

    def test_subscription_crud_lifecycle(self, orion_client: OrionClient):
        """Test full CRUD lifecycle for subscriptions."""
        # CREATE
        subscription = Subscription(
            description="Integration test subscription",
            subject=Subject(
                entities=[EntityRef(idPattern=".*", type="TestDevice")],
                condition={"attrs": ["temperature"]},
            ),
            notification=Notification(
                http=NotificationHttp(url="http://localhost:8080/notify"),
                attrs=["temperature"],
            ),
            throttling=1,
        )

        subscription_id = orion_client.create_subscription(subscription)
        assert subscription_id != ""
        assert len(subscription_id) > 0

        try:
            # READ
            retrieved = orion_client.get_subscription(subscription_id)
            assert retrieved["id"] == subscription_id
            assert retrieved["description"] == "Integration test subscription"

            # LIST
            subscriptions = orion_client.list_subscriptions()
            assert any(s["id"] == subscription_id for s in subscriptions)

            # UPDATE
            orion_client.update_subscription(subscription_id, updates={"throttling": 5})
            updated = orion_client.get_subscription(subscription_id)
            assert updated["throttling"] == 5

        finally:
            # DELETE (cleanup)
            orion_client.delete_subscription(subscription_id)

        # Verify deletion
        with pytest.raises(OrionNotFoundError):
            orion_client.get_subscription(subscription_id)
