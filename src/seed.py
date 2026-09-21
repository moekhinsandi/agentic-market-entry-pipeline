"""Load the Germany Head of Operations seed fixture for offline runs."""
from __future__ import annotations

import json
from pathlib import Path

from src.schemas.report_schema import (
    MarketScanResult,
    RegulatoryFinding,
    SalaryBenchmark,
)

SEED_ROLE = "Head of Operations"
SEED_MARKET = "Germany"
FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "germany_head_of_operations.json"


def load_seed_payload(path: Path | None = None) -> dict:
    fixture = path or FIXTURE_PATH
    with fixture.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_market_scan(payload: dict | None = None) -> MarketScanResult:
    data = payload or load_seed_payload()
    return MarketScanResult.model_validate(data["market_scan"])


def load_regulatory(payload: dict | None = None) -> list[RegulatoryFinding]:
    data = payload or load_seed_payload()
    return [RegulatoryFinding.model_validate(item) for item in data["regulatory_findings"]]


def load_salaries(payload: dict | None = None) -> list[SalaryBenchmark]:
    data = payload or load_seed_payload()
    return [SalaryBenchmark.model_validate(item) for item in data["salary_benchmarks"]]


def load_caveats(payload: dict | None = None) -> list[str]:
    data = payload or load_seed_payload()
    return list(data.get("caveats", []))
