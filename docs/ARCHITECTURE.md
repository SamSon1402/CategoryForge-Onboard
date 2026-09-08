# Architecture

CategoryForge is the **customer/configuration control plane** for the other two projects.

```text
CUSTOMER CSV / JSON
        |
        v
schema + parsing
        |
        v
normalization
        |
        v
char n-gram TF-IDF mapping
        |
        +---- high confidence ----> AUTO MAP
        +---- ambiguous ----------> HUMAN REVIEW
        `---- weak ---------------> UNMAPPED
        |
        v
customer taxonomy
        |
        +---- grading policy
        +---- routing policy
        `---- confidence/OOD policy
        |
        v
HISTORICAL REPLAY
        |
        v
READINESS GATE
        |
        v
VERSIONED CONFIG BUNDLE
        |
        +---- SHA-256 integrity
        +---- optional HMAC signature
        +---- model compatibility
        |
        v
SHADOW -> CANARY -> ACTIVE / ROLLBACK
        |
        v
GARMENTGRADER EDGE
        |
        `---- taxonomy_version + policy_version on every GarmentEvent
                         |
                         v
                 SORTDRIFT SENTINEL
```

## Why the taxonomy baseline is intentionally simple

Customer labels are usually messy in deterministic ways: spelling, punctuation, abbreviations,
pluralization and local naming. Character n-gram TF-IDF is cheap, explainable, fast on CPU and
works well as a first gate. A semantic embedding fallback can be added for the review band, but
an LLM should not silently decide production routing policy.

## Safety boundary

CategoryForge does not push arbitrary configs directly into a live conveyor. A bundle must:

1. pass schema validation;
2. pass mapping/readiness review;
3. pass historical replay;
4. have an integrity hash/signature;
5. declare compatible model versions;
6. enter shadow;
7. enter a limited canary;
8. be promoted or rolled back.

## Connection to the other projects

- **GarmentGrader** consumes the versioned taxonomy/grading/routing bundle.
- Every GarmentGrader event carries `taxonomy_version` / `policy_version`.
- **SortDrift Sentinel** can then distinguish model drift from a customer-config change.

This is important: a changed route distribution is not automatically model drift. It may be a
new customer policy or taxonomy version.
