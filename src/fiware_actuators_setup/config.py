"""Centralized configuration for FIWARE actuators.

This module defines the ``Settings`` class, which loads and validates the
environment configuration required to interact with the IoT Agent,
Orion Context Broker, and other components of the FIWARE ecosystem.

Configuration is loaded from environment variables.
"""

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Load and validate the system configuration.

    Attributes
    ----------
    iota_base_url : str
        URL of the IoT Agent (UL). Includes protocol and port.
    orion_base_url : str
        URL of the Orion Context Broker.
    fiware_service : str
        FIWARE service name.
    fiware_servicepath : str
        FIWARE service-path.
    request_timeout : int
        Maximum allowed time for HTTP requests.
    """

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    iota_base_url: str = Field(default="http://localhost:4061", alias="IOTA_URL")
    orion_base_url: str = Field(default="http://localhost:1026", alias="ORION_URL")

    fiware_service: str = Field(default="openiot", alias="FIWARE_SERVICE")
    fiware_servicepath: str = Field(default="/", alias="FIWARE_SERVICEPATH")
    fiware_resource: str = Field(default="/iot/d", alias="FIWARE_RESOURCE")

    api_token: str | None = Field(default=None, alias="MY_TOKEN")

    request_timeout: int = Field(default=5, alias="TIMEOUT")


# Global reusable instance
settings = Settings()
