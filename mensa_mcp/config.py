import logging
import os
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

# --- Server Settings ---
HOST = os.environ.get("MENSA_HOST", "0.0.0.0")
PORT = int(os.environ.get("MENSA_PORT", "8080"))
WORKERS = int(os.environ.get("MENSA_WORKERS", "4"))
LOG_LEVEL = os.environ.get("MENSA_LOG_LEVEL", "info")
API_KEY = os.environ.get("MENSA_API_KEY", "")

# --- Scraper Settings ---
API_URL = os.environ.get(
    "MENSA_API_URL",
    "https://sw-osnabrueck.maxmanager.xyz/inc/ajax-php_konnektor.inc.php",
)
API_TIMEOUT = float(os.environ.get("MENSA_API_TIMEOUT", "10.0"))
PDF_BASE_URL = os.environ.get(
    "MENSA_PDF_BASE_URL",
    "https://www.maxmanager.de/daten-extern/os-neu/pdf/wochenplaene",
)

# --- Cache Settings ---
CACHE_TTL = int(os.environ.get("MENSA_CACHE_TTL", "86400"))  # seconds

# --- Data Config File ---
CONFIG_FILE = os.environ.get("MENSA_CONFIG_FILE", "")


# --- Default Data ---

_DEFAULT_RESTAURANTS = {
    "mensa-schlossgarten": {
        "id": 7,
        "name": "Mensa Schlossgarten",
        "address": "Ritterstraße 10, 49074 Osnabrück",
        "opening_times": {
            "Mensa": {
                "Mo-Fr": "11:30 – 14:15 Uhr",
                "Sa": "12:00 – 14:00 Uhr",
            },
            "Café Lounge": {
                "Mo-Fr": "09:00 – 15:00 Uhr",
            },
        },
    },
    "mensa-westerberg": {
        "id": 1,
        "name": "Mensa am Westerberg",
        "address": "Barbarastraße 20, 49076 Osnabrück",
        "opening_times": {
            "Mensa": {
                "Mo-Fr": "11:30 – 14:15 Uhr",
            },
            "Café Lounge": {
                "Mo-Fr": "09:00 – 16:30 Uhr",
            },
        },
    },
    "bistro-caprivi": {
        "id": 5,
        "name": "Bistro Caprivi",
        "address": "Caprivistraße 30a, 49076 Osnabrück",
        "opening_times": {
            "Bistro": {
                "Mo-Fr": "09:00 – 15:00 Uhr",
            },
        },
    },
    "mensa-haste": {
        "id": 3,
        "name": "Mensa Haste",
        "address": "Oldenburger Landstraße, 49090 Osnabrück",
        "opening_times": {
            "Mensa": {
                "Mo-Fr": "11:30 – 14:00 Uhr",
            },
            "Cafeteria": {
                "Mo-Do": "09:00 – 16:30 Uhr",
                "Fr": "09:00 – 14:30 Uhr",
            },
        },
    },
    "mensa-vechta": {
        "id": 4,
        "name": "Mensa Vechta",
        "address": "Universitätsstraße 1, 49377 Vechta",
        "opening_times": {
            "Mensa": {
                "Mo-Fr": "11:30 – 14:00 Uhr",
            },
            "Bistro": {
                "Mo-Do": "09:00 – 15:00 Uhr",
                "Fr": "09:00 – 14:00 Uhr",
            },
        },
    },
    "mensa-lingen": {
        "id": 9,
        "name": "Mensa Lingen",
        "address": "Kaiserstraße 10e, 49809 Lingen",
        "opening_times": {
            "Mensa": {
                "Mo-Fr": "11:30 – 14:00 Uhr",
            },
            "Cafeteria": {
                "Mo-Fr": "09:00 – 14:30 Uhr",
            },
        },
    },
}

_DEFAULT_ALLERGENS = {
    "a1": "Weizen",
    "a2": "Roggen",
    "a3": "Gerste",
    "a4": "Hafer",
    "a5": "Dinkel",
    "a6": "Kamut",
    "b":  "Krebstiere",
    "c":  "Hühnerei",
    "d":  "Fisch",
    "e":  "Erdnüsse",
    "f":  "Soja",
    "g":  "Milch und Laktose",
    "h1": "Mandeln",
    "h2": "Haselnüsse",
    "h3": "Walnüsse",
    "h4": "Kaschunüsse",
    "h5": "Pecannüsse",
    "h6": "Paranüsse",
    "h7": "Pistazien",
    "h8": "Macadamia",
    "i":  "Sellerie",
    "j":  "Senf",
    "k":  "Schwefeldioxid und Sulfite",
    "l":  "Lupine",
    "m":  "Sesam",
    "n":  "Weichtiere",
}

_DEFAULT_ADDITIVES = {
    "1":  "Mit Farbstoff",
    "2":  "Mit Konservierungsstoff",
    "3":  "Mit Antioxidationsmittel",
    "4":  "Mit Geschmacksverstärker",
    "5":  "Geschwefelt",
    "6":  "Geschwärzt",
    "7":  "Gewachst",
    "8":  "Mit Phosphat",
    "9":  "Mit Süßungsmittel",
    "10": "Enthält eine Phenylalaninquelle",
    "15": "Mit Alkohol",
    "23": "Mit Gelatine (Schwein)",
    "24": "Aus nachhaltiger Fischerei",
    "25": "Mit Gelatine (Rind)",
}

_DEFAULT_ICON_MAP = {
    "13": "Schwein",
    "14": "Rind",
    "16": "Klimateller",
    "17": "Knoblauch",
    "18": "Artgerechte Tierhaltung",
    "20": "Vegetarisch",
    "21": "Vegan",
    "40": "Geflügel",
    "43": "Fisch",
    "44": "Wild",
}


def _load_config_file() -> dict:
    """Load optional YAML config file for overriding defaults."""
    if not CONFIG_FILE:
        return {}

    path = Path(CONFIG_FILE)
    if not path.exists():
        logger.warning("Config file not found: %s — using defaults", CONFIG_FILE)
        return {}

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        logger.info("Loaded config from %s", CONFIG_FILE)
        return data or {}
    except (yaml.YAMLError, OSError) as e:
        logger.error("Failed to load config file %s: %s — using defaults", CONFIG_FILE, e)
        return {}


def load():
    """Load and return all data config, merging file overrides with defaults."""
    overrides = _load_config_file()
    return {
        "restaurants": overrides.get("restaurants", _DEFAULT_RESTAURANTS),
        "allergens": overrides.get("allergens", _DEFAULT_ALLERGENS),
        "additives": overrides.get("additives", _DEFAULT_ADDITIVES),
        "icon_map": overrides.get("icon_map", _DEFAULT_ICON_MAP),
    }
