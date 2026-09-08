from __future__ import annotations

from .schemas import CategoryMapping, MappingDecision, ReadinessReport, ReplayResult


def _weighted_mapping_stats(
    mappings: list[CategoryMapping], volumes: dict[str, int] | None = None
) -> tuple[float, float, float]:
    if not mappings:
        return 0.0, 0.0, 1.0
    volumes = volumes or {}
    weights = [max(1, int(volumes.get(m.raw_name, 1))) for m in mappings]
    total = float(sum(weights))
    covered = sum(
        w for m, w in zip(mappings, weights) if m.decision != MappingDecision.UNMAPPED
    ) / total
    review = sum(
        w for m, w in zip(mappings, weights) if m.decision == MappingDecision.REVIEW
    ) / total
    unmapped = sum(
        w for m, w in zip(mappings, weights) if m.decision == MappingDecision.UNMAPPED
    ) / total
    return covered, review, unmapped


def estimate_auto_map_precision(
    mappings: list[CategoryMapping], reviewed_truth: dict[str, str] | None
) -> float | None:
    if not reviewed_truth:
        return None
    auto = [m for m in mappings if m.decision == MappingDecision.AUTO_MAP and m.raw_name in reviewed_truth]
    if not auto:
        return None
    correct = sum(m.top1 and m.top1.canonical_category == reviewed_truth[m.raw_name] for m in auto)
    return float(correct) / len(auto)


def build_readiness_report(
    customer_id: str,
    mappings: list[CategoryMapping],
    volumes: dict[str, int] | None = None,
    reviewed_truth: dict[str, str] | None = None,
    replay: ReplayResult | None = None,
) -> ReadinessReport:
    coverage, review_rate, unmapped_rate = _weighted_mapping_stats(mappings, volumes)
    precision = estimate_auto_map_precision(mappings, reviewed_truth)
    route_agreement = replay.route_agreement if replay else None
    projected_review = replay.projected_manual_review_rate if replay else None

    blockers: list[str] = []
    recommendations: list[str] = []

    if coverage < 0.95:
        blockers.append("taxonomy coverage below 95%")
        recommendations.append("Review unmapped high-volume customer categories first.")
    if precision is not None and precision < 0.98:
        blockers.append("measured auto-map precision below 98%")
        recommendations.append("Raise the auto-map threshold or add reviewed aliases.")
    if route_agreement is not None and route_agreement < 0.95:
        blockers.append("historical route agreement below 95%")
        recommendations.append("Inspect route-policy mismatches before shadow deployment.")
    if projected_review is not None and projected_review > 0.15:
        recommendations.append("Manual-review load is high; tune thresholds only after error review.")

    precision_component = precision if precision is not None else 0.95
    route_component = route_agreement if route_agreement is not None else 0.95
    review_component = 1.0 - min(review_rate, 1.0)
    score = (
        0.35 * coverage
        + 0.25 * precision_component
        + 0.25 * route_component
        + 0.15 * review_component
    )

    return ReadinessReport(
        customer_id=customer_id,
        ready=not blockers,
        score=max(0.0, min(1.0, score)),
        taxonomy_coverage=coverage,
        auto_map_precision=precision,
        review_rate=review_rate,
        unmapped_rate=unmapped_rate,
        historical_route_agreement=route_agreement,
        projected_manual_review_rate=projected_review,
        blockers=blockers,
        recommendations=recommendations,
    )
