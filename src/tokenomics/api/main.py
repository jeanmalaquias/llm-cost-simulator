"""FastAPI surface — catalog, estimate, compare, break-even, scenario sharing."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .. import __version__
from ..catalog import Catalog, load_catalog
from ..estimator import (
    BreakEven,
    CostResult,
    ModelCost,
    SelfHostSpec,
    break_even,
    compare_models,
    estimate,
)
from ..scenario import Scenario, decode_scenario, encode_scenario
from ..workload import Optimization, Workload

app = FastAPI(title="LLM Cost Simulator", version=__version__)
_catalog = load_catalog()


class EstimateRequest(BaseModel):
    model_id: str
    workload: Workload
    optimization: Optimization = Optimization()


class BreakEvenRequest(EstimateRequest):
    spec: SelfHostSpec


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/catalog")
async def catalog() -> Catalog:
    """The versioned pricing catalog (with as_of date and disclaimer)."""
    return _catalog


@app.post("/estimate")
async def estimate_endpoint(req: EstimateRequest) -> CostResult:
    """Baseline vs. optimized monthly cost."""
    return estimate(_catalog, req.workload, req.model_id, req.optimization)


@app.post("/compare")
async def compare_endpoint(workload: Workload) -> list[ModelCost]:
    """Naive monthly cost of the workload on every model, cheapest first."""
    return compare_models(_catalog, workload)


@app.post("/breakeven")
async def breakeven_endpoint(req: BreakEvenRequest) -> BreakEven:
    """Self-host vs. API break-even for the (optimized) workload."""
    result = estimate(_catalog, req.workload, req.model_id, req.optimization)
    return break_even(result.optimized_monthly, req.workload, req.spec)


@app.post("/scenario/encode")
async def scenario_encode(scenario: Scenario) -> dict[str, str]:
    """Encode a scenario to a shareable token."""
    token = encode_scenario(scenario)
    return {"token": token, "share": f"?s={token}"}


@app.get("/scenario/decode")
async def scenario_decode(token: str) -> Scenario:
    """Decode a share token back into a scenario."""
    return decode_scenario(token)
