from __future__ import annotations

from contextlib import suppress

import streamlit as st

from lkybot.runtime_env import mirror_secrets
from lkybot.ui.chat import main
from lkybot.ui.styles import apply_styles

st.set_page_config(
    page_title="LKY Oracle",
    page_icon="L",
    layout="centered",
    initial_sidebar_state="expanded",
)

with suppress(Exception):
    mirror_secrets(st.secrets)

apply_styles()
main()
