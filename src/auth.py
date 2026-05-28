"""Autenticação: hash bcrypt, login, troca de senha, sessão."""
from __future__ import annotations

from typing import Optional

import bcrypt
import streamlit as st

from . import db


# ---------- hashing -----------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------- sessão ------------------------------------------------------------

SESSION_KEYS = ("user", "page")


def init_session() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "login")


def login(email: str, password: str) -> tuple[bool, str]:
    user = db.get_user_by_email(email)
    if not user:
        return False, "Email ou senha inválidos."
    if not user["IS_ACTIVE"]:
        return False, "Usuário inativo. Procure um administrador."
    if not verify_password(password, user["PASSWORD_HASH"]):
        return False, "Email ou senha inválidos."

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
