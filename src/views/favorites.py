"""Tela de favoritos do usuário logado."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import auth, db
from . import _cards


_EMPTY_MSG = (
    "Você ainda não favoritou nenhuma aplicação. "
    "Na aba *Aplicações*, clique na estrela (☆) no canto superior direito "
    "de um card para favoritá-lo."
)


def render() -> None:
    user = auth.require_login()
    st.markdown(_cards.CARD_CSS, unsafe_allow_html=True)

    st.markdown(
        "<h2 style='text-align:center;color:var(--fgv-blue);margin:0.4rem 0 0.2rem 0'>"
        "⭐ Meus favoritos</h2>"
        "<p style='text-align:left;color:var(--fgv-muted);margin:0 0 1.4rem 0'>"
        "Aplicações que você marcou como favoritas.</p>",
        unsafe_allow_html=True,
    )

    def _fetch() -> pd.DataFrame:
        df = db.list_favorite_applications(user["id"])
        if df.empty:
            return df
        return df.sort_values(by="NAME", key=lambda s: s.str.upper(), kind="stable")

    _cards.render_grid(
        fetch=_fetch,
        user_id=user["id"],
        context="favorites",
        access_token=auth.get_access_token(),
        refresh_token=auth.get_refresh_token(),
        empty_message=_EMPTY_MSG,
    )
