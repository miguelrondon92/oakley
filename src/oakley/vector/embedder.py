"""Gemini text embeddings."""

from __future__ import annotations

import time

import google.generativeai as genai

from oakley.config import get_settings


def _embedding_model() -> str:
    return get_settings().embedding_model


def configure_genai() -> None:
    settings = get_settings()
    api_key = settings.require_gemini()
    genai.configure(api_key=api_key)


def embed_texts(texts: list[str], batch_size: int = 5, max_retries: int = 8) -> list[list[float]]:
    if not texts:
        return []
    configure_genai()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        for attempt in range(max_retries):
            try:
                result = genai.embed_content(
                    model=_embedding_model(),
                    content=batch,
                    task_type="retrieval_document",
                )
                embeddings = result.get("embedding")
                if embeddings and isinstance(embeddings[0], (int, float)):
                    all_embeddings.append(list(embeddings))
                else:
                    for emb in embeddings:
                        all_embeddings.append(list(emb))
                time.sleep(1.0)
                break
            except Exception as exc:
                msg = str(exc).lower()
                if "429" in msg or "resource_exhausted" in msg or "quota" in msg:
                    wait = min(60, 2 ** attempt * 2)
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"Embedding failed: {exc}") from exc
        else:
            raise RuntimeError(f"Embedding batch failed after {max_retries} retries (rate limit).")

    return all_embeddings


def embed_query(text: str) -> list[float]:
    configure_genai()
    result = genai.embed_content(
        model=_embedding_model(),
        content=text,
        task_type="retrieval_query",
    )
    emb = result.get("embedding")
    return list(emb)
