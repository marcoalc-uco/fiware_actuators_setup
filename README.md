# 🪐FIWARE Actuators Setup SDK

Python SDK for provisioning actuators and managing context data through the **FIWARE IoT Agent (UltraLight)** and **Orion Context Broker**. It provides strongly typed clients, models, and helpers to wire a complete actuator workflow: service group → device → entity → subscription.

## 📑 Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Local FIWARE stack](#local-fiware-stack)
5. [Quick start](#quick-start)
6. [Makefile commands](#makefile-commands)
7. [Running tests](#running-tests)
8. [Project layout](#project-layout)
9. [Documentation](#documentation)

## 📋 Requirements

- Python **3.14+** (see `pyproject.toml`)
- `requests`, `pydantic`, and `pydantic-settings` for HTTP and config handling
- Docker (optional) for the integration test stack

## 📦 Installation

### From GitHub (recommended)

```bash
pip install git+https://github.com/marcoalc-uco/fiware_actuators_setup.git
```

### For Development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/marcoalc-uco/fiware_actuators_setup.git
cd fiware_actuators_setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
cp .env.example .env
pip install -r requirements.txt
pip install -e .
```

## ⚙️ Configuration

Settings are loaded from environment variables via `fiware_actuators_setup.config.Settings`. Create a `.env` file in the project root (or copy from `.env.example`):

```env
ORION_URL=http://localhost:1026
IOTA_URL=http://localhost:4061
FIWARE_SERVICE=openiot
FIWARE_SERVICEPATH=/
FIWARE_RESOURCE=/iot/d
TIMEOUT=10
```

Key variables:

| Variable             | Purpose                        | Default                 |
| -------------------- | ------------------------------ | ----------------------- |
| `ORION_URL`          | Orion Context Broker base URL  | `http://orion:1026`     |
| `IOTA_URL`           | IoT Agent base URL             | `http://iot-agent:4061` |
| `FIWARE_SERVICE`     | Tenant name                    | `openiot`               |
| `FIWARE_SERVICEPATH` | Sub-service path               | `/`                     |
| `FIWARE_RESOURCE`    | IoT Agent resource path        | `/iot/d`                |
| `TIMEOUT`            | HTTP request timeout (seconds) | `5`                     |

## 🐳 Local FIWARE Stack

A full FIWARE stack for integration testing is defined in `docker-compose.yaml` (Orion, IoT Agent UL, Mosquitto, MongoDB, QuantumLeap, CrateDB, and Grafana). Bring it up with:

```bash
docker-compose up -d
```

Services expose the standard FIWARE ports (e.g., Orion on `1026`, IoT Agent on `4061`, MQTT on `1883`). Stop the stack with `docker-compose down` when finished.

## 🚀 Quick Start

Use the typed clients to provision a service group and device, then explore entities in Orion:

```python
from fiware_actuators_setup.clients import IoTAgentClient, OrionClient
from fiware_actuators_setup.config import Settings
from fiware_actuators_setup.models import Command, Device, IoTService

settings = Settings()  # reads .env automatically

iot_agent = IoTAgentClient.from_settings(settings)
orion = OrionClient.from_settings(settings)

# Health checks
assert iot_agent.check_status()
assert orion.check_status()

# 1) Create a service group (required before devices)
service = IoTService(
    apikey="my-api-key",
    cbroker=settings.orion_base_url,
    entity_type="Actuator",
    resource=settings.fiware_resource,
)
iot_agent.create_service_group(service)

# 2) Provision a device linked to the service group
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

# 3) Inspect entities created in Orion
entities = orion.list_entities()
print(entities)
```

## 🛠️ Makefile Commands

This project includes a Makefile with common development tasks. Run `make help` to see all available commands:

| Command                 | Description                                |
| ----------------------- | ------------------------------------------ |
| `make help`             | Show available commands                    |
| `make install`          | Install production dependencies            |
| `make install-dev`      | Install all dependencies + pre-commit      |
| `make test`             | Run all tests                              |
| `make test-unit`        | Run only unit tests (no integration)       |
| `make test-integration` | Run only integration tests                 |
| `make lint`             | Run pylint on source code                  |
| `make format`           | Format code with isort and black           |
| `make type-check`       | Run mypy type checking                     |
| `make pre-commit`       | Run all pre-commit hooks                   |
| `make docker-up`        | Start FIWARE services                      |
| `make docker-down`      | Stop FIWARE services                       |
| `make docker-logs`      | Show container logs                        |
| `make clean`            | Remove cache and temp files                |
| `make all`              | Run format + lint + type-check + test-unit |

> **Note (Windows):** Requires [GnuWin32 Make](http://gnuwin32.sourceforge.net/packages/make.htm) installed and added to PATH.

## 🧪 Running Tests

- **Unit tests (mocked):**

  ```bash
  pytest -m "not integration"
  ```

- **Integration tests (requires Docker stack running):**

  ```bash
  docker-compose up -d
  pytest -m integration
  docker-compose down
  ```

- **All tests:** `pytest`

## 📁 Project Layout

```
fiware_actuators_setup/
├── src/fiware_actuators_setup
│   ├── clients/                # IoT Agent and Orion clients
│   ├── models/                 # Pydantic models for FIWARE payloads
│   ├── config.py               # Environment-backed Settings loader
│   └── exceptions.py           # Custom HTTP exception hierarchy
├── docs/architecture.md        # System overview and data flow
├── docker/                     # IoT Agent and broker configuration
├── docker-compose.yaml         # Local FIWARE stack for tests
├── tests/                      # Unit and integration suites
└── requirements.txt            # Development/runtime dependencies
```

## 📚 Documentation

- [Architecture](docs/architecture.md) – system diagram, data flow, and error handling notes.

## 📄 License

MIT
