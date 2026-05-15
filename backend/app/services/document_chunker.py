"""
Document Chunker Service

Extracts text from uploaded files, splits the document into structural chunks using an LLM,
and persists the chunks in the ``document_chunks`` table (linked by ``file_id``).
"""

from __future__ import annotations

import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.models import DocumentChunk, DocumentVersion, File
from app.services.comparison_chat import extract_text_from_file

logger = logging.getLogger(__name__)

DOCUMENT_CHUNK_PROMPT = """\
You are a specialized legal document processing system designed to chunk civil public contract documents based on natural document entities and structural elements, preserving the exact original text.

## Input
You will receive a civil public contract document in text format.
The input may contain page markers like "--- Page N ---" — these are metadata only. Do NOT include page markers in your output chunks.

## Processing Instructions

### 1. Entity-Based Chunking Strategy
Chunk the document based on its natural structural entities:

**Primary Document Entities:**
- **Header Block**: Document title, case numbers, court information
- **Party Block**: Complete party identification sections
- **Recital Block**: Each "WHEREAS" or "RECITAL" paragraph
- **Definition Block**: Complete definition sections or individual definitions
- **Article/Section Block**: Complete numbered articles or sections
- **Paragraph Entity**: Self-contained paragraphs with complete legal meaning
- **Clause Block**: Individual clauses (including sub-clauses as single entity)
- **List Block**: Enumerated items, bullet points, or numbered lists as complete units
- **Signature Block**: Execution and signature sections
- **Exhibit Block**: Each exhibit or appendix as separate entities

### 2. Text Preservation Rules

**CRITICAL: EXACT TEXT PRESERVATION**
- **NO ALTERATIONS**: Copy text exactly as it appears in the input
- **NO SUMMARIZATION**: Include complete, unmodified text
- **NO PARAPHRASING**: Maintain original wording precisely
- **NO CORRECTIONS**: Keep typos, formatting, spacing exactly as written
- **PRESERVE FORMATTING**: strict requirement to Maintain line breaks, indentation, spacing, capitalization
- **KEEP PUNCTUATION**: Retain all punctuation marks exactly as they appear
- **PRESERVE NUMBERING**: Keep section numbers, bullet points, lettering systems intact

### 3. Chunking Rules

**DO:**
- Split at natural document boundaries (sections, paragraphs, clauses)
- Keep complete legal provisions together
- Copy and paste exact text with no modifications
- Maintain original whitespace and line breaks
- Preserve all special characters and formatting
- convert tables as markdown before chunking

**DON'T: Strict**
- do not keep the entore document in single chunk
- Change any words, phrases, or sentences
- Fix grammar, spelling, or formatting errors
- Add explanatory text or commentary
- Remove or add punctuation
- Alter capitalization or spacing
- Split mid-sentence unless there's a natural document break

### 4. Extraction Process
1. Identify natural document entity boundaries
2. Extract complete entities from start to end
3. Copy text exactly character-for-character
4. Preserve all original formatting and structure
5. Include each complete entity as one chunk

## Output Format
Provide a simple list of strings, where each string contains the exact original text of one complete document entity:

```
[
  "EXACT TEXT FROM DOCUMENT - First complete entity...",
  "EXACT TEXT FROM DOCUMENT - Second complete entity...",
  ...
]
```

## Quality Control
- Verify every chunk contains verbatim text from the original
- Ensure no text is lost, added, or modified
- Confirm original formatting and structure is maintained
- Check that all entities represent complete, natural document boundaries

---

**Process the legal document by extracting complete document entities and output each as an exact, unmodified text string in a list format.**
"""

SUPPORTED_FILE_TYPES = {"pdf", "docx", "doc"}


class _ChunkResponse(BaseModel):
    chunks: list[str] = Field(description="list of chunks")


def _resolve_path_and_type(db: Session, file_id: int) -> tuple[str, str]:
    rec = db.query(File).filter(File.id == file_id).first()
    if rec is None:
        raise ValueError(f"File id={file_id} not found")
    if not rec.file_path:
        raise ValueError(f"File id={file_id} has no file_path")
    ft = (rec.file_type or "").lower().strip()
    if not ft and rec.original_filename:
        ft = rec.original_filename.rsplit(".", 1)[-1].lower()
    return rec.file_path, ft or "pdf"


async def chunk_file(db: Session, file_id: int) -> list[DocumentChunk]:
    """Extract text from the file row, LLM-chunk it, and store rows on ``file_id``."""
    logger.debug("chunk_file called: file_id=%s", file_id)

    try:
        file_path, file_type = _resolve_path_and_type(db, file_id)
    except ValueError:
        logger.exception("_resolve_path_and_type failed for file_id=%s", file_id)
        return []

    logger.debug("Resolved file: path=%s  type=%s", file_path, file_type)

    if file_type not in SUPPORTED_FILE_TYPES:
        logger.info("Skipping chunking – unsupported file type %r (file_id=%s)", file_type, file_id)
        return []

    import os

    logger.debug("File exists on disk: %s  (cwd=%s)", os.path.isfile(file_path), os.getcwd())

    try:
        document_text = extract_text_from_file(file_path, file_type)
    except Exception:
        logger.exception("Text extraction failed for file_id=%s path=%s", file_id, file_path)
        return []

    text_len = len(document_text) if document_text else 0
    logger.debug("Extracted text length: %d chars for file_id=%s", text_len, file_id)

    if not document_text or not document_text.strip():
        logger.warning("No text extracted for file_id=%s", file_id)
        return []

    logger.debug("Calling LLM for chunking (%d chars) …", text_len)
    llm = ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4")).with_structured_output(_ChunkResponse)

    try:
        response: _ChunkResponse = await llm.ainvoke(
            [
                SystemMessage(content=DOCUMENT_CHUNK_PROMPT),
                HumanMessage(content=document_text),
            ]
        )
    except Exception:
        logger.exception("LLM chunking failed for file_id=%s", file_id)
        return []

    logger.debug("LLM returned %d chunks for file_id=%s", len(response.chunks), file_id)

    db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).delete()

    chunks: list[DocumentChunk] = []
    for idx, text in enumerate(response.chunks):
        row = DocumentChunk(
            file_id=file_id,
            chunk_index=idx,
            content=text,
        )
        db.add(row)
        chunks.append(row)

    db.commit()
    for c in chunks:
        db.refresh(c)

    logger.info("Stored %d chunks for file_id=%s", len(chunks), file_id)
    return chunks


async def chunk_contract_version(db: Session, version_id: int) -> list[DocumentChunk]:
    """Chunk using the ``DocumentVersion``'s ``file_id``."""
    ver = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not ver or not ver.file_id:
        logger.warning("chunk_contract_version: version %s missing or has no file_id", version_id)
        return []
    return await chunk_file(db, ver.file_id)


def get_chunks_for_file(db: Session, file_id: int) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.file_id == file_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


def get_chunks_for_version(db: Session, version_id: int) -> list[DocumentChunk]:
    ver = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not ver or not ver.file_id:
        return []
    return get_chunks_for_file(db, ver.file_id)


# Backward-compatible alias
def get_chunks_for_drive_file(db: Session, file_id: int) -> list[DocumentChunk]:
    """Drive files are ``File`` rows with ``folder_id`` set; id is ``files.id``."""
    return get_chunks_for_file(db, file_id)
