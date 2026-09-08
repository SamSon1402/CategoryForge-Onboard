from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class MappingDecision(StrEnum):
    AUTO_MAP = "AUTO_MAP"
    REVIEW = "REVIEW"
    UNMAPPED = "UNMAPPED"


class ClientCategory(BaseModel):
    raw_name: str
    examples: list[str] = Field(default_factory=list)
    volume: int = Field(default=1, ge=0)


class MappingCandidate(BaseModel):
    canonical_category: str
    score: float = Field(ge=0, le=1)


class CategoryMapping(BaseModel):
    raw_name: str
    normalized_name: str
    top1: MappingCandidate | None = None
    top2: MappingCandidate | None = None
    decision: MappingDecision
    reviewed_category: str | None = None
    explanation: str = ""

    @property
    def resolved_category(self) -> str | None:
        return self.reviewed_category or (self.top1.canonical_category if self.top1 else None)


class GradeRule(BaseModel):
    max_hole_mm: float | None = Field(default=None, ge=0)
    max_stain_area_pct: float | None = Field(default=None, ge=0)
    max_defect_severity: float | None = Field(default=None, ge=0, le=1)


class RouteRule(BaseModel):
    route: str
    allowed_grades: list[str] = Field(default_factory=list)
    min_value_eur: float | None = Field(default=None, ge=0)
    max_value_eur: float | None = Field(default=None, ge=0)
    min_fiber_confidence: float | None = Field(default=None, ge=0, le=1)
    require_category: list[str] = Field(default_factory=list)


class ConfidencePolicy(BaseModel):
    category_min: float = Field(default=0.75, ge=0, le=1)
    grade_min: float = Field(default=0.75, ge=0, le=1)
    nir_min: float = Field(default=0.80, ge=0, le=1)
    ood_max: float = Field(default=0.65, ge=0, le=1)


class CustomerPolicy(BaseModel):
    customer_id: str
    policy_version: int = Field(ge=1)
    taxonomy_version: str
    compatible_model_prefixes: list[str] = Field(default_factory=lambda: ["grader-rgb-"])
    grades: dict[str, GradeRule]
    routes: list[RouteRule]
    confidence: ConfidencePolicy = Field(default_factory=ConfidencePolicy)


class HistoricalGarment(BaseModel):
    garment_id: str
    source_category: str
    predicted_category: str
    category_confidence: float = Field(ge=0, le=1)
    grade: str
    grade_confidence: float = Field(ge=0, le=1)
    estimated_value_eur: float = Field(ge=0)
    nir_confidence: float = Field(ge=0, le=1)
    ood_score: float = Field(ge=0, le=1)
    actual_route: str | None = None


class ReplayResult(BaseModel):
    sample_count: int
    route_agreement: float = Field(ge=0, le=1)
    projected_manual_review_rate: float = Field(ge=0, le=1)
    unknown_category_rate: float = Field(ge=0, le=1)
    low_confidence_rate: float = Field(ge=0, le=1)
    route_counts: dict[str, int]
    mismatches: list[dict[str, Any]] = Field(default_factory=list)


class ReadinessReport(BaseModel):
    customer_id: str
    ready: bool
    score: float = Field(ge=0, le=1)
    taxonomy_coverage: float = Field(ge=0, le=1)
    auto_map_precision: float | None = Field(default=None, ge=0, le=1)
    review_rate: float = Field(ge=0, le=1)
    unmapped_rate: float = Field(ge=0, le=1)
    historical_route_agreement: float | None = Field(default=None, ge=0, le=1)
    projected_manual_review_rate: float | None = Field(default=None, ge=0, le=1)
    blockers: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DeploymentBundle(BaseModel):
    bundle_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str
    bundle_version: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "category-forge"
    taxonomy: dict[str, str]
    policy: CustomerPolicy
    model_compatibility: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_sha256: str = ""
    hmac_sha256: str | None = None

    @model_validator(mode="after")
    def customer_matches_policy(self) -> "DeploymentBundle":
        if self.customer_id != self.policy.customer_id:
            raise ValueError("bundle customer_id must match policy customer_id")
        return self


class DeploymentState(StrEnum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SHADOW = "SHADOW"
    CANARY = "CANARY"
    ACTIVE = "ACTIVE"
    ROLLED_BACK = "ROLLED_BACK"


class DeploymentRecord(BaseModel):
    deployment_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str
    site_id: str
    bundle_version: int
    bundle_sha256: str
    state: DeploymentState = DeploymentState.DRAFT
    canary_percent: int = Field(default=0, ge=0, le=100)
    previous_bundle_version: int | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
