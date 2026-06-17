# LLM Cost Simulator — web

An interactive Next.js 15 calculator: compose a workload, pick a model, slide the
caching and compression levers, and watch the monthly cost and per-model
comparison update live. Shares any scenario as a `?s=...` link.

It computes client-side (so it deploys statically to Vercel with no backend),
mirroring the Python cost engine in [`lib/cost.ts`](lib/cost.ts).

## Pricing data

[`data/catalog.json`](data/catalog.json) mirrors the canonical
[`src/tokenomics/data/catalog.json`](../src/tokenomics/data/catalog.json); the
weekly price-refresh workflow keeps both in sync. Prices are indicative and
dated — see [../docs/methodology.md](../docs/methodology.md).

## Develop

```bash
cd web
npm install
npm run dev      # http://localhost:3000
npm run build    # production build
```

Stack: Next.js 15 (App Router) · React 19 · Recharts · TypeScript.
