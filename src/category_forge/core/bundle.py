from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from .schemas import CustomerPolicy, DeploymentBundle


def canonical_payload(bundle: DeploymentBundle) -> bytes:
    data = bundle.model_dump(mode="json")
    data["content_sha256"] = ""
    data["hmac_sha256"] = None
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_bundle(bundle: DeploymentBundle, secret: str | None = None) -> DeploymentBundle:
    payload = canonical_payload(bundle)
    digest = hashlib.sha256(payload).hexdigest()
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest() if secret else None
    return bundle.model_copy(update={"content_sha256": digest, "hmac_sha256": signature})


def verify_bundle(bundle: DeploymentBundle, secret: str | None = None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    payload = canonical_payload(bundle)
    expected_hash = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(expected_hash, bundle.content_sha256):
        reasons.append("content SHA-256 mismatch")

    if secret:
        expected_hmac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not bundle.hmac_sha256 or not hmac.compare_digest(expected_hmac, bundle.hmac_sha256):
            reasons.append("HMAC signature mismatch")
    return not reasons, reasons


def build_bundle(
    customer_id: str,
    bundle_version: int,
    taxonomy_mapping: dict[str, str],
    policy: CustomerPolicy,
    created_by: str,
    secret: str | None = None,
) -> DeploymentBundle:
    bundle = DeploymentBundle(
        customer_id=customer_id,
        bundle_version=bundle_version,
        created_by=created_by,
        taxonomy=taxonomy_mapping,
        policy=policy,
        model_compatibility=policy.compatible_model_prefixes,
        metadata={
            "purpose": "GarmentGrader customer configuration",
            "sort_drift_dimension": "taxonomy_version",
        },
    )
    return sign_bundle(bundle, secret=secret)


def diff_bundles(old: DeploymentBundle, new: DeploymentBundle) -> list[dict[str, Any]]:
    old_data = old.model_dump(mode="json")
    new_data = new.model_dump(mode="json")
    changes: list[dict[str, Any]] = []

    def walk(path: str, a: Any, b: Any) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(set(a) | set(b)):
                walk(f"{path}.{key}" if path else key, a.get(key), b.get(key))
        elif a != b and path not in {"content_sha256", "hmac_sha256", "created_at", "bundle_id"}:
            changes.append({"path": path, "old": a, "new": b})

    walk("", old_data, new_data)
    return changes


def compatible_with_model(bundle: DeploymentBundle, model_version: str) -> bool:
    return any(model_version.startswith(prefix) for prefix in bundle.model_compatibility)
