"""
Build a contract knowledge graph from stored ``document_chunks`` using LangChain's
``LLMGraphTransformer``, and persist the result as JSON (list of GraphDocument dicts).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.models.models import DocumentChunk, DocumentVersion, VersionKnowledgeGraph

logger = logging.getLogger(__name__)


def load_version_text_for_graph(db: Session, contract_id: int, version_id: int) -> tuple[str, dict[str, Any]]:
    """Load ordered chunk text for a contract document version. Raises ``ValueError`` if unusable."""
    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.contract_id == contract_id,
        )
        .first()
    )
    if not version:
        raise ValueError("Document version not found for this contract")
    if not version.file_id:
        raise ValueError("Version has no file; upload a document first")
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.file_id == version.file_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    if not chunks:
        raise ValueError(
            "No document chunks for this version. Wait for background chunking to finish or re-upload the file."
        )
    full_text = "\n\n".join(c.content for c in chunks)
    metadata: dict[str, Any] = {
        "contract_id": contract_id,
        "document_version_id": version_id,
        "file_id": version.file_id,
    }
    return full_text, metadata


def transform_text_to_graph_list(full_text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Split concatenated text into LangChain documents, run ``LLMGraphTransformer``,
    return JSON-serializable dicts (``GraphDocument.model_dump(mode='json')``).
    """
    lc_metadata = {
        **metadata,
        "source": f"contract_{metadata.get('contract_id')}_version_{metadata.get('document_version_id')}",
    }
    base_doc = Document(page_content=full_text, metadata=lc_metadata)
    # chunk_size = int(os.environ.get("CLM_KG_CHUNK_SIZE", "10000"))
    # chunk_overlap = int(os.environ.get("CLM_KG_CHUNK_OVERLAP", "400"))
    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap,
    #     length_function=len,
    # )
    # splitted_documents = splitter.split_documents([base_doc])
    model = os.environ.get("CLM_KG_LLM_MODEL", "gpt-5.4")
    llm = ChatOpenAI(model=model, temperature=0)
    transformer = LLMGraphTransformer(llm=llm)
    graph_documents = transformer.convert_to_graph_documents([base_doc])
    return [rec.model_dump(mode="json") for rec in graph_documents]


def persist_version_knowledge_graph(
    db: Session,
    contract_id: int,
    version_id: int,
    graph_documents_json: list[dict[str, Any]],
) -> VersionKnowledgeGraph:
    row = (
        db.query(VersionKnowledgeGraph)
        .filter(VersionKnowledgeGraph.document_version_id == version_id)
        .first()
    )
    if row:
        row.graph_documents_json = graph_documents_json
        row.contract_id = contract_id
    else:
        row = VersionKnowledgeGraph(
            contract_id=contract_id,
            document_version_id=version_id,
            graph_documents_json=graph_documents_json,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def build_graph(db: Session, contract_id: int, version_id: int) -> list[dict[str, Any]]:
    """
    End-to-end: load chunk text, run LLM graph extraction, persist one row per version.

    Returns ``graph_data`` (list of GraphDocument dicts), same shape as stored in the DB.
    """
    full_text, meta = load_version_text_for_graph(db, contract_id, version_id)
    if not (full_text or "").strip():
        raise ValueError("Document text is empty")
    data = transform_text_to_graph_list(full_text, meta)
    persist_version_knowledge_graph(db, contract_id, version_id, data)
    return data
