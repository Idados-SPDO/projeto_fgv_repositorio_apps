"""Renderização compartilhada do card de aplicação com botão de favorito."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import areas as areas_mod
from .. import db


CARD_CSS = """
<style>
/* container do card (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border: 1px solid #e3e7ee !important;
    box-shadow: 0 1px 2px rgba(15, 30, 60, 0.04);
    transition: box-shadow 0.12s ease, border-color 0.12s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 18px rgba(15, 30, 60, 0.10);
    border-color: #c7d2e3 !important;
}
/* botao da estrela: discreto */
button[data-testid="stBaseButton-secondary"]:has(div:is(p):only-child) {
    /* fallback geral */
}
.fgv-card-icon { font-size: 1.9rem; line-height: 1; padding-top: 4px; }
.fgv-card-title { font-size: 1.05rem; font-weight: 600; color: #1f2937; margin: 4px 0 2px 0; }
.fgv-card-desc  { font-size: 0.88rem; color: #6b7280; margin: 0 0 6px 0; }
.fgv-card-area  { font-size: 0.82rem; color: #1f4e79; font-weight: 600; margin: 0 0 10px 0; }
.fgv-card-area b { font-weight: 700; }
.fgv-card-open  {
    background: #1f4e79;
    color: #fff !important;
    text-decoration: none !important;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    display: inline-block;
}
.fgv-card-open:hover { background: #163a5c; }
</style>
"""


def render_card(
    app: pd.Series,
    *,
    fav_ids: set[int],
    user_id: int,
    context: str,
) -> None:
    """Renderiza um card de aplicação dentro de um st.container."""
    app_id = int(app["APP_ID"])
    is_fav = app_id in fav_ids
    icon = app["ICON"] or "⚙️"

    with st.container(border=True):
        head_l, head_r = st.columns([4, 1])
        with head_l:
            st.markdown(
                f"<div class='fgv-card-icon'>{icon}</div>",
                unsafe_allow_html=True,
            )
        with head_r:
            label = "⭐" if is_fav else "☆"
            if st.button(
                label,
                key=f"fav_{context}_{app_id}",
                help="Desfavoritar" if is_fav else "Favoritar",
                use_container_width=True,
            ):
                db.toggle_favorite(user_id, app_id)
                st.rerun()

        st.markdown(
            f"<p class='fgv-card-title'>{app['NAME']}</p>",
            unsafe_allow_html=True,
        )
        if app["DESCRIPTION"]:
            st.markdown(
                f"<p class='fgv-card-desc'>{app['DESCRIPTION']}</p>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<p class='fgv-card-area'><b>Área:</b> {areas_mod.display_name(app['AREA'])}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<a class='fgv-card-open' href='{app['URL']}' target='_blank' rel='noopener'>"
            f"Abrir &nbsp;&rsaquo;</a>",
            unsafe_allow_html=True,
        )


def render_grid(
    apps: pd.DataFrame,
    *,
    fav_ids: set[int],
    user_id: int,
    context: str,
    cols: int = 3,
) -> None:
    """Renderiza um grid de cards (cols por linha)."""
    if apps.empty:
        return
    rows = [apps.iloc[i : i + cols] for i in range(0, len(apps), cols)]
    for i, row in enumerate(rows):
        columns = st.columns(cols, gap="medium")
        for col, (_, app) in zip(columns, row.iterrows()):
            with col:
                render_card(
                    app,
                    fav_ids=fav_ids,
                    user_id=user_id,
                    context=f"{context}_{i}",
                )
