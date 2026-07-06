"""Entry point do Repositório de Aplicações FGV IBRE."""
from __future__ import annotations

import streamlit as st

from src import auth, branding
from src.views import (
    admin_apps,
    admin_permissions,
    admin_users,
    change_password,
    favorites,
    home,
    login,
)


PAGES = {
    "home": home.render,
    "favorites": favorites.render,
    "change_password": change_password.render,
    "admin_users": admin_users.render,
    "admin_apps": admin_apps.render,
    "admin_permissions": admin_permissions.render,
    "login": login.render,
}

ADMIN_PAGES = {"admin_users", "admin_apps", "admin_permissions"}

PRE_LOGIN_PAGES = {"login", "change_password"}

_HIDE_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }
section[data-testid="stSidebar"] + div { margin-left: 0 !important; }
.block-container { padding-top: 3rem; }
</style>
"""

_SIDEBAR_CSS = """
<style>
.fgv-logo-wrap {
    display: flex; justify-content: center; align-items: center;
    padding: 4px 0 14px 0;
    border-bottom: 1px solid #e3e7ee;
    margin-bottom: 14px;
}
.fgv-user-card {
    background: #f4f6fa; border-radius: 10px;
    padding: 12px 14px; margin-bottom: 14px;
}
.fgv-user-card .welcome { font-size: 0.78rem; color: #6b7280; margin: 0 0 2px 0; }
.fgv-user-card .name    { font-size: 1.0rem;  color: #1f2937; font-weight: 600; margin: 0; }
.fgv-user-card .email   { font-size: 0.82rem; color: #4b5563; margin: 6px 0 0 0; word-break: break-all; }
.fgv-user-card .role-badge {
    display: inline-block; margin-top: 8px;
    background: #1f4e79; color: #fff;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 3px 10px; border-radius: 999px;
}
.fgv-user-card .role-badge.analista { background: #4b5d76; }
.fgv-nav-label {
    font-size: 0.72rem; color: #6b7280; letter-spacing: 0.5px;
    text-transform: uppercase; margin: 10px 0 4px 0;
}
</style>
"""


def _page_config() -> None:
    title = st.secrets.get("app", {}).get("title", "Repositório de Aplicações FGV IBRE")
    st.set_page_config(
        page_title=title,
        page_icon="\U0001F4DA",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _sidebar(user: dict) -> None:
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

        st.markdown(
            f"<div class='fgv-logo-wrap'>{branding.logo_html(height_px=52)}</div>",
            unsafe_allow_html=True,
        )

        role = user.get("role", "")
        st.markdown(
            f"""
            <div class='fgv-user-card'>
                <p class='welcome'>Bem-vindo,</p>
                <p class='name'>{user['name']}</p>
                <p class='email'>{user['email']}</p>
                <span class='role-badge {role}'>{role}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page = st.session_state.get("page")

        st.markdown("<div class='fgv-nav-label'>Navegação</div>", unsafe_allow_html=True)
        if st.button("⭐ Favoritos", use_container_width=True,
                     type="primary" if page == "favorites" else "secondary"):
            st.session_state["page"] = "favorites"
            st.rerun()
        if st.button("Aplicações", use_container_width=True,
                     type="primary" if page == "home" else "secondary"):
            st.session_state["page"] = "home"
            st.rerun()

        if auth.is_admin():
            st.markdown("<div class='fgv-nav-label'>Administração</div>", unsafe_allow_html=True)
            if st.button("Gerenciar usuários", use_container_width=True,
                         type="primary" if page == "admin_users" else "secondary"):
                st.session_state["page"] = "admin_users"
                st.rerun()
            if st.button("Gerenciar aplicações", use_container_width=True,
                         type="primary" if page == "admin_apps" else "secondary"):
                st.session_state["page"] = "admin_apps"
                st.rerun()
            if st.button("Gerenciar acessos", use_container_width=True,
                         type="primary" if page == "admin_permissions" else "secondary"):
                st.session_state["page"] = "admin_permissions"
                st.rerun()

        st.markdown("<div class='fgv-nav-label'>Conta</div>", unsafe_allow_html=True)
        if st.button("Alterar senha", use_container_width=True):
            st.session_state["page"] = "change_password"
            st.rerun()
        if st.button("Sair", use_container_width=True):
            auth.logout()
            st.rerun()


def main() -> None:
    _page_config()
    auth.init_session()

    user = auth.current_user()
    page = st.session_state.get("page", "login")

    if not user:
        page = "login"
    elif user.get("must_change_password") and page != "change_password":
        page = "change_password"
        st.session_state["page"] = page
    elif page in ADMIN_PAGES and not auth.is_admin():
        page = "home"
        st.session_state["page"] = page

    if page in PRE_LOGIN_PAGES:
        st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
    else:
        _sidebar(user)

    PAGES.get(page, login.render)()
    branding.render_footer()


if __name__ == "__main__":
    main()
