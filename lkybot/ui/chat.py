"""Streamlit chat interface for LKY Oracle."""

from __future__ import annotations

import os

import streamlit as st

from lkybot.answer import Answer, ask
from lkybot.corpus import build_chunks, load_docs
from lkybot.demo import extractive_answer
from lkybot.providers import ProviderError, get_provider
from lkybot.retrieve import BM25Index

EXAMPLES = [
    "Why did Singapore have to separate from Malaysia?",
    "What did you say about English and mother tongue education?",
    "How should a small country handle bigger neighbours?",
    "What did you think about welfare and subsidies?",
]


@st.cache_resource(show_spinner="Building the index over the speech corpus...")
def load_index() -> tuple[BM25Index, int]:
    docs = load_docs()
    chunks = build_chunks(docs)
    return BM25Index(chunks), len(docs)


def available_providers() -> list[str]:
    names = ["demo"]
    if os.getenv("GEMINI_API_KEY"):
        names.append("gemini")
    if os.getenv("OPENROUTER_API_KEY"):
        names.append("openrouter")
    if os.getenv("COMMANDCODE_API_KEY"):
        names.append("commandcode")
    return names


def render_sources(answer: Answer) -> None:
    if not answer.citations:
        return
    with st.expander(f"Sources ({len(answer.citations)} verified)"):
        for citation in answer.citations:
            st.markdown(
                f"**{citation.title}**  \n{citation.date} · [archive record]({citation.source_url})"
            )
            st.markdown(f"> {citation.quote}")
            st.caption(f"chunk {citation.chunk_id}")


def answer_question(question: str, provider_name: str, index: BM25Index, k: int) -> Answer:
    if provider_name == "demo":
        return extractive_answer(question, index, k=k)
    provider = get_provider(provider_name)
    return ask(question, index, provider, k=k)


def main() -> None:
    index, doc_count = load_index()

    with st.sidebar:
        st.header("Settings")
        provider_name = st.selectbox("Answer engine", available_providers())
        k = st.slider("Passages retrieved", 3, 8, 5)
        st.caption(
            f"{doc_count} speeches in the corpus. Demo mode returns the top passage "
            "verbatim and makes no model call."
        )
        st.divider()
        st.markdown(
            "Every answer must cite a verbatim span from a speech. Quotes are checked "
            "as substrings of the cited chunk, and an answer with no verifiable citation "
            "is returned as a refusal."
        )

    st.title("LKY Oracle")
    st.caption(
        "Ask about independence, geopolitics, language, housing, or welfare. Answers are "
        "grounded in transcripts from the National Archives of Singapore, 1965 to 1990."
    )

    if "history" not in st.session_state:
        st.session_state.history = []

    if not st.session_state.history:
        st.markdown("**Try one of these**")
        columns = st.columns(2)
        for position, example in enumerate(EXAMPLES):
            if columns[position % 2].button(example, key=f"ex{position}"):
                st.session_state.pending = example
                st.rerun()

    for entry in st.session_state.history:
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(entry["answer"].text)
            if entry["answer"].refused:
                st.warning("No passage in the archive supported an answer.")
            render_sources(entry["answer"])

    question = st.chat_input("Ask Lee Kuan Yew")
    if "pending" in st.session_state:
        question = st.session_state.pop("pending")

    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving passages and drafting an answer..."):
                try:
                    result = answer_question(question, provider_name, index, k)
                except ProviderError as exc:
                    st.error(str(exc))
                    st.stop()
            st.markdown(result.text)
            if result.refused:
                st.warning("No passage in the archive supported an answer.")
            render_sources(result)
            st.caption(
                f"{len(result.citations)} verified citations, "
                f"{result.invalid_citations} rejected, {result.latency_s:.1f}s"
            )
        st.session_state.history.append({"question": question, "answer": result})
