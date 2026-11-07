"""Load the speech corpus and cut it into retrievable chunks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "docs.jsonl"
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Doc:
    id: str
    title: str
    date: str
    source_url: str
    text: str

    @property
    def label(self) -> str:
        return f"{self.title[:90]} ({self.date})"


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    title: str
    date: str
    source_url: str
    text: str


def load_docs(path: Path | str = DEFAULT_CORPUS) -> list[Doc]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            raw = json.loads(line)
            rows.append(
                Doc(
                    id=raw["id"],
                    title=raw["title"],
                    date=raw["date"],
                    source_url=raw["source_url"],
                    text=raw["text"],
                )
            )
    return rows


def chunk_doc(doc: Doc, size: int = 900, overlap: int = 150) -> list[Chunk]:
    """Split on sentence boundaries, keeping chunks near ``size`` characters."""
    sentences = SENTENCE_END.split(doc.text)
    chunks: list[Chunk] = []
    buffer: list[str] = []
    length = 0

    def flush() -> None:
        nonlocal buffer, length
        body = " ".join(buffer).strip()
        if len(body) > 200:
            index = len(chunks)
            chunks.append(
                Chunk(
                    id=f"{doc.id}:{index:03d}",
                    doc_id=doc.id,
                    title=doc.title,
                    date=doc.date,
                    source_url=doc.source_url,
                    text=body,
                )
            )
        if overlap > 0 and body:
            tail = body[-overlap:]
            buffer = [tail]
            length = len(tail)
        else:
            buffer = []
            length = 0

    for sentence in sentences:
        piece = sentence.strip()
        if not piece:
            continue
        if length + len(piece) > size and buffer:
            flush()
        buffer.append(piece)
        length += len(piece) + 1
    if buffer:
        body = " ".join(buffer).strip()
        if len(body) > 200:
            chunks.append(
                Chunk(
                    id=f"{doc.id}:{len(chunks):03d}",
                    doc_id=doc.id,
                    title=doc.title,
                    date=doc.date,
                    source_url=doc.source_url,
                    text=body,
                )
            )
    return chunks


def build_chunks(docs: list[Doc]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(chunk_doc(doc))
    return chunks
