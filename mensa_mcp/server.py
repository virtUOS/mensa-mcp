import logging
from mcp.server.fastmcp import FastMCP
from datetime import date
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from mensa_mcp.scraper import scrape_menu
from mensa_mcp.cache import DailyCache
from mensa_mcp.models import (
    RESTAURANTS, ALLERGENS, ADDITIVES,
    DailyMenu, Dish, get_pdf_urls, resolve_codes,
)
from mensa_mcp.exceptions import ScraperError, RestaurantNotFoundError, InvalidDateError

logger = logging.getLogger(__name__)

mcp = FastMCP("Mensa Server")
cache = DailyCache()


def _validate_restaurant(restaurant: str) -> None:
    """Raise if restaurant key is unknown."""
    if restaurant not in RESTAURANTS:
        available = ", ".join(RESTAURANTS.keys())
        raise RestaurantNotFoundError(
            f"Unknown restaurant: '{restaurant}'. Available: {available}"
        )


def _parse_date(day: str) -> date:
    """Parse date string or return today."""
    if not day:
        return date.today()
    try:
        return date.fromisoformat(day)
    except ValueError:
        raise InvalidDateError(
            f"Invalid date: '{day}'. Please use YYYY-MM-DD format."
        )


def _format_dish(dish: Dish) -> str:
    """Format a single dish as readable text."""
    lines = [f"  🍽️  {dish.name}"]
    lines.append(f"     Price: {dish.price_student} / {dish.price_employee} €")

    if dish.tags:
        lines.append(f"     Tags: {', '.join(dish.tags)}")

    if dish.allergens:
        resolved = resolve_codes(dish.allergens)
        if resolved["allergens"]:
            lines.append(f"     Allergens: {', '.join(resolved['allergens'])}")
        if resolved["additives"]:
            lines.append(f"     Additives: {', '.join(resolved['additives'])}")

    if dish.co2_value:
        lines.append(f"     CO2: {dish.co2_value}")

    if dish.nutrition:
        n = dish.nutrition
        parts = []
        if n.energy_kcal:
            parts.append(f"{n.energy_kcal} kcal")
        if n.fat:
            parts.append(f"Fat: {n.fat}g")
        if n.carbohydrates:
            parts.append(f"Carbs: {n.carbohydrates}g")
        if n.protein:
            parts.append(f"Protein: {n.protein}g")
        if n.salt:
            parts.append(f"Salt: {n.salt}g")
        if parts:
            lines.append(f"     Nutrition: {' | '.join(parts)}")

    return "\n".join(lines)


def _format_menu(menu: DailyMenu) -> str:
    """Format a full menu as readable text."""
    if not menu.dishes:
        return (
            f"No dishes found for {menu.restaurant} on {menu.date}.\n"
            f"The restaurant may be closed on this day."
        )

    lines = [f"=== {menu.restaurant} — {menu.date} ===\n"]

    current_category = ""
    for dish in menu.dishes:
        if dish.category != current_category:
            current_category = dish.category
            lines.append(f"\n📋 {current_category}")
        lines.append(_format_dish(dish))

    return "\n".join(lines)


async def _get_menu_cached(restaurant_key: str, target_date: date) -> DailyMenu:
    """Fetch menu with daily caching."""
    cache_key = f"{restaurant_key}:{target_date.isoformat()}"
    cached = cache.get(cache_key, target_date)

    if cached is not None:
        return cached

    menu = await scrape_menu(restaurant_key, target_date)
    cache.set(cache_key, menu, target_date)
    return menu


@mcp.tool()
async def get_restaurants() -> str:
    """List all available university restaurants with addresses."""
    lines = ["Available restaurants:\n"]
    for key, info in RESTAURANTS.items():
        lines.append(f"  • {info['name']}")
        lines.append(f"    📍 {info['address']}")
        lines.append(f"    (key: {key})")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def get_menu(restaurant: str, day: str = "") -> str:
    """
    Get the menu for a specific restaurant and day.

    Args:
        restaurant: Restaurant key (e.g. 'mensa-schlossgarten', 'mensa-westerberg').
                    Use get_restaurants() to see all available keys.
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    try:
        _validate_restaurant(restaurant)
        target_date = _parse_date(day)
        menu = await _get_menu_cached(restaurant, target_date)
        return _format_menu(menu)
    except (RestaurantNotFoundError, InvalidDateError) as e:
        return str(e)
    except ScraperError as e:
        logger.error("Scraper error: %s", e)
        return f"⚠️ Error fetching menu: {e}"
    except Exception as e:
        logger.exception("Unexpected error in get_menu")
        return f"⚠️ Unexpected error: {e}"


@mcp.tool()
async def search_dishes(query: str, day: str = "") -> str:
    """
    Search for a dish across all restaurants.

    Args:
        query: Search term (e.g. 'pizza', 'vegan', 'fisch').
               Searches dish names, tags, and allergen names.
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    try:
        target_date = _parse_date(day)
    except InvalidDateError as e:
        return str(e)

    query_lower = query.lower()
    results: list[str] = []
    errors: list[str] = []

    for key in RESTAURANTS:
        try:
            menu = await _get_menu_cached(key, target_date)
            for dish in menu.dishes:
                name_match = query_lower in dish.name.lower()
                tag_match = any(query_lower in t.lower() for t in dish.tags)
                allergen_match = any(
                    query_lower in v.lower()
                    for v in [
                        *[ALLERGENS.get(a, "") for a in dish.allergens],
                        *[ADDITIVES.get(a, "") for a in dish.allergens],
                    ]
                )
                if name_match or tag_match or allergen_match:
                    results.append(f"[{menu.restaurant}]\n{_format_dish(dish)}")
        except ScraperError as e:
            errors.append(f"⚠️ {RESTAURANTS[key]['name']}: {e}")
            continue

    output = []
    if results:
        output.append(f"Search results for '{query}' on {target_date}:\n")
        output.append("\n\n".join(results))
    else:
        output.append(f"No results for '{query}' on {target_date}.")

    if errors:
        output.append("\n\n--- Errors ---")
        output.extend(errors)

    return "\n".join(output)


@mcp.tool()
async def get_weekly_menu_pdf(restaurant: str) -> str:
    """
    Get PDF download links for the weekly menu of a restaurant.

    Args:
        restaurant: Restaurant key (e.g. 'mensa-schlossgarten').
    """
    try:
        _validate_restaurant(restaurant)
    except RestaurantNotFoundError as e:
        return str(e)

    urls = get_pdf_urls(restaurant)
    name = RESTAURANTS[restaurant]["name"]
    return (
        f"Weekly menu PDFs for {name}:\n\n"
        f"  📄 Current week:\n  {urls['current_week']}\n\n"
        f"  📄 Next week:\n  {urls['next_week']}"
    )


@mcp.tool()
async def get_opening_times(restaurant: str = "") -> str:
    """
    Get opening times for a restaurant, or all restaurants if none specified.

    Args:
        restaurant: Restaurant key (e.g. 'mensa-schlossgarten'). Leave empty for all.
    """
    if restaurant:
        try:
            _validate_restaurant(restaurant)
        except RestaurantNotFoundError as e:
            return str(e)

    targets = {restaurant: RESTAURANTS[restaurant]} if restaurant else RESTAURANTS

    lines = []
    for key, info in targets.items():
        lines.append(f"📍 {info['name']}")
        lines.append(f"   {info['address']}")

        for section, times in info["opening_times"].items():
            lines.append(f"   {section}:")
            for days, hours in times.items():
                lines.append(f"     {days}: {hours}")
        lines.append("")

    return "\n".join(lines)


async def _health_check(request):
    return JSONResponse({"status": "healthy"})


app = Starlette(routes=[
    Route("/health", _health_check),
    Mount("/", mcp.streamable_http_app()),
])
