# LLM Cost Simulator

> Estimate and optimize LLM inference cost across providers. Compose a workload,
> compare providers from a **versioned, sourced** pricing catalog, simulate
> **semantic caching / prompt compression / model routing**, find the
> **self-host break-even**, and share any scenario as a URL.

<!-- Badges placeholder: CI, license, coverage -->

---

## Honesty first

Prices change constantly and tokenization is provider-specific, so this is a
**decision aid, not a billing oracle**. The pricing catalog is versioned
(`as_of` date), sourced (a URL per model), and disclaimed; the cost engine works
on **token counts you provide**, never guessed. Read
[docs/methodology.md](docs/methodology.md) before trusting a number.

## What it does

- **Workload composer** — tokens in/out per request × request volume.
- **Provider catalog** — top models across OpenAI, Anthropic, Azure, AWS, Google
  in one [versioned JSON](src/tokenomics/data/catalog.json).
- **Optimization simulator** — semantic cache hit-rate, prompt compression %, and
  weighted model routing, composed.
- **Self-host break-even** — API $/request vs. a GPU instance, with explicit
  assumptions.
- **Shareable scenarios** — every scenario encodes to a `?s=...` URL; no database
  needed.

## Quick start

```bash
pip install -e ".[dev]"

# Estimate a scenario
llmcost estimate examples/scenario.yaml

# Serve the API
uvicorn tokenomics.api.main:app --port 8086

# Interactive calculator (Vercel-ready)
cd web && npm install && npm run dev
```

## Architecture

See [docs/architecture.md](docs/architecture.md) — cost model, optimization
levers, and break-even formulas.

## Status

- [ ] Versioned pricing catalog + loader
- [ ] Cost engine + optimization + break-even
- [ ] Scenario encode/decode (shareable URLs)
- [ ] Token estimator (approximation, caveated)
- [ ] FastAPI surface + CLI
- [ ] Next.js interactive calculator
- [ ] CI + weekly price-refresh workflow

## License

MIT (see [LICENSE](LICENSE)).
