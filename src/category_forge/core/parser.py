from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .schemas import ClientCategory


def parse_client_bytes(filename: str, content: bytes) -> list[ClientCategory]:
    suffix = Path(filename).suffix.lower()
    text = content.decode("utf-8-sig")

    if suffix == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            name = row.get("category") or row.get("name") or row.get("label")
            if not name:
                continue
            examples = [x.strip() for x in (row.get("examples") or "").split("|") if x.strip()]
            try:
                volume = int(row.get("volume") or 1)
            except ValueError:
                volume = 1
            rows.append(ClientCategory(raw_name=name, examples=examples, volume=volume))
        return rows

    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("categories", [])
        return [ClientCategory.model_validate(item) for item in data]

    raise ValueError("supported client files are .csv and .json")
