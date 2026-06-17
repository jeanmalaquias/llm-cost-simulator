import pytest

from tokenomics.catalog import load_catalog
from tokenomics.estimator import (
    SelfHostSpec,
    break_even,
    compare_models,
    estimate,
)
from tokenomics.scenario import (
    Scenario,
    decode_scenario,
    encode_scenario,
    load_scenario,
)
from tokenomics.tokens import estimate_tokens
from tokenomics.workload import Optimization, Route, Workload


def test_catalog_loads_and_lookup():
    cat = load_catalog()
    assert cat.as_of
    assert cat.disclaimer
    assert "claude-opus-4-8" in cat.ids()
    assert cat.get("claude-opus-4-8").input == 5.0
    with pytest.raises(KeyError, match="Unknown model"):
        cat.get("nope")


def test_catalog_override_path(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(
        '{"as_of":"2026-01-01","currency":"USD","unit":"per_million_tokens",'
        '"disclaimer":"x","models":[{"id":"m","provider":"p","display_name":"M",'
        '"input":1.0,"output":2.0,"source":"http://x"}]}'
    )
    assert load_catalog(p).get("m").output == 2.0


def test_baseline_cost_is_exact():
    cat = load_catalog()
    wl = Workload(tokens_in=1000, tokens_out=1000, requests_per_month=1000)
    # opus: 5 in / 25 out per MTok → 1000 * (0.005 + 0.025) = 30.00
    result = estimate(cat, wl, "claude-opus-4-8")
    assert result.baseline_monthly == 30.0
    assert result.optimized_monthly == 30.0  # no optimization
    assert result.savings_pct == 0.0


def test_optimization_reduces_cost():
    cat = load_catalog()
    wl = Workload(tokens_in=2000, tokens_out=500, requests_per_month=100000)
    opt = Optimization(cache_hit_rate=0.3, input_reduction=0.2)
    result = estimate(cat, wl, "claude-opus-4-8", opt)
    assert result.optimized_monthly < result.baseline_monthly
    assert result.savings_pct > 0


def test_routing_to_cheaper_models_saves():
    cat = load_catalog()
    wl = Workload(tokens_in=2000, tokens_out=500, requests_per_month=100000)
    opt = Optimization(routes=[
        Route(model_id="claude-haiku-4-5", weight=0.8),
        Route(model_id="claude-sonnet-4-6", weight=0.2),
    ])
    result = estimate(cat, wl, "claude-opus-4-8", opt)
    # Routing mostly to Haiku is far cheaper than all-Opus baseline.
    assert result.optimized_monthly < result.baseline_monthly


def test_compare_models_sorted_cheapest_first():
    cat = load_catalog()
    wl = Workload(tokens_in=1000, tokens_out=1000, requests_per_month=1000)
    rows = compare_models(cat, wl)
    assert len(rows) == len(cat.models)
    assert rows == sorted(rows, key=lambda r: r.monthly)


def test_zero_traffic_zero_savings():
    cat = load_catalog()
    wl = Workload(tokens_in=0, tokens_out=0, requests_per_month=0)
    result = estimate(cat, wl, "gpt-4o", Optimization(cache_hit_rate=0.5))
    assert result.baseline_monthly == 0.0
    assert result.savings_pct == 0.0


def test_break_even():
    cat = load_catalog()
    wl = Workload(tokens_in=1000, tokens_out=1000, requests_per_month=1000)
    api = estimate(cat, wl, "claude-opus-4-8").optimized_monthly  # 30.0
    be = break_even(api, wl, SelfHostSpec(instance_hourly_usd=1.0, throughput_rps=10))
    assert be.self_host_monthly == 730.0
    assert be.break_even_requests == pytest.approx(730 / 0.03, rel=1e-3)
    assert be.feasible_on_one_instance is True
    assert be.cheaper_at_current_volume == "api"


def test_break_even_none_when_no_traffic():
    wl = Workload(tokens_in=0, tokens_out=0, requests_per_month=0)
    be = break_even(0.0, wl, SelfHostSpec(instance_hourly_usd=1.0, throughput_rps=1))
    assert be.break_even_requests is None


def test_route_weights_must_be_positive():
    with pytest.raises(ValueError):
        Optimization(routes=[Route(model_id="m", weight=0.0)])


def test_scenario_roundtrip_and_load(tmp_path):
    s = Scenario(
        model_id="gpt-4o",
        workload=Workload(tokens_in=100, tokens_out=50, requests_per_month=10),
        optimization=Optimization(cache_hit_rate=0.5),
    )
    token = encode_scenario(s)
    assert "=" not in token  # unpadded
    assert decode_scenario(token) == s

    p = tmp_path / "s.yaml"
    p.write_text("model_id: gpt-4o\nworkload:\n  tokens_in: 1\n  tokens_out: 1\n"
                 "  requests_per_month: 1\n")
    assert load_scenario(p).model_id == "gpt-4o"


def test_token_estimator():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100
    with pytest.raises(ValueError):
        estimate_tokens("x", chars_per_token=0)
