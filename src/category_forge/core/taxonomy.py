from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CanonicalCategory:
    name: str
    aliases: tuple[str, ...]
    description: str = ""


class CanonicalTaxonomy:
    def __init__(self, version: str, categories: list[CanonicalCategory]) -> None:
        self.version = version
        self.categories = categories

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CanonicalTaxonomy":
        data = yaml.safe_load(Path(path).read_text())
        categories = [
            CanonicalCategory(
                name=item["name"],
                aliases=tuple(item.get("aliases", [])),
                description=item.get("description", ""),
            )
            for item in data["categories"]
        ]
        return cls(version=str(data["version"]), categories=categories)

    def names(self) -> list[str]:
        return [c.name for c in self.categories]
