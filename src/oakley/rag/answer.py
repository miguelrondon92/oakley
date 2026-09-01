"""RAG answer generation and formatting."""

from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai

from oakley.config import MIN_SCORE_THRESHOLD, get_settings
from oakley.vector.embedder import configure_genai, embed_query
from oakley.vector.store import search

REFUSAL_TEMPLATE = (
    "I couldn't find a clear answer in the Oakwood Glen HOA bylaws or Harris County "
    "regulations provided. Try rephrasing, or specify whether you're asking about "
    "HOA rules or county regulations."
)

HISTORY_MAX_MESSAGES = 10
HISTORY_MAX_CHARS = 4000


def _confidence(max_score: float) -> str:
    if max_score >= 0.75:
        return "high"
    if max_score >= 0.55:
        return "medium"
    return "low"


def trim_history(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if not history:
        return []
    trimmed = history[-HISTORY_MAX_MESSAGES:]
    total = 0
    result: list[dict[str, str]] = []
    for item in reversed(trimmed):
        content = item.get("content", "")
        role = item.get("role", "user")
        if not content.strip():
            continue
        if total + len(content) > HISTORY_MAX_CHARS:
            break
        result.insert(0, {"role": role, "content": content})
        total += len(content)
    return result


def _format_history_block(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = ["Prior conversation:"]
    for turn in history:
        label = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{label}: {turn['content']}")
    return "\n".join(lines) + "\n\n"


def build_prompt(
    question: str,
    chunks: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
) -> str:
    context_parts = []
    for i, ch in enumerate(chunks, 1):
        title = ch.get("document_title", "Unknown")
        page = ch.get("page_start", "?")
        heading = ch.get("section_heading") or ""
        excerpt = ch.get("context_doc_excerpt") or ""
        context_line = (
            f"[Source {i}] {title}, p. {page}"
            + (f", section: {heading}" if heading else "")
        )
        if excerpt:
            context_line += f"\nFolder context: {excerpt}"
        context_parts.append(context_line + f"\n{ch['text']}\n")
    context = "\n---\n".join(context_parts)
    history_block = _format_history_block(trim_history(history))
    return f"""You are Oakley, an assistant for Oakwood Glen HOA and Harris County regulations.
Answer ONLY using the provided sources. Include inline citations like [Document Title, p. N].
If the sources do not contain enough information, say so — do not invent rules.
Use prior conversation for context when the current question is a follow-up.

{history_block}Current question: {question}

Sources:
{context}

Provide a clear, concise answer with citations."""


def _extract_citations(answer: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    cited_indices: set[int] = set()

    for i, ch in enumerate(chunks):
        title = ch.get("document_title", "")
        if title and title in answer:
            cited_indices.add(i)

    if not cited_indices:
        cited_indices = {0} if chunks else set()

    for i in sorted(cited_indices):
        ch = chunks[i]
        quote = ch["text"][:300].replace("\n", " ")
        citations.append(
            {
                "document_title": ch.get("document_title", ""),
                "source_file": ch.get("source_file", ""),
                "source_type": ch.get("source_type", ""),
                "page_start": int(ch.get("page_start", 0)),
                "page_end": int(ch.get("page_end", 0)),
                "section_heading": ch.get("section_heading", ""),
                "doc_category": ch.get("doc_category", ""),
                "chunk_id": ch.get("chunk_id", ""),
                "quote": quote,
            }
        )
    return citations


def ask_question(
    question: str,
    source_type: str | None = None,
    top_k: int | None = None,
    min_score: float = MIN_SCORE_THRESHOLD,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    settings.require_gemini()
    top_k = top_k or settings.top_k

    query_emb = embed_query(question)
    chunks = search(query_emb, top_k=top_k, source_type=source_type)
    max_score = max((c["score"] for c in chunks), default=0.0)
    filters = {"source_type": source_type} if source_type else {}

    base = {
        "question": question,
        "retrieved_chunk_ids": [c["chunk_id"] for c in chunks],
        "provider_model": settings.gemini_model,
        "retrieval": {"top_k": top_k, "filters": filters, "max_score": round(max_score, 4)},
    }

    if not chunks or max_score < min_score:
        return {
            **base,
            "answer": REFUSAL_TEMPLATE,
            "citations": [],
            "confidence": "low",
            "refused": True,
            "refusal_reason": "no_relevant_chunks" if not chunks else "low_confidence",
        }

    configure_genai()
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = build_prompt(question, chunks, history=history)
    response = model.generate_content(prompt)
    answer_text = (response.text or "").strip()

    confidence = _confidence(max_score)
    refused = confidence == "low"
    citations = _extract_citations(answer_text, chunks)

    result = {
        **base,
        "answer": REFUSAL_TEMPLATE if refused else answer_text,
        "citations": [] if refused else citations,
        "confidence": confidence,
        "refused": refused,
        "refusal_reason": "low_confidence" if refused else None,
    }
    return result


def format_answer_pretty(result: dict[str, Any]) -> str:
    lines = [result["answer"], ""]
    if result.get("citations"):
        lines.append("Sources:")
        for c in result["citations"]:
            pages = c["page_start"]
            if c.get("page_end") and c["page_end"] != c["page_start"]:
                pages = f"{c['page_start']}-{c['page_end']}"
            lines.append(f"  - {c['document_title']}, p. {pages} ({c['source_file']})")
    if result.get("refused"):
        lines.append(f"\n(confidence: {result['confidence']})")
    return "\n".join(lines)


def format_answer_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2)
