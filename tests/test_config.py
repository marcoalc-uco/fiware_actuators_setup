"""Pruebas unitarias para la configuración del microservicio FIWARE Actuator.

Se valida la carga de variables desde `.env`, los valores por defecto
y la estructura de los campos críticos como URLs y token API.
"""

from fiware_actuators_setup.config import settings


def test_environment_loaded():
    """Verifica que la configuración se carga correctamente desde el .env."""
    assert settings.iota_base_url, "IOTA_BASE_URL no debe estar vacío"
    assert settings.orion_base_url, "ORION_BASE_URL no debe estar vacío"
    assert settings.fiware_service, "FIWARE_SERVICE no debe estar vacío"
    assert settings.fiware_servicepath is not None, "FIWARE_SERVICEPATH debe existir"


def test_urls_are_valid():
    """Comprueba superficialmente que las URLs parecen válidas."""
    iota_url = getattr(settings, "iota_base_url", None)
    orion_url = getattr(settings, "orion_base_url", None)
    assert isinstance(iota_url, str) and iota_url.startswith("http")
    assert isinstance(orion_url, str) and orion_url.startswith("http")


def test_request_timeout_positive():
    """El timeout debe ser un entero positivo."""
    assert settings.request_timeout > 0, "El timeout debe ser mayor que cero"


def test_token_present_if_defined():
    """El token no puede ser una cadena vacía."""
    token = getattr(settings, "api_token", None)
    if token is not None:
        assert token.strip(), "El token API está definido pero vacío"
