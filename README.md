# FIWARE Actuators Setup SDK

A Python SDK for interacting with FIWARE IoT Agent and Orion Context Broker.

## Features

- **IoT Agent Client**: CRUD operations for Service Groups and Devices
- **Orion Client**: CRUD operations for Entities and Subscriptions
- **Pydantic Models**: Type-safe data validation
- **TDD Approach**: Comprehensive unit and integration tests

## Installation

```bash
pip install -e .
```

## Quick Start

### Configuration

Create a `.env` file:

```env
ORION_URL=http://localhost:1026
IOTA_URL=http://localhost:4061
FIWARE_SERVICE=openiot
FIWARE_SERVICEPATH=/
REQUEST_TIMEOUT=10
```

### Usage

```python
from fiware_actuators_setup.clients import IoTAgentClient, OrionClient
from fiware_actuators_setup.models import IoTService, Device, Command

# Initialize clients
orion = OrionClient(
    base_url="http://localhost:1026",
    fiware_service="openiot",
    fiware_servicepath="/",
    request_timeout=10,
)

iot_agent = IoTAgentClient(
    base_url="http://localhost:4061",
    fiware_service="openiot",
    fiware_servicepath="/",
    request_timeout=10,
)

# Check connectivity
print(orion.check_status())      # True
print(iot_agent.check_status())  # True

# Create a Service Group (FIRST)
service = IoTService(
    apikey="my-api-key",
    cbroker="http://orion:1026",
    entity_type="Actuator",
    resource="/iot/d",
)
iot_agent.create_service_group(service)

# Create a Device (inherits apikey from service)
device = Device(
    device_id="actuator001",
    entity_name="urn:ngsi-ld:Actuator:001",
    entity_type=service.entity_type,
    transport="MQTT",
    protocol="PDI-IoTA-UltraLight",
    apikey=service.apikey,
    commands=[Command(name="switch", type="command")],
)
iot_agent.create_device(device)

# List entities in Orion
entities = orion.list_entities()
```

## Running Tests

### Unit Tests
```bash
pytest -m "not integration"
```

### Integration Tests (requires Docker)
```bash
docker-compose up -d
pytest -m integration
docker-compose down
```

### All Tests
```bash
pytest
```

## Project Structure

```
fiware_actuators_setup/
├── src/fiware_actuators_setup/
│   ├── clients/
│   │   ├── iot_agent.py      # IoT Agent Client
│   │   └── orion.py          # Orion Context Broker Client
│   ├── models/
│   │   ├── device.py         # Device model
│   │   ├── service.py        # IoTService model
│   │   └── subscription.py   # Subscription model
│   ├── config.py             # Settings configuration
│   └── exceptions.py         # Custom exceptions
├── tests/
│   ├── units/                # Unit tests (mocked)
│   └── integration/          # Integration tests (real FIWARE)
├── docker/
│   └── config/               # FIWARE service configs
└── docker-compose.yaml       # Local FIWARE stack
```

## Documentation

- [Architecture](docs/architecture.md)

## License

MIT
