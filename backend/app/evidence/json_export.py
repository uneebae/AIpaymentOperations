"""Pure serialization — no new content generated at export time."""
from __future__ import annotations

from app.models.schemas import InvestigationResult


def to_json_bytes(result: InvestigationResult) -> bytes:
    return result.model_dump_json(indent=2).encode("utf-8")
