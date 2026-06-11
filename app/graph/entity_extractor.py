from __future__ import annotations

import re

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "into", "is", "it", "its", "of", "on", "or", "our", "that", "the", "their",
    "them", "there", "these", "this", "those", "to", "with", "without", "you", "your",
    "says", "say", "said", "can", "could", "should", "would", "will", "may", "must",
}


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

        if len(seen) >= 2:
            return seen

        fallback = re.findall(r"\b[A-Za-z]{3,}\b", text)
        for token in fallback:
            normalized = token.strip().title() if token.islower() else token.strip()
            if normalized.lower() not in STOPWORDS and normalized not in seen:
                seen.append(normalized)
            if len(seen) >= limit:
                break

        return seen

