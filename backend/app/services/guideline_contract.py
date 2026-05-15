"""Map guideline library snapshots ↔ Contract ORM columns (AI automation)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

# Keys must match `guideline_sections.section_key` / seed JSON top-level keys.
GUIDELINE_SECTION_KEYS: tuple[str, ...] = (
    "financial_limits",
    "mandatory_clauses",
    "technical_standards",
    "compliance_requirements",
    "contractor_eligibility",
    "work_execution_standards",
    "measurement_payment",
    "contract_administration",
    "defect_liability",
    "documentation_requirements",
    "decision_thresholds",
    "validation_weights",
    "critical_issues",
)


def gl_column_name(section_key: str) -> str:
    return f"gl_{section_key}"


def apply_guideline_snapshot(contract: Any, snap: Optional[dict]) -> None:
    """Write a bundle-style snapshot dict onto Contract columns."""
    if not snap or not isinstance(snap, dict):
        return
    slug = snap.get("framework_slug")
    if slug is not None:
        contract.guideline_framework_slug = slug
    if snap.get("framework_title") is not None:
        contract.guideline_framework_title = snap.get("framework_title")
    if snap.get("framework_version_label") is not None:
        contract.guideline_framework_version_label = snap.get("framework_version_label")
    if snap.get("framework_summary") is not None:
        contract.guideline_framework_summary = snap.get("framework_summary")
    loaded = snap.get("loaded_at")
    if loaded:
        try:
            if isinstance(loaded, str):
                contract.guideline_loaded_at = datetime.fromisoformat(loaded.replace("Z", "+00:00"))
            elif isinstance(loaded, datetime):
                contract.guideline_loaded_at = loaded
        except Exception:
            contract.guideline_loaded_at = datetime.utcnow()
    if snap.get("catalog") is not None:
        contract.guideline_catalog = snap.get("catalog")

    for sec in snap.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        key = sec.get("section_key")
        body = sec.get("body")
        if key in GUIDELINE_SECTION_KEYS and hasattr(contract, gl_column_name(key)):
            setattr(contract, gl_column_name(key), body)


def contract_to_guideline_snapshot(contract: Any) -> dict:
    """Rebuild API-friendly snapshot from Contract columns (for editors / export)."""
    sections = []
    for key in GUIDELINE_SECTION_KEYS:
        col = gl_column_name(key)
        body = getattr(contract, col, None)
        if body is not None:
            sections.append({"section_key": key, "title": key.replace("_", " ").title(), "body": body})
    return {
        "framework_slug": getattr(contract, "guideline_framework_slug", None),
        "framework_title": getattr(contract, "guideline_framework_title", None),
        "framework_version_label": getattr(contract, "guideline_framework_version_label", None),
        "framework_summary": getattr(contract, "guideline_framework_summary", None),
        "loaded_at": (
            contract.guideline_loaded_at.isoformat()
            if getattr(contract, "guideline_loaded_at", None)
            else None
        ),
        "sections": sections,
        "catalog": getattr(contract, "guideline_catalog", None),
    }
