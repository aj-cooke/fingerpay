from __future__ import annotations

import os
from pathlib import Path

from .core import FingerPayError

DEFAULT_DIR = Path.home() / ".fingerpay"
DEFAULT_K_PATH = DEFAULT_DIR / "k.token"


def save_k_token(k_token: str, path: str | None = None) -> Path:
    target = Path(path).expanduser() if path else DEFAULT_K_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(k_token, encoding="utf-8")

    # Best effort: owner read/write only.
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass

    return target


def load_k_token(path: str | None = None) -> str:
    target = Path(path).expanduser() if path else DEFAULT_K_PATH
    if not target.exists():
        raise FingerPayError(f"K file not found: {target}")
    return target.read_text(encoding="utf-8").strip()
