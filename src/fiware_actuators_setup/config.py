"""Configuración centralizada para atuadores FIWARE.

Este módulo define la clase Settings, que carga y valida la
configuración de entorno necesaria para interactuar con el IoT Agent,
Orion Context Broker y otros componentes del ecosistema FIWARE.

La configuración se carga desde variables de entorno.
"""

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Carga y valida la configuración del sistema.

    Atributos
    ---------
    iota_base_url : str
        URL del IoT Agent (UL). Incluye protocolo y puerto.
    orion_base_url : str
        URL del Orion Context Broker.
    fiware_service : str
        Nombre del servicio FIWARE.
    fiware_servicepath : str
        Ruta del service path FIWARE.
    request_timeout : int
        Tiempo máximo permitido para peticiones HTTP.
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


# Instancia global y reutilizable
settings = Settings()
