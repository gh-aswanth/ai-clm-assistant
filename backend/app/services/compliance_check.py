"""
LLM-based compliance checks from stored ``document_chunks`` (per ``file_id``).

Structured output is persisted as ``ComplianceRecord`` rows (``record_type='compliance'``).

Flow: load prior ``compliance`` rows into the prompt when rerunning; generate from chunks (LLM) first; \
only then delete previous rows and insert the new set in one transaction so failures leave existing data intact. \
Successful runs append a ``Milestone`` (``Compliance checks updated``) for audit.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.models import ComplianceRecord, DocumentVersion, Milestone
from app.services.document_chunker import get_chunks_for_file

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHARS = 120_000
MAX_PREVIOUS_COMPLIANCE_CHARS = 14_000

COMPLIANCE_SYSTEM_PROMPT = """\
You are a contract compliance analyst specialising in PWD (Public Works Department) construction and works contracts governed by Indian law. You receive the contract text split \
into numbered chunks ([Chunk index=N] prefixes). Each chunk is verbatim excerpt text from the document.

When a "Previous compliance snapshot" section appears above the document text, treat it as the last \
saved run for this contract. Use it to keep check names stable where still applicable, spot material \
changes versus the current document, and reflect updates in status/findings. The authoritative \
evidence is always the current chunks; the snapshot is for continuity and diff-style reasoning only.

You MUST evaluate ONLY the following 20 PWD compliance categories — do not add, remove, or rename \
them. Produce exactly one check row per category (check_name must match the label exactly as listed):

 1. Contract Sum & Payment Terms
    Verify the contract sum is clearly stated; confirm progress payment schedule, payment certificate \
    period, and any milestone-based payment triggers.

 2. Performance Bond / Security Deposit
    Confirm a performance bond or security deposit is required (typically 5 % of contract sum); \
    verify the form (bank guarantee / insurance bond), validity period, and release conditions.

 3. Advance Payment
    Check whether an advance payment is provided (typically up to 10 % of contract sum); verify the \
    advance payment bond / guarantee and repayment/recovery schedule.

 4. Retention Money
    Confirm retention deduction rate (typically 5 % capped at 5 % of contract sum); verify \
    half-release on practical completion and balance release on Defects Liability Period expiry.

 5. Liquidated & Ascertained Damages (LAD)
    Verify LAD rate is stated (RM/day or % per week), identify the cap amount if any, and confirm \
    the trigger conditions (failure to complete by completion date).

 6. Defects Liability Period (DLP)
    Confirm DLP duration (minimum 12 months under PWD 203/203A); verify commencement trigger \
    (date of practical completion) and contractor obligations during DLP.

 7. Completion Period & Milestone Schedule
    Confirm the contract period / completion date is stated; check for a programme of works or \
    milestone schedule requirement and notice-to-commence provisions.

 8. Extension of Time (EOT)
    Verify EOT grounds (force majeure, variation, employer delay, etc.); confirm notice period \
    requirement (typically 28 days) and the Engineer/S.O. decision timeline.

 9. Variation Orders (VO)
    Confirm the VO procedure, authority levels for approval, pricing mechanism (BQ rates / \
    daywork), and any cap on total variations (commonly ± 10–20 % of original contract sum).

10. Sub-Contracting & Nominated Sub-Contractors
    Check sub-contracting restrictions (employer written consent required); identify nominated \
    sub-contractors / suppliers and domestic sub-contractor obligations.

11. Insurance Requirements
    Verify that Contractor's All Risk (CAR), Third-Party / Public Liability, and Workmen's \
    Compensation / SOCSO insurance are required; confirm minimum cover amounts and endorsements.

12. Health, Safety & Environment (HSE)
    Confirm HSE Plan / Method Statement requirement; check OSHA 1994 compliance clause, site \
    safety obligations, and environmental protection conditions.

13. CIDB Registration & Statutory Compliance
    Verify CIDB contractor registration grade is stated and appropriate for contract value; confirm \
    CIDB Levy (0.125 % of contract sum) obligation and EPF / SOCSO compliance for workers.

14. Quality Assurance & Testing
    Confirm QA/QC plan or quality management system requirement; verify testing, inspection, and \
    material approval procedures.

15. Force Majeure
    Verify force majeure is defined; confirm notice period, relief scope (time and/or cost), and \
    termination rights if force majeure persists beyond a stated period.

16. Termination Clauses
    Confirm termination-for-default grounds (abandonment, persistent breach, insolvency) and \
    termination-for-convenience provisions; verify consequences (measurement, payment, contractor \
    obligations on termination).

17. Dispute Resolution — Adjudication & Arbitration
    Confirm that adjudication under CIPAA 2012 is preserved; verify arbitration clause (scope, \
    seat, rules) and any tiered dispute-resolution escalation.

18. Governing Law & Jurisdiction
    Confirm Malaysian law governs; verify jurisdiction clause (Malaysian courts) and language of \
    contract requirement.

19. Indemnity & Limitation of Liability
    Check indemnity obligations (contractor indemnifies employer against third-party claims); verify \
    whether a liability cap applies and its amount or formula.

20. Contractual Notices & Communication
    Confirm notice provisions (form, address, deemed-receipt period); verify language requirements \
    and the authorised representative / Superintending Officer (S.O.) identification.

Rules:
- Evaluate ALL 20 categories above — do not skip any. If the document is silent on a category, \
return status=warning with findings explaining it was not found or not addressed.
- status must be one of: passed, failed, warning (lowercase).
  * passed  — the requirement is clearly and adequately addressed in the contract.
  * failed  — the requirement is missing, contradicts a mandatory PWD/statutory obligation, or \
    poses an unacceptable risk.
  * warning — the requirement is partially addressed, ambiguous, or cannot be confirmed from the \
    available text.
- check_name must match the category label EXACTLY as listed (e.g. "Retention Money", \
"Liquidated & Ascertained Damages (LAD)") — do not paraphrase.
- chunk_index: the integer N from the "[Chunk index=N]" line for the primary evidence chunk; \
null only if no single chunk applies.
- page_number: 1-based PDF page estimate if inferable; null otherwise.
- findings: 1–3 concise sentences citing the contract clause or the absence thereof; note material \
changes vs the prior snapshot where relevant.
"""


class ComplianceCheckItem(BaseModel):
    check_name: str = Field(description="Short label for the compliance check")
    status: Literal["passed", "failed", "warning"] = Field(
        description="passed | failed | warning"
    )
    findings: str = Field(description="Brief explanation citing what in the contract supports this")
    chunk_index: Optional[int] = Field(
        default=None,
        description="The N from [Chunk index=N] for the primary evidence chunk, or null",
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Approximate 1-based page number if inferable, else null",
    )


class ComplianceChecksResponse(BaseModel):
    checks: list[ComplianceCheckItem] = Field(
        default_factory=list,
        description="Exactly 20 PWD compliance check rows, one per required category",
    )


def _format_previous_compliance_snapshot(
    db: Session, contract_id: int, document_version_id: int
) -> str:
    """Return a text block of existing compliance rows for this version (prompt context)."""
    rows = (
        db.query(ComplianceRecord)
        .filter(
            ComplianceRecord.contract_id == contract_id,
            ComplianceRecord.record_type == "compliance",
            ComplianceRecord.document_version_id == document_version_id,
        )
        .order_by(ComplianceRecord.id)
        .all()
    )
    if not rows:
        return ""

    lines: list[str] = []
    for r in rows:
        pg = str(r.page_number) if r.page_number is not None else "—"
        findings = (r.findings or "").replace("\r\n", " ").replace("\n", " ").strip()
        if len(findings) > 600:
            findings = findings[:597] + "..."
        ci = str(r.chunk_index) if getattr(r, "chunk_index", None) is not None else "—"
        lines.append(f"- {r.check_name} | status={r.status} | chunk={ci} | page={pg} | findings: {findings}")

    text = "\n".join(lines)
    if len(text) > MAX_PREVIOUS_COMPLIANCE_CHARS:
        text = text[: MAX_PREVIOUS_COMPLIANCE_CHARS - 40] + "\n[... previous snapshot truncated ...]"
    return text


def _build_chunk_document_text(db: Session, file_id: int, max_chars: int) -> tuple[str, bool]:
    """Join chunk content up to ``max_chars``; returns (text, truncated)."""
    chunks = get_chunks_for_file(db, file_id)
    if not chunks:
        return "", False

    parts: list[str] = []
    total = 0
    truncated = False
    for c in chunks:
        header = f"[Chunk index={c.chunk_index}]\n"
        piece = header + (c.content or "")
        if total + len(piece) > max_chars:
            truncated = True
            remain = max_chars - total
            if remain > len(header):
                parts.append(piece[:remain])
            break
        parts.append(piece)
        total += len(piece)

    body = "\n\n".join(parts)
    if truncated:
        body += "\n\n[Document context truncated for length; prioritize findings from the text above.]"
    return body, truncated


def record_compliance_run_milestone(
    db: Session,
    contract_id: int,
    file_id: int,
    *,
    count: int,
    trigger: str,
    version_id: Optional[int] = None,
) -> None:
    """Append a completed milestone for an automated compliance run (commits its own transaction)."""
    ver_label = ""
    if version_id is not None:
        ver = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
        if ver and ver.contract_id == contract_id:
            ver_label = f"v{ver.version_number}"
    if not ver_label:
        ver = (
            db.query(DocumentVersion)
            .filter(
                DocumentVersion.contract_id == contract_id,
                DocumentVersion.file_id == file_id,
            )
            .order_by(DocumentVersion.version_number.desc())
            .first()
        )
        if ver:
            ver_label = f"v{ver.version_number}"

    parts = [f"Trigger: {trigger}.", f"File #{file_id}."]
    if ver_label:
        parts.append(f"Document version {ver_label}.")
    parts.append(f"{count} automated compliance check(s) saved.")
    desc = " ".join(parts)

    db.add(
        Milestone(
            contract_id=contract_id,
            title="Compliance checks updated",
            description=desc,
            due_date=datetime.utcnow(),
            status="completed",
        )
    )
    db.commit()


async def generate_compliance_checks_from_file(
    db: Session,
    file_id: int,
    *,
    contract_id: Optional[int] = None,
    document_version_id: Optional[int] = None,
) -> ComplianceChecksResponse:
    """
    Load ``document_chunks`` for ``file_id`` and return structured LLM output.

    If ``contract_id`` and ``document_version_id`` are set, prior compliance rows for that version \
    are included in the prompt (before the chunk text). Rows are not removed until \
    :func:`replace_compliance_records_atomic` runs after a successful response.

    Raises:
        ValueError: ``no_chunks`` when there is nothing to analyze.
    """
    prev_snapshot = ""
    if contract_id is not None and document_version_id is not None:
        prev_snapshot = _format_previous_compliance_snapshot(db, contract_id, document_version_id)

    prev_block_len = len(prev_snapshot) + (400 if prev_snapshot else 0)
    chunk_budget = max(24_000, MAX_CONTEXT_CHARS - prev_block_len)

    body, truncated = _build_chunk_document_text(db, file_id, chunk_budget)
    if not body.strip():
        raise ValueError("no_chunks")

    if prev_snapshot:
        human_content = (
            "## Previous compliance snapshot (last saved run — compare to current document below)\n\n"
            f"{prev_snapshot}\n\n"
            "## Current document (from stored chunks)\n\n"
            f"{body}"
        )
    else:
        human_content = body

    if truncated and prev_snapshot:
        human_content += (
            "\n\n[Note: document section was truncated; reconcile with snapshot if labels diverge.]"
        )

    llm = ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4")).with_structured_output(ComplianceChecksResponse)
    response: ComplianceChecksResponse = await llm.ainvoke(
        [
            SystemMessage(content=COMPLIANCE_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]
    )
    return response


def replace_compliance_records_atomic(
    db: Session,
    contract_id: int,
    response: ComplianceChecksResponse,
    document_version_id: int,
) -> int:
    """
    Delete existing ``record_type='compliance'`` rows for this contract **and document version**,
    then insert the new set in one transaction.
    """
    try:
        db.query(ComplianceRecord).filter(
            ComplianceRecord.contract_id == contract_id,
            ComplianceRecord.record_type == "compliance",
            ComplianceRecord.document_version_id == document_version_id,
        ).delete(synchronize_session=False)
        for item in response.checks:
            db.add(
                ComplianceRecord(
                    contract_id=contract_id,
                    document_version_id=document_version_id,
                    record_type="compliance",
                    check_name=item.check_name,
                    status=item.status,
                    findings=item.findings,
                    page_number=item.page_number,
                    chunk_index=item.chunk_index,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    n = len(response.checks)
    logger.info(
        "Stored %d compliance record(s) for contract_id=%s document_version_id=%s (atomic replace)",
        n,
        contract_id,
        document_version_id,
    )
    return n


async def extract_and_store_compliance_checks(
    db: Session,
    *,
    contract_id: int,
    file_id: int,
    document_version_id: Optional[int] = None,
) -> int:
    """
    Background path: generate from chunks, then replace rows for the resolved document version.
    On LLM or DB failure returns 0 and leaves existing rows unchanged.
    """
    if document_version_id is None:
        ver = (
            db.query(DocumentVersion)
            .filter(
                DocumentVersion.contract_id == contract_id,
                DocumentVersion.file_id == file_id,
            )
            .order_by(DocumentVersion.version_number.desc())
            .first()
        )
        if not ver:
            logger.warning(
                "No document version for contract_id=%s file_id=%s — skipping compliance",
                contract_id,
                file_id,
            )
            return 0
        document_version_id = ver.id

    try:
        response = await generate_compliance_checks_from_file(
            db,
            file_id,
            contract_id=contract_id,
            document_version_id=document_version_id,
        )
    except ValueError as e:
        if str(e) == "no_chunks":
            logger.info(
                "No document chunks for file_id=%s — skipping compliance (contract_id=%s)",
                file_id,
                contract_id,
            )
            return 0
        raise
    except Exception:
        logger.exception(
            "Compliance LLM failed contract_id=%s file_id=%s",
            contract_id,
            file_id,
        )
        return 0

    try:
        n = replace_compliance_records_atomic(db, contract_id, response, document_version_id)
    except Exception:
        logger.exception(
            "Compliance DB replace failed contract_id=%s file_id=%s",
            contract_id,
            file_id,
        )
        return 0

    try:
        record_compliance_run_milestone(
            db,
            contract_id,
            file_id,
            count=n,
            trigger="Automatic after document indexing (chunking)",
            version_id=document_version_id,
        )
    except Exception:
        logger.exception(
            "Compliance milestone failed contract_id=%s file_id=%s",
            contract_id,
            file_id,
        )
    return n
