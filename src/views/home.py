"""Tela principal: abas por área (alfabéticas) com filtro e cards."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import areas as areas_mod
from .. import auth, branding, db
from . import _cards


_TAB_CSS = """
<style>
div[data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 2px solid #e3e7ee;
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: #6b7280 !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    border-radius: 8px 8px 0 0 !important;
    letter-spacing: 0.5px;
}
button[data-baseweb="tab"]:hover {
    background: #f4f6fa !important;
    color: #1f4e79 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #1f4e79 !important;
    font-weight: 700 !important;
    border-bottom: 3px solid #1f4e79 !important;
}
.empty-area { color: #94a3b8; font-style: italic; padding: 1rem 0; }
</style>
"""


def render() -> None:
    user = auth.require_login()
    st.markdown(_cards.CARD_CSS, unsafe_allow_html=True)
    st.markdown(_TAB_CSS, unsafe_allow_html=True)

    st.markdown(
        f"<h2 style='text-align:center;color:#1f4e79;margin:0.4rem 0 0.2rem 0'>"
        f"{branding.APP_NAME}</h2>"
        "<p style='text-align:left;color:#6b7280;margin:0 0 1.4rem 0'>"
        "Selecione uma área para ver as aplicações disponíveis.</p>",
        unsafe_allow_html=True,
    )

    apps_df = db.list_applications(only_active=True)
    fav_ids = db.list_favorite_app_ids(user["id"])

    ordered_areas = areas_mod.AREAS_ALPHA
    tab_labels = [areas_mod.display_name(a) for a in ordered_areas]
    tabs = st.tabs(tab_labels)

    for tab, area_name in zip(tabs, ordered_areas):
        with tab:
            area_apps = (
                apps_df[apps_df["AREA"] == area_name].copy()
                if not apps_df.empty
                else pd.DataFrame()
            )

            if area_apps.empty:
                st.markdown(
                    "<div class='empty-area'>Nenhuma aplicação cadastrada nesta área.</div>",
                    unsafe_allow_html=True,
                )
                continue

            area_apps = area_apps.sort_values(
                by="NAME", key=lambda s: s.str.upper(), kind="stable"
            )

            options = ["Todas as aplicações"] + area_apps["NAME"].tolist()
            choice = st.selectbox(
                "Filtrar aplicação",
                options=options,
                key=f"filter_{area_name}",
                label_visibility="collapsed",
            )
            if choice and choice != "Todas as aplicações":
                area_apps = area_apps[area_apps["NAME"] == choice]

            _cards.render_grid(
                area_apps,
                fav_ids=fav_ids,
                user_id=user["id"],
                context=f"home_{area_name}",
                access_token=auth.get_access_token(),
                refresh_token=auth.get_refresh_token(),
            )
