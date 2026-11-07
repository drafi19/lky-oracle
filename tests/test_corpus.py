"""Chunking keeps ids unique and pieces readable."""

from __future__ import annotations

from lkybot.corpus import Doc, build_chunks, chunk_doc

TEXT = " ".join(
    f"This is sentence number {i} about housing, language, and the defence of a small country."
    for i in range(80)
)


def _doc() -> Doc:
    return Doc(id="d1", title="A speech", date="1965-10-15", source_url="u", text=TEXT)


def test_chunks_are_bounded() -> None:
    chunks = chunk_doc(_doc(), size=600, overlap=100)
    assert len(chunks) > 1
    assert max(len(c.text) for c in chunks) < 900


def test_chunk_ids_are_unique_and_ordered() -> None:
    chunks = chunk_doc(_doc(), size=600, overlap=100)
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))
    assert ids[0].startswith("d1:")


def test_chunks_keep_document_metadata() -> None:
    chunks = build_chunks([_doc()])
    assert all(c.doc_id == "d1" for c in chunks)
    assert all(c.date == "1965-10-15" for c in chunks)
    assert all(c.source_url == "u" for c in chunks)
