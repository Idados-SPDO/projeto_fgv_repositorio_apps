-- =============================================================
-- Tabela de favoritos por usuario
-- Database : BASES_SPDO
-- Schema   : DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO
-- =============================================================

USE DATABASE BASES_SPDO;
USE SCHEMA   DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO;

CREATE TABLE IF NOT EXISTS TBL_FAVORITOS_PROD (
    USER_ID    NUMBER NOT NULL,
    APP_ID     NUMBER NOT NULL,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USER_ID, APP_ID)
);
