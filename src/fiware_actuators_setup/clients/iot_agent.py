import logging

import requests

from fiware_actuators_setup.models.device import Device
from fiware_actuators_setup.models.service import IoTService

logger = logging.getLogger(__name__)


class IoTAgentClient:
    """Client for interacting with the FIWARE IoT Agent (JSON/UltraLight)."""

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
    def from_settings(cls, settings) -> "IoTAgentClient":
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

    def create_service_group(self, service_group: IoTService) -> None:
        """Create a service group in the IoT Agent.

        Args:
            service_group: The ServiceGroup model to create.
        """
        url = f"{self._base_url}/iot/services"
        payload = {"services": [service_group.model_dump(exclude_none=True)]}

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Service group created successfully: {service_group.apikey}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create service group: {e}")
            raise

    def provision_device(self, device: Device) -> None:
        """Provision a device in the IoT Agent.

        Args:
            device: The Device model to provision.
        """
        url = f"{self._base_url}/iot/devices"
        payload = {"devices": [device.model_dump(exclude_none=True)]}

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=self._request_timeout
            )
            response.raise_for_status()
            logger.info(f"Device provisioned successfully: {device.device_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to provision device: {e}")
            raise
