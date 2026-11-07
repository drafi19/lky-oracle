"""Retrieval must put the right speech near the top, and answer.py must police citations."""

from __future__ import annotations

import pytest

from lkybot.answer import ask
from lkybot.corpus import Doc, build_chunks
from lkybot.providers.base import ProviderError
from lkybot.providers.fake import FakeProvider
from lkybot.retrieve import BM25Index

MALAYSIA = (
    "Singapore separated from Malaysia on the ninth of August nineteen sixty five. "
    "The separation was not my choice, but the union had become impossible to hold together. "
    "We had disagreements over citizenship, over the common market, and over how the country "
    "should be governed. I signed the agreement with a heavy heart because there was no "
    "alternative left for a small island with no natural resources."
)
DEFENCE = (
    "A small country must be able to defend itself because no one else will do it for you. "
    "We built national service so that every young man would know how to hold a rifle. "
    "Deterrence is cheaper than defeat, and a credible defence is the foundation of every "
    "other policy we pursued in those years."
)


def _index() -> BM25Index:
    docs = [
        Doc(id="sep1965", title="Separation from Malaysia", date="1965-08-09", source_url="u1", text=MALAYSIA),
        Doc(id="def1967", title="National service", date="1967-06-19", source_url="u2", text=DEFENCE),
    ]
    return BM25Index(build_chunks(docs))


def test_retrieval_finds_the_right_speech() -> None:
    hits = _index().search("why did Singapore separate from Malaysia", k=2)
    assert hits
    assert hits[0][0].doc_id == "sep1965"


def test_valid_citation_is_kept() -> None:
    index = _index()
    chunk = index.search("separation from Malaysia", k=1)[0][0]
    quote = " ".join(chunk.text.split()[:18])
    provider = FakeProvider(
        [
            {
                "answer": "We separated because the union had become impossible.",
                "citations": [{"chunk_id": chunk.id, "quote": quote}],
                "refused": False,
                "note": "",
            }
        ]
    )
    result = ask("separation from Malaysia", index, provider)
    assert result.refused is False
    assert len(result.citations) == 1
    assert result.citations[0].valid is True


def test_fabricated_quote_forces_a_refusal() -> None:
    index = _index()
    chunk = index.search("separation from Malaysia", k=1)[0][0]
    provider = FakeProvider(
        [
            {
                "answer": "I always wanted independence from the start.",
                "citations": [
                    {
                        "chunk_id": chunk.id,
                        "quote": "I always wanted independence from the very beginning and said so often",
                    }
                ],
                "refused": False,
                "note": "",
            }
        ]
    )
    result = ask("separation from Malaysia", index, provider)
    assert result.refused is True
    assert result.citations == []
    assert result.invalid_citations == 1


def test_no_retrieval_means_no_model_call() -> None:
    index = _index()
    provider = FakeProvider([])
    result = ask("quantum chromodynamics lattice spacing", index, provider)
    assert result.refused is True
    assert "no record" in result.text.lower()


def test_provider_error_is_wrapped() -> None:
    index = _index()
    provider = FakeProvider([])
    with pytest.raises(ProviderError):
        ask("separation from Malaysia", index, provider)
