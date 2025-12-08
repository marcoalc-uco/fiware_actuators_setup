"""Fixtures for integration tests.

These fixtures require FIWARE services running via docker-compose.
Run: docker-compose up -d
"""

import pytest

from fiware_actuators_setup.clients import IoTAgentClient, OrionClient


@pytest.fixture(scope="module")
def orion_client():
    """Create OrionClient connected to local Docker Orion."""
    return OrionClient(
        base_url="http://localhost:1026",
        fiware_service="openiot",
        fiware_servicepath="/",
        request_timeout=10,
    )


@pytest.fixture(scope="module")
def iot_agent_client():
    """Create IoTAgentClient connected to local Docker IoT Agent."""
    return IoTAgentClient(
        base_url="http://localhost:4061",
        fiware_service="openiot",
        fiware_servicepath="/",
        request_timeout=10,
    )
