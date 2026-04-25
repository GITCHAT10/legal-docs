import pytest
from mnos.core.db.base_class import Base
from mnos.core.db.session import engine

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
