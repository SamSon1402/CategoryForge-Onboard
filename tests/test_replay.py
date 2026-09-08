from pathlib import Path

import yaml

from category_forge.core.replay import replay_history
from category_forge.core.schemas import CustomerPolicy, HistoricalGarment

ROOT = Path(__file__).resolve().parents[1]


def policy():
    return CustomerPolicy.model_validate(yaml.safe_load((ROOT / "configs/texaid_policy.yaml").read_text()))


def test_low_confidence_routes_to_review():
    item = HistoricalGarment(
        garment_id="x",
        source_category="x",
        predicted_category="t_shirt",
        category_confidence=0.4,
        grade="A",
        grade_confidence=0.95,
        estimated_value_eur=50,
        nir_confidence=0.95,
        ood_score=0.1,
        actual_route="manual_review",
    )
    result = replay_history([item], policy())
    assert result.projected_manual_review_rate == 1.0
    assert result.route_agreement == 1.0
