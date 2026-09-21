"""Pipeline orchestrator.

Usage:
    python -m src.pipeline --role "Head of Operations" --market "Germany"
    python -m src.pipeline --role "Head of Operations" --market "Germany" --offline

Runs the three research agents, merges results into a MarketEntryReport,
and writes both a Markdown brief and a JSON file to sample_output/.
"""
from __future__ import annotations

import argparse
import time

from src.agents.market_scanner import scan_market
from src.agents.regulatory_agent import check_regulatory
from src.agents.report_builder import build_report, save_report
from src.agents.salary_benchmark_agent import benchmark_salary
from src.config import config
from src.mcp_client import format_search_context, search_public_sources
from src.schemas.report_schema import (
    MarketScanResult,
    RegulatoryFinding,
    SalaryBenchmark,
    SourcedClaim,
)
from src.seed import SEED_MARKET, SEED_ROLE, load_caveats

DEFAULT_CAVEATS = [
    "Salary figures are market aggregates; treat as ranges, not guarantees.",
    "Regulatory classification should be confirmed with the employer and immigration counsel.",
]


def derive_key_findings(
    scan: MarketScanResult,
    regulatory: list[RegulatoryFinding],
    salaries: list[SalaryBenchmark],
) -> list[SourcedClaim]:
    """Pull the first high-signal claims from each agent into a top-line list."""
    findings: list[SourcedClaim] = []
    findings.extend(scan.tam_or_demand[:2])
    for item in regulatory[:2]:
        findings.append(item.citation)
    if salaries:
        findings.append(salaries[0].citation)
    findings.extend(scan.funding_landscape[:1])
    return findings


def run(
    role: str,
    market: str,
    *,
    offline: bool = False,
    output_dir: str | None = None,
    stem: str | None = None,
) -> tuple[str, str, float]:
    started = time.time()
    use_offline = offline or not config.has_api_key()
    if use_offline:
        if (role, market) != (SEED_ROLE, SEED_MARKET):
            print(
                f"Offline mode uses the {SEED_MARKET} / {SEED_ROLE} seed fixture; "
                f"ignoring requested role={role!r} market={market!r}."
            )
        role, market = SEED_ROLE, SEED_MARKET
        run_mode = "offline"
        print(f"[1/4] Loading seed employers for '{role}' in {market}...")
        scan = scan_market(role, market, offline=True)
        print("[2/4] Loading seed regulatory/visa thresholds...")
        regulatory = check_regulatory(role, market, offline=True)
        print("[3/4] Loading seed salary ranges...")
        salaries = benchmark_salary(role, market, offline=True)
        caveats = load_caveats() or DEFAULT_CAVEATS
    else:
        config.validate()
        run_mode = "live"
        print(f"[1/4] Scanning target employers for '{role}' in {market}...")
        search_context = format_search_context(
            search_public_sources(f"{role} {market} visa salary employers funding")
        )
        scan = scan_market(role, market, search_context=search_context)
        print("[2/4] Checking regulatory/visa thresholds...")
        regulatory = check_regulatory(role, market, search_context=search_context)
        print("[3/4] Benchmarking salary ranges...")
        salaries = benchmark_salary(role, market, search_context=search_context)
        caveats = list(DEFAULT_CAVEATS)

    print("[4/4] Building report...")
    key_findings = derive_key_findings(scan, regulatory, salaries)
    report = build_report(
        role,
        market,
        scan,
        regulatory,
        salaries,
        key_findings,
        caveats,
        run_mode=run_mode,
    )
    if use_offline and stem is None:
        stem = f"{market}_{role}".replace(" ", "_")
    md_path, json_path = save_report(report, output_dir or config.output_dir, stem=stem)
    return md_path, json_path, round(time.time() - started, 2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", default=SEED_ROLE, help='e.g. "Head of Operations"')
    parser.add_argument("--market", default=SEED_MARKET, help='e.g. "Germany"')
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the Germany seed fixture (no API key required).",
    )
    args = parser.parse_args()
    md_path, json_path, elapsed = run(args.role, args.market, offline=args.offline)
    print(f"\nDone in {elapsed}s. Report saved to:\n  {md_path}\n  {json_path}")
    print("Log this run time against a manual-research baseline for your portfolio README.")


if __name__ == "__main__":
    main()
