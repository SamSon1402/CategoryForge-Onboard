from __future__ import annotations

from .schemas import CustomerPolicy, HistoricalGarment


def requires_manual_review(item: HistoricalGarment, policy: CustomerPolicy) -> tuple[bool, str]:
    c = policy.confidence
    if item.category_confidence < c.category_min:
        return True, "category confidence below policy"
    if item.grade_confidence < c.grade_min:
        return True, "grade confidence below policy"
    if item.nir_confidence < c.nir_min:
        return True, "NIR confidence below policy"
    if item.ood_score > c.ood_max:
        return True, "OOD score above policy"
    return False, ""


def route_item(item: HistoricalGarment, policy: CustomerPolicy) -> tuple[str, str]:
    manual, reason = requires_manual_review(item, policy)
    if manual:
        return "manual_review", reason

    for rule in policy.routes:
        if rule.allowed_grades and item.grade not in rule.allowed_grades:
            continue
        if rule.min_value_eur is not None and item.estimated_value_eur < rule.min_value_eur:
            continue
        if rule.max_value_eur is not None and item.estimated_value_eur > rule.max_value_eur:
            continue
        if rule.min_fiber_confidence is not None and item.nir_confidence < rule.min_fiber_confidence:
            continue
        if rule.require_category and item.predicted_category not in rule.require_category:
            continue
        return rule.route, f"matched route rule: {rule.route}"

    return "manual_review", "no routing rule matched"
