from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from category_forge.core.bundle import verify_bundle
from category_forge.core.schemas import DeploymentBundle

path = Path(sys.argv[1])
bundle = DeploymentBundle.model_validate(json.loads(path.read_text()))
ok, reasons = verify_bundle(bundle, os.getenv("CATEGORY_FORGE_SIGNING_SECRET"))
print("VALID" if ok else "INVALID")
for reason in reasons:
    print("-", reason)
raise SystemExit(0 if ok else 1)
