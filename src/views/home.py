"""Tela principal: abas por área (alfabéticas) com filtro e cards."""
from __future__ import annotations

import streamlit as st

from .. import areas as areas_mod
from .. import auth, branding, db
from . import _cards


def render() -> None:
    user = auth.require_login()
    st.markdown(_cards.CARD_CSS, unsafe_allow_html=True)

    st.markdown(
        f"<h2 style='text-align:center;color:var(--fgv-blue);margin:0.4rem 0 0.2rem 0'>"
        f"{branding.APP_NAME}</h2>"
        "<p style='text-align:left;color:var(--fgv-muted);margin:0 0 1.4rem 0'>"
        "Selecione uma área para ver as aplicações disponíveis.</p>",
        unsafe_allow_html=True,
    )

    apps_df = db.list_applications(only_active=True)

    # só mostra abas de áreas que têm aplicações (menos ruído, menos DOM)
    if apps_df.empty:
        st.info("Nenhuma aplicação cadastrada ainda.")
        return

    non_empty_areas = [
        a for a in areas_mod.AREAS_ALPHA if (apps_df["AREA"] == a).any()
    ]
    if not non_empty_areas:
        st.info("Nenhuma aplicação cadastrada ainda.")
        return

    # tokens calculados uma vez (get_access_token pode renovar via rede)
    access_token = auth.get_access_token()
    refresh_token = auth.get_refresh_token()

    tab_labels = [
        f"{areas_mod.display_name(a)} ({int((apps_df['AREA'] == a).sum())})"
        for a in non_empty_areas
    ]
    tabs = st.tabs(tab_labels)

    for tab, area_name in zip(tabs, non_empty_areas):
        with tab:
            area_apps = apps_df[apps_df["AREA"] == area_name].sort_values(
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
                fetch=lambda df=area_apps: df,
                user_id=user["id"],
                context=f"home_{area_name}",
                access_token=access_token,
                refresh_token=refresh_token,
            )
