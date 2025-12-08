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
