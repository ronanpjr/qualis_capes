"""
Shared fixtures for PyTest:
  - SQLite in-memory database (fast, isolated, no Docker needed)
  - FastAPI TestClient with DB dependency override
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# Engine SQLite in-memory para isolamento total dos testes
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Cria esquema + dados de exemplo uma única vez por sessão de teste."""
    Base.metadata.create_all(bind=engine)

    # Popula com dados de fixture
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO periodicos (issn, titulo, area, estrato) VALUES
            ('0000-0001', 'Journal of Testing A1',      'COMPUTAÇÃO', 'A1'),
            ('0000-0002', 'Journal of Testing A2',      'COMPUTAÇÃO', 'A2'),
            ('0000-0003', 'Journal of Testing B1',      'COMPUTAÇÃO', 'B1'),
            ('0000-0004', 'Journal of Testing C',       'COMPUTAÇÃO', 'C'),
            ('0000-0005', 'Revista Médica A1',          'MEDICINA I', 'A1'),
            ('0000-0006', 'Revista Médica A2',          'MEDICINA I', 'A2'),
            ('0000-0007', 'Advances in Engineering A1', 'ENGENHARIAS I', 'A1'),
            ('0000-0008', 'Testing ISSN Search',       'COMPUTAÇÃO', 'A3'),
            ('1234-5678', 'ISSN Finder',               'COMPUTAÇÃO', 'B2')
        """))
        conn.commit()

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(db_engine):
    """Sessão de banco de dados isolada com rollback após cada teste."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient com override da dependência de banco de dados."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
