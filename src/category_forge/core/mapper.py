from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .normalize import normalize_label
from .schemas import CategoryMapping, MappingCandidate, MappingDecision
from .taxonomy import CanonicalTaxonomy


@dataclass(frozen=True)
class MappingThresholds:
    auto_map: float = 0.72
    review: float = 0.38
    ambiguity_margin: float = 0.08


class TaxonomyMapper:
    """Fast, deterministic baseline for customer-category onboarding.

    Character n-grams are deliberately used before a heavier semantic model because
    customer taxonomy noise is often spelling, punctuation, abbreviations and word-shape
    variation. A semantic fallback can be added behind the same interface later.
    """

    def __init__(
        self,
        taxonomy: CanonicalTaxonomy,
        thresholds: MappingThresholds | None = None,
    ) -> None:
        self.taxonomy = taxonomy
        self.thresholds = thresholds or MappingThresholds()
        self._candidate_texts: list[str] = []
        self._candidate_names: list[str] = []

        for category in taxonomy.categories:
            aliases = " ".join(normalize_label(x) for x in category.aliases)
            combined = " ".join(
                x for x in [normalize_label(category.name), aliases, category.description] if x
            )
            self._candidate_texts.append(combined)
            self._candidate_names.append(category.name)

        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1)
        self.canonical_matrix = self.vectorizer.fit_transform(self._candidate_texts)

    def map_one(self, raw_name: str) -> CategoryMapping:
        normalized = normalize_label(raw_name)
        query = self.vectorizer.transform([normalized])
        scores = cosine_similarity(query, self.canonical_matrix)[0]
        order = np.argsort(scores)[::-1]

        def candidate(idx: int) -> MappingCandidate:
            return MappingCandidate(
                canonical_category=self._candidate_names[int(idx)],
                score=float(np.clip(scores[int(idx)], 0.0, 1.0)),
            )

        top1 = candidate(int(order[0]))
        top2 = candidate(int(order[1])) if len(order) > 1 else None
        margin = top1.score - (top2.score if top2 else 0.0)

        if top1.score >= self.thresholds.auto_map and margin >= self.thresholds.ambiguity_margin:
            decision = MappingDecision.AUTO_MAP
            explanation = "High lexical match with enough separation from the second candidate."
        elif top1.score >= self.thresholds.review:
            decision = MappingDecision.REVIEW
            explanation = "Plausible match, but confidence or ambiguity requires human review."
        else:
            decision = MappingDecision.UNMAPPED
            explanation = "No canonical category is similar enough to auto-map safely."

        return CategoryMapping(
            raw_name=raw_name,
            normalized_name=normalized,
            top1=top1,
            top2=top2,
            decision=decision,
            explanation=explanation,
        )

    def map_many(self, raw_names: list[str]) -> list[CategoryMapping]:
        return [self.map_one(name) for name in raw_names]
