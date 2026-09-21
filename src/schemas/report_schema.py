"""Structured output schemas.

Every agent must return data that fits one of these models. This is what
makes the pipeline's output machine-readable (JSON) as well as
human-readable (rendered to Markdown) — and forces every claim to carry
a source, so nothing in the final report is unsourced.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class SourcedClaim(BaseModel):
    claim: str
    source: str = Field(
        ...,
        description="URL, dataset name, or 'user-provided, <source>, accessed <date>'",
    )
    confidence: Literal["high", "medium", "low"] = "medium"
    is_synthetic: bool = Field(
        default=False,
        description="Set True for any placeholder/test data. Must never be False for fabricated numbers.",
    )


class TargetEmployer(BaseModel):
    name: str
    industry: str
    sponsorship_signal: str  # e.g. "confirmed sponsor, per careers page"
    notes: str = ""


class RegulatoryFinding(BaseModel):
    threshold_or_rule: str
    value: str
    citation: SourcedClaim


class SalaryBenchmark(BaseModel):
    role_title: str
    market: str
    low: float | None = None
    average: float | None = None
    high: float | None = None
    currency: str = "EUR"
    citation: SourcedClaim


class MarketScanResult(BaseModel):
    target_employers: list[TargetEmployer]
    tam_or_demand: list[SourcedClaim] = Field(default_factory=list)
    funding_landscape: list[SourcedClaim] = Field(default_factory=list)


class MarketEntryReport(BaseModel):
    role: str
    market: str
    generated_at: str
    target_employers: list[TargetEmployer]
    regulatory_findings: list[RegulatoryFinding]
    salary_benchmarks: list[SalaryBenchmark]
    key_findings: list[SourcedClaim]
    caveats: list[str]
    tam_or_demand: list[SourcedClaim] = Field(default_factory=list)
    funding_landscape: list[SourcedClaim] = Field(default_factory=list)
    run_mode: str = "offline"
