from category_forge.core.readiness import build_readiness_report
from category_forge.core.schemas import CategoryMapping, MappingCandidate, MappingDecision


def test_unmapped_high_volume_blocks_readiness():
    mappings = [
        CategoryMapping(raw_name="tee", normalized_name="tee", top1=MappingCandidate(canonical_category="t_shirt", score=0.99), decision=MappingDecision.AUTO_MAP),
        CategoryMapping(raw_name="mystery", normalized_name="mystery", top1=MappingCandidate(canonical_category="shirt", score=0.1), decision=MappingDecision.UNMAPPED),
    ]
    report = build_readiness_report("c", mappings, {"tee": 10, "mystery": 10})
    assert not report.ready
    assert report.taxonomy_coverage == 0.5
