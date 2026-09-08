from __future__ import annotations

import json
from pathlib import Path

from category_forge.core.schemas import DeploymentBundle, DeploymentRecord, ReadinessReport


class LocalStore:
    def __init__(self, root: str | Path = "runtime/category_forge") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _append(self, name: str, data: dict) -> None:
        path = self.root / name
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, sort_keys=True) + "\n")

    def save_bundle(self, bundle: DeploymentBundle) -> None:
        self._append("bundles.jsonl", bundle.model_dump(mode="json"))

    def save_readiness(self, report: ReadinessReport) -> None:
        self._append("readiness.jsonl", report.model_dump(mode="json"))

    def save_deployment(self, deployment: DeploymentRecord) -> None:
        self._append("deployments.jsonl", deployment.model_dump(mode="json"))
