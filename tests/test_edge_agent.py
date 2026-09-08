from pathlib import Path

import yaml

from category_forge.core.bundle import build_bundle
from category_forge.core.schemas import CustomerPolicy
from category_forge.edge.agent import EdgeConfigAgent

ROOT = Path(__file__).resolve().parents[1]


def test_edge_agent_checks_model_compatibility():
    policy = CustomerPolicy.model_validate(yaml.safe_load((ROOT / "configs/texaid_policy.yaml").read_text()))
    bundle = build_bundle("texaid-demo", 1, {}, policy, "test", "secret")
    good = EdgeConfigAgent("grader-rgb-0.9.4", "secret").validate(bundle)
    bad = EdgeConfigAgent("legacy-model-2", "secret").validate(bundle)
    assert good.accepted
    assert not bad.accepted
