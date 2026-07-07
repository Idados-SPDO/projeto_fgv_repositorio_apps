"""Cookie de sessão criptografado (Fernet) para persistir o login entre reloads.

O cookie `fgv_session` guarda, cifrado, o refresh_token + identidade mínima.
Só texto cifrado trafega no browser: sem a chave do servidor
(`st.secrets["session"]["cookie_key"]`) não vira credencial reutilizável.
"""
from __future__ import annotations

import json
from typing import Optional

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from streamlit_cookies_controller import CookieController

COOKIE_NAME = "fgv_session"
_PAYLOAD_VERSION = 1
_REMEMBER_MAX_AGE = 7 * 24 * 60 * 60  # 7 dias, em segundos


def _fernet() -> Optional[Fernet]:
    """Fernet a partir do segredo, ou None se o segredo não estiver configurado.

    Degradar para None (em vez de levantar) faz a persistência via cookie virar
    um no-op silencioso quando `st.secrets["session"]["cookie_key"]` falta ou é
    inválido — o login/carregamento continua funcionando, só sem "lembrar".
    """
    try:
        key = st.secrets["session"]["cookie_key"]
    except Exception:
        return None
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError):
        return None


def _encode(fernet: Fernet, refresh_token: str, user_id: int, email: str, remember: bool) -> str:
    payload = {
        "rt": refresh_token,
        "uid": user_id,
        "email": email,
        "remember": remember,
        "v": _PAYLOAD_VERSION,
    }
    return fernet.encrypt(json.dumps(payload).encode()).decode()


def _decode(fernet: Fernet, token: str) -> Optional[dict]:
    try:
        raw = fernet.decrypt(token.encode())
    except (InvalidToken, ValueError, TypeError):
        return None
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict) or payload.get("v") != _PAYLOAD_VERSION:
        return None
    return payload


def _controller() -> CookieController:
    return CookieController()


def save(refresh_token: str, user_id: int, email: str, remember: bool) -> None:
    fernet = _fernet()
    if fernet is None:
        return
    token = _encode(fernet, refresh_token, user_id, email, remember)
    ctrl = _controller()
    if remember:
        ctrl.set(COOKIE_NAME, token, max_age=_REMEMBER_MAX_AGE, secure=True, same_site="strict")
    else:
        ctrl.set(COOKIE_NAME, token, secure=True, same_site="strict")


def load() -> Optional[dict]:
    fernet = _fernet()
    if fernet is None:
        return None
    token = _controller().get(COOKIE_NAME)
    if not token:
        return None
    return _decode(fernet, token)


def clear() -> None:
    _controller().remove(COOKIE_NAME)
