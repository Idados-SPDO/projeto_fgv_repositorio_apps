"""Tela de favoritos do usuário logado."""
from __future__ import annotations

import streamlit as st

from .. import auth, db
from . import _cards


def render() -> None:
    user = auth.require_login()
    st.markdown(_cards.CARD_CSS, unsafe_allow_html=True)

    st.markdown(
        "<h2 style='text-align:center;color:#1f4e79;margin:0.4rem 0 0.2rem 0'>"
        "⭐ Meus favoritos</h2>"
        "<p style='text-align:left;color:#6b7280;margin:0 0 1.4rem 0'>"
        "Aplicações que você marcou como favoritas.</p>",
        unsafe_allow_html=True,
    )

    favs_df = db.list_favorite_applications(user["id"])

    if favs_df.empty:
        st.info(
            "Você ainda não favoritou nenhuma aplicação. "
            "Na aba *Aplicações*, clique na estrela (☆) no canto superior direito "
            "de um card para favoritá-lo."
        )
        return

    favs_df = favs_df.sort_values(
        by="NAME", key=lambda s: s.str.upper(), kind="stable"
    )

    fav_ids = set(favs_df["APP_ID"].astype(int).tolist())
    _cards.render_grid(
        favs_df,
        fav_ids=fav_ids,
        user_id=user["id"],
        context="favorites",
    )
