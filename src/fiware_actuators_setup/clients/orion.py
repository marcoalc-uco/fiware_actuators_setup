"""Client for interacting with the FIWARE Orion Context Broker."""

import logging
from typing import Any

import requests
from requests.exceptions import HTTPError

from fiware_actuators_setup.config import Settings
from fiware_actuators_setup.exceptions import (
    OrionClientError,
    OrionNotFoundError,
    OrionServerError,
)
from fiware_actuators_setup.models import Subscription

logger = logging.getLogger(__name__)


class OrionClient:
    """Client for interacting with the FIWARE Orion Context Broker.

    Provides read and delete operations for entities. Entity creation
    and updates are managed through the IoT Agent.
    """

    def __init__(
        self,
        base_url: str,
        fiware_service: str,
        fiware_servicepath: str,
        request_timeout: int,
    ):
        self._base_url = base_url.rstrip("/")
        self._service = fiware_service
        self._servicepath = fiware_servicepath
        self._request_timeout = request_timeout
        self._headers = {
            "fiware-service": self._service,
            "fiware-servicepath": self._servicepath,
            "Content-Type": "application/json",
        }

    @classmethod
    def from_settings(cls, settings: Settings) -> "OrionClient":
        """Create a client instance using a Settings object.

        Parameters
        ----------
        settings : Settings
            The configuration settings loaded from environment variables.

        Returns
        -------
        OrionClient
            A configured OrionClient instance.
        """
        return cls(
            base_url=settings.orion_base_url,
            fiware_service=settings.fiware_service,
            fiware_servicepath=settings.fiware_servicepath,
            request_timeout=settings.request_timeout,
        )

    # =========================================================================
    # Health Check
    # =========================================================================

    def check_status(self) -> bool:
        """Check whether the Orion Context Broker is reachable.

        Returns
        -------
        bool
            True if Orion responds with HTTP 200, False otherwise.
        """
        try:
            response = requests.get(
                f"{self._base_url}/version",
                timeout=self._request_timeout,
            )
            return response.status_code == 200
        except ConnectionError as e:
            logger.error(f"Error checking Orion status: {e}")
            return False

    # =========================================================================
    # Error Handling
    # =========================================================================

    def _handle_http_error(
        self, error: HTTPError, operation: str, entity_id: str | None = None
    ) -> None:
        """Convert HTTPError to appropriate custom exception.

        Parameters
        ----------
        error : HTTPError
            The HTTP error from requests library.
        operation : str
            Description of the operation that failed.
        entity_id : str | None
            Entity identifier for 404 errors.

        Raises
        ------
        OrionNotFoundError
            For HTTP 404 errors.
        OrionClientError
            For HTTP 4xx client errors.
        OrionServerError
            For HTTP 5xx server errors.
        """
        response = error.response
        status_code = response.status_code
        response_body = response.text

        if status_code == 404:
            logger.error(f"Entity not found during {operation}: {entity_id}")
            raise OrionNotFoundError(
                entity_id=entity_id or operation,
                response_body=response_body,
            ) from error
        elif 400 <= status_code < 500:
            logger.error(f"Client error during {operation}: {status_code}")
            raise OrionClientError(
                status_code=status_code,
                message=f"{operation} failed",
                response_body=response_body,
            ) from error
        elif 500 <= status_code < 600:
            logger.error(f"Server error during {operation}: {status_code}")
            raise OrionServerError(
                status_code=status_code,
                message=f"{operation} failed",
                response_body=response_body,
            ) from error
        else:
            raise error

    # =========================================================================
    # Entity Operations
    # =========================================================================

    def get_entity(self, entity_id: str) -> dict[str, Any]:
        """Retrieve a specific entity from Orion.

        Parameters
        ----------
        entity_id : str
            The unique identifier of the entity.

        Returns
        -------
        dict[str, Any]
            Entity data dictionary.

        Raises
        ------
        OrionNotFoundError
            If the entity is not found.
        """
        url = f"{self._base_url}/v2/entities/{entity_id}"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except HTTPError as e:
            self._handle_http_error(e, "get_entity", entity_id=entity_id)
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get entity: {e}")
            raise

    def list_entities(self) -> list[dict[str, Any]]:
        """Retrieve all entities from Orion.

        Returns
        -------
        list[dict[str, Any]]
            List of entity dictionaries.
        """
        url = f"{self._base_url}/v2/entities"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result
        except HTTPError as e:
            self._handle_http_error(e, "list_entities")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list entities: {e}")
            raise

    def delete_entity(self, entity_id: str) -> None:
        """Delete an entity from Orion.

        Parameters
        ----------
        entity_id : str
            The unique identifier of the entity.
        """
        url = f"{self._base_url}/v2/entities/{entity_id}"

        try:
            response = requests.delete(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Entity deleted successfully: {entity_id}")
        except HTTPError as e:
            self._handle_http_error(e, "delete_entity", entity_id=entity_id)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete entity: {e}")
            raise

    # =========================================================================
    # Subscription CRUD Operations
    # =========================================================================

    def create_subscription(self, subscription: Subscription) -> str:
        """Create a subscription in Orion.

        Parameters
        ----------
        subscription : Subscription
            The subscription model to create.

        Returns
        -------
        str
            The ID of the created subscription.
        """

        url = f"{self._base_url}/v2/subscriptions"
        payload = subscription.model_dump(exclude_none=True)

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=self._request_timeout
            )
            response.raise_for_status()
            location = response.headers.get("Location", "")
            subscription_id = location.split("/")[-1]
            logger.info(f"Subscription created successfully: {subscription_id}")
            return subscription_id
        except HTTPError as e:
            self._handle_http_error(e, "create_subscription")
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create subscription: {e}")
            raise

    def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Retrieve a specific subscription from Orion.

        Parameters
        ----------
        subscription_id : str
            The unique identifier of the subscription.

        Returns
        -------
        dict[str, Any]
            Subscription data dictionary.

        Raises
        ------
        OrionNotFoundError
            If the subscription is not found.
        """
        url = f"{self._base_url}/v2/subscriptions/{subscription_id}"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except HTTPError as e:
            self._handle_http_error(e, "get_subscription", entity_id=subscription_id)
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get subscription: {e}")
            raise

    def list_subscriptions(self) -> list[dict[str, Any]]:
        """Retrieve all subscriptions from Orion.

        Returns
        -------
        list[dict[str, Any]]
            List of subscription dictionaries.
        """
        url = f"{self._base_url}/v2/subscriptions"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result
        except HTTPError as e:
            self._handle_http_error(e, "list_subscriptions")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list subscriptions: {e}")
            raise

    def update_subscription(
        self, subscription_id: str, updates: dict[str, Any]
    ) -> None:
        """Update a subscription in Orion.

        Parameters
        ----------
        subscription_id : str
            The unique identifier of the subscription.
        updates : dict[str, Any]
            Dictionary of fields to update.
        """
        url = f"{self._base_url}/v2/subscriptions/{subscription_id}"

        try:
            response = requests.patch(
                url, headers=self._headers, json=updates, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Subscription updated successfully: {subscription_id}")
        except HTTPError as e:
            self._handle_http_error(e, "update_subscription", entity_id=subscription_id)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update subscription: {e}")
            raise

    def delete_subscription(self, subscription_id: str) -> None:
        """Delete a subscription from Orion.

        Parameters
        ----------
        subscription_id : str
            The unique identifier of the subscription.
        """
        url = f"{self._base_url}/v2/subscriptions/{subscription_id}"

        try:
            response = requests.delete(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Subscription deleted successfully: {subscription_id}")
        except HTTPError as e:
            self._handle_http_error(e, "delete_subscription", entity_id=subscription_id)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete subscription: {e}")
            raise
