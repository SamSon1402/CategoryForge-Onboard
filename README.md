# CategoryForge Onboard

A small production-style **customer onboarding and configuration control plane** for an industrial garment-sorting CV system.

It is the third project in this connected portfolio:

```text
CategoryForge Onboard
        |
        | versioned taxonomy + grading + routing config
        v
GarmentGrader
        |
        | real GarmentEvent + config/model versions
        v
SortDrift Sentinel
```

## The problem

A garment sorter can have a good vision model and still fail a customer.

Different customers use different names and different business rules:

```text
"tracksuit bottoms" -> pants
"wind-breaker"      -> jacket

Customer A: Grade B -> resale
Customer B: Grade B -> repair
```

Hard-coding these rules inside the CV model or edge application makes every onboarding slow and risky.

CategoryForge turns a customer's file and rules into a **validated, versioned deployment bundle** that GarmentGrader can consume.

## What it does

```text
CSV / JSON
   |
   v
validate + normalize
   |
   v
map customer labels to canonical taxonomy
   |
   +-- AUTO MAP
   +-- REVIEW
   `-- UNMAPPED
   |
   v
configure grading / routing / confidence rules
   |
   v
replay historical garments
   |
   v
readiness gate
   |
   v
SHA-256 + optional HMAC bundle
   |
   v
shadow -> canary -> active / rollback
```

## Why this design

The CV model should answer **what is in front of the camera**.

The customer configuration should decide **what that result means for this customer**.

Keeping those two concerns separate means a new customer taxonomy or route rule does not require retraining the perception model.

The mapper starts with character n-gram TF-IDF because it is fast, explainable and strong for spelling/alias noise. Ambiguous mappings go to review instead of pretending confidence is certainty.

Historical replay answers a more important question than "does this YAML parse?":

> If we deploy this policy, where would yesterday's garments go?

## Important files

```text
src/category_forge/core/mapper.py       taxonomy mapping
src/category_forge/core/replay.py       historical policy replay
src/category_forge/core/readiness.py    deployment readiness gate
src/category_forge/core/bundle.py       versioned hash/signed bundle
src/category_forge/core/deployment.py   shadow/canary/rollback state machine
src/category_forge/edge/agent.py        GarmentGrader edge validation boundary
src/category_forge/service.py           FastAPI control plane
configs/                                canonical taxonomy + customer policy
examples/client_files/                  sample customer files
```

## Run

```bash
python -m pip install -e ".[dev]"
python scripts/run_demo.py
pytest -q
uvicorn category_forge.service:app --reload
```

Then open:

```text
http://127.0.0.1:8000/dashboard
http://127.0.0.1:8000/docs
```

## YC products used

Two YC products are optional integrations, not dependencies in the edge hot path:

- **Supabase (YC S20)** — Postgres-backed storage for customer bundles, readiness reports and deployment state.
- **PostHog (YC W20)** — onboarding/product events such as `taxonomy_mapping_generated`, `readiness_calculated`, `bundle_created`, and rollout transitions.

The project runs locally without either service.

## YC product ideas used as references

These companies are **architecture/product references, not copied code or claimed partnerships**:

- **GroundControl (YC Spring 2025)** — manufacturing workflows where validation, review, traceability and approval matter.
- **Allus AI (YC Fall 2025)** — fast configuration of manufacturing vision tasks from small amounts of customer context.
- **Bucket Robotics (YC Summer 2024)** — industrial vision systems that need to adapt as parts, defects and production lines change.
- **Control Seat (YC Summer 2026)** — one operational source of truth for industrial configuration, history and changes.

The lesson borrowed from them is simple: industrial AI is not only a model. It is the workflow around the model that makes deployment safe and fast.

## What is real vs intentionally unfinished

Implemented here:

- CSV/JSON parsing
- deterministic taxonomy normalization
- char n-gram TF-IDF mapping
- auto-map / review / unmapped gates
- customer grading/routing/confidence policy schema
- historical replay
- readiness scoring
- bundle hashing + optional HMAC
- config diff
- model compatibility check
- shadow/canary/promote/rollback state machine
- FastAPI API
- optional Supabase/PostHog adapters
- tests

Not claimed as production-complete:

- real customer authentication / RBAC
- KMS/HSM key management
- Excel parser
- semantic embedding fallback
- PLC/fleet rollout backend
- human-review collaboration UI
- production audit/compliance controls

Those are the remaining 20%. The core architecture is visible and testable without pretending this repository is already running a real sorting centre.
