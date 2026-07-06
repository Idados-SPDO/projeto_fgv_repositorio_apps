"""Gerenciamento de acessos: concede/revoga o acesso de um colaborador a um app.

Grava em TBL_USUARIOS_PERMISSOES_PROD (USER_ID, APP_ID, CREATED_AT) — a mesma
tabela consultada pela lambda_auth para autorizar o acesso à aplicação.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import areas as areas_mod
from .. import auth, db


_TABLE_CSS = """
<style>
.perm-table-header {
    background: #f4f6fa; border-bottom: 2px solid #1f4e79;
    padding: 8px 4px; border-radius: 6px 6px 0 0;
}
.perm-table-header span { color: #1f4e79; font-weight: 700; font-size: 0.82rem;
    text-transform: uppercase; letter-spacing: 0.4px; }
.perm-meta { color: #94a3b8; font-size: 0.72rem; margin-top: 2px; }
</style>
"""


def _guard() -> dict:
    user = auth.require_login()
    if not auth.is_admin():
        st.error("Acesso restrito a administradores.")
        st.stop()
    return user


@st.dialog("Confirmar revogação de acesso")
def _dialog_revoke(user_id: int, app_id: int, who: str, app_name: str) -> None:
    st.warning(
        f"Revogar o acesso de **{who}** à aplicação **{app_name}**?\n\n"
        "O colaborador deixará de conseguir abrir essa aplicação."
    )
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True, key=f"cancel_rev_{user_id}_{app_id}"):
        st.rerun()
    if c2.button(
        "Confirmar revogação",
        type="primary",
        use_container_width=True,
        key=f"confirm_rev_{user_id}_{app_id}",
    ):
        db.revoke_app_permission(user_id, app_id)
        st.session_state["_flash"] = f"Acesso de {who} a {app_name} revogado."
        st.rerun()


def _grant_form(users_df: pd.DataFrame, apps_df: pd.DataFrame) -> None:
    st.markdown("#### Conceder acesso")
    if users_df.empty or apps_df.empty:
        st.info("É preciso ter ao menos um usuário e uma aplicação cadastrados.")
        return

    user_labels = {
        int(r["USER_ID"]): f"{r['FULL_NAME']} ({r['EMAIL']})"
        for _, r in users_df.iterrows()
    }
    app_labels = {
        int(r["APP_ID"]): f"[{areas_mod.display_name(r['AREA'])}] {r['NAME']}"
        for _, r in apps_df.iterrows()
    }

    with st.form("grant_permission_form"):
        c1, c2 = st.columns(2)
        with c1:
            user_id = st.selectbox(
                "Colaborador *",
                options=list(user_labels.keys()),
                format_func=lambda i: user_labels[i],
            )
        with c2:
            app_id = st.selectbox(
                "Aplicação *",
                options=list(app_labels.keys()),
                format_func=lambda i: app_labels[i],
            )
        submitted = st.form_submit_button("Conceder acesso", type="primary")

    if submitted:
        granted = db.grant_app_permission(int(user_id), int(app_id))
        who = user_labels[int(user_id)]
        app_name = app_labels[int(app_id)]
        if granted:
            st.session_state["_flash"] = f"Acesso concedido: {who} → {app_name}."
        else:
            st.session_state["_flash"] = (
                f"{who} já tinha acesso a {app_name}; nada foi alterado."
            )
        st.rerun()


# proporções das colunas da tabela de acessos
_COL_SPEC = [2.6, 2.4, 1.4, 0.9]
_COL_LABELS = ["Colaborador", "Aplicação", "Concedido em", "Revogar"]


def _table_header() -> None:
    cols = st.columns(_COL_SPEC, gap="small")
    for col, label in zip(cols, _COL_LABELS):
        col.markdown(
            f"<div class='perm-table-header'><span>{label}</span></div>",
            unsafe_allow_html=True,
        )


def _table_row(row: pd.Series) -> None:
    user_id = int(row["USER_ID"])
    app_id = int(row["APP_ID"])
    who = str(row["FULL_NAME"])
    app_name = str(row["APP_NAME"])
    cols = st.columns(_COL_SPEC, gap="small")

    cols[0].write(who)
    cols[0].markdown(
        f"<div class='perm-meta'>{row['EMAIL']}</div>", unsafe_allow_html=True
    )

    cols[1].write(app_name)
    cols[1].markdown(
        f"<div class='perm-meta'>{areas_mod.display_name(row['AREA'])}</div>",
        unsafe_allow_html=True,
    )

    if pd.notna(row.get("CREATED_AT")):
        cols[2].write(pd.to_datetime(row["CREATED_AT"]).strftime("%d/%m/%Y %H:%M"))
    else:
        cols[2].write("—")

    if cols[3].button(
        "🗑️",
        key=f"revoke_{user_id}_{app_id}",
        use_container_width=True,
        help=f"Revogar acesso de {who} a {app_name}",
    ):
        _dialog_revoke(user_id, app_id, who, app_name)


def render() -> None:
    _guard()
    st.header("Gerenciar acessos")
    st.caption(
        "Conceda ou revogue o acesso de um colaborador a uma aplicação. "
        "O acesso vale para o login único (SSO) das aplicações protegidas."
    )
    st.markdown(_TABLE_CSS, unsafe_allow_html=True)

    flash = st.session_state.pop("_flash", None)
    if flash:
        st.success(flash)

    users_df = db.list_users()
    apps_df = db.list_applications(only_active=False)

    _grant_form(users_df, apps_df)
    st.divider()

    st.markdown("#### Acessos concedidos")
    perms_df = db.list_permissions()
    if perms_df.empty:
        st.info("Nenhum acesso concedido ainda.")
        return

    st.caption(f"{len(perms_df)} acesso(s) concedido(s).")
    _table_header()
    for _, row in perms_df.iterrows():
        _table_row(row)
