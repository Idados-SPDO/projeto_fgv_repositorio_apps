# Repositório de Aplicações FGV IBRE

App Streamlit que centraliza o acesso (domínio/URL) das aplicações internas da FGV IBRE, organizado por área:
**COWEB · COLETA · PRODUÇÃO SETORIAL · GESTÃO DE DADOS · P&D**.

Persistência em **Snowflake** (banco `BASES_SPDO`, schema `DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO`).

## Funcionalidades

- **Login** por email/senha (hash bcrypt) com troca obrigatória no primeiro acesso.
- **Perfis**:
  - `admin` — gerencia usuários, cadastra/edita aplicações.
  - `analista` — apenas visualiza e acessa as aplicações.
- **Aplicações em abas por área** (ordem alfabética) com filtro por nome.
- **Favoritos** por usuário (estrela ⭐ no card); abre como tela inicial se o usuário tiver pelo menos uma aplicação favoritada.
- **Gerenciamento de usuários** (admin) com edição inline, popups de confirmação para reset/ativar/excluir.
- **Senha padrão** para novos usuários e resets: `FGV@12345`.

## Stack

- Streamlit 1.57
- Snowflake (`snowflake-connector-python`)
- bcrypt
- pandas

## Estrutura

```
projeto_fgv_repositorio_apps/
├── app.py                          # entry point + roteamento + sidebar
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml                 # tema (versionado)
│   ├── secrets.toml                # credenciais (NÃO versionado)
│   └── secrets.toml.example        # template para o secrets.toml
├── assets/
│   └── fgv_ibre.png                # logo usado no app
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_seed_admin.sql
│   └── 03_create_favoritos.sql
├── scripts/
│   └── bootstrap_db.py             # cria tabelas e (opcional) admin inicial
└── src/
    ├── auth.py                     # login + hash + sessão
    ├── db.py                       # acesso ao Snowflake
    ├── areas.py                    # constantes das áreas
    ├── branding.py                 # logo + rodapé
    └── views/
        ├── login.py
        ├── change_password.py
        ├── home.py                 # abas por área
        ├── favorites.py            # tela de favoritos
        ├── admin_users.py
        ├── admin_apps.py
        └── _cards.py               # card compartilhado (com estrela)
```

## Setup local

### 1. Dependências

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Credenciais

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# edite .streamlit\secrets.toml com seus dados do Snowflake
```

### 3. Criar tabelas + admin

Use o script ou execute os SQLs em `sql/` no Snowflake.

```powershell
# cria as 3 tabelas e o admin inicial
python scripts\bootstrap_db.py --email seu.email@fgv.br --name "Seu Nome" --password "SenhaInicial123"

# alternativa: só as tabelas (criar admin via SQL depois)
python scripts\bootstrap_db.py --tables-only
```

### 4. Rodar

```powershell
streamlit run app.py
```

Abre em http://localhost:8501. Faça login com o email/senha definidos; o sistema obrigará troca de senha.

## Deploy no Streamlit Cloud

1. **Push do repo** para o GitHub (público ou privado conectado).
2. Acesse https://share.streamlit.io e clique em **New app**.
3. Configure:
   - **Repository**: `seu-usuario/projeto_fgv_repositorio_apps`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Python version**: 3.12 (recomendado)
4. Em **Advanced settings → Secrets**, cole o conteúdo do seu `secrets.toml` (idêntico ao `.streamlit/secrets.toml.example`, já preenchido):

   ```toml
   [snowflake]
   account   = "..."
   user      = "..."
   password  = "..."
   role      = "..."
   warehouse = "..."
   database  = "BASES_SPDO"
   schema    = "DB_GESTAO_DADOS_EXTERNOS_APP_REPOSITORIO"

   [app]
   title = "Repositório de Aplicações FGV IBRE"
   ```

5. Clique em **Deploy** — o Streamlit Cloud lê o `requirements.txt` automaticamente.

> **Atenção:** o arquivo `.streamlit/secrets.toml` está no `.gitignore` e **nunca** deve ser commitado. As credenciais ficam apenas no painel do Streamlit Cloud.

## Senhas

- **Admin inicial**: definida no `bootstrap_db.py` (parâmetro `--password`).
- **Novos usuários** criados pelo admin: senha padrão **`FGV@12345`**, troca obrigatória no 1º login.
- **Reset** (admin): redefine para **`FGV@12345`**, troca obrigatória no próximo login.
- **Troca pelo usuário**: mínimo 8 caracteres, diferente da senha atual.
