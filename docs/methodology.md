# Methodology & limitations

This tool is a **decision aid, not a billing oracle.** Read this before trusting
a number.

## Where prices come from

`pricing/catalog.json` holds per-model input/output prices in USD per million
tokens. Every entry carries a `source` URL (the provider's public pricing page)
and the catalog carries an `as_of` date. The shipped values are list prices for
standard (non-batch, on-demand) usage in a primary region.

**Verify before deciding.** Prices change frequently and vary by:

- region,
- committed-use / enterprise discounts,
- batch vs. real-time tiers,
- prompt-caching read/write rates,
- context-length tiers.

The catalog is a starting point with a visible date — not a contract. The
`update-prices.yml` workflow opens a refresh PR weekly for a human to confirm.

## How cost is computed

The cost engine takes **explicit token counts** you provide (tokens in/out per
request) and a request volume. It does not guess your tokens. The formula and
the optimization levers (semantic cache, prompt compression, model routing) and
the self-host break-even are specified in
[architecture.md](architecture.md) §3. The math is deliberately simple and
transparent so you can audit every number.

## On tokenization (the 2% question)

Exact token counts are **provider-specific**: OpenAI uses `tiktoken`, Anthropic
exposes a `count_tokens` endpoint, Google/Vertex has its own tokenizer. Counts
for the same text differ across providers, sometimes materially for code or
non-English text.

Because of that, the cost engine **takes token counts as input** rather than
deriving them — so tokenizer error can never silently distort a cost estimate.
The optional `tokens.estimate_tokens()` helper is a **rough approximation**
(calibrated chars-per-token) for back-of-envelope sizing only. For
billing-grade counts, call the provider's real tokenizer/endpoint and feed those
numbers in. The helper documents its expected error band and does not claim
parity.

## Known limitations

- Static list prices; no live discount/commitment modeling.
- Caching is modeled as a single hit-rate with a cache-read multiplier — real
  semantic caches vary by query distribution and TTL.
- Self-host break-even uses simplified throughput/utilization assumptions that
  you supply; it ignores ops burden, cold starts, and reliability cost.
- No latency or quality modeling — this is a *cost* tool. Pair it with an eval
  harness for the quality side of the tradeoff.
