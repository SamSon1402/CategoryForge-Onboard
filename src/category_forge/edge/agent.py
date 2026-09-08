from __future__ import annotations

from dataclasses import dataclass

from category_forge.core.bundle import compatible_with_model, verify_bundle
from category_forge.core.schemas import DeploymentBundle


@dataclass(frozen=True)
class ApplyResult:
    accepted: bool
    reasons: list[str]


class EdgeConfigAgent:
    """The boundary between the control plane and GarmentGrader edge runtime."""

    def __init__(self, model_version: str, signing_secret: str | None = None) -> None:
        self.model_version = model_version
        self.signing_secret = signing_secret
        self.active_bundle: DeploymentBundle | None = None

    def validate(self, bundle: DeploymentBundle) -> ApplyResult:
        ok, reasons = verify_bundle(bundle, self.signing_secret)
        if not compatible_with_model(bundle, self.model_version):
            reasons.append(f"bundle is incompatible with edge model {self.model_version}")
        return ApplyResult(accepted=not reasons, reasons=reasons)

    def apply(self, bundle: DeploymentBundle) -> ApplyResult:
        result = self.validate(bundle)
        if result.accepted:
            self.active_bundle = bundle
        return result
