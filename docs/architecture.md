# LLM Cost Simulator — Architecture

> Status: **Design** · Owner: Jean Malaquias · Last updated: 2026-06-16

A tool to estimate and optimize LLM inference cost across providers. This
document is the authoritative design and states the principles the
implementation must hold to.

---

## 1. Problem statement

Inference cost scales linearly with adoption and surprises finance. Teams need
to answer, *before* committing: what will this workload cost on each provider,
how much do caching / compression / routing actually save, and at what volume
does self-hosting beat the API? This tool answers those questions from a
**versioned pricing catalog** and a transparent cost model.

---

## 2. Principles (non-negotiable)

1. **Deterministic core.** The cost engine operates on **explicit token counts**
   the user supplies (tokens in/out per request). It needs no tokenizer and no
   network, so results are reproducible and the test suite is hermetic.
2. **Honesty about data.** Prices change constantly and differ by region,
   commitment, and batch tier. The catalog is therefore:
   - **versioned** (`as_of` date on every snapshot),
   - **sourced** (a `source` URL per model), and
   - **disclaimed** — the methodology page states prices are *indicative* and
     must be verified against the provider's pricing page before any decision.
   The tool never presents a number as authoritative.
3. **Honesty about tokenization.** Exact token counts are provider-specific
   (tiktoken for OpenAI, the Messages `count_tokens` endpoint for Anthropic,
   etc.). The optional `tokens` estimator is a documented *approximation* for
   sizing only; the cost engine itself takes real counts, so tokenizer error
   never silently corrupts a cost estimate.
4. **One source of truth for prices.** Backend and frontend both read the same
   `pricing/catalog.json`. No duplicated price tables.
5. **Typed everything** (Pydantic v2) and **100% tested** core.

---

## 3. Cost model

For a single model and workload:

```
requests        = requests_per_month
input_cost      = requests × tokens_in  / 1e6 × input_price_per_mtok
output_cost     = requests × tokens_out / 1e6 × output_price_per_mtok
monthly_cost    = input_cost + output_cost
```

### Optimization levers (applied to the input/output token stream)

| Lever | Effect |
|-------|--------|
| **Semantic cache** (`hit_rate`) | A `hit_rate` fraction of requests are served from cache: those pay only a small **cache-read** cost on input (configurable multiplier, default 0.1×) and **no output** cost. |
| **Prompt compression** (`input_reduction`) | Multiplies `tokens_in` by `(1 − input_reduction)` on the non-cached path. |
| **Model routing** (`routes`) | Splits traffic by weight across models; total cost is the weighted sum of each route's cost. |

These compose: routing picks the model per slice; within a slice, compression
shrinks input and the cache serves a fraction cheaply.

### Self-host break-even

```
api_cost_per_request        = monthly_cost / requests
self_host_cost_per_hour      = instance_hourly_usd
self_host_requests_per_hour  = throughput_rps × 3600
self_host_cost_per_request   = self_host_cost_per_hour / self_host_requests_per_hour
break_even_requests_per_month = self_host_fixed_monthly / (api_cost_per_request − self_host_cost_per_request)
```

Reported with the explicit assumptions (utilization, throughput) so the reader
can challenge them — the point is the *method*, not a single magic number.

---

## 4. Components

```
backend (Python / FastAPI)
├── pricing/catalog.json     # versioned, sourced, disclaimed
├── catalog.py               # load + validate the catalog
├── workload.py              # Workload, Optimization, Route models
├── estimator.py             # cost engine + optimization + break-even
├── scenario.py              # Scenario model + URL-safe encode/decode (sharing)
├── tokens.py                # optional token estimator (approximation, caveated)
├── api/main.py              # FastAPI endpoints
└── cli.py                   # estimate from a scenario file

frontend (Next.js)
└── an interactive calculator that imports the same catalog.json and mirrors
    the cost formula client-side, so the demo runs on Vercel with no backend.
```

### Sharing

A scenario (workload + optimization + model selection) encodes to a URL-safe
base64 string — `?s=...` — so any scenario is shareable as a link with **no
database**. Named, persisted saves use PostgreSQL in production (out of scope for
the hermetic v1).

---

## 5. Pricing catalog refresh

`pricing/catalog.json` carries `as_of` and a `source` per model. A weekly GitHub
Action (`update-prices.yml`) is the refresh *cadence*: it opens a PR for a human
to verify against the providers' pricing pages. Prices are not blindly scraped —
a wrong auto-scrape is worse than a known-stale catalog with a visible date.

---

## 6. Testing

- Cost engine, optimization, break-even, scenario encode/decode, catalog load,
  token estimator, API, CLI — all unit-tested, hermetic, 100% target.
- Frontend build verified with `next build`.
