// Client-side cost math — mirrors src/tokenomics/estimator.py (_model_monthly_cost).
// Kept in sync intentionally so the demo runs on Vercel without the backend.

export interface ModelPrice {
  id: string;
  provider: string;
  display_name: string;
  input: number;
  output: number;
  source: string;
}

export interface Workload {
  tokens_in: number;
  tokens_out: number;
  requests_per_month: number;
}

export interface Optimization {
  cache_hit_rate: number;
  cache_read_multiplier: number;
  input_reduction: number;
}

const MTOK = 1_000_000;

export const NO_OPT: Optimization = {
  cache_hit_rate: 0,
  cache_read_multiplier: 0.1,
  input_reduction: 0,
};

export function modelMonthly(
  price: ModelPrice,
  wl: Workload,
  opt: Optimization,
): number {
  const effIn = wl.tokens_in * (1 - opt.input_reduction);
  const cached = wl.requests_per_month * opt.cache_hit_rate;
  const uncached = wl.requests_per_month - cached;
  const uncachedCost =
    uncached * ((effIn / MTOK) * price.input + (wl.tokens_out / MTOK) * price.output);
  const cachedCost =
    cached * (effIn / MTOK) * price.input * opt.cache_read_multiplier;
  return uncachedCost + cachedCost;
}

export function encodeScenario(obj: unknown): string {
  const json = JSON.stringify(obj);
  return btoa(unescape(encodeURIComponent(json)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}
