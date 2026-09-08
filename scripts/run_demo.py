from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from category_forge.core.bundle import build_bundle, verify_bundle
from category_forge.core.mapper import TaxonomyMapper
from category_forge.core.parser import parse_client_bytes
from category_forge.core.readiness import build_readiness_report
from category_forge.core.replay import replay_history
from category_forge.core.schemas import CustomerPolicy, HistoricalGarment
from category_forge.core.taxonomy import CanonicalTaxonomy

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    taxonomy = CanonicalTaxonomy.from_yaml(ROOT / "configs/canonical_taxonomy.yaml")
    mapper = TaxonomyMapper(taxonomy)
    csv_path = ROOT / "examples/client_files/texaid.csv"
    categories = parse_client_bytes(csv_path.name, csv_path.read_bytes())
    mappings = mapper.map_many([x.raw_name for x in categories])

    policy = CustomerPolicy.model_validate(yaml.safe_load((ROOT / "configs/texaid_policy.yaml").read_text()))
    history = [HistoricalGarment.model_validate(x) for x in json.loads((ROOT / "examples/historical_texaid.json").read_text())]
    replay = replay_history(history, policy)

    reviewed_truth = {
        "T-Shirts": "t_shirt",
        "Tracksuit bottoms": "pants",
        "Wind-breaker": "jacket",
        "Hooded Sweatshirt": "hoodie",
        "Denim trousers": "pants",
        "Ladies gown": "dress",
    }
    volumes = {x.raw_name: x.volume for x in categories}
    readiness = build_readiness_report("texaid-demo", mappings, volumes, reviewed_truth, replay)

    resolved = {
        m.raw_name: m.resolved_category
        for m in mappings
        if m.resolved_category is not None and m.decision.value != "UNMAPPED"
    }
    secret = os.getenv("CATEGORY_FORGE_SIGNING_SECRET", "demo-secret")
    bundle = build_bundle("texaid-demo", 42, resolved, policy, "sameer", secret)
    valid, reasons = verify_bundle(bundle, secret)

    out = ROOT / "examples/output"
    out.mkdir(exist_ok=True)
    (out / "texaid_bundle.json").write_text(json.dumps(bundle.model_dump(mode="json"), indent=2))
    (out / "texaid_readiness.json").write_text(json.dumps(readiness.model_dump(mode="json"), indent=2))

    print("CATEGORY MAPPINGS")
    for m in mappings:
        top = m.top1.canonical_category if m.top1 else "-"
        score = m.top1.score if m.top1 else 0
        print(f"  {m.raw_name:24} -> {top:12} {score:.3f} {m.decision.value}")
    print("\nREADINESS")
    print(readiness.model_dump_json(indent=2))
    print(f"\nBUNDLE VERIFIED: {valid} {reasons}")
    print(f"BUNDLE SHA256: {bundle.content_sha256}")


if __name__ == "__main__":
    main()
