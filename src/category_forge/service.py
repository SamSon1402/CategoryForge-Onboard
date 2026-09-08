from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from category_forge.core.bundle import build_bundle, diff_bundles, verify_bundle
from category_forge.core.deployment import DeploymentController
from category_forge.core.mapper import TaxonomyMapper
from category_forge.core.parser import parse_client_bytes
from category_forge.core.readiness import build_readiness_report
from category_forge.core.replay import replay_history
from category_forge.core.schemas import (
    ClientCategory,
    CustomerPolicy,
    DeploymentBundle,
    DeploymentRecord,
    HistoricalGarment,
)
from category_forge.core.taxonomy import CanonicalTaxonomy
from category_forge.integrations.posthog import ProductAnalytics
from category_forge.storage.local import LocalStore

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = CanonicalTaxonomy.from_yaml(ROOT / "configs/canonical_taxonomy.yaml")
MAPPER = TaxonomyMapper(TAXONOMY)
STORE = LocalStore(ROOT / "runtime")
ANALYTICS = ProductAnalytics()
DEPLOY = DeploymentController()

app = FastAPI(title="CategoryForge Onboard", version="0.3.0")


class MappingRequest(BaseModel):
    customer_id: str
    categories: list[ClientCategory]


class ReadinessRequest(BaseModel):
    customer_id: str
    categories: list[ClientCategory]
    reviewed_truth: dict[str, str] | None = None
    history: list[HistoricalGarment] = []
    policy: CustomerPolicy | None = None


class BundleRequest(BaseModel):
    customer_id: str
    bundle_version: int
    created_by: str = "sameer"
    mappings: dict[str, str]
    policy: CustomerPolicy


class DiffRequest(BaseModel):
    old: DeploymentBundle
    new: DeploymentBundle


@app.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict:
    return {"status": "ready", "taxonomy_version": TAXONOMY.version, "categories": len(TAXONOMY.categories)}


@app.get("/dashboard")
def dashboard():
    return FileResponse(ROOT / "dashboard/index.html")


@app.post("/v1/client-file/parse")
async def parse_file(file: UploadFile = File(...)) -> dict:
    try:
        items = parse_client_bytes(file.filename or "upload.csv", await file.read())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"count": len(items), "categories": [x.model_dump() for x in items]}


@app.post("/v1/mappings")
def mappings(request: MappingRequest) -> dict:
    results = MAPPER.map_many([x.raw_name for x in request.categories])
    ANALYTICS.capture(request.customer_id, "taxonomy_mapping_generated", {"count": len(results)})
    return {"taxonomy_version": TAXONOMY.version, "mappings": [x.model_dump() for x in results]}


@app.post("/v1/readiness")
def readiness(request: ReadinessRequest) -> dict:
    mappings_ = MAPPER.map_many([x.raw_name for x in request.categories])
    volumes = {x.raw_name: x.volume for x in request.categories}
    replay = replay_history(request.history, request.policy) if request.history and request.policy else None
    report = build_readiness_report(
        customer_id=request.customer_id,
        mappings=mappings_,
        volumes=volumes,
        reviewed_truth=request.reviewed_truth,
        replay=replay,
    )
    STORE.save_readiness(report)
    ANALYTICS.capture(request.customer_id, "readiness_calculated", {"ready": report.ready, "score": report.score})
    return report.model_dump(mode="json")


@app.post("/v1/bundles")
def bundle(request: BundleRequest) -> dict:
    if request.policy.customer_id != request.customer_id:
        raise HTTPException(status_code=400, detail="policy customer_id mismatch")
    secret = os.getenv("CATEGORY_FORGE_SIGNING_SECRET")
    result = build_bundle(
        customer_id=request.customer_id,
        bundle_version=request.bundle_version,
        taxonomy_mapping=request.mappings,
        policy=request.policy,
        created_by=request.created_by,
        secret=secret,
    )
    STORE.save_bundle(result)
    ANALYTICS.capture(request.customer_id, "bundle_created", {"bundle_version": result.bundle_version})
    return result.model_dump(mode="json")


@app.post("/v1/bundles/verify")
def verify(bundle: DeploymentBundle) -> dict:
    valid, reasons = verify_bundle(bundle, os.getenv("CATEGORY_FORGE_SIGNING_SECRET"))
    return {"valid": valid, "reasons": reasons}


@app.post("/v1/bundles/diff")
def diff(request: DiffRequest) -> dict:
    return {"changes": diff_bundles(request.old, request.new)}


@app.post("/v1/deployments")
def deployment(record: DeploymentRecord) -> dict:
    record = DEPLOY.validate(record)
    STORE.save_deployment(record)
    return record.model_dump(mode="json")


@app.post("/v1/deployments/{action}")
def deployment_action(action: str, record: DeploymentRecord, canary_percent: int = 10) -> dict:
    try:
        if action == "shadow":
            updated = DEPLOY.shadow(record)
        elif action == "canary":
            updated = DEPLOY.canary(record, canary_percent)
        elif action == "promote":
            updated = DEPLOY.promote(record)
        elif action == "rollback":
            updated = DEPLOY.rollback(record)
        else:
            raise HTTPException(status_code=404, detail="unknown deployment action")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    STORE.save_deployment(updated)
    ANALYTICS.capture(updated.customer_id, f"deployment_{action}", {"bundle_version": updated.bundle_version})
    return updated.model_dump(mode="json")
