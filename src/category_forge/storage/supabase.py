from __future__ import annotations

import os

from category_forge.core.schemas import DeploymentBundle, DeploymentRecord, ReadinessReport


class SupabaseStore:
    """Optional YC-backed Postgres adapter.

    Supabase is not required to run the project. This adapter is intentionally small so
    the domain logic does not depend on the vendor SDK.
    """

    def __init__(self) -> None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
        from supabase import create_client

        self.client = create_client(url, key)

    def save_bundle(self, bundle: DeploymentBundle) -> None:
        self.client.table("category_forge_bundles").insert(bundle.model_dump(mode="json")).execute()

    def save_readiness(self, report: ReadinessReport) -> None:
        self.client.table("category_forge_readiness").insert(report.model_dump(mode="json")).execute()

    def save_deployment(self, deployment: DeploymentRecord) -> None:
        self.client.table("category_forge_deployments").insert(deployment.model_dump(mode="json")).execute()
