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


def _fernet() -> Fernet:
    key = st.secrets["session"]["cookie_key"]
    return Fernet(key.encode() if isinstance(key, str) else key)


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
