from __future__ import annotations

import re


class EntityExtractor:
    def extract(self, text: str, limit: int = 12) -> list[str]:
        candidates = re.findall(r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3}\b", text)
        seen: list[str] = []
        for candidate in candidates:
            normalized = candidate.strip()
            if len(normalized) > 2 and normalized not in seen:
                seen.append(normalized)
            if len(seen) >= limit:
                break
        return seen

