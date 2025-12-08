from __future__ import annotations

from typing import Any, List, Literal

from pydantic import BaseModel, Field, model_validator


class Command(BaseModel):
    """Represents a command exposed to the FIWARE IoT Agent.

    Parameters
    ----------
    name : str
        Command name registered in the IoT Agent.
    type : str
        Command type, must be "command", default is "command".
    """

    name: str = Field(min_length=1)
    type: Literal["command"] = "command"


class Device(BaseModel):
    """Minimal FIWARE actuator device definition for IoT Agent UL protocol.

    Parameters
    ----------
    device_id : str
        Unique identifier for the device.
    entity_name : str
        NGSI entity name.
    entity_type : str
        NGSI entity type.
    transport : str
        Communication protocol: ``HTTP`` or ``MQTT``.
    protocol : str
        IoT Agent protocol label.
    apikey : str
        apikey link device to service.
    commands : list[Command]
        Actuator command list. Must not be empty.
    attributes : list[dict[str, Any]]
        Optional list of device attributes.
    """

    device_id: str = Field(..., min_length=1)
    entity_name: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    transport: str = Field(..., pattern=r"^(HTTP|MQTT)$")
    protocol: str = Field(..., min_length=1)
    apikey: str = Field(..., min_length=1)
    commands: List[Command]
    attributes: List[dict[str, Any]] | None = Field(default=None)

    @model_validator(mode="after")
    def validate_commands(self) -> Device:
        if not self.commands:
            raise ValueError("Actuator devices must define at least one command.")
        return self
