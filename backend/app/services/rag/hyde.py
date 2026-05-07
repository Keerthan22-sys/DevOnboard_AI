from __future__ import annotations

import logging

from app.services.llm.ollama_client import generate_response

logger = logging.getLogger(__name__)

HYDE_SYSTEM_PROMPT = (
    "You are a technical documentation writer. Given a developer's question, "
    "write a short, factual paragraph (3-5 sentences) that would appear in "
    "project documentation answering that question. Do NOT say 'I don't know'. "
    "Write as if you are the documentation itself. Be specific and technical."
)


async def generate_hypothetical_answer(question: str) -> str:
    """Generate a hypothetical document passage that answers the question.

    HyDE (Hypothetical Document Embeddings) bridges the semantic gap
    between a short question and a long documentation passage by
    generating a fake answer, embedding it, and using that for retrieval.
    The factual accuracy of the generated text doesn't matter — only its
    semantic proximity to real relevant passages.
    """
    try:
        hypothesis = await generate_response(
            prompt=question,
            system_prompt=HYDE_SYSTEM_PROMPT,
        )
        logger.info("[HyDE] Generated %d-char hypothesis for: %r", len(hypothesis), question[:80])
        return hypothesis
    except Exception:
        logger.warning("[HyDE] Generation failed, falling back to raw query", exc_info=True)
        return question
