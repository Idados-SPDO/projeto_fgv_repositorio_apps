"""Tela de login."""
from __future__ import annotations

import streamlit as st

from .. import auth, branding


def render() -> None:
    title = st.secrets.get("app", {}).get("title", "Repositório de Aplicações")

    # logo no canto superior esquerdo
    st.markdown(
        f"<div style='margin: 0 0 1.2rem 0;'>{branding.logo_html(height_px=56)}</div>",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(
            f"<h2 style='text-align:center;margin-bottom:0.2rem;color:#1f4e79'>{title}</h2>"
            "<p style='text-align:center;color:#666;margin-top:0'>Acesse com seu email corporativo</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="seu.email@fgv.br")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Informe email e senha.")
                return
            ok, msg = auth.login(email.strip(), password)
            if ok:
                st.rerun()
            else:
                st.error(msg)
