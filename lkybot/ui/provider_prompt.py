"""Ask the visitor which engine to use, once per session."""

from __future__ import annotations

import streamlit as st


def provider_dialog(options: list[str], labels: dict[str, str], state_key: str) -> None:
    """Show a modal on first visit; the choice is remembered for the session."""

    def _panel() -> None:
        st.markdown(
            "Choose the engine that will answer. **Demo** runs offline and makes no "
            "model call. The cloud engines need a configured key and are rate limited."
        )
        for name in options:
            if st.button(
                labels.get(name, name),
                key=f"choose_engine_{name}",
                use_container_width=True,
            ):
                st.session_state[state_key] = name
                st.rerun()
        st.caption("You can change this later in the sidebar.")

    opener = getattr(st, "dialog", None)
    if opener is None:
        st.info("Pick an engine in the sidebar before you start.")
        return
    try:
        opener("Which engine should answer?")(_panel)()
    except Exception:  # noqa: BLE001
        st.info("Pick an engine in the sidebar before you start.")
