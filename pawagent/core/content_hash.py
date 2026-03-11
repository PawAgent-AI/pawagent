from __future__ import annotations

import hashlib
from pathlib import Path


def compute_content_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    if path.exists():
        hasher.update(path.read_bytes())
    else:
        hasher.update(str(path.resolve()).encode("utf-8"))
    return hasher.hexdigest()
