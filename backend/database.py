"""
Database configuration — SQLAlchemy engine and session factory.
Connection URL is read from DATABASE_URL environment variable.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()


POSTGRES_USER = os.getenv("POSTGRES_USER", "qualis_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "qualis_pass")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres") # Nome do serviço no docker-compose
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "qualis_db")

# 2. Agora montamos a URL com o 'f'. 
# Como as variáveis acima já foram definidas, o NameError some.
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_URL)

engine = create_engine(DATABASE_URL)


engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # verifica conexão antes de usar
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency injection — yields a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
