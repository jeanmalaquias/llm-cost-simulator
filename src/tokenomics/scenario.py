"""Scenario model + URL-safe encode/decode for shareable links (no database)."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import yaml
from pydantic import BaseModel

from .workload import Optimization, Workload


class Scenario(BaseModel):
    """A complete, shareable cost scenario."""

    model_id: str
    workload: Workload
    optimization: Optimization = Optimization()


def encode_scenario(scenario: Scenario) -> str:
    """Encode a scenario to a URL-safe, unpadded base64 token (the ``?s=`` value)."""
    payload = json.dumps(scenario.model_dump(), separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_scenario(token: str) -> Scenario:
    """Decode a share token back into a Scenario (inverse of ``encode_scenario``)."""
    padded = token + "=" * (-len(token) % 4)
    payload = base64.urlsafe_b64decode(padded.encode("ascii"))
    return Scenario.model_validate(json.loads(payload))


def load_scenario(path: str | Path) -> Scenario:
    """Load a scenario from a YAML file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Scenario.model_validate(data)
