"""Bootstrap do banco no Snowflake: cria tabelas e (opcionalmente) o admin inicial.

Lê as credenciais do Snowflake de `.streamlit/secrets.toml` na raiz do projeto.

Uso:
    # cria apenas as tabelas
    python scripts/bootstrap_db.py --tables-only

    # cria as tabelas e o usuário admin inicial
    python scripts/bootstrap_db.py \
        --email seu.email@fgv.br \
        --name "Seu Nome" \
        --password "SenhaInicial123"

O usuário admin é criado com MUST_CHANGE_PASSWORD = TRUE, portanto será
obrigado a trocar a senha no primeiro login.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

import bcrypt
import snowflake.connector


ROOT = Path(__file__).resolve().parent.parent
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"


CREATE_USUARIOS = """
CREATE TABLE IF NOT EXISTS TBL_USUARIOS_PROD (
    USER_ID              NUMBER AUTOINCREMENT PRIMARY KEY,
    EMAIL                VARCHAR(255) NOT NULL UNIQUE,
    PASSWORD_HASH        VARCHAR(255) NOT NULL,
    FULL_NAME            VARCHAR(150) NOT NULL,
    ROLE                 VARCHAR(20)  NOT NULL,
    AREA                 VARCHAR(50),
    IS_ACTIVE            BOOLEAN DEFAULT TRUE,
    MUST_CHANGE_PASSWORD BOOLEAN DEFAULT TRUE,
    LAST_LOGIN_AT        TIMESTAMP_NTZ,
    CREATED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT CK_TBL_USUARIOS_PROD_ROLE CHECK (ROLE IN ('admin', 'analista'))
)
"""

CREATE_DOMINIOS = """
CREATE TABLE IF NOT EXISTS TBL_DOMINIOS_APPS_PROD (
    APP_ID       NUMBER AUTOINCREMENT PRIMARY KEY,
    AREA         VARCHAR(50)  NOT NULL,
    NAME         VARCHAR(150) NOT NULL,
    DESCRIPTION  VARCHAR(1000),
    URL          VARCHAR(1000) NOT NULL,
    ICON         VARCHAR(50),
    IS_ACTIVE    BOOLEAN DEFAULT TRUE,
    CREATED_BY   NUMBER,
    CREATED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
"""

CREATE_FAVORITOS = """
CREATE TABLE IF NOT EXISTS TBL_FAVORITOS_PROD (
    USER_ID    NUMBER NOT NULL,
    APP_ID     NUMBER NOT NULL,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USER_ID, APP_ID)
)
"""

MERGE_ADMIN = """
MERGE INTO TBL_USUARIOS_PROD t
USING (SELECT %s AS EMAIL, %s AS PASSWORD_HASH, %s AS FULL_NAME, %s AS ROLE) s
ON t.EMAIL = s.EMAIL
WHEN NOT MATCHED THEN
    INSERT (EMAIL, PASSWORD_HASH, FULL_NAME, ROLE, IS_ACTIVE, MUST_CHANGE_PASSWORD)
    VALUES (s.EMAIL, s.PASSWORD_HASH, s.FULL_NAME, s.ROLE, TRUE, TRUE)
"""


def _connect():
    if not SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo {SECRETS_PATH} não encontrado. "
            "Copie .streamlit/secrets.toml.example para .streamlit/secrets.toml "
            "e preencha as credenciais."
        )
    with SECRETS_PATH.open("rb") as fh:
        cfg = tomllib.load(fh)["snowflake"]

    return snowflake.connector.connect(
        account=cfg["account"],
        user=cfg["user"],
        password=cfg["password"],
        role=cfg.get("role"),
        warehouse=cfg["warehouse"],
        database=cfg["database"],
        schema=cfg["schema"],
    )


def main(email: str | None, name: str | None, password: str | None) -> int:
    conn = _connect()
    cur = conn.cursor()

    print("[1] criando TBL_USUARIOS_PROD ...")
    cur.execute(CREATE_USUARIOS)

    print("[2] criando TBL_DOMINIOS_APPS_PROD ...")
    cur.execute(CREATE_DOMINIOS)

    print("[3] criando TBL_FAVORITOS_PROD ...")
    cur.execute(CREATE_FAVORITOS)

    if email and name and password:
        if len(password) < 6:
            print("ERRO: a senha deve ter ao menos 6 caracteres.", file=sys.stderr)
            return 2
        print(f"[4] inserindo admin {email} ...")
        pwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
        cur.execute(MERGE_ADMIN, [email, pwd_hash, name, "admin"])

    print()
    print("[verificação] tabelas criadas:")
    cur.execute(
        "SELECT TABLE_NAME, ROW_COUNT "
        "FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_NAME IN ('TBL_USUARIOS_PROD','TBL_DOMINIOS_APPS_PROD','TBL_FAVORITOS_PROD') "
        "ORDER BY TABLE_NAME"
    )
    for row in cur.fetchall():
        print(" ", row)

    cur.close()
    conn.close()
    print()
    print("OK: bootstrap concluído.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap do banco no Snowflake.")
    parser.add_argument("--tables-only", action="store_true",
                        help="Apenas cria as tabelas (não insere admin).")
    parser.add_argument("--email", help="Email do admin a ser criado.")
    parser.add_argument("--name", help="Nome completo do admin.")
    parser.add_argument("--password", help="Senha inicial do admin (trocada no 1º login).")
    args = parser.parse_args()

    if args.tables_only:
        sys.exit(main(None, None, None))

    if not all([args.email, args.name, args.password]):
        parser.error(
            "Forneça --email, --name e --password (ou use --tables-only para "
            "criar apenas as tabelas)."
        )
    sys.exit(main(args.email, args.name, args.password))
