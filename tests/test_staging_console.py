import hashlib
import sqlite3

import pytest
from fastapi.testclient import TestClient

from staging_console import COOKIE, Store, create_app


@pytest.fixture
def setup(tmp_path, monkeypatch):
    path = str(tmp_path / "auth.sqlite")
    monkeypatch.setenv("MAC_EOS_ENV", "staging")
    monkeypatch.setenv("MAC_EOS_STAGING_ORIGIN", "https://testserver")
    monkeypatch.setenv("MAC_EOS_STAGING_DB", path)
    store = Store(path)
    store.provision("test-manager", "test-only-password-12345", "manager")
    store.provision("test-front", "test-only-password-12345", "front_desk")
    return store, TestClient(create_app(), base_url="https://testserver")


def login(client, username="test-manager"):
    return client.post("/session", json={"username": username, "password": "test-only-password-12345"}, headers={"origin": "https://testserver"})


def test_login_cookie_status_logout(setup):
    store, client = setup
    assert client.get("/status").status_code == 401
    response = login(client)
    assert response.status_code == 200
    for flag in ("HttpOnly", "Secure", "SameSite=strict"):
        assert flag in response.headers["set-cookie"]
    token = client.cookies.get(COOKIE)
    assert client.get("/status").json()["live_operations"] is False
    assert client.get("/audit").status_code == 200
    assert client.post("/logout", headers={"origin": "https://testserver"}).status_code == 200
    assert store.actor(token) is None
    assert client.get("/status").status_code == 401


def test_legacy_routes_and_csrf_denied(setup):
    _, client = setup
    assert client.post("/session", json={"username": "test-manager", "password": "anything"}).status_code == 403
    assert client.post("/session", json={}, headers={"origin": "https://evil.test"}).status_code == 403
    login(client)
    for path in ("/imoxon/hospitality/book", "/imoxon/aegis/identity/login", "/imoxon/payouts/release"):
        assert client.post(path, headers={"origin": "https://testserver"}).status_code == 404


def test_role_scope_and_identity_spoofing(setup):
    _, client = setup
    assert client.get("/status", headers={"X-AEGIS-IDENTITY": "SYSTEM"}).status_code == 401
    login(client, "test-front")
    assert client.get("/audit").status_code == 403
    assert client.get("/status?property=other").json()["property"] == "SALA_OMAGILI_TEST"


def test_expiry_revocation_and_persistence(setup):
    store, client = setup
    login(client)
    token = client.cookies.get(COOKIE)
    assert Store(store.path).actor(token)["role"] == "manager"
    with store.connect() as db:
        db.execute("UPDATE users SET active=0 WHERE username='test-manager'")
    assert store.actor(token) is None
    with store.connect() as db:
        db.execute("UPDATE users SET active=1")
        db.execute("UPDATE sessions SET expires=0")
    assert store.actor(token) is None


def test_failed_password_and_lockout(setup):
    store, _ = setup
    for _ in range(5):
        assert store.login("test-manager", "wrong") is None
    assert store.login("test-manager", "test-only-password-12345") is None
    with store.connect() as db:
        db.execute("UPDATE attempts SET until=0")
    assert store.login("test-manager", "test-only-password-12345")
    assert store.login("unknown", "test-only-password-12345") is None


def test_no_plaintext_tokens_or_passwords(setup):
    store, client = setup
    login(client)
    token = client.cookies.get(COOKIE)
    with store.connect() as db:
        assert db.execute("SELECT token FROM sessions").fetchone()[0] == hashlib.sha256(token.encode()).hexdigest()
        assert "test-only-password" not in db.execute("SELECT password FROM users LIMIT 1").fetchone()[0]
        assert token not in str(list(db.execute("SELECT * FROM audit")))


def test_config_fails_closed(setup, monkeypatch):
    monkeypatch.setenv("MAC_EOS_ENV", "production")
    with pytest.raises(RuntimeError):
        create_app()
    monkeypatch.setenv("MAC_EOS_ENV", "staging")
    monkeypatch.setenv("MAC_EOS_STAGING_ORIGIN", "http://testserver")
    with pytest.raises(RuntimeError):
        create_app()


def test_duplicate_account_cannot_override_role(setup):
    store, _ = setup
    with pytest.raises(sqlite3.IntegrityError):
        store.provision("test-front", "test-only-password-12345", "manager")
