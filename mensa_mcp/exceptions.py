
class MensaError(Exception):
    """Base exception for mensa-mcp."""


class ScraperError(MensaError):
    """Failed to fetch or parse menu data."""


class RestaurantNotFoundError(MensaError):
    """Unknown restaurant key."""


class InvalidDateError(MensaError):
    """Invalid or unparseable date."""
