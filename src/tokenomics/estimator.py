"""Cost engine: per-model cost, optimization, comparison, and break-even.

All math is explicit and auditable (see docs/architecture.md §3). Costs are
monthly, in the catalog's currency.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .catalog import Catalog, ModelPrice
from .workload import Optimization, Workload

_MTOK = 1_000_000
_HOURS_PER_MONTH = 730  # 365 * 24 / 12


def _model_monthly_cost(
    price: ModelPrice, workload: Workload, opt: Optimization
) -> float:
    """Monthly cost of running a full workload on one model, with levers applied."""
    requests = workload.requests_per_month
    eff_in = workload.tokens_in * (1.0 - opt.input_reduction)
    cached = requests * opt.cache_hit_rate
    uncached = requests - cached

    uncached_cost = uncached * (
        eff_in / _MTOK * price.input + workload.tokens_out / _MTOK * price.output
    )
    # Cache hits: input billed at the cache-read multiplier, no output generation.
    cached_cost = cached * (eff_in / _MTOK * price.input * opt.cache_read_multiplier)
    return uncached_cost + cached_cost


def _routed_monthly_cost(
    catalog: Catalog, workload: Workload, opt: Optimization
) -> float:
    """Cost when traffic is split across routes (weights normalized)."""
    total_weight = sum(r.weight for r in opt.routes)
    cost = 0.0
    for route in opt.routes:
        share = route.weight / total_weight
        slice_workload = workload.model_copy(
            update={"requests_per_month": workload.requests_per_month * share}
        )
        cost += _model_monthly_cost(catalog.get(route.model_id), slice_workload, opt)
    return cost


class CostResult(BaseModel):
    """Baseline vs. optimized monthly cost for a model selection."""

    model_id: str
    baseline_monthly: float
    optimized_monthly: float
    savings_monthly: float
    savings_pct: float
    currency: str
    as_of: str


def estimate(
    catalog: Catalog,
    workload: Workload,
    model_id: str,
    optimization: Optimization | None = None,
) -> CostResult:
    """Estimate baseline (no levers) vs. optimized monthly cost."""
    opt = optimization or Optimization()
    baseline = _model_monthly_cost(catalog.get(model_id), workload, Optimization())
    if opt.routes:
        optimized = _routed_monthly_cost(catalog, workload, opt)
    else:
        optimized = _model_monthly_cost(catalog.get(model_id), workload, opt)
    savings = baseline - optimized
    pct = round(savings / baseline, 4) if baseline else 0.0
    return CostResult(
        model_id=model_id,
        baseline_monthly=round(baseline, 4),
        optimized_monthly=round(optimized, 4),
        savings_monthly=round(savings, 4),
        savings_pct=pct,
        currency=catalog.currency,
        as_of=catalog.as_of,
    )


class ModelCost(BaseModel):
    model_id: str
    display_name: str
    monthly: float


def compare_models(catalog: Catalog, workload: Workload) -> list[ModelCost]:
    """Naive monthly cost of the workload on every model, cheapest first."""
    rows = [
        ModelCost(
            model_id=m.id,
            display_name=m.display_name,
            monthly=round(_model_monthly_cost(m, workload, Optimization()), 4),
        )
        for m in catalog.models
    ]
    return sorted(rows, key=lambda r: r.monthly)


class SelfHostSpec(BaseModel):
    """Always-on self-hosting assumptions (the reader supplies these)."""

    instance_hourly_usd: float = Field(gt=0)
    throughput_rps: float = Field(gt=0)


class BreakEven(BaseModel):
    """Self-host vs. API break-even for the current workload."""

    api_monthly: float
    self_host_monthly: float
    break_even_requests: float | None  # None = API is free / never breaks even
    capacity_per_month: float
    feasible_on_one_instance: bool
    cheaper_at_current_volume: str  # "api" | "self_host"


def break_even(
    api_monthly: float, workload: Workload, spec: SelfHostSpec
) -> BreakEven:
    """Compare always-on self-hosting to the API at the current volume."""
    requests = workload.requests_per_month
    self_host_monthly = spec.instance_hourly_usd * _HOURS_PER_MONTH
    capacity = spec.throughput_rps * 3600 * _HOURS_PER_MONTH
    api_cost_per_request = api_monthly / requests if requests else 0.0
    be = self_host_monthly / api_cost_per_request if api_cost_per_request else None
    return BreakEven(
        api_monthly=round(api_monthly, 4),
        self_host_monthly=round(self_host_monthly, 4),
        break_even_requests=round(be, 2) if be is not None else None,
        capacity_per_month=capacity,
        feasible_on_one_instance=requests <= capacity,
        cheaper_at_current_volume="self_host"
        if self_host_monthly < api_monthly
        else "api",
    )
