# mensa_mcp/cache.py
from datetime import date, datetime
from dataclasses import dataclass
from typing import Any

from mensa_mcp import config


@dataclass
class CacheEntry:
    data: Any
    fetched_at: datetime
    valid_for_date: date


class DailyCache:
    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._ttl = config.CACHE_TTL

    def get(self, key: str, target_date: date | None = None) -> Any | None:
        target_date = target_date or date.today()
        entry = self._store.get(key)

        if entry is None:
            return None

        if entry.valid_for_date != target_date:
            return None

        age = (datetime.now() - entry.fetched_at).total_seconds()
        if age > self._ttl:
            return None

        return entry.data

    def set(self, key: str, data: Any, target_date: date | None = None):
        target_date = target_date or date.today()
        self._store[key] = CacheEntry(
            data=data,
            fetched_at=datetime.now(),
            valid_for_date=target_date,
        )

    def invalidate(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()
