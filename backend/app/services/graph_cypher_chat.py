"""
Neo4j + LangChain GraphCypherQAChain for the contract graph chatbot WebSocket.

All credentials come from environment variables — never commit API keys or DB passwords.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any


def _normalize_context_value(value: Any, buttons: list[str]) -> None:
    """Collect button labels from mixed context payloads."""
    if isinstance(value, str):
        button = value.strip()
        if button:
            buttons.append(button)
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            _normalize_context_value(item, buttons)
        return

    if isinstance(value, dict):
        nested_value = value.get("value")
        if nested_value is not None:
            _normalize_context_value(nested_value, buttons)


logger = logging.getLogger(__name__)

_chain: Any = None


class GraphChatConfigError(RuntimeError):
    """Raised when required env vars for graph chat are missing."""


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise GraphChatConfigError(f"Missing environment variable: {name}")
    return v


@lru_cache(maxsize=1)
def _build_chain():
    """Lazy singleton: connects to Neo4j and builds GraphCypherQAChain."""
    from langchain_neo4j import Neo4jGraph
    from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
    from langchain_openai import ChatOpenAI

    _require_env("OPENAI_API_KEY")

    url = _require_env("NEO4J_URI")
    username = os.getenv("NEO4J_USER", os.getenv("NEO4J_USERNAME", "")).strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    database = os.getenv("NEO4J_DATABASE", "neo4j").strip() or "neo4j"

    if not username or not password:
        raise GraphChatConfigError("NEO4J_USER (or NEO4J_USERNAME) and NEO4J_PASSWORD are required")

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4").strip()

    graph = Neo4jGraph(
        url=url,
        username=username,
        password=password,
        database=database,
        enhanced_schema=os.getenv("NEO4J_ENHANCED_SCHEMA", "true").lower() in ("1", "true", "yes"),
    )

    llm = ChatOpenAI(model=model, temperature=0)

    return GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=os.getenv("GRAPH_CHAT_VERBOSE", "").lower() in ("1", "true", "yes"),
        return_intermediate_steps=True,
        allow_dangerous_requests=True,
        return_direct=False,
        validate_cypher=True,
    )


def get_graph_cypher_chain():
    global _chain
    if _chain is None:
        _chain = _build_chain()
    return _chain


def reset_graph_cypher_chain():
    """Clear cached chain (e.g. after config change in tests)."""
    global _chain
    _chain = None
    _build_chain.cache_clear()


def run_graph_chat_question(question: str) -> dict:
    """Run the QA chain; returns assistant text (may include markdown)."""
    q = (question or "").strip()
    if not q:
        return "Please send a non-empty question."

    chain = get_graph_cypher_chain()
    result = chain.invoke({"query": q})
    answer = result.get("result")
    response = {"response": answer}
    intermediate_steps = result.get("intermediate_steps")
    if intermediate_steps:
        logger.info("Intermediate steps: %s", intermediate_steps)
        for step in intermediate_steps:
            if "context" in step:
                response["context"] = step["context"]


    return response
