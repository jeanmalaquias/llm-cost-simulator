"""Load and validate the versioned pricing catalog.

The catalog is the single source of truth for prices, shared with the frontend.
Every model carries a ``source`` URL and the catalog an ``as_of`` date — see
docs/methodology.md for the honesty contract.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from pydantic import BaseModel


class ModelPrice(BaseModel):
    """Per-model pricing (USD per million tokens)."""

    id: str
    provider: str
    display_name: str
    input: float
    output: float
    source: str


class Catalog(BaseModel):
    """A dated, sourced snapshot of model prices."""

    as_of: str
    currency: str
    unit: str
    disclaimer: str
    models: list[ModelPrice]

    def ids(self) -> list[str]:
        return [m.id for m in self.models]

    def get(self, model_id: str) -> ModelPrice:
        for model in self.models:
            if model.id == model_id:
                return model
        known = ", ".join(self.ids())
        raise KeyError(f"Unknown model '{model_id}'. Known: {known}")


def load_catalog(path: str | Path | None = None) -> Catalog:
    """Load the bundled catalog, or an override path."""
    if path is not None:
        raw = Path(path).read_text(encoding="utf-8")
    else:
        raw = files("tokenomics.data").joinpath("catalog.json").read_text(
            encoding="utf-8"
        )
    return Catalog.model_validate(json.loads(raw))
