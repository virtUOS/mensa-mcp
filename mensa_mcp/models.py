# mensa_mcp/models.py
from dataclasses import dataclass, field
from datetime import date

from mensa_mcp import config

_data = config.load()

RESTAURANTS = _data["restaurants"]
ALLERGENS = _data["allergens"]
ADDITIVES = _data["additives"]
ICON_MAP = _data["icon_map"]


def resolve_codes(codes: list[str]) -> dict[str, list[str]]:
    """Resolve allergen/additive codes to human-readable names."""
    resolved_allergens = []
    resolved_additives = []

    for code in codes:
        if code in ALLERGENS:
            resolved_allergens.append(f"{code} = {ALLERGENS[code]}")
        elif code in ADDITIVES:
            resolved_additives.append(f"{code} = {ADDITIVES[code]}")

    return {
        "allergens": resolved_allergens,
        "additives": resolved_additives,
    }


def get_pdf_urls(restaurant_key: str) -> dict[str, str]:
    loc_id = RESTAURANTS[restaurant_key]["id"]
    return {
        "current_week": f"{config.PDF_BASE_URL}/{loc_id}/aktuell_de.pdf",
        "next_week": f"{config.PDF_BASE_URL}/{loc_id}/naechste-woche_de.pdf",
    }


@dataclass
class NutritionInfo:
    energy_kj: str | None = None
    energy_kcal: str | None = None
    fat: str | None = None
    saturated_fat: str | None = None
    carbohydrates: str | None = None
    sugar: str | None = None
    protein: str | None = None
    salt: str | None = None


@dataclass
class Dish:
    name: str
    category: str
    price_student: str
    price_employee: str
    allergens: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    co2_value: str | None = None
    nutrition: NutritionInfo | None = None


@dataclass
class DailyMenu:
    restaurant: str
    date: date
    dishes: list[Dish] = field(default_factory=list)
