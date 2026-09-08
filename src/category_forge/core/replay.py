from __future__ import annotations

from .policy import route_item
from .schemas import CustomerPolicy, HistoricalGarment, ReplayResult


def replay_history(items: list[HistoricalGarment], policy: CustomerPolicy) -> ReplayResult:
    if not items:
        return ReplayResult(
            sample_count=0,
            route_agreement=0.0,
            projected_manual_review_rate=0.0,
            unknown_category_rate=0.0,
            low_confidence_rate=0.0,
            route_counts={},
        )

    agreement = 0
    comparable = 0
    manual = 0
    unknown = 0
    low_conf = 0
    counts: dict[str, int] = {}
    mismatches: list[dict] = []

    for item in items:
        route, reason = route_item(item, policy)
        counts[route] = counts.get(route, 0) + 1
        manual += int(route == "manual_review")
        unknown += int(item.predicted_category == "unknown")
        low_conf += int(
            item.category_confidence < policy.confidence.category_min
            or item.grade_confidence < policy.confidence.grade_min
            or item.nir_confidence < policy.confidence.nir_min
        )

        if item.actual_route is not None:
            comparable += 1
            if item.actual_route == route:
                agreement += 1
            elif len(mismatches) < 25:
                mismatches.append(
                    {
                        "garment_id": item.garment_id,
                        "actual_route": item.actual_route,
                        "candidate_route": route,
                        "reason": reason,
                    }
                )

    n = len(items)
    return ReplayResult(
        sample_count=n,
        route_agreement=(agreement / comparable) if comparable else 0.0,
        projected_manual_review_rate=manual / n,
        unknown_category_rate=unknown / n,
        low_confidence_rate=low_conf / n,
        route_counts=counts,
        mismatches=mismatches,
    )
