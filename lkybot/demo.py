"""Extractive fallback so the app works without an API key."""

from __future__ import annotations

from lkybot.answer import Answer, Citation
from lkybot.retrieve import BM25Index


def extractive_answer(question: str, index: BM25Index, k: int = 5) -> Answer:
    passages = index.search(question, k=k)
    if not passages:
        return Answer(
            text="I have no record of speaking on that. I will not invent one.",
            refused=True,
            note="Demo mode, no passage matched.",
        )
    chunk, _score = passages[0]
    sentences = chunk.text.split(". ")
    excerpt = ". ".join(sentences[:3]).strip()
    if not excerpt.endswith("."):
        excerpt += "."
    words = excerpt.split()
    quote = " ".join(words[: min(28, len(words))])
    return Answer(
        text=(
            f"[demo mode, extractive] {excerpt}"
        ),
        citations=[
            Citation(
                chunk_id=chunk.id,
                quote=quote,
                title=chunk.title,
                date=chunk.date,
                source_url=chunk.source_url,
                valid=True,
            )
        ],
        refused=False,
        note="No model call was made. The answer is the top retrieved passage.",
        retrieved=passages,
    )
