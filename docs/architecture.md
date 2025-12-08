# Architecture

## Overview

This SDK provides Python clients for FIWARE IoT platform components:

```
┌─────────────────────────────────────────────────────────────────┐
│                      FIWARE Actuators Setup SDK                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │  IoTAgentClient │              │   OrionClient   │          │
│  ├─────────────────┤              ├─────────────────┤          │
│  │ • Service Groups│              │ • Entities      │          │
│  │ • Devices       │              │ • Subscriptions │          │
│  └────────┬────────┘              └────────┬────────┘          │
│           │                                │                    │
└───────────┼────────────────────────────────┼────────────────────┘
            │                                │
            ▼                                ▼
    ┌───────────────┐                ┌───────────────┐
    │  IoT Agent    │ ───────────────│    Orion      │
    │  (Port 4061)  │                │  (Port 1026)  │
    └───────┬───────┘                └───────────────┘
            │
            ▼
    ┌───────────────┐
    │   Mosquitto   │
    │  (Port 1883)  │
    └───────────────┘
```

## Components

### Clients

| Client | Purpose | Base URL |
|--------|---------|----------|
| `IoTAgentClient` | Manage IoT devices and service groups | `http://localhost:4061` |
| `OrionClient` | Manage context entities and subscriptions | `http://localhost:1026` |

### Models

| Model | Description |
|-------|-------------|
| `IoTService` | Service Group configuration (apikey, entity_type, resource) |
| `Device` | IoT device with commands |
| `Command` | Device command definition |
| `Subscription` | Orion subscription for notifications |

### Data Flow

```
1. Create IoTService    →  Defines apikey & entity_type
         │
         ▼
2. Create Device        →  Uses same apikey (links to service)
         │
         ▼
3. Device sends data    →  IoT Agent forwards to Orion
         │
         ▼
4. Entity updated       →  Orion stores context data
         │
         ▼
5. Subscription fires   →  Notification sent to endpoint
```

## Error Handling

```
BaseException
    └── IoTAgentError / OrionError
            ├── ClientError (4xx)
            ├── ServerError (5xx)
            └── NotFoundError (404)
```

## Headers

All requests include FIWARE headers:
- `fiware-service`: Tenant/organization
- `fiware-servicepath`: Sub-path within tenant
- `Content-Type: application/json` (only for POST/PATCH)
