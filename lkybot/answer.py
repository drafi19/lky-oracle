"""Answer a question in Lee Kuan Yew's voice, grounded in retrieved passages."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from lkybot.corpus import Chunk
from lkybot.providers.base import Provider, ProviderError
from lkybot.retrieve import BM25Index

SYSTEM = """You answer questions as Lee Kuan Yew, the first Prime Minister of Singapore.

You are given numbered passages from his speeches and press transcripts. Use only those passages. Never use outside knowledge, never invent a date, a name, a number, or a quotation.

Voice:
- First person, past tense for events that happened.
- Short declarative sentences. No hedging, no corporate language, no exclamation marks.
- Dry, practical, unsentimental. Argue from consequences, not from ideology.
- Two to four short paragraphs at most.

Grounding rules:
- Every factual claim must come from a passage.
- Support the answer with one to three citations. Each citation must copy a span of at least 12 words verbatim from the passage it cites.
- If the passages do not answer the question, set refused to true and say plainly that you did not speak about it, or that the record available does not cover it. Do not substitute a plausible opinion for a real record.
- If the passages answer only part of the question, answer that part and say what the record does not cover.

Output strict JSON only:
{"answer":"...","citations":[{"chunk_id":"...","quote":"..."}],"refused":false,"note":"..."}

Do not add commentary outside the JSON object."""


@dataclass
class Citation:
    chunk_id: str
    quote: str
    title: str
    date: str
    source_url: str
    valid: bool


@dataclass
class Answer:
    text: str
    citations: list[Citation] = field(default_factory=list)
    refused: bool = False
    note: str = ""
    retrieved: list[tuple[Chunk, float]] = field(default_factory=list)
    invalid_citations: int = 0
    latency_s: float = 0.0


def _normalize(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def _prompt(question: str, passages: list[tuple[Chunk, float]]) -> str:
    blocks = []
    for chunk, score in passages:
        blocks.append(
            f"[{chunk.id}] {chunk.title} ({chunk.date}), retrieval score {score:.2f}\n{chunk.text}"
        )
    joined = "\n\n".join(blocks)
    return f"QUESTION:\n{question}\n\nPASSAGES:\n{joined}"


def ask(
    question: str,
    index: BM25Index,
    provider: Provider,
    k: int = 5,
    min_quote_words: int = 12,
) -> Answer:
    started = time.perf_counter()
    passages = index.search(question, k=k)
    if not passages:
        return Answer(
            text="I have no record of speaking on that. I will not invent one.",
            refused=True,
            note="No passage matched the question.",
            latency_s=time.perf_counter() - started,
        )

    try:
        payload = provider.generate_json(SYSTEM, _prompt(question, passages), "{}")
    except ProviderError as exc:
        raise ProviderError(f"Answer generation failed: {exc}", transient=exc.transient) from exc

    raw_citations = payload.get("citations") or []
    by_id = {chunk.id: chunk for chunk, _ in passages}
    citations: list[Citation] = []
    invalid = 0
    for raw in raw_citations:
        chunk_id = str(raw.get("chunk_id", "")).strip()
        quote = str(raw.get("quote", "")).strip()
        chunk = by_id.get(chunk_id)
        ok = (
            chunk is not None
            and len(quote.split()) >= min_quote_words
            and _normalize(quote) in _normalize(chunk.text)
        )
        if chunk is None:
            invalid += 1
            continue
        citations.append(
            Citation(
                chunk_id=chunk_id,
                quote=quote,
                title=chunk.title,
                date=chunk.date,
                source_url=chunk.source_url,
                valid=ok,
            )
        )
        if not ok:
            invalid += 1

    valid = [c for c in citations if c.valid]
    refused = bool(payload.get("refused")) or not valid
    text = str(payload.get("answer", "")).strip()
    if refused and not text:
        text = "The record I have does not cover that, and I will not pretend it does."

    return Answer(
        text=text,
        citations=valid,
        refused=refused,
        note=str(payload.get("note", "")),
        retrieved=passages,
        invalid_citations=invalid,
        latency_s=time.perf_counter() - started,
    )
