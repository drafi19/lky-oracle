"""The app must answer from the corpus without an API key."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_app_loads_with_examples() -> None:
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert app.title[0].value == "LKY Oracle"
    assert len(app.button) >= 4


def test_demo_answer_has_a_verified_citation() -> None:
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    app.button[0].click().run()
    assert not app.exception
    history = app.session_state["history"]
    assert history, "clicking an example produced no answer"
    answer = history[0]["answer"]
    assert answer.citations, "demo answer came back without a citation"
    assert all(citation.valid for citation in answer.citations)
