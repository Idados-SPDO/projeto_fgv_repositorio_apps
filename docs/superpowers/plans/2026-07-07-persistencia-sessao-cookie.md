# Persistência de sessão via cookie criptografado — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Manter o login do hub Streamlit vivo através de reloads (F5) e hibernação do Community Cloud, via um cookie de sessão criptografado com o `refresh_token` + identidade.

**Architecture:** Um novo módulo `src/session_cookie.py` cifra `{refresh_token, user_id, email, remember, v}` com Fernet e grava/lê no cookie `fgv_session`. `src/auth.py` grava o cookie no login, reescreve na rotação do token, apaga no logout, e no `init_session()` reidrata a sessão a partir do cookie chamando `/refresh` + `db.get_user_by_email`. A tela de login ganha um checkbox "Lembrar de mim".

**Tech Stack:** Python, Streamlit (Community Cloud), `streamlit-cookies-controller` 0.0.4, `cryptography` (Fernet) 49.x, Snowflake connector, pytest.

## Global Constraints

- Host: Streamlit Community Cloud (componentes customizados e pacotes de `requirements.txt` funcionam; app hiberna por inatividade → sem store server-side durável).
- Nome do cookie: `fgv_session`. Flags: `secure=True`, `same_site="strict"`.
- Payload cifrado (Fernet): `{"rt": refresh_token, "uid": user_id, "email": email, "remember": bool, "v": 1}`.
- Chave Fernet vem de `st.secrets["session"]["cookie_key"]`.
- `remember=True` → cookie com `max_age=604800` (7 dias); `remember=False` → cookie de sessão (sem `max_age`/`expires`).
- `access_token` NUNCA é persistido — sempre re-derivado via `/refresh`.
- Proibido criar tabela nova no Snowflake.
- Auth server é a autoridade: todo cold load revalida via `/refresh`.

---

### Task 1: Módulo `session_cookie` — núcleo de criptografia + dependências e scaffolding de teste

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `src/session_cookie.py`
- Test: `tests/test_session_cookie_crypto.py`

**Interfaces:**
- Consumes: nada (primeira task).
- Produces:
  - `session_cookie._encode(fernet: Fernet, refresh_token: str, user_id: int, email: str, remember: bool) -> str`
  - `session_cookie._decode(fernet: Fernet, token: str) -> dict | None`
  - Constantes `session_cookie.COOKIE_NAME`, `session_cookie._REMEMBER_MAX_AGE`, `session_cookie._PAYLOAD_VERSION`.

- [ ] **Step 1: Instalar dependências (já vão pro requirements na Step 6)**

Run: `.venv/Scripts/python.exe -m pip install streamlit-cookies-controller pytest`
Expected: instala sem erro (`cryptography` já está presente).

- [ ] **Step 2: Criar `pytest.ini` e `tests/` para os testes acharem o pacote `src`**

Create `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Create `tests/__init__.py` (arquivo vazio).

- [ ] **Step 3: Escrever o teste que falha**

Create `tests/test_session_cookie_crypto.py`:

```python
import json

from cryptography.fernet import Fernet

from src import session_cookie


def _f() -> Fernet:
    return Fernet(Fernet.generate_key())


def test_encode_decode_roundtrip():
    f = _f()
    token = session_cookie._encode(f, "rt-123", 7, "a@fgv.br", True)
    assert session_cookie._decode(f, token) == {
        "rt": "rt-123", "uid": 7, "email": "a@fgv.br", "remember": True, "v": 1,
    }


def test_decode_wrong_key_returns_none():
    token = session_cookie._encode(_f(), "rt", 1, "a@fgv.br", False)
    assert session_cookie._decode(_f(), token) is None


def test_decode_corrupted_returns_none():
    assert session_cookie._decode(_f(), "isto-nao-e-um-token") is None


def test_decode_wrong_version_returns_none():
    f = _f()
    bad = f.encrypt(
        json.dumps({"rt": "x", "uid": 1, "email": "e", "remember": False, "v": 99}).encode()
    ).decode()
    assert session_cookie._decode(f, bad) is None
```

- [ ] **Step 4: Rodar o teste e confirmar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_session_cookie_crypto.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.session_cookie'`.

- [ ] **Step 5: Implementar o núcleo do módulo**

Create `src/session_cookie.py`:

```python
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
```

- [ ] **Step 6: Adicionar as dependências aos requirements**

Modify `requirements.txt` — adicionar ao final:

```
cryptography>=42
streamlit-cookies-controller>=0.0.4
```

Create `requirements-dev.txt`:

```
-r requirements.txt
pytest>=8
```

- [ ] **Step 7: Rodar os testes e confirmar que passam**

Run: `.venv/Scripts/python.exe -m pytest tests/test_session_cookie_crypto.py -v`
Expected: PASS (4 passed).

- [ ] **Step 8: Commit**

```bash
git add requirements.txt requirements-dev.txt pytest.ini tests/__init__.py tests/test_session_cookie_crypto.py src/session_cookie.py
git commit -m "feat(auth): núcleo de cripto do cookie de sessão (Fernet)"
```

---

### Task 2: Módulo `session_cookie` — I/O do cookie (save/load/clear)

**Files:**
- Modify: `src/session_cookie.py`
- Test: `tests/test_session_cookie_io.py`

**Interfaces:**
- Consumes: `_encode`, `_decode`, `_fernet`, `COOKIE_NAME`, `_REMEMBER_MAX_AGE` (Task 1).
- Produces:
  - `session_cookie.save(refresh_token: str, user_id: int, email: str, remember: bool) -> None`
  - `session_cookie.load() -> dict | None`
  - `session_cookie.clear() -> None`
  - `session_cookie._controller() -> CookieController` (seam para testes).

- [ ] **Step 1: Escrever o teste que falha**

Create `tests/test_session_cookie_io.py`:

```python
import pytest
from cryptography.fernet import Fernet

from src import session_cookie


class FakeController:
    def __init__(self):
        self.store = {}
        self.calls = []

    def set(self, name, value, **kwargs):
        self.store[name] = value
        self.calls.append((name, kwargs))

    def get(self, name):
        return self.store.get(name)

    def remove(self, name, **kwargs):
        self.store.pop(name, None)


@pytest.fixture
def fake(monkeypatch):
    f = Fernet(Fernet.generate_key())
    ctrl = FakeController()
    monkeypatch.setattr(session_cookie, "_fernet", lambda: f)
    monkeypatch.setattr(session_cookie, "_controller", lambda: ctrl)
    return ctrl


def test_save_remember_sets_max_age(fake):
    session_cookie.save("rt", 5, "e@fgv.br", True)
    name, kwargs = fake.calls[-1]
    assert name == session_cookie.COOKIE_NAME
    assert kwargs.get("max_age") == session_cookie._REMEMBER_MAX_AGE
    assert kwargs.get("secure") is True
    assert kwargs.get("same_site") == "strict"


def test_save_session_cookie_has_no_max_age(fake):
    session_cookie.save("rt", 5, "e@fgv.br", False)
    _, kwargs = fake.calls[-1]
    assert kwargs.get("max_age") is None
    assert kwargs.get("secure") is True


def test_load_roundtrip(fake):
    session_cookie.save("rt-9", 5, "e@fgv.br", True)
    assert session_cookie.load() == {
        "rt": "rt-9", "uid": 5, "email": "e@fgv.br", "remember": True, "v": 1,
    }


def test_load_absent_returns_none(fake):
    assert session_cookie.load() is None


def test_clear_removes_cookie(fake):
    session_cookie.save("rt", 5, "e@fgv.br", True)
    session_cookie.clear()
    assert session_cookie.load() is None
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_session_cookie_io.py -v`
Expected: FAIL com `AttributeError: module 'src.session_cookie' has no attribute 'save'`.

- [ ] **Step 3: Implementar save/load/clear**

Append em `src/session_cookie.py`:

```python
def _controller() -> CookieController:
    return CookieController()


def save(refresh_token: str, user_id: int, email: str, remember: bool) -> None:
    token = _encode(_fernet(), refresh_token, user_id, email, remember)
    ctrl = _controller()
    if remember:
        ctrl.set(COOKIE_NAME, token, max_age=_REMEMBER_MAX_AGE, secure=True, same_site="strict")
    else:
        ctrl.set(COOKIE_NAME, token, secure=True, same_site="strict")


def load() -> Optional[dict]:
    token = _controller().get(COOKIE_NAME)
    if not token:
        return None
    return _decode(_fernet(), token)


def clear() -> None:
    _controller().remove(COOKIE_NAME)
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `.venv/Scripts/python.exe -m pytest tests/test_session_cookie_io.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/session_cookie.py tests/test_session_cookie_io.py
git commit -m "feat(auth): I/O do cookie de sessão (save/load/clear)"
```

---

### Task 3: Integração em `src/auth.py` (restore, login, refresh, logout)

**Files:**
- Modify: `src/auth.py` (import na linha 11; `init_session` 19-24; `login` 35-86; `refresh_session` 91-115; `logout` 139-148)
- Test: `tests/test_auth_restore.py`

**Interfaces:**
- Consumes: `session_cookie.save/load/clear` (Task 2); `db.get_user_by_email`, `db.list_favorite_app_ids` (existentes).
- Produces:
  - `auth.login(email: str, password: str, remember: bool = False) -> tuple[bool, str]` (assinatura estendida — Task 4 depende disso)
  - `auth._restore_from_cookie() -> None`
  - `auth._sync_cookie_token() -> None`

- [ ] **Step 1: Escrever o teste que falha**

Create `tests/test_auth_restore.py`:

```python
import pytest

from src import auth, session_cookie


@pytest.fixture
def state(monkeypatch):
    s = {}
    monkeypatch.setattr(auth.st, "session_state", s)
    return s


_USER = {
    "USER_ID": 7, "EMAIL": "a@fgv.br", "FULL_NAME": "Ana",
    "ROLE": "user", "AREA": "IBRE", "MUST_CHANGE_PASSWORD": False,
}


def test_restore_success_populates_user(monkeypatch, state):
    monkeypatch.setattr(session_cookie, "load",
                        lambda: {"rt": "rt-1", "uid": 7, "email": "a@fgv.br", "remember": True, "v": 1})
    monkeypatch.setattr(auth, "refresh_session", lambda: True)
    monkeypatch.setattr(auth.db, "get_user_by_email", lambda email: _USER)
    monkeypatch.setattr(auth.db, "list_favorite_app_ids", lambda uid: set())

    auth.init_session()

    assert state["user"]["email"] == "a@fgv.br"
    assert state["refresh_token"] == "rt-1"
    assert state["page"] == "home"


def test_restore_refresh_rejected_stays_logged_out(monkeypatch, state):
    monkeypatch.setattr(session_cookie, "load",
                        lambda: {"rt": "rt-x", "uid": 7, "email": "a@fgv.br", "remember": False, "v": 1})
    monkeypatch.setattr(auth, "refresh_session", lambda: False)

    def _boom(email):
        raise AssertionError("não deveria consultar o banco quando o refresh falha")

    monkeypatch.setattr(auth.db, "get_user_by_email", _boom)

    auth.init_session()

    assert state["user"] is None


def test_restore_no_cookie_is_noop(monkeypatch, state):
    monkeypatch.setattr(session_cookie, "load", lambda: None)
    auth.init_session()
    assert state["user"] is None
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_auth_restore.py -v`
Expected: FAIL (`test_restore_success_populates_user` quebra: `state["user"]` fica `None` porque `init_session` ainda não reidrata do cookie).

- [ ] **Step 3: Importar `session_cookie` em `auth.py`**

Modify `src/auth.py` linha 11 — trocar:

```python
from . import db
```

por:

```python
from . import db, session_cookie
```

- [ ] **Step 4: Reidratar no `init_session` + adicionar `_restore_from_cookie`**

Modify `src/auth.py` — substituir o corpo de `init_session` (linhas 19-24) por:

```python
def init_session() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("refresh_token", None)
    st.session_state.setdefault("token_expires_at", 0)
    if st.session_state.get("user") is None:
        _restore_from_cookie()


def _restore_from_cookie() -> None:
    """Reconstrói a sessão a partir do cookie criptografado (sobrevive ao F5).

    O guard `_restoring` evita reentrância dentro da mesma execução (o
    refresh_session pode chamar logout -> init_session). Entre reruns o flag
    volta a False, então uma sincronização atrasada do cookie é reavaliada.
    """
    if st.session_state.get("_restoring"):
        return
    st.session_state["_restoring"] = True
    try:
        payload = session_cookie.load()
        if not payload:
            return
        st.session_state["refresh_token"] = payload["rt"]
        if not refresh_session():
            return  # refresh_session já fez logout + limpou o cookie
        user = db.get_user_by_email(payload["email"])
        if not user:
            session_cookie.clear()
            return
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
        elif st.session_state.get("page", "login") == "login":
            has_favs = bool(db.list_favorite_app_ids(user["USER_ID"]))
            st.session_state["page"] = "favorites" if has_favs else "home"
    finally:
        st.session_state["_restoring"] = False
```

Nota: NÃO chamar `db.touch_last_login` aqui — reload não é login novo.

- [ ] **Step 5: Gravar o cookie no `login`**

Modify `src/auth.py` — assinatura do `login` (linha 35):

```python
def login(email: str, password: str, remember: bool = False) -> tuple[bool, str]:
```

E logo após o bloco que monta `st.session_state["user"] = {...}` (após a linha 80), antes do `if user["MUST_CHANGE_PASSWORD"]:`, inserir:

```python
    session_cookie.save(refresh_token, user["USER_ID"], user["EMAIL"], remember)
```

- [ ] **Step 6: Reescrever o cookie na rotação do token (`refresh_session`)**

Modify `src/auth.py` — dentro de `refresh_session`, no bloco de sucesso (após setar `token_expires_at`, antes de `return True`), inserir a chamada e adicionar o helper logo após a função:

No bloco de sucesso:

```python
                st.session_state["token_expires_at"] = time.time() + (14 * 60)
                _sync_cookie_token()
                return True
```

Novo helper (adicionar após o `return False` final de `refresh_session`):

```python
def _sync_cookie_token() -> None:
    """Reescreve o cookie com o refresh_token rotacionado, preservando o remember.

    Lê uid/email/remember do cookie atual e reemite com o novo refresh_token.
    Se não há cookie (usuário não optou por persistir ou cookies bloqueados),
    não cria um do zero.
    """
    existing = session_cookie.load()
    if existing is None:
        return
    session_cookie.save(
        st.session_state["refresh_token"],
        existing["uid"],
        existing["email"],
        existing["remember"],
    )
```

- [ ] **Step 7: Apagar o cookie no `logout`**

Modify `src/auth.py` — em `logout`, inserir `session_cookie.clear()` logo antes do loop que limpa as chaves:

```python
def logout() -> None:
    token = st.session_state.get("access_token")
    if token:
        try:
            requests.post(f"{_auth_api_url()}/logout", json={"token": token}, timeout=5)
        except requests.RequestException:
            pass  # logout local prossegue mesmo se a revogação central falhar
    session_cookie.clear()
    for key in SESSION_KEYS:
        st.session_state.pop(key, None)
    init_session()
```

- [ ] **Step 8: Rodar os testes e confirmar que passam**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Expected: PASS (todos: crypto + io + restore).

- [ ] **Step 9: Commit**

```bash
git add src/auth.py tests/test_auth_restore.py
git commit -m "feat(auth): reidrata sessão do cookie e sincroniza rotação/logout"
```

---

### Task 4: Checkbox "Lembrar de mim" na tela de login

**Files:**
- Modify: `src/views/login.py` (bloco do formulário, linhas 30-44)

**Interfaces:**
- Consumes: `auth.login(email, password, remember)` (Task 3).
- Produces: nada (folha da árvore).

- [ ] **Step 1: Adicionar o checkbox e passar `remember` ao login**

Modify `src/views/login.py` — substituir o bloco do formulário (linhas 30-44) por:

```python
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="seu.email@fgv.br")
            password = st.text_input("Senha", type="password")
            remember = st.checkbox("Lembrar de mim", value=False)
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Informe email e senha.")
                return
            with st.spinner("Entrando..."):
                ok, msg = auth.login(email.strip(), password, remember)
            if ok:
                st.rerun()
            else:
                st.error(msg)
```

- [ ] **Step 2: Verificar que a suíte segue verde (nada quebrou)**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Expected: PASS (mesma contagem da Task 3).

- [ ] **Step 3: Commit**

```bash
git add src/views/login.py
git commit -m "feat(login): checkbox 'Lembrar de mim'"
```

---

### Task 5: Configuração do segredo + verificação manual ponta a ponta

**Files:**
- Modify (local, NÃO commitar): `.streamlit/secrets.toml`

**Interfaces:**
- Consumes: tudo das Tasks 1-4.
- Produces: nada (verificação).

- [ ] **Step 1: Gerar a chave Fernet**

Run: `.venv/Scripts/python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
Expected: imprime uma chave base64 (~44 chars). Copiar.

- [ ] **Step 2: Adicionar o segredo localmente**

Em `.streamlit/secrets.toml` (junto de `[snowflake]`, `[auth_api]`, `[app]`), adicionar:

```toml
[session]
cookie_key = "<cole a chave da Step 1>"
```

E no deploy: **Streamlit Community Cloud → app → Settings → Secrets** adicionar a mesma seção `[session]` com a mesma chave. (Trocar a chave depois = deslogar todos — é o kill switch de emergência.)

- [ ] **Step 3: Subir o app**

Run: `.venv/Scripts/streamlit run app.py`
Expected: app sobe sem erro em `http://localhost:8501`.

- [ ] **Step 4: Roteiro manual (marcar cada um)**

- [ ] Login SEM marcar "Lembrar de mim" → F5 → continua logado.
- [ ] Ainda sem "lembrar": fechar o browser e reabrir na URL → cai na tela de login.
- [ ] Login MARCANDO "Lembrar de mim" → fechar/reabrir o browser → continua logado.
- [ ] Clicar "Sair" → cookie some (F5 leva ao login).
- [ ] Após um F5 logado, abrir o card SSO do app 801 (url-updater) → abre autenticado (o `refresh_token` foi restaurado).

Nota conhecida (aceita): no primeiríssimo cold load pode haver um flash rápido da tela de login antes de reidratar (o componente de cookie sincroniza em um rerun). E após F5 o usuário volta à página inicial (favoritos/home), não necessariamente à página exata onde estava — a página não é persistida no cookie (YAGNI).

- [ ] **Step 5: Commit (se algum ajuste de código foi necessário no roteiro)**

Se o roteiro exigiu correções, commitar. Caso contrário, nada a commitar (a config de secrets não vai pro git).

```bash
git add -A && git commit -m "fix(auth): ajustes do roteiro manual de sessão persistente"
```

---

## Self-Review

**1. Spec coverage:**
- Módulo `session_cookie` (save/load/clear + cripto) → Tasks 1-2. ✓
- `init_session`/`_restore_from_cookie`/`login`/`refresh_session`/`logout` → Task 3. ✓
- Checkbox "Lembrar de mim" → Task 4. ✓
- `remember` no payload (correção da auto-revisão do spec) → payload em Task 1 + Task 2 (save) + Task 3 (`_sync_cookie_token` lê `remember`). ✓
- Gotcha do load assíncrono → guard `_restoring` + retry entre reruns (Task 3, Step 4) + nota na Task 5. ✓
- Dependências (`streamlit-cookies-controller`, `cryptography`) + secret `[session].cookie_key` → Task 1 (deps) + Task 5 (secret). ✓
- Segurança (Secure/SameSite=Strict, access_token nunca persistido, autoridade do auth server) → constraints globais + Task 2 (flags) + Task 3 (só rt persistido, refresh no cold load). ✓
- Testes (unit cripto + unit restore + manual) → Tasks 1, 2, 3, 5. ✓

**2. Placeholder scan:** `<cole a chave...>` na Task 5 é intencional (valor gerado pelo usuário, não vai pro git). Nenhum TODO/TBD em código.

**3. Type consistency:** payload usa sempre as chaves `rt`/`uid`/`email`/`remember`/`v`; `save(refresh_token, user_id, email, remember)` idêntico em Tasks 2/3; `login(..., remember=False)` idêntico em Tasks 3/4. ✓
