"""
Premium CPWD Copilot — builds structured context for review/draft agents.

Bundles guideline snapshot (contract columns), recent compliance rows for the
working version, scoring summary, and optionally saved workspace review items
(Draft only — Review omits saved items so responses are not anchored to prior
saved review rows).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import models
from app.services.guideline_contract import GUIDELINE_SECTION_KEYS


_SCORING_CONTRACT_TEXT_MAX = 12000


def _parse_scoring_result_json(result_json: Any) -> Optional[dict[str, Any]]:
    """Normalize DB JSON (dict) or legacy string payloads into a dict."""
    if result_json is None:
        return None
    if isinstance(result_json, dict):
        return result_json
    if isinstance(result_json, str):
        s = result_json.strip()
        if not s:
            return None
        # Strip optional leading markdown title line (see demo result.json)
        lines = s.split("\n", 1)
        if lines and lines[0].lstrip().startswith("#"):
            s = lines[1].strip() if len(lines) > 1 else ""
        if not s:
            return None
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None
    return None


def _format_scoring_result_for_prompt(data: dict[str, Any]) -> str:
    """Turn multi-agent scoring JSON into readable sections for the LLM."""
    sections: list[str] = []

    meta = data.get("contract_metadata")
    if isinstance(meta, dict) and meta:
        lines = [f"- {k.replace('_', ' ')}: {v}" for k, v in meta.items() if v is not None]
        sections.append("### Contract metadata\n" + "\n".join(lines))

    ctext = data.get("contract_text")
    if isinstance(ctext, str) and ctext.strip():
        body = ctext.strip()
        if len(body) > _SCORING_CONTRACT_TEXT_MAX:
            body = (
                body[:_SCORING_CONTRACT_TEXT_MAX]
                + f"\n\n… (truncated; {len(ctext)} characters total)"
            )
        sections.append("### Extracted contract text\n" + body)

    classifications = data.get("classifications")
    if isinstance(classifications, dict) and classifications:
        cl_parts: list[str] = []
        for key, block in classifications.items():
            if not isinstance(block, dict):
                continue
            title = str(key).replace("_", " ").title()
            sub: list[str] = [f"#### {title}"]
            if block.get("priority"):
                sub.append(f"- Priority: {block['priority']}")
            secs = block.get("contract_sections")
            if isinstance(secs, list) and secs:
                sub.append("- Contract sections: " + ", ".join(str(x) for x in secs))
            vf = block.get("validation_focus")
            if isinstance(vf, list) and vf:
                sub.append("- Validation focus:")
                sub.extend(f"  - {x}" for x in vf if x)
            cl_parts.append("\n".join(sub))
        sections.append("### Agent validation plans (classifications)\n" + "\n\n".join(cl_parts))

    results = data.get("validation_results")
    if isinstance(results, list) and results:
        vr_parts: list[str] = []
        for block in results:
            if not isinstance(block, dict):
                continue
            agent = block.get("agent_type") or "unknown_agent"
            vr_parts.append(f"#### {agent}")
            if block.get("overall_score") is not None:
                vr_parts.append(f"- Overall score: {block['overall_score']}")
            if block.get("compliance_status"):
                vr_parts.append(f"- Compliance status: {block['compliance_status']}")
            cs = block.get("category_scores")
            if isinstance(cs, dict) and cs:
                vr_parts.append("- Category scores:")
                for ck, cv in cs.items():
                    vr_parts.append(f"  - {str(ck).replace('_', ' ')}: {cv}")
            crit = block.get("critical_issues")
            if isinstance(crit, list) and crit:
                vr_parts.append("- Critical issues:")
                for it in crit:
                    if isinstance(it, dict):
                        msg = it.get("issue") or it.get("description") or ""
                        cat = it.get("category", "")
                        imp = it.get("impact") or it.get("severity", "")
                        extra = " | ".join(x for x in (cat, imp) if x)
                        vr_parts.append(f"  - {msg}" + (f" ({extra})" if extra else ""))
                    else:
                        vr_parts.append(f"  - {it}")
            findings = block.get("findings")
            if isinstance(findings, list) and findings:
                vr_parts.append("- Findings:")
                for f in findings[:50]:
                    if not isinstance(f, dict):
                        vr_parts.append(f"  - {f}")
                        continue
                    if "issue" in f:
                        cat = f.get("category", "")
                        sev = f.get("severity", "")
                        imp = f.get("score_impact")
                        tail = ", ".join(
                            str(x)
                            for x in (f"category={cat}" if cat else "", f"severity={sev}" if sev else "")
                            if x
                        )
                        if imp is not None:
                            tail = f"{tail}, score_impact={imp}" if tail else f"score_impact={imp}"
                        line = f.get("issue", "")
                        vr_parts.append(f"  - {line}" + (f" ({tail})" if tail else ""))
                    elif "finding" in f:
                        cat = f.get("category", "")
                        comp = f.get("compliance", "")
                        line = f.get("finding", "")
                        tail = ", ".join(x for x in (cat, comp) if x)
                        vr_parts.append(f"  - {line}" + (f" ({tail})" if tail else ""))
                    else:
                        sub = _flatten_value(f, max_depth=3)
                        vr_parts.append(f"  - {'; '.join(sub) if sub else str(f)}")
                if len(findings) > 50:
                    vr_parts.append(f"  - … ({len(findings) - 50} more findings omitted)")
            recs = block.get("recommendations")
            if isinstance(recs, list) and recs:
                vr_parts.append("- Recommendations:")
                for i, r in enumerate(recs[:40], 1):
                    vr_parts.append(f"  {i}. {r}")
                if len(recs) > 40:
                    vr_parts.append(f"  … ({len(recs) - 40} more omitted)")
            vd = block.get("validation_details")
            if isinstance(vd, dict) and vd:
                vr_parts.append("- Validation details:")
                vr_parts.extend(f"  - {k.replace('_', ' ')}: {v}" for k, v in vd.items())
        sections.append("### Validation results by agent\n" + "\n\n".join(vr_parts))

    fin = data.get("finance_analysis")
    if isinstance(fin, dict) and fin:
        fp: list[str] = ["### Financial analysis (CPWD)"]
        for k in (
            "overall_compliance_score",
            "financial_risk_rating",
            "approval_recommendation",
        ):
            if fin.get(k) is not None:
                fp.append(f"- {k.replace('_', ' ')}: {fin[k]}")
        if fin.get("executive_summary"):
            fp.append(f"- Executive summary: {fin['executive_summary']}")
        cond = fin.get("conditions_for_approval")
        if isinstance(cond, list) and cond:
            fp.append("- Conditions for approval:")
            fp.extend(f"  - {x}" for x in cond)
        fci = fin.get("critical_issues")
        if isinstance(fci, list) and fci:
            fp.append("- Financial critical issues:")
            for it in fci:
                if isinstance(it, dict):
                    fp.append(
                        f"  - [{it.get('issue_type', '')}] {it.get('description', '')}"
                    )
                else:
                    fp.append(f"  - {it}")
        frec = fin.get("recommendations")
        if isinstance(frec, list) and frec:
            fp.append("- Financial recommendations:")
            for it in frec[:25]:
                if isinstance(it, dict):
                    cat = it.get("category", "")
                    pri = it.get("priority", "")
                    rec = it.get("recommendation", "")
                    impl = it.get("implementation", "")
                    line = rec
                    if impl:
                        line = f"{rec} — {impl}"
                    fp.append(f"  - [{cat}] ({pri}) {line}" if cat or pri else f"  - {line}")
                else:
                    fp.append(f"  - {it}")
        cd = fin.get("compliance_details")
        if isinstance(cd, dict) and cd:
            fp.append("- Compliance detail keys: " + ", ".join(sorted(cd.keys())))
        sections.append("\n".join(fp))

    cross = data.get("cross_validation_result")
    if isinstance(cross, dict) and cross:
        flat = _flatten_value(cross, max_depth=4)
        if flat:
            sections.append("### Cross-validation\n" + "\n".join(flat))

    if not sections:
        # Fallback: shallow flatten if schema differs
        return "\n".join(_flatten_value(data, max_depth=4)) or "(empty scoring payload)"

    return "\n\n".join(sections)


def _flatten_value(val: Any, depth: int = 0, max_depth: int = 5) -> list[str]:
    lines: list[str] = []
    if depth > max_depth:
        return lines
    if val is None:
        return lines
    if isinstance(val, (str, int, float, bool)):
        t = str(val).strip()
        if t:
            lines.append(t)
        return lines
    if isinstance(val, list):
        for item in val:
            lines.extend(_flatten_value(item, depth + 1, max_depth))
        return lines
    if isinstance(val, dict):
        for k, v in val.items():
            sub = _flatten_value(v, depth + 1, max_depth)
            if sub:
                label = str(k).replace("_", " ")
                if len(sub) == 1:
                    lines.append(f"- {label}: {sub[0]}")
                else:
                    lines.append(f"- {label}:")
                    lines.extend(f"  {x}" for x in sub[:40])
        return lines
    return lines


def build_cpwd_copilot_augmentation(
    db: Session,
    *,
    contract_id: int,
    version_id: Optional[int] = None,
    include_saved_review_items: bool = True,
) -> str:
    """Return a single text block for the LLM (empty if contract missing)."""
    c = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not c:
        return ""

    parts: list[str] = []

    fw = c.guideline_framework_title or c.guideline_framework_slug or "none"
    parts.append(f"## Attached guideline framework\n- Title/slug: {fw}")

    g_lines: list[str] = []
    for key in GUIDELINE_SECTION_KEYS:
        col = f"guideline_{key}"
        body = getattr(c, col, None)
        if body is None:
            continue
        g_lines.append(f"### {key.replace('_', ' ').title()}")
        g_lines.extend(_flatten_value(body))
    if g_lines:
        parts.append("## Guideline snapshot (structured)\n" + "\n".join(g_lines))
    else:
        parts.append("## Guideline snapshot\n(No guideline sections stored on this contract.)")

    q = db.query(models.ComplianceRecord).filter(models.ComplianceRecord.contract_id == contract_id)
    if version_id is not None:
        q = q.filter(
            (models.ComplianceRecord.document_version_id == version_id)
            | (models.ComplianceRecord.document_version_id.is_(None))
        )
    recs = q.order_by(models.ComplianceRecord.created_at.desc()).limit(40).all()
    if recs:
        clines = []
        for r in recs:
            fn = (r.findings or "").replace("\n", " ").strip()
            clines.append(f"- [{r.status}] {r.check_name}: {fn}")
        parts.append("## Recent compliance checks (this version when possible)\n" + "\n".join(clines))
    else:
        parts.append("## Compliance checks\n(No compliance records found.)")

    sq = (
        db.query(models.ScoringResult)
        .filter(models.ScoringResult.contract_id == contract_id)
        .order_by(models.ScoringResult.created_at.desc())
    )
    if version_id is not None:
        sq = sq.filter(
            (models.ScoringResult.document_version_id == version_id)
            | (models.ScoringResult.document_version_id.is_(None))
        )
    score = sq.first()
    parsed = _parse_scoring_result_json(getattr(score, "result_json", None) if score else None)
    if parsed is not None:
        structured = _format_scoring_result_for_prompt(parsed)
        parts.append("## Latest multi-agent scoring (structured summary)\n" + structured)
    elif score and score.result_json is not None:
        try:
            fallback = str(score.result_json)
        except Exception:
            fallback = "(unreadable scoring payload)"
        parts.append("## Latest multi-agent scoring (raw)\n" + fallback[:20000])
    else:
        parts.append("## Multi-agent scoring\n(No scoring result stored.)")

    if include_saved_review_items:
        riv = (
            db.query(models.ReviewItem)
            .filter(models.ReviewItem.contract_id == contract_id)
            .order_by(models.ReviewItem.created_at.desc())
            .limit(15)
            .all()
        )
        if riv:
            rlines = []
            for it in riv:
                body = (it.content or "").replace("\n", " ").strip()
                sev = f" [{it.severity}]" if it.severity else ""
                rlines.append(f"- ({it.item_type}){sev} {it.title or 'Item'}: {body}")
            parts.append("## Saved review items (workspace)\n" + "\n".join(rlines))

    return "\n\n".join(parts)
