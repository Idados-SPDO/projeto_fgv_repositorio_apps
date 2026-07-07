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


def test_restore_user_not_found_clears_tokens(monkeypatch, state):
    monkeypatch.setattr(session_cookie, "load",
                        lambda: {"rt": "rt-1", "uid": 7, "email": "sumiu@fgv.br", "remember": True, "v": 1})
    monkeypatch.setattr(auth, "refresh_session", lambda: True)
    monkeypatch.setattr(auth.db, "get_user_by_email", lambda email: None)
    cleared = {"cookie": False}
    monkeypatch.setattr(session_cookie, "clear", lambda: cleared.__setitem__("cookie", True))

    auth.init_session()

    assert state["user"] is None
    assert state["refresh_token"] is None
    assert state["access_token"] is None
    assert cleared["cookie"] is True


def test_logout_does_not_re_restore(monkeypatch, state):
    # sessão logada
    state["user"] = {"id": 7, "email": "a@fgv.br"}
    state["access_token"] = "acc"
    state["refresh_token"] = "rt-1"
    # a chamada de rede do /logout é stubada
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: None)
    # simula cookie NÃO propagado: clear é no-op e load ainda devolve payload
    monkeypatch.setattr(session_cookie, "clear", lambda: None)
    monkeypatch.setattr(session_cookie, "load",
                        lambda: {"rt": "rt-1", "uid": 7, "email": "a@fgv.br", "remember": True, "v": 1})
    monkeypatch.setattr(auth, "refresh_session", lambda: True)
    monkeypatch.setattr(auth.db, "get_user_by_email", lambda email: {
        "USER_ID": 7, "EMAIL": "a@fgv.br", "FULL_NAME": "Ana",
        "ROLE": "user", "AREA": "IBRE", "MUST_CHANGE_PASSWORD": False})

    auth.logout()

    assert state.get("user") is None


def test_sync_cookie_token_uses_meta_not_cookie(monkeypatch, state):
    state["refresh_token"] = "rt-NEW"
    state["_cookie_meta"] = {"uid": 7, "email": "a@fgv.br", "remember": True}
    saved = {}
    monkeypatch.setattr(session_cookie, "save",
                        lambda rt, uid, email, remember: saved.update(
                            rt=rt, uid=uid, email=email, remember=remember))
    # se ler o cookie, falha o teste:
    monkeypatch.setattr(session_cookie, "load",
                        lambda: (_ for _ in ()).throw(AssertionError("não deveria reler o cookie")))

    auth._sync_cookie_token()

    assert saved == {"rt": "rt-NEW", "uid": 7, "email": "a@fgv.br", "remember": True}


def test_sync_cookie_token_noop_without_meta(monkeypatch, state):
    state["refresh_token"] = "rt-NEW"
    called = {"saved": False}
    monkeypatch.setattr(session_cookie, "save",
                        lambda *a, **k: called.__setitem__("saved", True))
    auth._sync_cookie_token()
    assert called["saved"] is False
