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


def test_save_without_secret_is_noop(monkeypatch):
    monkeypatch.setattr(session_cookie, "_fernet", lambda: None)
    calls = []
    monkeypatch.setattr(session_cookie, "_controller",
                        lambda: type("C", (), {"set": lambda self, *a, **k: calls.append(a)})())
    session_cookie.save("rt", 5, "e@fgv.br", True)  # não deve levantar
    assert calls == []


def test_load_without_secret_returns_none(monkeypatch):
    monkeypatch.setattr(session_cookie, "_fernet", lambda: None)
    assert session_cookie.load() is None
