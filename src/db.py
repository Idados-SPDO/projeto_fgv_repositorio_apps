"""Camada de acesso a dados (Snowflake).

Tabelas:
- TBL_USUARIOS_PROD             (usuarios da plataforma)
- TBL_DOMINIOS_APPS_PROD        (dominios/URLs das aplicacoes internas)
- TBL_FAVORITOS_PROD            (favoritos por usuario)
- TBL_USUARIOS_PERMISSOES_PROD  (acesso de um usuario a um app; lido pela lambda_auth)
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


# ---------- cache ------------------------------------------------------------
#
# Streamlit re-executa o script inteiro a cada interação. Sem cache, cada rerun
# repaga o custo das queries de leitura no Snowflake. As leituras abaixo são
# cacheadas (@st.cache_data) e invalidadas explicitamente após cada escrita que
# as afeta, via _bust(). TTL curto como rede de segurança para mudanças feitas
# fora do app. get_user_by_email NÃO é cacheada (usada na autenticação: precisa
# sempre refletir o hash de senha atual).

_CACHE_TTL = 300  # segundos


def _bust(*funcs) -> None:
    """Limpa o cache das funções de leitura passadas."""
    for fn in funcs:
        try:
            fn.clear()
        except Exception:
            pass


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


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
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
    _bust(list_users)


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
    _bust(list_users, list_permissions)


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
    _bust(list_users)


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
    _bust(list_users)


def touch_last_login(user_id: int) -> None:
    _execute(
        "UPDATE TBL_USUARIOS_PROD SET LAST_LOGIN_AT = CURRENT_TIMESTAMP() WHERE USER_ID = %s",
        [user_id],
    )
    _bust(list_users)


def delete_user(user_id: int) -> None:
    _execute("DELETE FROM TBL_USUARIOS_PROD WHERE USER_ID = %s", [user_id])
    _bust(list_users, list_permissions)


# ---------- TBL_DOMINIOS_APPS_PROD --------------------------------------------

@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
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
    _bust(list_applications, list_favorite_applications, list_permissions)


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
    _bust(list_applications, list_favorite_applications, list_favorite_app_ids, list_permissions)


def delete_application(app_id: int) -> None:
    _execute("DELETE FROM TBL_DOMINIOS_APPS_PROD WHERE APP_ID = %s", [app_id])
    _execute("DELETE FROM TBL_FAVORITOS_PROD WHERE APP_ID = %s", [app_id])
    _bust(list_applications, list_favorite_applications, list_favorite_app_ids, list_permissions)


# ---------- TBL_FAVORITOS_PROD ------------------------------------------------

@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
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
            result = False
        else:
            cur.execute(
                "INSERT INTO TBL_FAVORITOS_PROD (USER_ID, APP_ID) VALUES (%s, %s)",
                [user_id, app_id],
            )
            result = True
    _bust(list_favorite_app_ids, list_favorite_applications)
    return result


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
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


# ---------- TBL_USUARIOS_PERMISSOES_PROD --------------------------------------

@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def list_permissions() -> pd.DataFrame:
    """Todas as permissões concedidas, já com nome do usuário e da aplicação."""
    rows = _run(
        """
        SELECT p.USER_ID, p.APP_ID, p.CREATED_AT,
               u.FULL_NAME, u.EMAIL,
               a.NAME AS APP_NAME, a.AREA
          FROM TBL_USUARIOS_PERMISSOES_PROD p
          JOIN TBL_USUARIOS_PROD      u ON u.USER_ID = p.USER_ID
          JOIN TBL_DOMINIOS_APPS_PROD a ON a.APP_ID = p.APP_ID
         ORDER BY a.NAME, u.FULL_NAME
        """
    )
    return pd.DataFrame(rows)


def grant_app_permission(user_id: int, app_id: int) -> bool:
    """Concede acesso do usuário ao app. Retorna True se inseriu, False se já existia.

    O INSERT ... WHERE NOT EXISTS evita linhas duplicadas mesmo sem constraint
    de unicidade na tabela. CREATED_AT usa o default CURRENT_TIMESTAMP().
    """
    inserted = _execute(
        """
        INSERT INTO TBL_USUARIOS_PERMISSOES_PROD (USER_ID, APP_ID, CREATED_AT)
        SELECT %s, %s, CURRENT_TIMESTAMP()
         WHERE NOT EXISTS (
             SELECT 1 FROM TBL_USUARIOS_PERMISSOES_PROD
              WHERE USER_ID = %s AND APP_ID = %s
         )
        """,
        [user_id, app_id, user_id, app_id],
    )
    _bust(list_permissions)
    return inserted > 0


def revoke_app_permission(user_id: int, app_id: int) -> None:
    _execute(
        "DELETE FROM TBL_USUARIOS_PERMISSOES_PROD WHERE USER_ID = %s AND APP_ID = %s",
        [user_id, app_id],
    )
    _bust(list_permissions)
