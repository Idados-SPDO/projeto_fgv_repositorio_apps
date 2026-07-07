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
