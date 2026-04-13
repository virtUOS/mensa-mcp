# mensa-mcp

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides menu information for the university restaurants of [Studierendenwerk Osnabrück](https://www.studentenwerk-osnabrueck.de).

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- 🍽️ **Daily menus** for all 6 university restaurants
- 🥗 **Dietary tags** — Vegan, Vegetarian, Fish, etc.
- ⚠️ **Allergen & additive information** with human-readable descriptions
- 🧪 **Nutritional values** — calories, fat, carbs, protein, salt
- 🌱 **CO2 footprint** per dish
- 🕐 **Opening times** and addresses for all restaurants
- 📄 **Weekly menu PDFs** for current and next week
- 🔍 **Cross-restaurant dish search** by name, tag, or allergen
- ⚡ **Daily caching** to avoid unnecessary requests
- 🐳 **Docker support** for easy deployment

## Restaurants

| Key | Name | Location |
|-----|------|----------|
| `mensa-schlossgarten` | Mensa Schlossgarten | Osnabrück |
| `mensa-westerberg` | Mensa am Westerberg | Osnabrück |
| `bistro-caprivi` | Bistro Caprivi | Osnabrück |
| `mensa-haste` | Mensa Haste | Osnabrück |
| `mensa-vechta` | Mensa Vechta | Vechta |
| `mensa-lingen` | Mensa Lingen | Lingen |

## Tools

### `get_restaurants()`

List all available restaurants with their addresses and keys.

**Example:**
```python
# Returns:
# Available restaurants:
#   • Mensa Schlossgarten
#     📍 Ritterstraße 10, 49074 Osnabrück
#     (key: mensa-schlossgarten)
#   • Mensa am Westerberg
#     📍 Barbarastraße 20, 49076 Osnabrück
#     (key: mensa-westerberg)
#   ...
```

### `get_menu(restaurant, day="")`

Get the menu for a specific restaurant and day.

**Arguments:**
- `restaurant` (required): Restaurant key (e.g., `'mensa-schlossgarten'`)
- `day` (optional): Date in YYYY-MM-DD format. Defaults to today.

**Example:**
```python
get_menu("mensa-schlossgarten", "2026-04-15")
# Returns formatted menu with dishes, prices, allergens, and nutritional info
```

### `search_dishes(query, day="")`

Search for a dish across all restaurants by name, tag, or allergen.

**Arguments:**
- `query` (required): Search term (e.g., `'pizza'`, `'vegan'`, `'fisch'`)
- `day` (optional): Date in YYYY-MM-DD format. Defaults to today.

**Example:**
```python
search_dishes("vegan", "2026-04-15")
# Returns all vegan dishes across all restaurants for the specified date
```

### `get_opening_times(restaurant="")`

Get opening times for one restaurant or all restaurants.

**Arguments:**
- `restaurant` (optional): Restaurant key. Leave empty for all.

**Example:**
```python
get_opening_times("mensa-schlossgarten")
# Returns opening times for Mensa Schlossgarten

get_opening_times()
# Returns opening times for all restaurants
```

### `get_weekly_menu_pdf(restaurant)`

Get PDF download links for the weekly menu.

**Arguments:**
- `restaurant` (required): Restaurant key

**Example:**
```python
get_weekly_menu_pdf("mensa-schlossgarten")
# Returns:
# Weekly menu PDFs for Mensa Schlossgarten:
#   📄 Current week: https://www.maxmanager.de/.../aktuell_de.pdf
#   📄 Next week: https://www.maxmanager.de/.../naechste-woche_de.pdf
```

## Installation

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Local Installation

```bash
# Clone the repository
git clone https://github.com/timb/mensa-mcp
cd mensa-mcp

# Install dependencies
uv pip install -e .

# Or with pip
pip install -e .
```

### Quick Start

```bash
# Create environment file
cp .env.example .env
# Edit .env as needed (see Configuration section)

# Run the server
uv run mensa-mcp
```

The server will start on `http://127.0.0.1:8080` by default.

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `MENSA_HOST` | `127.0.0.1` | Server host address |
| `MENSA_PORT` | `8080` | Server port |
| `MENSA_WORKERS` | `4` | Number of worker processes |
| `MENSA_LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |
| `MENSA_API_KEY` | *(empty)* | API key for authentication (optional) |
| `MENSA_API_URL` | `https://sw-osnabrueck.maxmanager.xyz/...` | MaxManager API URL |
| `MENSA_API_TIMEOUT` | `10.0` | API request timeout in seconds |
| `MENSA_PDF_BASE_URL` | `https://www.maxmanager.de/...` | Base URL for weekly menu PDFs |
| `MENSA_CACHE_TTL` | `86400` | Cache time-to-live in seconds (24 hours) |
| `MENSA_CONFIG_FILE` | *(empty)* | Path to optional YAML config file |

### YAML Configuration File

Create a `config.yaml` file to override default restaurant data, allergens, and additives:

```yaml
# config.yaml is optional — it overrides the defaults set in config.py

restaurants:
  mensa-schlossgarten:
    id: 7
    name: Mensa Schlossgarten
    address: "Ritterstraße 10, 49074 Osnabrück"
    opening_times:
      Mensa:
        Mo-Fr: "11:30 – 14:15 Uhr"
        Sa: "12:00 – 14:00 Uhr"
      Café Lounge:
        Mo-Fr: "09:00 – 15:00 Uhr"

allergens:
  a1: Weizen
  a2: Roggen
  g: Milch und Laktose
  # ... only override what you need

additives:
  "1": Mit Farbstoff
  # ... only override what you need
```

Set the config file path via environment variable:
```bash
MENSA_CONFIG_FILE=/path/to/config.yaml
```

## Docker Setup

### Build and Run with Docker Compose

```bash
# Create environment file
cp .env.example .env
# Edit .env as needed

# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t mensa-mcp .

# Run the container
docker run -d \
  --name mensa-mcp \
  -p 8080:8080 \
  --env-file .env \
  mensa-mcp
```

### Docker Health Check

The container includes a health check endpoint at `/health`. Docker will automatically check this endpoint every 30 seconds.

## Client Configuration

### VS Code / Claude Desktop

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "mensa": {
      "url": "http://localhost:8080/sse",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

## Data Sources

Menu data is fetched from the MaxManager API used by Studierendenwerk Osnabrück.
Opening times and addresses are hardcoded from the official restaurant pages
and should be updated manually if they change.

## License

MIT

## Authors

virtUOS, Osnabrueck University
