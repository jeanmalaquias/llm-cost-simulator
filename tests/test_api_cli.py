from fastapi.testclient import TestClient

from tokenomics import cli
from tokenomics.api.main import app

client = TestClient(app)


def test_healthz_and_catalog():
    assert client.get("/healthz").json() == {"status": "ok"}
    cat = client.get("/catalog").json()
    assert cat["as_of"]
    assert any(m["id"] == "claude-opus-4-8" for m in cat["models"])


def test_estimate_compare_breakeven():
    wl = {"tokens_in": 1000, "tokens_out": 1000, "requests_per_month": 1000}
    est = client.post("/estimate", json={"model_id": "claude-opus-4-8", "workload": wl})
    assert est.json()["baseline_monthly"] == 30.0

    comp = client.post("/compare", json=wl).json()
    assert comp == sorted(comp, key=lambda r: r["monthly"])

    be = client.post("/breakeven", json={
        "model_id": "claude-opus-4-8", "workload": wl,
        "spec": {"instance_hourly_usd": 1.0, "throughput_rps": 10},
    }).json()
    assert be["cheaper_at_current_volume"] == "api"


def test_scenario_encode_decode_roundtrip():
    scenario = {
        "model_id": "gpt-4o",
        "workload": {"tokens_in": 100, "tokens_out": 50, "requests_per_month": 10},
        "optimization": {"cache_hit_rate": 0.5},
    }
    enc = client.post("/scenario/encode", json=scenario).json()
    assert enc["share"].startswith("?s=")
    dec = client.get("/scenario/decode", params={"token": enc["token"]}).json()
    assert dec["model_id"] == "gpt-4o"
    assert dec["optimization"]["cache_hit_rate"] == 0.5


def test_cli_estimate(capsys):
    code = cli.main(["estimate", "examples/scenario.yaml", "--compare", "--share"])
    assert code == 0
    out = capsys.readouterr().out
    assert "optimized_monthly" in out
    assert "Provider comparison" in out
    assert "?s=" in out
