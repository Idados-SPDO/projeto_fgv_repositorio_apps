"""Tela de troca de senha (usuário autenticado)."""
from __future__ import annotations

import streamlit as st

from .. import auth, branding


def render() -> None:
    user = auth.require_login()
    forced = user.get("must_change_password", False)

    st.markdown(
        f"<div style='margin: 0 0 1.2rem 0;'>{branding.logo_html(height_px=56)}</div>",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.subheader("Alterar senha")
        if forced:
            st.warning("Por segurança, defina uma nova senha antes de prosseguir.")

        with st.form("change_pwd_form", clear_on_submit=True):
            current = st.text_input("Senha atual", type="password")
            new1 = st.text_input("Nova senha", type="password", help="Mínimo 8 caracteres")
            new2 = st.text_input("Confirme a nova senha", type="password")
            submitted = st.form_submit_button("Alterar senha", use_container_width=True, type="primary")

        if submitted:
            if not all([current, new1, new2]):
                st.error("Preencha todos os campos.")
                return
            if new1 != new2:
                st.error("As novas senhas não conferem.")
                return
            ok, msg = auth.change_own_password(user["id"], current, new1)
            if ok:
                st.success(msg)
                st.session_state["page"] = "home"
                st.rerun()
            else:
                st.error(msg)

        if not forced:
            if st.button("Voltar", use_container_width=True):
                st.session_state["page"] = "home"
                st.rerun()
