from __future__ import annotations

import hashlib


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def frame_changed(new_hash: str, previous_hash: str | None) -> bool:
    return previous_hash is None or new_hash != previous_hash
