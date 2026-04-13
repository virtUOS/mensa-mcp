# mensa_mcp/scraper.py
import logging
import re

import httpx
from bs4 import BeautifulSoup, Tag
from datetime import date

from mensa_mcp import config
from mensa_mcp.models import RESTAURANTS, ICON_MAP, Dish, DailyMenu, NutritionInfo
from mensa_mcp.exceptions import ScraperError

logger = logging.getLogger(__name__)


async def fetch_menu_page(loc_id: int, target_date: date) -> BeautifulSoup:
    """Fetch menu HTML from MaxManager API."""
    try:
        async with httpx.AsyncClient(timeout=config.API_TIMEOUT) as client:
            response = await client.post(
                config.API_URL,
                data={
                    "func": "make_spl",
                    "locId": loc_id,
                    "date": target_date.isoformat(),
                    "lang": "de",
                },
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise ScraperError(
            f"Timeout fetching menu (locId={loc_id}, date={target_date})"
        )
    except httpx.ConnectError:
        raise ScraperError(
            "Cannot connect to menu server. Is it reachable?"
        )
    except httpx.HTTPStatusError as e:
        raise ScraperError(
            f"Server error fetching menu: HTTP {e.response.status_code}"
        )
    except httpx.HTTPError as e:
        raise ScraperError(f"Network error: {e}")

    content = response.text.strip()
    if not content:
        logger.info("Empty response for locId=%s, date=%s", loc_id, target_date)
        return BeautifulSoup("", "html.parser")

    return BeautifulSoup(content, "html.parser")


def _extract_icon_id(src: str) -> str | None:
    """Extract icon ID from src like 'assets/icons/20.png?v=1' → '20'."""
    match = re.search(r"/(\d+)\.png", src)
    return match.group(1) if match else None


def _parse_dish_name_and_allergens(
    artikeltext: Tag,
) -> tuple[str, list[str], list[str]]:
    """Extract dish name, allergen codes, and tags from an artikel div."""
    components: list[str] = []
    allergens: list[str] = []
    tags: list[str] = []

    inline_divs = artikeltext.find_all(
        "div",
        style=lambda s: s and "inline-block" in s,
    )

    for div in inline_divs:
        for img in div.find_all("img"):
            src = img.get("src", "")
            icon_id = _extract_icon_id(src)
            if icon_id and icon_id in ICON_MAP:
                tag = ICON_MAP[icon_id]
                if tag not in tags:
                    tags.append(tag)

        text = div.get_text(strip=True)
        text = text.replace("\xa0", " ").strip()

        allergen_match = re.search(r"\(([a-z0-9,\s]+)\)\s*$", text)
        if allergen_match:
            codes = [c.strip() for c in allergen_match.group(1).split(",")]
            allergens.extend(codes)
            text = text[: allergen_match.start()].strip()

        if text:
            components.append(text)

    name = " + ".join(components)
    allergens = list(dict.fromkeys(allergens))
    return name, allergens, tags


def _parse_price(artikel: Tag) -> tuple[str, str]:
    """Extract student and employee price."""
    price_div = artikel.find("div", class_="artColInnerCenter")
    if not price_div:
        return "?", "?"

    text = price_div.get_text(strip=True)
    text = text.replace("€", "").replace("\xa0", " ").strip()

    parts = text.split("/")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return text, text


def _parse_co2(artikel: Tag) -> str | None:
    """Extract CO2 value like '321 g CO2e'."""
    co2_div = artikel.find("div", class_="co2Wert")
    if co2_div:
        match = re.search(r"(\d+)\s*g\s*CO2e", co2_div.get_text())
        if match:
            return f"{match.group(1)} g CO2e"
    return None


def _parse_nutrition(artikel: Tag) -> NutritionInfo | None:
    """Extract nutritional values from the naehrwerte div."""
    nw_div = artikel.find("div", class_="naehrwerte")
    if not nw_div:
        return None

    text = nw_div.get_text()
    info = NutritionInfo()

    match = re.search(r"Brennwert\s*=\s*([\d.,]+)\s*kJ\s*\(([\d.,]+)\s*kcal\)", text)
    if match:
        info.energy_kj = match.group(1)
        info.energy_kcal = match.group(2)

    match = re.search(r"Fett\s*=\s*([\d.,]+)\s*g", text)
    if match:
        info.fat = match.group(1)

    match = re.search(r"gesättigte Fettsäuren\s*=\s*([\d.,]+)\s*g", text)
    if match:
        info.saturated_fat = match.group(1)

    match = re.search(r"Kohlenhydrate\s*=\s*([\d.,]+)\s*g", text)
    if match:
        info.carbohydrates = match.group(1)

    match = re.search(r"Zucker\s*=\s*([\d.,]+)\s*g", text)
    if match:
        info.sugar = match.group(1)

    match = re.search(r"Eiweiß\s*=\s*([\d.,]+)\s*g", text)
    if match:
        info.protein = match.group(1)

    match = re.search(r"Salz\s*=\s*([\d.,]+)\s*g", text)
    if match:
        info.salt = match.group(1)

    return info


def parse_menu(
    soup: BeautifulSoup, restaurant_name: str, target_date: date
) -> DailyMenu:
    """Parse the menu HTML returned by the API."""
    menu = DailyMenu(restaurant=restaurant_name, date=target_date)
    current_category = "Unbekannt"

    for element in soup.children:
        if not isinstance(element, Tag):
            continue

        cat_div = element.find("div", class_="kategorietitel")
        if cat_div:
            current_category = cat_div.get_text(strip=True)

        for artikel in element.find_all("div", class_="artikel"):
            try:
                artikeltext = artikel.find("div", class_="artikeltext")
                if not artikeltext:
                    continue

                name, allergens, tags = _parse_dish_name_and_allergens(artikeltext)
                price_student, price_employee = _parse_price(artikel)
                co2 = _parse_co2(artikel)
                nutrition = _parse_nutrition(artikel)

                if name:
                    menu.dishes.append(
                        Dish(
                            name=name,
                            category=current_category,
                            price_student=price_student,
                            price_employee=price_employee,
                            allergens=allergens,
                            tags=tags,
                            co2_value=co2,
                            nutrition=nutrition,
                        )
                    )
            except Exception as e:
                logger.warning("Failed to parse dish: %s", e)
                continue

    return menu


async def scrape_menu(restaurant_key: str, target_date: date) -> DailyMenu:
    """Main entry point: fetch and parse menu for a restaurant + date."""
    info = RESTAURANTS[restaurant_key]
    soup = await fetch_menu_page(info["id"], target_date)
    return parse_menu(soup, info["name"], target_date)
