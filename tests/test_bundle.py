from pathlib import Path

import yaml

from category_forge.core.bundle import build_bundle, diff_bundles, verify_bundle
from category_forge.core.schemas import CustomerPolicy

ROOT = Path(__file__).resolve().parents[1]


def policy():
    return CustomerPolicy.model_validate(yaml.safe_load((ROOT / "configs/texaid_policy.yaml").read_text()))


def test_signed_bundle_verifies_and_tamper_fails():
    bundle = build_bundle("texaid-demo", 1, {"tee": "t_shirt"}, policy(), "test", "secret")
    ok, reasons = verify_bundle(bundle, "secret")
    assert ok and not reasons
    tampered = bundle.model_copy(update={"taxonomy": {"tee": "jacket"}})
    ok, reasons = verify_bundle(tampered, "secret")
    assert not ok
    assert reasons


def test_bundle_diff_exposes_policy_change():
    old = build_bundle("texaid-demo", 1, {"tee": "t_shirt"}, policy(), "test", "secret")
    p2 = policy().model_copy(update={"policy_version": 8})
    new = build_bundle("texaid-demo", 2, {"tee": "t_shirt"}, p2, "test", "secret")
    changes = diff_bundles(old, new)
    assert any(x["path"] == "policy.policy_version" for x in changes)
