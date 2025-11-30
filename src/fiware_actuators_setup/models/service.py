from __future__ import annotations

from pydantic import BaseModel, Field


class IoTService(BaseModel):
    """Minimal FIWARE device service definition for Orion Context Broker.

    Parameters
    ----------
    apikey : str
        API key used for associating devices.
    cbroker : str
        Orion Context Broker URL.
    entity_type : str
        NGSIv2 entity type.
    resource : str
        Resource path exposed by the IoT Agent, e.g. ``/iot/d``.
    """

    apikey: str = Field(..., min_length=1)
    cbroker: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    resource: str = Field(..., min_length=1)
