from pathlib import Path

from category_forge.core.mapper import TaxonomyMapper
from category_forge.core.schemas import MappingDecision
from category_forge.core.taxonomy import CanonicalTaxonomy

ROOT = Path(__file__).resolve().parents[1]


def test_known_alias_maps_to_pants():
    mapper = TaxonomyMapper(CanonicalTaxonomy.from_yaml(ROOT / "configs/canonical_taxonomy.yaml"))
    result = mapper.map_one("Tracksuit bottoms")
    assert result.top1 is not None
    assert result.top1.canonical_category == "pants"
    assert result.decision == MappingDecision.AUTO_MAP


def test_unknown_is_not_silently_accepted():
    mapper = TaxonomyMapper(CanonicalTaxonomy.from_yaml(ROOT / "configs/canonical_taxonomy.yaml"))
    result = mapper.map_one("mystery accessories")
    assert result.decision in {MappingDecision.REVIEW, MappingDecision.UNMAPPED}
