"""llmcost CLI: estimate a scenario and compare providers."""

from __future__ import annotations

import argparse
import json

from .catalog import load_catalog
from .estimator import compare_models, estimate
from .scenario import encode_scenario, load_scenario


def _estimate(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    s = load_scenario(args.scenario)
    result = estimate(catalog, s.workload, s.model_id, s.optimization)
    print(json.dumps(result.model_dump(), indent=2))
    print(f"\nPrices as of {catalog.as_of} — {catalog.disclaimer}")
    if args.compare:
        print("\nProvider comparison (naive monthly, cheapest first):")
        for row in compare_models(catalog, s.workload):
            print(f"  {row.monthly:>12,.2f}  {row.display_name}")
    if args.share:
        print(f"\nShare: ?s={encode_scenario(s)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="llmcost")
    sub = parser.add_subparsers(dest="command", required=True)
    est = sub.add_parser("estimate", help="Estimate cost for a scenario YAML.")
    est.add_argument("scenario")
    est.add_argument("--compare", action="store_true", help="Compare all providers.")
    est.add_argument("--share", action="store_true", help="Print a shareable token.")
    est.set_defaults(func=_estimate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
