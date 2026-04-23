import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_apollo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_apollo_deploy_init_fail_closed():
    # No Device ID -> Should fail 401
    res = client.post("/api/v1/apollo/deploy/init", params={"handshake_id": "MIG-01"})
    assert res.status_code == 422 # FastAPI validation for Header(...)

def test_apollo_deploy_init_success():
    res = client.post(
        "/api/v1/apollo/deploy/init",
        params={"handshake_id": "MIG-APOLLO-SKYI-2026-CTRL-01"},
        headers={"X-Device-ID": "MIG-HW-ENCLAVE-01"}
    )
    assert res.status_code == 200
    assert "deploy_id" in res.json()

def test_profit_guard_logic():
    from mnos.core.apollo.components.core import ProfitGuard
    pg = ProfitGuard()
    assert pg.check_threshold(100.0, 50.0) is True
    assert pg.check_threshold(50.0, 100.0) is False
