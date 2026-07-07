"""Entry point do Repositório de Aplicações FGV IBRE."""
from __future__ import annotations

import streamlit as st

from src import auth, branding, styles
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
    styles.inject_base()
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
        st.markdown(styles.HIDE_SIDEBAR, unsafe_allow_html=True)
    else:
        _sidebar(user)

    PAGES.get(page, login.render)()
    branding.render_footer()


if __name__ == "__main__":
    main()
