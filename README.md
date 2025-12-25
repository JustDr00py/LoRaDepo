# LoRaDepo

LoRa Database deployment and management tools.

## Projects

This repository contains three main components:

### 1. LoRaDB
The core LoRa database - a Rust-based time-series database optimized for LoRa sensor data.

**Directory**: `LoRaDB/`

### 2. LoRaDB-UI
Web interface for LoRaDB with Node.js backend and React frontend.

**Directory**: `LoRaDB-UI/`

### 3. LoRaDB-manager
Textual TUI application for managing multiple LoRaDB instances on a single machine.

**Directory**: `LoRaDB-manager/`

See the [LoRaDB-manager README](./LoRaDB-manager/README.md) for deployment instructions.

## Quick Start

### LoRaDB Manager

The easiest way to get started with managing multiple LoRaDB instances:

```bash
cd LoRaDB-manager
./run.sh
```

See [LoRaDB-manager/QUICKSTART.md](./LoRaDB-manager/QUICKSTART.md) for more details.

## Prerequisites

- **Docker** and Docker Compose V2
- **Python 3.10+** (for LoRaDB-manager)
- **Rust** (for LoRaDB development)
- **Node.js 18+** (for LoRaDB-UI development)

## Project Structure

```
LoRaDepo/
├── LoRaDB/              # Rust time-series database
├── LoRaDB-UI/           # Web interface (Node.js + React)
├── LoRaDB-manager/      # TUI instance manager (Python)
└── README.md            # This file
```

## Development

Each project has its own development setup. See individual README files:

- [LoRaDB README](./LoRaDB/README.md)
- [LoRaDB-UI README](./LoRaDB-UI/README.md)
- [LoRaDB-manager README](./LoRaDB-manager/README.md)

## License

This project is part of the LoRaDepo ecosystem.
