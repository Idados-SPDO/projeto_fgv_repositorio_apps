# Persistência de sessão via cookie criptografado

**Data:** 2026-07-07
**Autor:** murilo.flores (com Claude)
**Status:** Aprovado (design) — aguardando revisão do spec

## Problema

O hub Streamlit (Repositório de Aplicações FGV IBRE) perde o login a cada
reload da página (F5). Toda a identidade e os tokens de sessão vivem em
`st.session_state`, que está amarrado à conexão WebSocket da aba: no F5 o
browser abre uma conexão nova, o Streamlit cria uma sessão vazia, e
`auth.current_user()` volta `None` — o usuário cai na tela de login.

Não é bug do código; é limitação conhecida do Streamlit (`session_state` nunca
sobrevive a reload). Falta persistir a credencial em algo que sobreviva ao F5.

## Contexto e restrições

- **Hospedagem:** Streamlit Community Cloud. Componentes customizados
  (`streamlit-cookies-controller`) e pacotes de `requirements.txt` funcionam;
  chamadas de rede externas funcionam. Porém o app **hiberna por inatividade** e
  reinicia a cada push → qualquer store **in-memory** ou em **filesystem** é
  volátil (perde a cada sleep/redeploy).
- **Sem tabela nova no Snowflake:** não é permitido criar tabela de sessões.
- **Sem FS persistente.** Logo **não há store server-side durável disponível** →
  a persistência precisa vir do browser (cookie), obrigatoriamente.
- **Autenticação atual:** `src/auth.py` faz login via API externa
  (`auth_api.base_url`, hoje `http://100.30.180.22:8080` — um serviço em ECS,
  não uma Lambda), recebendo `access_token` (JWT, ~15 min) e `refresh_token`
  (JWT, 7 dias). O perfil do usuário (nome, role, área, must_change_password)
  vem do Snowflake via `db.get_user_by_email`.
- **Os tokens são usados DEPOIS do login:** em `src/views/_cards.py:109-132`, o
  botão "Abrir" do app 801 (url-updater) faz um POST oculto com `access_token` +
  `refresh_token` para o `/auth-login` do sidecar de destino (SSO). Portanto,
  após um reload, **o `refresh_token` precisa estar disponível** — persistir só
  a identidade não basta (quebraria o SSO dos cards).

## Abordagem escolhida

**Cookie de sessão criptografado (stateless).** O cookie guarda
`Fernet.encrypt({refresh_token, user_id, email, remember, v:1})`. É a única
opção que:

1. Sobrevive a sleep e redeploy do Community Cloud (é stateless, mora no browser).
2. Mantém o SSO dos cards funcionando após F5 (temos o `refresh_token` de volta).
3. Mantém o auth server como autoridade (todo cold load revalida via `/refresh`).
4. Se o cookie vazar (XSS/log), o atacante obtém **texto cifrado** — sem a chave
   do servidor não vira credencial reutilizável.

Alternativas descartadas:
- **Store server-side (tabela Snowflake / SQLite / in-memory):** sem tabela
  permitida; SQLite e in-memory morrem no sleep/redeploy do Community Cloud.
- **Cookie de identidade assinado (sem token):** quebraria o SSO dos cards, que
  precisa do `refresh_token` após o reload.
- **Cookie com `refresh_token` cru:** token legível por JS (risco XSS sem a
  camada de cifra).

## Arquitetura

### Novo módulo: `src/session_cookie.py`

Isola toda a lógica de cookie + criptografia numa unidade testável.
Depende de: `streamlit-cookies-controller`, `cryptography` (Fernet), `st.secrets`.

Interface:

- `save(refresh_token: str, user_id: int, email: str, remember: bool) -> None`
  - Serializa `{rt, uid, email, remember, v:1}`, cifra com Fernet e grava o
    cookie `fgv_session` com `Secure`, `SameSite=Strict`. O `remember` vai no
    payload para que `refresh_session()` saiba, na rotação em cold load, se
    reemite como cookie de 7 dias ou de sessão.
  - `remember=True` → `max-age` de 7 dias; `remember=False` → cookie de sessão
    (sem expiry: sobrevive ao F5, morre ao fechar o browser).
- `load() -> dict | None`
  - Lê e descriptografa o cookie. Retorna o payload ou `None` se ausente,
    corrompido, com chave errada ou expirado (`InvalidToken`).
- `clear() -> None`
  - Remove o cookie `fgv_session`.
- Internamente, uma única instância de `CookieController` por run e
  `_fernet()` que lê a chave de `st.secrets["session"]["cookie_key"]`.

### Mudanças em `src/auth.py`

- `init_session()`: após os defaults, se `user is None`, chama
  `_restore_from_cookie()`.
- `_restore_from_cookie() -> None` (novo):
  1. `payload = session_cookie.load()`; se `None`, retorna (segue deslogado).
  2. Coloca `refresh_token` no `session_state` e chama `refresh_session()`.
  3. Se o refresh der certo: `user = db.get_user_by_email(payload["email"])`;
     reidrata `session_state["user"]` (role/área/flags frescos do Snowflake) e
     define a página inicial (favoritos se houver, senão home;
     change_password se `must_change_password`).
  4. Se o refresh for rejeitado: `session_cookie.clear()` e segue deslogado.
- `login()`: no sucesso, além do `session_state`, chama `session_cookie.save(...)`
  com a flag `remember` recebida da tela de login.
- `refresh_session()`: como o `refresh_token` **rotaciona**, após renovar com
  sucesso reescreve o cookie com o novo token, lendo a flag `remember` do payload
  atual (`session_cookie.load()`) para reemitir com o mesmo tempo de vida. Sem
  isso, o cookie guardaria um token velho e o próximo reload falharia. Só
  reescreve se `load()` achou um cookie válido (evita criar cookie do zero
  quando o browser bloqueia cookies).
- `logout()`: adiciona `session_cookie.clear()` ao fluxo atual (que já faz
  `POST /logout` e limpa o `session_state`).

### Mudanças em `src/views/login.py`

- Adiciona um checkbox "Lembrar de mim" no formulário e passa o valor para
  `auth.login(email, password, remember)`.

### Gotcha do carregamento assíncrono do cookie

O `streamlit-cookies-controller` só sincroniza os cookies do browser após o
primeiro render do componente. Numa primeira passada "fria", `load()` pode
retornar `None` mesmo havendo cookie.

Mitigação: instanciar o controller cedo (uma vez por run); usar uma flag em
`session_state` (`_cookie_probe_done`) que garante **no máximo um** `st.rerun()`
extra para dar tempo do componente sincronizar antes de concluir "sem cookie =
deslogado". Sem loop infinito (a flag impede reruns repetidos).

## Dependências e configuração

- `requirements.txt`: adicionar `streamlit-cookies-controller`. `cryptography`
  (Fernet) provavelmente já vem como dependência transitiva do
  `snowflake-connector-python`; declarar explicitamente para garantir.
- `st.secrets` (Community Cloud → app settings) e `.streamlit/secrets.toml`
  local: nova seção
  ```toml
  [session]
  cookie_key = "<chave Fernet>"   # gerar com Fernet.generate_key().decode()
  ```
- **Rotação de chave = logout de todos** (todos os cookies existentes viram
  inválidos). É o "kill switch" de emergência aceito.

## Modelo de segurança

- No browser trafega **só texto cifrado** contendo `refresh_token` + identidade;
  sem a chave do servidor não vira credencial reutilizável.
- `access_token` **nunca** é persistido — é sempre re-derivado via `/refresh` no
  cold load.
- `Secure` (exige HTTPS — garantido no Community Cloud) + `SameSite=Strict`.
- Auth server permanece autoridade: todo cold load chama `/refresh`;
  revogação/expiração central derruba a sessão na hora.
- O `refresh_token` **rotaciona** a cada renovação → token vazado é invalidado no
  próximo refresh legítimo.

## Estratégia de testes

- **Unit (`session_cookie`):** round-trip encrypt/decrypt; `load()` retorna
  `None` para cookie ausente, corrompido, chave errada e expirado.
- **Unit (`auth._restore_from_cookie`):** com `db.get_user_by_email` e o
  `requests`/`refresh_session` mockados — casos refresh OK (reidrata user) e
  refresh rejeitado (limpa cookie, segue deslogado).
- **Manual (Streamlit):**
  1. Login (sem "lembrar") → F5 → continua logado.
  2. Sem "lembrar" + fechar e reabrir o browser → cai no login.
  3. Com "lembrar" + fechar/reabrir → continua logado.
  4. Logout → cookie some, F5 leva ao login.
  5. Após F5, o card SSO (app 801) ainda abre autenticado.

## Fora de escopo (YAGNI)

- Store server-side / tabela de sessões.
- "Logout de todos os dispositivos" além do que o `/logout` atual já faz.
- Grace period em falha transitória de rede no `/refresh` (mantém o
  comportamento estrito atual: falha no refresh → logout).
