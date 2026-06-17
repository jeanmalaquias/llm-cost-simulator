# LLM Cost Simulator

> Estimate and optimize LLM inference cost across providers. Compose a workload,
> compare providers from a **versioned, sourced** pricing catalog, simulate
> **semantic caching / prompt compression / model routing**, find the
> **self-host break-even**, and share any scenario as a URL.

<!-- Badges placeholder: CI · license · coverage -->

---

## Contents

- [Honesty first](#honesty-first)
- [What it does](#what-it-does)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Scenario format](#scenario-format)
- [Cost model](#cost-model)
- [HTTP API](#http-api)
- [Web calculator](#web-calculator)
- [Pricing catalog](#pricing-catalog)
- [Project layout](#project-layout)
- [Testing](#testing)
- [Limitations](#limitations)

## Honesty first

Prices change constantly and tokenization is provider-specific, so this is a
**decision aid, not a billing oracle**. The pricing catalog is versioned
(`as_of` date), sourced (a URL per model), and disclaimed; the cost engine works
on **token counts you provide**, never guessed. Read
[docs/methodology.md](docs/methodology.md) before trusting a number.

## What it does

- **Workload composer** — tokens in/out per request × request volume.
- **Provider catalog** — 10 models across OpenAI, Anthropic, Azure, AWS, Google
  in one [versioned JSON](src/tokenomics/data/catalog.json).
- **Optimization simulator** — semantic cache hit-rate, prompt compression %, and
  weighted model routing, composed.
- **Self-host break-even** — API $/request vs. a GPU instance, with explicit
  assumptions you supply.
- **Shareable scenarios** — every scenario encodes to a `?s=...` URL; no database.

## Prerequisites

- **Python 3.12+** for the engine, API, and CLI.
- Optional: **Node 20+** for the interactive web calculator.

## Installation

```bash
git clone https://github.com/jeanmalaquias/llm-cost-simulator.git
cd llm-cost-simulator
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

Estimate the bundled example scenario, comparing all providers:

```bash
llmcost estimate examples/scenario.yaml --compare --share
```

Expected output (abridged):

```
{
  "model_id": "claude-opus-4-8",
  "baseline_monthly": ...,
  "optimized_monthly": ...,
  "savings_pct": ...
}

Prices as of 2026-06-16 — Indicative list prices... verify against the source.

Provider comparison (naive monthly, cheapest first):
        ...   Gemini 2.0 Flash
        ...   Claude Haiku 4.5
        ...

Share: ?s=<token>
```

| Flag | Effect |
|------|--------|
| `--compare` | show the workload's cost on every model, cheapest first |
| `--share` | print a URL-safe token encoding the scenario |

## Scenario format

```yaml
model_id: claude-opus-4-8          # the "baseline" / primary model
workload:
  tokens_in: 2000
  tokens_out: 500
  requests_per_month: 1000000
optimization:                      # all optional, default to no-op
  cache_hit_rate: 0.3              # fraction served from a semantic cache
  cache_read_multiplier: 0.1       # input cost multiplier for cache hits
  input_reduction: 0.2             # prompt-compression fraction
  routes:                          # split traffic across cheaper models
    - { model_id: claude-haiku-4-5, weight: 0.7 }
    - { model_id: claude-sonnet-4-6, weight: 0.3 }
```

## Cost model

The engine computes monthly cost from **explicit token counts**:

```
monthly = requests × (tokens_in/1e6 × input_$ + tokens_out/1e6 × output_$)
```

Optimization levers and the self-host break-even formula are documented in full
in [docs/architecture.md](docs/architecture.md) §3 — the math is deliberately
simple so every number is auditable.

## HTTP API

```bash
uvicorn tokenomics.api.main:app --port 8086
```

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/healthz` | liveness |
| GET | `/catalog` | the versioned pricing catalog (with `as_of` + disclaimer) |
| POST | `/estimate` | baseline vs. optimized monthly cost |
| POST | `/compare` | per-model cost for a workload |
| POST | `/breakeven` | self-host vs. API break-even |
| POST | `/scenario/encode` · GET `/scenario/decode` | shareable scenario tokens |

## Web calculator

```bash
cd web && npm install && npm run dev   # http://localhost:3000
```

An interactive Next.js 15 calculator (workload inputs, cache/compression
sliders, live per-model comparison chart, share button). It computes
**client-side** — deployable statically to Vercel with no backend — mirroring the
Python cost engine in `web/lib/cost.ts`.

## Pricing catalog

[`src/tokenomics/data/catalog.json`](src/tokenomics/data/catalog.json) is the
single source of truth (the web app mirrors it). Each model carries a `source`
URL; the catalog carries an `as_of` date and a disclaimer. The weekly
`update-prices.yml` workflow checks staleness and opens a refresh issue — it does
**not** blindly scrape (a wrong auto-update is worse than a known-dated one).

## Project layout

```
src/tokenomics/
├── data/catalog.json   # versioned, sourced pricing catalog
├── catalog.py          # loader + validation
├── workload.py         # Workload, Route, Optimization models
├── estimator.py        # cost engine, comparison, break-even
├── scenario.py         # Scenario + URL-safe encode/decode
├── tokens.py           # caveated token estimator (approximation)
├── api/main.py         # FastAPI surface
└── cli.py              # llmcost estimate
web/                    # Next.js interactive calculator
examples/scenario.yaml  # sample workload
```

## Testing

```bash
pytest --cov --cov-report=term-missing   # 16 tests, 100% source coverage
ruff check src tests
```

## Limitations

- Static list prices; no live discount/commitment/batch-tier modeling.
- Caching is a single hit-rate × cache-read multiplier — real caches vary by
  query distribution and TTL.
- Self-host break-even uses simplified throughput/utilization assumptions you
  supply; it ignores ops burden and reliability cost.
- This is a **cost** tool — no latency or quality modeling. Pair it with the
  [LLM Eval Harness](https://github.com/jeanmalaquias/llm-eval-harness).

## License

MIT (see [LICENSE](LICENSE)).
