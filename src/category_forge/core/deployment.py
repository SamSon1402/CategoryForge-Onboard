from __future__ import annotations

from datetime import datetime, timezone

from .schemas import DeploymentRecord, DeploymentState


class DeploymentController:
    """Small state machine used by the demo control plane.

    Real production rollout would integrate with the site's actual config agent/PLC gateway.
    """

    def validate(self, record: DeploymentRecord) -> DeploymentRecord:
        return record.model_copy(update={"state": DeploymentState.VALIDATED, "updated_at": datetime.now(timezone.utc)})

    def shadow(self, record: DeploymentRecord) -> DeploymentRecord:
        if record.state not in {DeploymentState.VALIDATED, DeploymentState.CANARY}:
            raise ValueError("bundle must be validated before shadow")
        return record.model_copy(update={"state": DeploymentState.SHADOW, "canary_percent": 0, "updated_at": datetime.now(timezone.utc)})

    def canary(self, record: DeploymentRecord, percent: int = 10) -> DeploymentRecord:
        if record.state != DeploymentState.SHADOW:
            raise ValueError("bundle must be in shadow before canary")
        if not 1 <= percent <= 50:
            raise ValueError("demo canary must be between 1 and 50 percent")
        return record.model_copy(update={"state": DeploymentState.CANARY, "canary_percent": percent, "updated_at": datetime.now(timezone.utc)})

    def promote(self, record: DeploymentRecord) -> DeploymentRecord:
        if record.state != DeploymentState.CANARY:
            raise ValueError("bundle must pass canary before activation")
        return record.model_copy(update={"state": DeploymentState.ACTIVE, "canary_percent": 100, "updated_at": datetime.now(timezone.utc)})

    def rollback(self, record: DeploymentRecord) -> DeploymentRecord:
        return record.model_copy(update={"state": DeploymentState.ROLLED_BACK, "canary_percent": 0, "updated_at": datetime.now(timezone.utc)})
