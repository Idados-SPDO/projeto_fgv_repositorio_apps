-- =============================================================
-- Schema do Repositório de Aplicações FGV IBRE
-- Database : BASES_SPDO
-- Schema   : DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO
-- =============================================================

USE DATABASE BASES_SPDO;
USE SCHEMA   DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO;

-- Tabela de usuarios
CREATE TABLE IF NOT EXISTS TBL_USUARIOS_PROD (
    USER_ID              NUMBER AUTOINCREMENT PRIMARY KEY,
    EMAIL                VARCHAR(255) NOT NULL UNIQUE,
    PASSWORD_HASH        VARCHAR(255) NOT NULL,
    FULL_NAME            VARCHAR(150) NOT NULL,
    ROLE                 VARCHAR(20)  NOT NULL,            -- admin | analista
    AREA                 VARCHAR(50),                      -- COWEB | COLETA | PRODUCAO_SETORIAL | GESTAO_DADOS | P&D
    IS_ACTIVE            BOOLEAN DEFAULT TRUE,
    MUST_CHANGE_PASSWORD BOOLEAN DEFAULT TRUE,
    LAST_LOGIN_AT        TIMESTAMP_NTZ,
    CREATED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT CK_TBL_USUARIOS_PROD_ROLE CHECK (ROLE IN ('admin', 'analista'))
);

-- Tabela de dominios das aplicacoes
CREATE TABLE IF NOT EXISTS TBL_DOMINIOS_APPS_PROD (
    APP_ID       NUMBER AUTOINCREMENT PRIMARY KEY,
    AREA         VARCHAR(50)  NOT NULL,                    -- COWEB | COLETA | PRODUCAO_SETORIAL | GESTAO_DADOS | P&D
    NAME         VARCHAR(150) NOT NULL,
    DESCRIPTION  VARCHAR(1000),
    URL          VARCHAR(1000) NOT NULL,
    ICON         VARCHAR(50),                              -- emoji opcional
    IS_ACTIVE    BOOLEAN DEFAULT TRUE,
    CREATED_BY   NUMBER,                                   -- TBL_USUARIOS_PROD.USER_ID
    CREATED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
