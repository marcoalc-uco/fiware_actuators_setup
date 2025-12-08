"""Unit tests for the FIWARE Actuator microservice configuration.

These tests validate the loading of variables from `.env`, default values,
and the structure of critical fields such as URLs and API token.
"""

from fiware_actuators_setup.config import settings


def test_environment_loaded():
    """Verify that configuration is correctly loaded from the .env file."""
    assert settings.iota_base_url, "IOTA_BASE_URL must not be empty"
    assert settings.orion_base_url, "ORION_BASE_URL must not be empty"
    assert settings.fiware_service, "FIWARE_SERVICE must not be empty"
    assert settings.fiware_servicepath is not None, "FIWARE_SERVICEPATH must exist"


def test_urls_are_valid():
    """Superficially check that URLs appear to be valid."""
    iota_url = getattr(settings, "iota_base_url", None)
    orion_url = getattr(settings, "orion_base_url", None)
    assert isinstance(iota_url, str) and iota_url.startswith("http")
    assert isinstance(orion_url, str) and orion_url.startswith("http")


def test_request_timeout_positive():
    """The request timeout must be a positive integer."""
    assert settings.request_timeout > 0, "Timeout must be greater than zero"


def test_token_present_if_defined():
    """If API token is defined, it must not be an empty string."""
    token = getattr(settings, "api_token", None)
    if token is not None:
        assert token.strip(), "API token is defined but empty"
