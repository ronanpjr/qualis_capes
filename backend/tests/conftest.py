"""
Shared fixtures for PyTest:
  - SQLite in-memory database (fast, isolated, no Docker needed)
  - FastAPI TestClient with DB dependency override

Marcador @pytest.mark.postgres para testes que requerem PostgreSQL (ex: ILIKE),
skipados automaticamente no SQLite.
"""

import pytest
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from main import app


def pytest_collection_modifyitems(config, items):
    """Pula testes marcados com 'postgres' quando rodando em SQLite."""
    skip_pg = pytest.mark.skip(reason="Requer PostgreSQL (ILIKE, window functions avançadas)")
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip_pg)


# ---------------------------------------------------------------------------
# Engine SQLite com function-scope para isolamento total
# ---------------------------------------------------------------------------
SEEDS = """
    INSERT INTO periodicos (issn, titulo, area, estrato) VALUES
    ('0000-0001', 'Journal of Testing A1',      'COMPUTACAO', 'A1'),
    ('0000-0002', 'Journal of Testing A2',      'COMPUTACAO', 'A2'),
    ('0000-0003', 'Journal of Testing B1',      'COMPUTACAO', 'B1'),
    ('0000-0004', 'Journal of Testing C',       'COMPUTACAO', 'C'),
    ('0000-0005', 'Revista Medica A1',          'MEDICINA I', 'A1'),
    ('0000-0006', 'Revista Medica A2',          'MEDICINA I', 'A2'),
    ('0000-0007', 'Advances in Engineering A1', 'ENGENHARIAS I', 'A1'),
    ('0000-0008', 'Testing ISSN Search',        'COMPUTACAO', 'A3'),
    ('1234-5678', 'ISSN Finder',                'COMPUTACAO', 'B2')
"""


@pytest.fixture()
def db():
    """Banco SQLite in-memory por teste — isolamento garantido."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text(SEEDS))
        conn.commit()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


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
