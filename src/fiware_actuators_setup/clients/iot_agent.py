"""Client for interacting with the FIWARE IoT Agent (JSON/UltraLight)."""

import logging
from typing import Any
from urllib.parse import urlencode

import requests
from requests.exceptions import HTTPError

from fiware_actuators_setup.config import Settings
from fiware_actuators_setup.exceptions import (
    IoTAgentClientError,
    IoTAgentNotFoundError,
    IoTAgentServerError,
)
from fiware_actuators_setup.models import Device, IoTService

logger = logging.getLogger(__name__)


class IoTAgentClient:
    """Client for interacting with the FIWARE IoT Agent (JSON/UltraLight).

    Provides CRUD operations for Service Groups and Devices.
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
    def from_settings(cls, settings: Settings) -> "IoTAgentClient":
        """Create a client instance using a Settings object.

        Parameters
        ----------
        settings : Settings
            The configuration settings loaded from environment variables.

        Returns
        -------
        IoTAgentClient
            A configured IoTAgentClient instance.
        """
        return cls(
            base_url=settings.iota_base_url,
            fiware_service=settings.fiware_service,
            fiware_servicepath=settings.fiware_servicepath,
            request_timeout=settings.request_timeout,
        )

    # =========================================================================
    # Health Check
    # =========================================================================

    def check_status(self) -> bool:
        """Check whether the IoT Agent is reachable.

        Returns
        -------
        bool
            True if the IoT Agent responds with HTTP 200, False otherwise.
        """
        try:
            response = requests.get(
                f"{self._base_url}/iot/about",
                timeout=self._request_timeout,
            )
            return response.status_code == 200
        except ConnectionError as e:
            logger.error(f"Error checking IoT Agent status: {e}")
            return False

    # =========================================================================
    # Error Handling
    # =========================================================================

    def _handle_http_error(
        self, error: HTTPError, operation: str, resource: str | None = None
    ) -> None:
        """Convert HTTPError to appropriate custom exception.

        Parameters
        ----------
        error : HTTPError
            The HTTP error from requests library.
        operation : str
            Description of the operation that failed.
        resource : str | None
            Resource identifier for 404 errors.

        Raises
        ------
        IoTAgentNotFoundError
            For HTTP 404 errors.
        IoTAgentClientError
            For HTTP 4xx client errors.
        IoTAgentServerError
            For HTTP 5xx server errors.
        """
        response = error.response
        status_code = response.status_code
        response_body = response.text

        if status_code == 404:
            logger.error(f"Resource not found during {operation}: {resource}")
            raise IoTAgentNotFoundError(
                resource=resource or operation,
                response_body=response_body,
            ) from error
        elif 400 <= status_code < 500:
            logger.error(f"Client error during {operation}: {status_code}")
            raise IoTAgentClientError(
                status_code=status_code,
                message=f"{operation} failed",
                response_body=response_body,
            ) from error
        elif 500 <= status_code < 600:
            logger.error(f"Server error during {operation}: {status_code}")
            raise IoTAgentServerError(
                status_code=status_code,
                message=f"{operation} failed",
                response_body=response_body,
            ) from error
        else:
            raise error

    # =========================================================================
    # Service Group CRUD Operations
    # =========================================================================

    def create_service_group(self, service_group: IoTService) -> None:
        """Create a service group in the IoT Agent.

        Parameters
        ----------
        service_group : IoTService
            The service group model to create.
        """
        url = f"{self._base_url}/iot/services"
        payload = {"services": [service_group.model_dump(exclude_none=True)]}

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Service group created successfully: {service_group.apikey}")
        except HTTPError as e:
            self._handle_http_error(e, "create_service_group")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create service group: {e}")
            raise

    def get_service_groups(self) -> list[dict[str, Any]]:
        """Retrieve all service groups from the IoT Agent.

        Returns
        -------
        list[dict[str, Any]]
            List of service group dictionaries.
        """
        url = f"{self._base_url}/iot/services"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json().get("services", [])
            return result
        except HTTPError as e:
            self._handle_http_error(e, "get_service_groups")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get service groups: {e}")
            raise

    def update_service_group(
        self, resource: str, apikey: str, updates: dict[str, Any]
    ) -> None:
        """Update a service group in the IoT Agent.

        Parameters
        ----------
        resource : str
            The resource path of the service group (e.g., '/iot/d').
        apikey : str
            The API key of the service group.
        updates : dict[str, Any]
            Dictionary of fields to update.
        """
        query_params = urlencode({"resource": resource, "apikey": apikey})
        url = f"{self._base_url}/iot/services?{query_params}"

        try:
            response = requests.put(
                url, headers=self._headers, json=updates, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Service group updated successfully: {apikey}")
        except HTTPError as e:
            self._handle_http_error(
                e, "update_service_group", resource=f"{resource}:{apikey}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update service group: {e}")
            raise

    def delete_service_group(self, resource: str, apikey: str) -> None:
        """Delete a service group from the IoT Agent.

        Parameters
        ----------
        resource : str
            The resource path of the service group (e.g., '/iot/d').
        apikey : str
            The API key of the service group.
        """
        query_params = urlencode({"resource": resource, "apikey": apikey})
        url = f"{self._base_url}/iot/services?{query_params}"

        try:
            response = requests.delete(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Service group deleted successfully: {apikey}")
        except HTTPError as e:
            self._handle_http_error(
                e, "delete_service_group", resource=f"{resource}:{apikey}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete service group: {e}")
            raise

    # =========================================================================
    # Device CRUD Operations
    # =========================================================================

    def create_device(self, device: Device) -> None:
        """Create a device in the IoT Agent.

        Parameters
        ----------
        device : Device
            The device model to provision.
        """
        url = f"{self._base_url}/iot/devices"
        payload = {"devices": [device.model_dump(exclude_none=True)]}

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Device created successfully: {device.device_id}")
        except HTTPError as e:
            self._handle_http_error(e, "create_device")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create device: {e}")
            raise

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Retrieve a specific device from the IoT Agent.

        Parameters
        ----------
        device_id : str
            The unique identifier of the device.

        Returns
        -------
        dict[str, Any]
            Device data dictionary.

        Raises
        ------
        IoTAgentNotFoundError
            If the device is not found.
        """
        url = f"{self._base_url}/iot/devices/{device_id}"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except HTTPError as e:
            self._handle_http_error(e, "get_device", resource=device_id)
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get device: {e}")
            raise

    def list_devices(self) -> list[dict[str, Any]]:
        """Retrieve all devices from the IoT Agent.

        Returns
        -------
        list[dict[str, Any]]
            List of device dictionaries.
        """
        url = f"{self._base_url}/iot/devices"

        try:
            response = requests.get(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json().get("devices", [])
            return result
        except HTTPError as e:
            self._handle_http_error(e, "list_devices")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list devices: {e}")
            raise

    def update_device(self, device_id: str, updates: dict[str, Any]) -> None:
        """Update a device in the IoT Agent.

        Parameters
        ----------
        device_id : str
            The unique identifier of the device.
        updates : dict[str, Any]
            Dictionary of fields to update.
        """
        url = f"{self._base_url}/iot/devices/{device_id}"

        try:
            response = requests.put(
                url, headers=self._headers, json=updates, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Device updated successfully: {device_id}")
        except HTTPError as e:
            self._handle_http_error(e, "update_device", resource=device_id)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update device: {e}")
            raise

    def delete_device(self, device_id: str) -> None:
        """Delete a device from the IoT Agent.

        Parameters
        ----------
        device_id : str
            The unique identifier of the device.
        """
        url = f"{self._base_url}/iot/devices/{device_id}"

        try:
            response = requests.delete(
                url, headers=self._headers, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Device deleted successfully: {device_id}")
        except HTTPError as e:
            self._handle_http_error(e, "delete_device", resource=device_id)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete device: {e}")
            raise
