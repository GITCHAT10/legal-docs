"""Isolated MAC EOS inspection console. Never mount the legacy API here."""
import getpass
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

ROLES = {"front_desk", "housekeeping", "finance", "manager"}
COOKIE = "__Host-mac-eos-staging"
PROPERTY = "SALA_OMAGILI_TEST"


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()


class Store:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, salt TEXT NOT NULL, password TEXT NOT NULL,
                    role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY, username TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts (
                    username TEXT PRIMARY KEY, count INTEGER NOT NULL, until REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, at REAL NOT NULL, username TEXT NOT NULL, event TEXT NOT NULL);
            """)
        os.chmod(path, 0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def provision(self, username, password, role):
        if role not in ROLES or not 1 <= len(username) <= 128 or len(password) < 16:
            raise ValueError("Valid role, username, and password of at least 16 characters required")
        salt = secrets.token_hex(16)
        with self.connect() as db:
            db.execute("INSERT INTO users(username,salt,password,role) VALUES(?,?,?,?)",
                       (username, salt, password_hash(password, salt), role))
            db.execute("INSERT INTO audit(at,username,event) VALUES(?,?,?)", (time.time(), username, "provisioned"))

    def login(self, username, password):
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            attempt = db.execute("SELECT * FROM attempts WHERE username=?", (username,)).fetchone()
            if attempt and attempt["count"] >= 5 and attempt["until"] > now:
                return None
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            digest = password_hash(password, user["salt"] if user else "00" * 16)
            valid = user and user["active"] and hmac.compare_digest(digest, user["password"])
            db.execute("INSERT INTO audit(at,username,event) VALUES(?,?,?)",
                       (now, username, "login_ok" if valid else "login_denied"))
            if not valid:
                count = attempt["count"] + 1 if attempt and attempt["until"] > now else 1
                until = attempt["until"] if attempt and attempt["until"] > now else now + 900
                db.execute("INSERT OR REPLACE INTO attempts VALUES(?,?,?)", (username, count, until))
                return None
            db.execute("DELETE FROM attempts WHERE username=?", (username,))
            db.execute("DELETE FROM sessions WHERE expires<=?", (now,))
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO sessions VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), username, now + 1800))
            return token

    def actor(self, token):
        with self.connect() as db:
            row = db.execute("""SELECT u.username,u.role FROM sessions s JOIN users u ON u.username=s.username
                WHERE s.token=? AND s.expires>? AND u.active=1""",
                (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            return dict(row) if row and row["role"] in ROLES else None

    def logout(self, token):
        with self.connect() as db:
            key = hashlib.sha256(token.encode()).hexdigest()
            row = db.execute("SELECT username FROM sessions WHERE token=?", (key,)).fetchone()
            db.execute("DELETE FROM sessions WHERE token=?", (key,))
            if row:
                db.execute("INSERT INTO audit(at,username,event) VALUES(?,?,?)", (time.time(), row["username"], "logout"))


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


def create_app():
    if os.environ.get("MAC_EOS_ENV") != "staging":
        raise RuntimeError("MAC_EOS_ENV must explicitly be staging")
    origin = os.environ["MAC_EOS_STAGING_ORIGIN"].rstrip("/")
    if not origin.startswith("https://"):
        raise RuntimeError("HTTPS origin required")
    store = Store(os.environ["MAC_EOS_STAGING_DB"])
    # Load real code in this isolated process, without mounting its unsafe routes.
    from main import hospitality, shadow_core

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def boundaries(request, call_next):
        if request.method not in {"GET", "HEAD"} and request.headers.get("origin") != origin:
            return JSONResponse({"detail": "Origin denied"}, status_code=403)
        if request.headers.get("content-length", "0").isdigit() and int(request.headers.get("content-length", "0")) > 4096:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    def actor(request):
        result = store.actor(request.cookies.get(COOKIE, ""))
        if not result:
            raise HTTPException(401, "Login required")
        return result

    @app.get("/", response_class=HTMLResponse)
    def index():
        return Path(__file__).with_name("staging_ui.html").read_text()

    @app.get("/console.js")
    def script():
        from fastapi.responses import Response
        return Response(Path(__file__).with_name("staging_ui.js").read_text(), media_type="text/javascript")

    @app.get("/console.css")
    def stylesheet():
        from fastapi.responses import Response
        return Response(Path(__file__).with_name("staging_ui.css").read_text(), media_type="text/css")

    @app.post("/session")
    def login(credentials: Credentials):
        token = store.login(credentials.username, credentials.password)
        if not token:
            raise HTTPException(401, "Login denied; after repeated attempts, wait 15 minutes")
        response = JSONResponse({"authenticated": True})
        response.set_cookie(COOKIE, token, secure=True, httponly=True, samesite="strict", max_age=1800, path="/")
        return response

    @app.post("/logout")
    def logout(request: Request):
        store.logout(request.cookies.get(COOKIE, ""))
        response = JSONResponse({"authenticated": False})
        response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="strict", path="/")
        return response

    @app.get("/status")
    def status(request: Request):
        user = actor(request)
        return {"actor": user, "environment": "staging", "property": PROPERTY,
                "mode": "READ_ONLY_INSPECTION", "live_operations": False,
                "backend": type(hospitality).__name__, "shadow_integrity": shadow_core.verify_integrity(),
                "booking_uat": "BLOCKED: no durable room inventory or full hotel lifecycle verified",
                "property_seeded": False}

    @app.get("/audit")
    def audit(request: Request):
        if actor(request)["role"] != "manager":
            raise HTTPException(403, "Manager required")
        with store.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 50")]

    return app


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Provision a staging-only account locally; no default users")
    parser.add_argument("username")
    parser.add_argument("role", choices=sorted(ROLES))
    args = parser.parse_args()
    if os.environ.get("MAC_EOS_ENV") != "staging":
        raise SystemExit("Staging environment required")
    password = getpass.getpass("New password (16+ characters): ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords differ")
    Store(os.environ["MAC_EOS_STAGING_DB"]).provision(args.username, password, args.role)
    print("Staging-only account provisioned; no operational authority granted.")
