"""DOCX ↔ HTML conversion endpoints for the in-app editor."""

from __future__ import annotations

import base64
import io
import logging

import mammoth
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from htmldocx import HtmlToDocx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docx-editor")


class DocxToHtmlRequest(BaseModel):
    docx_b64: str          # base64-encoded .docx bytes
    filename: str = "document.docx"


class HtmlToDocxRequest(BaseModel):
    html: str
    filename: str = "edited_document.docx"


@router.post("/to-html")
def docx_to_html(body: DocxToHtmlRequest):
    """Convert a base64-encoded DOCX to HTML for the in-app editor."""
    try:
        docx_bytes = base64.b64decode(body.docx_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {exc}") from exc

    try:
        buf = io.BytesIO(docx_bytes)
        result = mammoth.convert_to_html(buf)
        html = result.value
        messages = [str(m) for m in result.messages]
        return {"html": html, "warnings": messages}
    except Exception as exc:
        logger.exception("mammoth conversion failed")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {exc}") from exc


@router.post("/from-html")
def html_to_docx(body: HtmlToDocxRequest):
    """Convert HTML back to a DOCX file and return it as base64."""
    try:
        parser = HtmlToDocx()
        doc = parser.parse_html_string(body.html)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        return {"docx_b64": b64, "filename": body.filename}
    except Exception as exc:
        logger.exception("html→docx conversion failed")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {exc}") from exc
