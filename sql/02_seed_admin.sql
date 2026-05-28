-- =============================================================
-- Seed do primeiro usuario admin
-- IMPORTANTE: substitua PASSWORD_HASH pelo hash bcrypt gerado.
--
-- Para gerar o hash localmente, execute no Python:
--     python -c "import bcrypt; print(bcrypt.hashpw(b'TROQUE_ESTA_SENHA', bcrypt.gensalt()).decode())"
--
-- Depois cole o hash retornado abaixo no lugar de <<HASH_BCRYPT>>.
-- O usuário admin será criado com MUST_CHANGE_PASSWORD = TRUE,
-- portanto será obrigado a trocar a senha no primeiro login.
-- =============================================================

USE DATABASE BASES_SPDO;
USE SCHEMA   DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO;

MERGE INTO TBL_USUARIOS_PROD t
USING (
    SELECT
        'admin@fgv.br'        AS EMAIL,
        '<<HASH_BCRYPT>>'     AS PASSWORD_HASH,
        'Administrador'       AS FULL_NAME,
        'admin'               AS ROLE,
        NULL                  AS AREA,
        TRUE                  AS IS_ACTIVE,
        TRUE                  AS MUST_CHANGE_PASSWORD
) s
ON t.EMAIL = s.EMAIL
WHEN NOT MATCHED THEN
    INSERT (EMAIL, PASSWORD_HASH, FULL_NAME, ROLE, AREA, IS_ACTIVE, MUST_CHANGE_PASSWORD)
    VALUES (s.EMAIL, s.PASSWORD_HASH, s.FULL_NAME, s.ROLE, s.AREA, s.IS_ACTIVE, s.MUST_CHANGE_PASSWORD);
