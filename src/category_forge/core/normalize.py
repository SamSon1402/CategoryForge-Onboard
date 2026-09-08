from __future__ import annotations

import re
import unicodedata


ALIASES = {
    "tee": "t shirt",
    "tshirt": "t shirt",
    "t shirts": "t shirt",
    "t-shirt": "t shirt",
    "trousers": "pants",
    "trouser": "pants",
    "tracksuit bottom": "pants",
    "tracksuit bottoms": "pants",
    "wind breaker": "windbreaker",
    "hooded sweatshirt": "hoodie",
}


def normalize_label(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[_/\\-]+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return ALIASES.get(text, text)
