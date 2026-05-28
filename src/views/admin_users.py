"""Gerenciamento de usuários (admin)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import areas as areas_mod
from .. import auth, db


# senha inicial padrão para novos usuários e resets
DEFAULT_PASSWORD = "FGV@12345"


_TABLE_CSS = """
<style>
.admin-table-row { border-bottom: 1px solid #eef1f6; padding: 6px 0; }
.admin-table-header {
    background: #f4f6fa; border-bottom: 2px solid #1f4e79;
    padding: 8px 4px; border-radius: 6px 6px 0 0;
}
.admin-table-header span { color: #1f4e79; font-weight: 700; font-size: 0.82rem;
    text-transform: uppercase; letter-spacing: 0.4px; }
.admin-meta { color: #94a3b8; font-size: 0.72rem; margin-top: 2px; }
</style>
"""


def _guard() -> dict:
    user = auth.require_login()
    if not auth.is_admin():
        st.error("Acesso restrito a administradores.")
        st.stop()
    return user


# ---------- dialogs (popups de confirmação) -----------------------------------

@st.dialog("Confirmar reset de senha")
def _dialog_reset_password(user_id: int, email: str) -> None:
    st.warning(
        f"A senha de **{email}** será resetada para **`{DEFAULT_PASSWORD}`**.\n\n"
        "O usuário será obrigado a trocar a senha no próximo login."
    )
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True, key=f"cancel_reset_{user_id}"):
        st.rerun()
    if c2.button(
        "Confirmar reset",
        type="primary",
        use_container_width=True,
        key=f"confirm_reset_{user_id}",
    ):
        db.reset_user_password(user_id, auth.hash_password(DEFAULT_PASSWORD))
        st.session_state["_flash"] = f"Senha de {email} resetada para {DEFAULT_PASSWORD}."
        st.rerun()


@st.dialog("Confirmar exclusão de usuário")
def _dialog_delete_user(user_id: int, email: str) -> None:
    st.warning(
        f"Excluir definitivamente o usuário **{email}**?\n\n"
        "Esta ação é **irreversível** — os favoritos do usuário também serão removidos."
    )
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True, key=f"cancel_del_{user_id}"):
        st.rerun()
    if c2.button(
        "Confirmar exclusão",
        type="primary",
        use_container_width=True,
        key=f"confirm_del_{user_id}",
    ):
        db.delete_user(user_id)
        st.session_state["_flash"] = f"Usuário {email} excluído."
        st.rerun()


@st.dialog("Confirmar alteração de status")
def _dialog_toggle_active(
    user_id: int, email: str, current_state: bool, full_name: str, role: str, area
) -> None:
    new_state = not current_state
    action_label = "ativar" if new_state else "desativar"
    if new_state:
        st.info(f"Deseja **ativar** o usuário **{email}**?")
    else:
        st.warning(
            f"Deseja **desativar** o usuário **{email}**?\n\n"
            "Ele não conseguirá fazer login enquanto estiver inativo."
        )
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True, key=f"cancel_toggle_{user_id}"):
        st.rerun()
    if c2.button(
        f"Sim, {action_label}",
        type="primary",
        use_container_width=True,
        key=f"confirm_toggle_{user_id}",
    ):
        db.update_user(
            user_id=user_id,
            full_name=full_name,
            role=role,
            area=area,
            is_active=new_state,
        )
        st.session_state["_flash"] = (
            f"Usuário {email} {'ativado' if new_state else 'desativado'}."
        )
        st.rerun()


# ---------- novo usuário ------------------------------------------------------

def _new_user_form() -> None:
    with st.expander("Novo usuário", expanded=False):
        st.info(
            f"A senha inicial será sempre **`{DEFAULT_PASSWORD}`**. "
            "O usuário será obrigado a trocá-la no primeiro login."
        )
        with st.form("create_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                email = st.text_input("Email *")
                full_name = st.text_input("Nome completo *")
            with c2:
                role = st.selectbox("Perfil *", options=["analista", "admin"])
                area = st.selectbox(
                    "Área",
                    options=[None] + areas_mod.AREA_NAMES,
                    format_func=areas_mod.display_name,
                )
            submitted = st.form_submit_button("Criar usuário", type="primary")

            if submitted:
                if not all([email, full_name]):
                    st.error("Preencha email e nome completo.")
                    return
                if db.get_user_by_email(email.strip()):
                    st.error("Já existe um usuário com esse email.")
                    return
                db.create_user(
                    email=email.strip(),
                    password_hash=auth.hash_password(DEFAULT_PASSWORD),
                    full_name=full_name.strip(),
                    role=role,
                    area=area,
                )
                st.success(
                    f"Usuário {email} criado. Senha inicial: **{DEFAULT_PASSWORD}**"
                )
                st.rerun()


# ---------- tabela com botões por linha ---------------------------------------

# proporções das colunas da tabela
_COL_SPEC = [2.4, 1.6, 1.0, 1.2, 0.9, 0.7, 0.7]
_COL_LABELS = ["Email", "Nome", "Perfil", "Área", "Status", "Reset", "Excluir"]


def _table_header() -> None:
    cols = st.columns(_COL_SPEC, gap="small")
    for col, label in zip(cols, _COL_LABELS):
        col.markdown(
            f"<div class='admin-table-header'><span>{label}</span></div>",
            unsafe_allow_html=True,
        )


def _autosave(user_id: int, email: str, is_active: bool, me_id: int) -> None:
    """Callback de auto-save: chamado quando Nome/Perfil/Área mudam na linha."""
    name = str(st.session_state.get(f"name_{user_id}", "")).strip()
    role = st.session_state.get(f"role_{user_id}")
    area = st.session_state.get(f"area_{user_id}")

    if not name:
        st.toast("⚠️ Nome não pode ficar vazio.", icon="⚠️")
        return
    if user_id == me_id and role != "admin":
        st.toast("⚠️ Você não pode remover seu próprio perfil admin.", icon="⚠️")
        return

    db.update_user(
        user_id=user_id,
        full_name=name,
        role=role,
        area=area or None,
        is_active=is_active,
    )
    st.toast(f"✓ {email} atualizado.", icon="✅")


def _table_row(row: pd.Series, me: dict) -> None:
    user_id = int(row["USER_ID"])
    is_self = user_id == me["id"]
    is_active = bool(row["IS_ACTIVE"])
    cols = st.columns(_COL_SPEC, gap="small")

    # email + meta
    cols[0].write(row["EMAIL"])
    meta_parts = []
    if pd.notna(row.get("LAST_LOGIN_AT")):
        meta_parts.append(
            f"Último login: {pd.to_datetime(row['LAST_LOGIN_AT']).strftime('%d/%m/%Y %H:%M')}"
        )
    if bool(row.get("MUST_CHANGE_PASSWORD")):
        meta_parts.append("⚠️ deve trocar senha")
    if meta_parts:
        cols[0].markdown(
            f"<div class='admin-meta'>{' · '.join(meta_parts)}</div>",
            unsafe_allow_html=True,
        )

    save_args = (user_id, row["EMAIL"], is_active, me["id"])

    # nome (editável, auto-save ao perder foco / Enter)
    cols[1].text_input(
        "Nome",
        value=row["FULL_NAME"],
        key=f"name_{user_id}",
        label_visibility="collapsed",
        on_change=_autosave,
        args=save_args,
    )

    # perfil (editável, auto-save ao trocar)
    cols[2].selectbox(
        "Perfil",
        options=["analista", "admin"],
        index=["analista", "admin"].index(row["ROLE"]),
        key=f"role_{user_id}",
        label_visibility="collapsed",
        on_change=_autosave,
        args=save_args,
    )

    # área (editável, auto-save ao trocar)
    area_options = [None] + areas_mod.AREA_NAMES
    current_area = row["AREA"] if row["AREA"] in areas_mod.AREA_NAMES else None
    cols[3].selectbox(
        "Área",
        options=area_options,
        index=area_options.index(current_area),
        key=f"area_{user_id}",
        format_func=areas_mod.display_name,
        label_visibility="collapsed",
        on_change=_autosave,
        args=save_args,
    )

    # status (botão que abre dialog de confirmação)
    is_active = bool(row["IS_ACTIVE"])
    status_label = "✓ Ativo" if is_active else "✗ Inativo"
    if cols[4].button(
        status_label,
        key=f"toggle_{user_id}",
        type="primary" if is_active else "secondary",
        use_container_width=True,
        disabled=is_self,
        help="Você não pode desativar a si mesmo." if is_self else "Clique para alterar",
    ):
        _dialog_toggle_active(
            user_id=user_id,
            email=row["EMAIL"],
            current_state=is_active,
            full_name=row["FULL_NAME"],
            role=row["ROLE"],
            area=row["AREA"],
        )

    # reset senha
    if cols[5].button(
        "🔑",
        key=f"reset_{user_id}",
        use_container_width=True,
        help=f"Resetar senha para {DEFAULT_PASSWORD}",
    ):
        _dialog_reset_password(user_id, row["EMAIL"])

    # excluir
    if cols[6].button(
        "🗑️",
        key=f"del_{user_id}",
        use_container_width=True,
        disabled=is_self,
        help="Você não pode excluir a si mesmo." if is_self else "Excluir usuário",
    ):
        _dialog_delete_user(user_id, row["EMAIL"])


# ---------- entrypoint --------------------------------------------------------

def render() -> None:
    me = _guard()
    st.header("Gerenciar usuários")
    st.caption("Cadastre, edite ou desative usuários da plataforma.")
    st.markdown(_TABLE_CSS, unsafe_allow_html=True)

    # mensagem flash de dialog anterior
    flash = st.session_state.pop("_flash", None)
    if flash:
        st.success(flash)

    users_df = db.list_users()

    _new_user_form()
    st.divider()

    if users_df.empty:
        st.info("Nenhum usuário cadastrado ainda.")
        return

    st.markdown("#### Usuários cadastrados")
    st.caption(
        "As alterações em **Nome**, **Perfil** e **Área** são salvas automaticamente. "
        "As ações **Status**, **Reset** e **Excluir** pedem confirmação ao clicar."
    )

    _table_header()
    for _, row in users_df.iterrows():
        _table_row(row, me)
