"""WebSocket-driven document comparison: extract text from two contract versions, stream LLM answer."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import WebSocket
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pypdf import PdfReader
from sqlalchemy.orm import Session, joinedload

from app import models

logger = logging.getLogger(__name__)

# PDF fonts often store character pairs as ligature glyphs. When the font's
# ToUnicode CMap is missing/broken, pypdf decodes them as the raw glyph index
# (e.g. the "ffi" ligature → "P"). This map covers both the Unicode ligature
# codepoints AND common mojibake replacements observed in the wild.
_LIGATURE_MAP: dict[str, str] = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

# Mojibake: when a font's ToUnicode CMap is broken, pypdf decodes ligature
# glyph IDs as their raw byte value. The "ff" ligature glyph (0x50) becomes
# ASCII "P".  We detect a mid-word uppercase "P" and replace it with "ff".
import re as _re

_FF_MOJIBAKE_RE = _re.compile(r"(?<=[a-zA-Z])P(?=[a-z])")


def _normalize_ligatures(text: str) -> str:
    """Replace Unicode ligatures and common mojibake with plain ASCII."""
    for lig, repl in _LIGATURE_MAP.items():
        text = text.replace(lig, repl)
    text = _FF_MOJIBAKE_RE.sub("ff", text)
    return text


COMPARE_MODEL = os.getenv("COMPARE_CHAT_MODEL", "gpt-5.4")
MAX_CHARS_PER_DOC = int(os.getenv("COMPARE_MAX_CHARS_PER_DOC", "55000"))


class ComparisonSystemError(RuntimeError):
    pass


COMPARISON_SYSTEM_PROMPT = """You are a **document comparison assistant** for legal and commercial agreements.

You receive **plain text for two document versions** on the same contract. Text is assembled from **stored document chunks** (same order as the chunker); if chunks are missing, text may come from direct file extraction.
- **Document A** — baseline / reference (treat as “left” or earlier unless the user specifies otherwise).
- **Document B** — comparison / revised (treat as “right” or later unless the user specifies otherwise).

## Behavior
1. Answer the user’s question using **both** documents. Do not answer from only one side unless the question is explicitly about a single document.
2. For almost every substantive answer, use **Markdown tables** so the user can scan **A vs B** quickly.
3. Default table shape (adapt headers if the user asks, but keep separate columns for A and B):

| Topic / clause / issue | Document A | Document B | Flag |Notes (differences, risk, alignment) |

4. Short factual questions may use a **one-row** or **two-row** table, or a very short list — but if there are multiple points, use a table.
5. If something exists only in one document, put **—** or **Not stated** in the other column and explain in **Notes**.
6. **Quote sparingly** — short phrases only; never dump the full extract.
7. If the supplied text is empty, garbled, or clearly truncated, say so in **Notes** and avoid inventing clauses.
8. You may add a **brief** concluding paragraph after the table when it helps readability.
9. use flag icons red green yellow (colours) use unicode icons
    - red :- major change 
    - green :- no change
    - yellow :-  minor change
"""


def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 120] + "\n\n[... document text truncated for model context limit ...]\n"


def extract_text_from_file(path: str, file_type: str) -> str:
    ft = (file_type or "").lower().strip()
    p = Path(path)
    if not p.is_file():
        raise ComparisonSystemError(f"File not found on server for path {p.name!r}.")

    if ft == "pdf":
        from langchain_community.document_loaders  import PyPDFLoader

        reader = PyPDFLoader(path, mode="single")
        parts: list[str] = []
        for page in reader.load():
            try:
                t = page.page_content
            except Exception:
                t = ""
            if t.strip():
                parts.append(t)
        return _normalize_ligatures("\n".join(parts))

    if ft in ("docx", "doc"):
        from docx import Document

        doc = Document(path)
        lines = [para.text for para in doc.paragraphs if para.text and para.text.strip()]
        return _normalize_ligatures("\n".join(lines))

    raise ComparisonSystemError(
        f"Unsupported file type for text extraction: {file_type or 'unknown'}. Use PDF or DOCX."
    )


def _get_version(db: Session, contract_id: int, version_id: int) -> models.DocumentVersion:
    v = (
        db.query(models.DocumentVersion)
        .options(joinedload(models.DocumentVersion.file))
        .filter(
            models.DocumentVersion.id == version_id,
            models.DocumentVersion.contract_id == contract_id,
        )
        .first()
    )
    if not v:
        raise ComparisonSystemError(f"Version id {version_id} was not found on this contract.")
    if not v.file_id and not (v.file and v.file.file_path):
        raise ComparisonSystemError(
            f"Version id {version_id} has no file; upload a document for this version first."
        )
    return v


def _text_for_compare_version(db: Session, v: models.DocumentVersion) -> str:
    """
    Prefer text from ``document_chunks`` (via ``file_id``); if none, fall back to reading the file on disk.
    """
    # Lazy import: document_chunker imports extract_text_from_file from this module.
    from app.services.document_chunker import get_chunks_for_version

    stored = get_chunks_for_version(db, v.id)
    if stored:
        return "\n\n".join(c.content for c in stored)

    if v.file and v.file.file_path:
        try:
            return extract_text_from_file(
                v.file.file_path,
                (v.file.file_type or "").lower().strip() or "pdf",
            )
        except ComparisonSystemError:
            raise
        except Exception as e:
            logger.exception("Compare: file extraction failed for version_id=%s", v.id)
            raise ComparisonSystemError(f"Could not read document for version {v.id}: {e}") from e

    raise ComparisonSystemError(
        f"No chunk text and no readable file for version id {v.id}. Run document chunking or attach a file."
    )


def version_label(v: models.DocumentVersion) -> str:
    bits = [f"v{v.version_number}"]
    if v.label:
        bits.append(str(v.label))
    if v.file_type:
        bits.append(str(v.file_type).upper())
    if v.is_latest:
        bits.append("latest")
    return " · ".join(bits)


def _chunk_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out: list[str] = []
        for part in content:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                if part.get("type") == "text":
                    out.append(str(part.get("text", "")))
                elif "text" in part:
                    out.append(str(part.get("text", "")))
        return "".join(out)
    return str(content)


async def run_document_compare(
    websocket: WebSocket,
    *,
    db: Session,
    contract_id: int,
    version_a_id: int,
    version_b_id: int,
    user_message: str,
) -> None:
    if version_a_id == version_b_id:
        raise ComparisonSystemError("Select two different document versions.")

    va = _get_version(db, contract_id, version_a_id)
    vb = _get_version(db, contract_id, version_b_id)

    try:
        text_a = _text_for_compare_version(db, va)
        text_b = _text_for_compare_version(db, vb)
    except ComparisonSystemError:
        raise
    except Exception as e:
        logger.exception("Building comparison document text failed")
        raise ComparisonSystemError(f"Could not load text for one of the documents: {e}") from e

    if not text_a.strip() and not text_b.strip():
        raise ComparisonSystemError("No readable text could be extracted from either file.")

    text_a = _truncate(text_a, MAX_CHARS_PER_DOC)
    text_b = _truncate(text_b, MAX_CHARS_PER_DOC)

    label_a = version_label(va)
    label_b = version_label(vb)
    ask = (user_message or "").strip() or (
        "Compare the two documents and summarize material differences in a Markdown table."
    )

    human = f"""## Document labels
- **Document A**: {label_a} (database version id {va.id})
- **Document B**: {label_b} (database version id {vb.id})

## Document text — Document A (chunks preferred)
{text_a}

## Document text — Document B (chunks preferred)
{text_b}

## User question
{ask}
"""

    model = ChatOpenAI(model=COMPARE_MODEL, streaming=True, temperature=0.2)

    messages = [
        SystemMessage(content=COMPARISON_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ]

    async for chunk in model.astream(messages):
        piece = _chunk_to_text(getattr(chunk, "content", None))
        if piece:
            await websocket.send_json({"type": "stream", "json_data": {"name": "model", "data": piece}})

    await websocket.send_json({"type": "done"})
