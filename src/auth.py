"""Autenticação: login via API centralizada, troca de senha, sessão."""
from __future__ import annotations

from typing import Optional

import bcrypt
import requests
import streamlit as st

from . import db


# ---------- sessão ------------------------------------------------------------

SESSION_KEYS = ("user", "page", "access_token", "refresh_token")


def init_session() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("refresh_token", None)


# ---------- login via API centralizada ----------------------------------------

def _auth_api_url() -> str:
    return st.secrets.get("auth_api", {}).get(
        "base_url", "http://54.172.164.97:8080"
    )


def login(email: str, password: str) -> tuple[bool, str]:
    url = f"{_auth_api_url()}/login"
    try:
        resp = requests.post(
            url,
            json={"email": email, "password": password},
            timeout=10,
        )
    except requests.RequestException as exc:
        return False, f"Erro de conexão com o serviço de autenticação: {exc}"

    if resp.status_code == 401:
        detail = resp.json().get("detail", "Email ou senha inválidos.")
        return False, detail
    if resp.status_code == 503:
        return False, "Serviço de autenticação indisponível no momento."
    if not resp.ok:
        return False, f"Erro inesperado (HTTP {resp.status_code})."

    data = resp.json()
    tokens = data.get("tokens", {})
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        return False, "Resposta inválida do serviço de autenticação."

    # Buscar dados completos do perfil no Snowflake (nome, role, area...)
    user = db.get_user_by_email(email)
    if not user:
        return False, "Usuário autenticado mas não encontrado na base de dados."

    # Guardar tokens e dados do usuário na sessão
    st.session_state["access_token"] = access_token
    st.session_state["refresh_token"] = refresh_token

    db.touch_last_login(user["USER_ID"])
    st.session_state["user"] = {
        "id": user["USER_ID"],
        "email": user["EMAIL"],
        "name": user["FULL_NAME"],
        "role": user["ROLE"],
        "area": user["AREA"],
        "must_change_password": bool(user["MUST_CHANGE_PASSWORD"]),
    }
    if user["MUST_CHANGE_PASSWORD"]:
        st.session_state["page"] = "change_password"
    else:
        has_favs = bool(db.list_favorite_app_ids(user["USER_ID"]))
        st.session_state["page"] = "favorites" if has_favs else "home"
    return True, ""


# ---------- token JWT ---------------------------------------------------------

def get_access_token() -> Optional[str]:
    """Retorna o access_token JWT da sessão atual (ou None)."""
    return st.session_state.get("access_token")


# ---------- sessão (cont.) ----------------------------------------------------

def logout() -> None:
    for key in SESSION_KEYS:
        st.session_state.pop(key, None)
    init_session()


def current_user() -> Optional[dict]:
    return st.session_state.get("user")


def is_admin() -> bool:
    user = current_user()
    return bool(user and user.get("role") == "admin")


def require_login() -> dict:
    user = current_user()
    if not user:
        st.session_state["page"] = "login"
        st.stop()
    return user


# ---------- troca de senha (mantida via Snowflake) ----------------------------

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def change_own_password(
    user_id: int, current_password: str, new_password: str
) -> tuple[bool, str]:
    user = db.get_user_by_email(st.session_state["user"]["email"])
    if not user or not verify_password(current_password, user["PASSWORD_HASH"]):
        return False, "Senha atual incorreta."
    if len(new_password) < 8:
        return False, "A nova senha deve ter ao menos 8 caracteres."
    if verify_password(new_password, user["PASSWORD_HASH"]):
        return False, "A nova senha precisa ser diferente da atual."

    db.change_user_password(user_id, hash_password(new_password))
    st.session_state["user"]["must_change_password"] = False
    return True, "Senha alterada com sucesso."
