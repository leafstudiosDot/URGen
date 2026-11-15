"""Shared helpers for upload modules (env loading, validation)."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass


def env(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def require_env(name: str) -> str:
    return env(name, required=True)  # type: ignore[return-value]


def file_size(path: Path) -> int:
    return path.stat().st_size
