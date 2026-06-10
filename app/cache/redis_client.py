from __future__ import annotations

import json
from typing import Any

from app.utils.config import Settings, get_settings


class Cache:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._store: dict[str, str] = {}
        self._client = self._connect()

    def _connect(self):
        if not self.settings.use_external_services:
            return None
        try:
            import redis

            client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            return client
        except Exception:
            return None

    def get(self, key: str) -> str | None:
        if self._client is not None:
            return self._client.get(key)
        return self._store.get(key)

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        if self._client is not None:
            self._client.set(key, value, ex=ttl_seconds)
            return
        self._store[key] = value

    def get_json(self, key: str) -> Any | None:
        value = self.get(key)
        return json.loads(value) if value else None

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        self.set(key, json.dumps(value), ttl_seconds=ttl_seconds)

    def append_json(self, key: str, value: Any, max_items: int = 30) -> None:
        payload = json.dumps(value)
        if self._client is not None:
            self._client.rpush(key, payload)
            self._client.ltrim(key, -max_items, -1)
            return
        existing = self.get_json(key) or []
        existing.append(value)
        self.set_json(key, existing[-max_items:])

    def list_json(self, key: str) -> list[Any]:
        if self._client is not None:
            return [json.loads(item) for item in self._client.lrange(key, 0, -1)]
        value = self.get_json(key)
        return value if isinstance(value, list) else []
