"""Workload, optimization, and routing models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Workload(BaseModel):
    """A request profile and volume."""

    tokens_in: int = Field(ge=0, description="Input tokens per request")
    tokens_out: int = Field(ge=0, description="Output tokens per request")
    requests_per_month: int = Field(ge=0)


class Route(BaseModel):
    """A weighted slice of traffic sent to a model."""

    model_id: str
    weight: float = Field(gt=0, description="Relative weight; weights are normalized")


class Optimization(BaseModel):
    """Optional cost levers, all default to no-op."""

    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    cache_read_multiplier: float = Field(
        default=0.1, ge=0.0, le=1.0,
        description="Input cost multiplier for cache hits (e.g. 0.1 = 10%)",
    )
    input_reduction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Prompt-compression fraction"
    )
    routes: list[Route] = Field(
        default_factory=list,
        description="If set, traffic is split across these models (weights normalized)",
    )
