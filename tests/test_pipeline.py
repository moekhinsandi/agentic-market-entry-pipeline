"""Tests: schema validation, JSON parse, offline pipeline, SYNTHETIC rendering.

Start with schema validation tests (fast, no API calls), then add
integration tests that mock the Anthropic client for the agents.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.agents.report_builder import build_report, render_markdown
from src.llm import JsonParseError, extract_json, parse_as
from src.pipeline import run
from src.schemas.report_schema import MarketEntryReport, SourcedClaim
from src.seed import load_market_scan, load_regulatory, load_salaries


def test_sourced_claim_requires_source():
    claim = SourcedClaim(claim="Test claim", source="https://example.com")
    assert claim.confidence == "medium"
    assert claim.is_synthetic is False


def test_sourced_claim_missing_source_raises():
    with pytest.raises(ValidationError):
        SourcedClaim(claim="Unsourced number")  # type: ignore[call-arg]


def test_market_entry_report_minimal():
    report = MarketEntryReport(
        role="Head of Operations",
        market="Germany",
        generated_at="2026-01-01",
        target_employers=[],
        regulatory_findings=[],
        salary_benchmarks=[],
        key_findings=[],
        caveats=["Test caveat"],
    )
    assert report.role == "Head of Operations"
    assert report.tam_or_demand == []
    assert report.funding_landscape == []
    assert report.run_mode == "offline"


def test_extract_json_from_fenced_block():
    payload = extract_json('Here you go:\n```json\n{"claim": "ok", "source": "https://x"}\n```')
    assert payload["claim"] == "ok"


def test_parse_as_sourced_claim():
    parsed = parse_as(
        '{"claim": "Threshold is 50700", "source": "https://example.com", "confidence": "high"}',
        SourcedClaim,
    )
    assert parsed.confidence == "high"
    assert parsed.source.startswith("https://")


def test_parse_as_rejects_invalid_payload():
    with pytest.raises(JsonParseError):
        parse_as("not json at all", SourcedClaim)


def test_seed_fixture_validates():
    scan = load_market_scan()
    assert len(scan.target_employers) >= 8
    assert scan.tam_or_demand
    assert scan.funding_landscape
    assert load_regulatory()
    salaries = load_salaries()
    assert any(item.citation.is_synthetic for item in salaries)
    assert any(not item.citation.is_synthetic for item in salaries)


def test_synthetic_flag_rendered_in_markdown():
    report = build_report(
        role="Head of Operations",
        market="Germany",
        employers=[],
        regulatory=[],
        salaries=[],
        key_findings=[
            SourcedClaim(
                claim="Placeholder wage band",
                source="SYNTHETIC",
                is_synthetic=True,
            )
        ],
        caveats=["Test"],
    )
    markdown = render_markdown(report)
    assert "**(SYNTHETIC)**" in markdown
    assert "Placeholder wage band" in markdown


def test_offline_pipeline_writes_markdown_and_json(tmp_path: Path):
    md_path, json_path, _ = run(
        "Head of Operations",
        "Germany",
        offline=True,
        output_dir=str(tmp_path),
        stem="Germany_Head_of_Operations",
    )
    markdown = Path(md_path).read_text(encoding="utf-8")
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    assert "Market-Entry Brief" in markdown
    assert "**(SYNTHETIC)**" in markdown
    assert payload["role"] == "Head of Operations"
    assert payload["market"] == "Germany"
    assert payload["run_mode"] == "offline"
    assert payload["target_employers"]
    assert payload["regulatory_findings"]
    assert payload["salary_benchmarks"]
    assert payload["key_findings"]


# TODO: add tests that mock anthropic.Anthropic().messages.create() and
# assert each agent correctly parses a sample JSON response into its schema.
