"""Camada de acesso a dados (Snowflake).

Tabelas:
- TBL_USUARIOS_PROD       (usuarios da plataforma)
- TBL_DOMINIOS_APPS_PROD  (dominios/URLs das aplicacoes internas)
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Optional

import pandas as pd
import snowflake.connector
import streamlit as st


# ---------- conexao -----------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _get_connection():
    cfg = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=cfg["account"],
        user=cfg["user"],
        password=cfg["password"],
        role=cfg.get("role"),
        warehouse=cfg["warehouse"],
        database=cfg["database"],
        schema=cfg["schema"],
        client_session_keep_alive=True,
    )


@contextmanager
def _cursor():
    conn = _get_connection()
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()


def _run(sql: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
    with _cursor() as cur:
        cur.execute(sql, params or [])
        cols = [c[0] for c in cur.description] if cur.description else []
        return [dict(zip(cols, row)) for row in cur.fetchall()] if cols else []


def _execute(sql: str, params: Optional[Iterable[Any]] = None) -> int:
    with _cursor() as cur:
        cur.execute(sql, params or [])
        return cur.rowcount or 0


# ---------- TBL_USUARIOS_PROD -------------------------------------------------

def get_user_by_email(email: str) -> Optional[dict]:
    rows = _run(
        """
        SELECT USER_ID, EMAIL, PASSWORD_HASH, FULL_NAME, ROLE, AREA,
               IS_ACTIVE, MUST_CHANGE_PASSWORD, LAST_LOGIN_AT
          FROM TBL_USUARIOS_PROD
         WHERE LOWER(EMAIL) = LOWER(%s)
        """,
        [email],
    )
    return rows[0] if rows else None


def list_users() -> pd.DataFrame:
    rows = _run(
        """
        SELECT USER_ID, EMAIL, FULL_NAME, ROLE, AREA,
               IS_ACTIVE, MUST_CHANGE_PASSWORD, LAST_LOGIN_AT, CREATED_AT
          FROM TBL_USUARIOS_PROD
         ORDER BY FULL_NAME
        """
    )
    return pd.DataFrame(rows)


def create_user(
    email: str,
    password_hash: str,
    full_name: str,
    role: str,
    area: Optional[str],
) -> None:
    _execute(
        """
        INSERT INTO TBL_USUARIOS_PROD
            (EMAIL, PASSWORD_HASH, FULL_NAME, ROLE, AREA, IS_ACTIVE, MUST_CHANGE_PASSWORD)
        VALUES (%s, %s, %s, %s, %s, TRUE, TRUE)
        """,
        [email, password_hash, full_name, role, area],
    )


def update_user(
    user_id: int,
    full_name: str,
    role: str,
    area: Optional[str],
    is_active: bool,
) -> None:
    _execute(
        """
        UPDATE TBL_USUARIOS_PROD
           SET FULL_NAME = %s,
               ROLE      = %s,
               AREA      = %s,
               IS_ACTIVE = %s,
               UPDATED_AT = CURRENT_TIMESTAMP()
         WHERE USER_ID = %s
        """,
        [full_name, role, area, is_active, user_id],
    )


def reset_user_password(user_id: int, new_password_hash: str) -> None:
    _execute(
        """
        UPDATE TBL_USUARIOS_PROD
           SET PASSWORD_HASH = %s,
               MUST_CHANGE_PASSWORD = TRUE,
               UPDATED_AT = CURRENT_TIMESTAMP()
         WHERE USER_ID = %s
        """,
        [new_password_hash, user_id],
    )


def change_user_password(user_id: int, new_password_hash: str) -> None:
    _execute(
        """
        UPDATE TBL_USUARIOS_PROD
           SET PASSWORD_HASH = %s,
               MUST_CHANGE_PASSWORD = FALSE,
               UPDATED_AT = CURRENT_TIMESTAMP()
         WHERE USER_ID = %s
        """,
        [new_password_hash, user_id],
    )


def touch_last_login(user_id: int) -> None:
    _execute(
        "UPDATE TBL_USUARIOS_PROD SET LAST_LOGIN_AT = CURRENT_TIMESTAMP() WHERE USER_ID = %s",
        [user_id],
    )


def delete_user(user_id: int) -> None:
    _execute("DELETE FROM TBL_USUARIOS_PROD WHERE USER_ID = %s", [user_id])


# ---------- TBL_DOMINIOS_APPS_PROD --------------------------------------------

def list_applications(only_active: bool = True) -> pd.DataFrame:
    where = "WHERE IS_ACTIVE = TRUE" if only_active else ""
    rows = _run(
        f"""
        SELECT APP_ID, AREA, NAME, DESCRIPTION, URL, ICON,
               IS_ACTIVE, CREATED_BY, CREATED_AT, UPDATED_AT
          FROM TBL_DOMINIOS_APPS_PROD
          {where}
         ORDER BY AREA, NAME
        """
    )
    return pd.DataFrame(rows)


def create_application(
    area: str,
    name: str,
    description: Optional[str],
    url: str,
    icon: Optional[str],
    created_by: int,
) -> None:
    _execute(
        """
        INSERT INTO TBL_DOMINIOS_APPS_PROD
            (AREA, NAME, DESCRIPTION, URL, ICON, IS_ACTIVE, CREATED_BY)
        VALUES (%s, %s, %s, %s, %s, TRUE, %s)
        """,
        [area, name, description, url, icon, created_by],
    )


def update_application(
    app_id: int,
    area: str,
    name: str,
    description: Optional[str],
    url: str,
    icon: Optional[str],
    is_active: bool,
) -> None:
    _execute(
        """
        UPDATE TBL_DOMINIOS_APPS_PROD
           SET AREA = %s,
               NAME = %s,
               DESCRIPTION = %s,
               URL = %s,
               ICON = %s,
               IS_ACTIVE = %s,
               UPDATED_AT = CURRENT_TIMESTAMP()
         WHERE APP_ID = %s
        """,
        [area, name, description, url, icon, is_active, app_id],
    )


def delete_application(app_id: int) -> None:
    _execute("DELETE FROM TBL_DOMINIOS_APPS_PROD WHERE APP_ID = %s", [app_id])
    _execute("DELETE FROM TBL_FAVORITOS_PROD WHERE APP_ID = %s", [app_id])


# ---------- TBL_FAVORITOS_PROD ------------------------------------------------

def list_favorite_app_ids(user_id: int) -> set[int]:
    rows = _run(
        "SELECT APP_ID FROM TBL_FAVORITOS_PROD WHERE USER_ID = %s",
        [user_id],
    )
    return {int(r["APP_ID"]) for r in rows}


def toggle_favorite(user_id: int, app_id: int) -> bool:
    """Inverte o status de favorito. Retorna True se ficou favoritado."""
    with _cursor() as cur:
        cur.execute(
            "DELETE FROM TBL_FAVORITOS_PROD WHERE USER_ID = %s AND APP_ID = %s",
            [user_id, app_id],
        )
        if cur.rowcount and cur.rowcount > 0:
            return False
        cur.execute(
            "INSERT INTO TBL_FAVORITOS_PROD (USER_ID, APP_ID) VALUES (%s, %s)",
            [user_id, app_id],
        )
        return True


def list_favorite_applications(user_id: int) -> pd.DataFrame:
    rows = _run(
        """
        SELECT a.APP_ID, a.AREA, a.NAME, a.DESCRIPTION, a.URL, a.ICON,
               a.IS_ACTIVE, a.CREATED_BY, a.CREATED_AT, a.UPDATED_AT,
               f.CREATED_AT AS FAVORITED_AT
          FROM TBL_DOMINIOS_APPS_PROD a
          JOIN TBL_FAVORITOS_PROD    f ON f.APP_ID = a.APP_ID
         WHERE f.USER_ID = %s AND a.IS_ACTIVE = TRUE
         ORDER BY a.AREA, a.NAME
        """,
        [user_id],
    )
    return pd.DataFrame(rows)
