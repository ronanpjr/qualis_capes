"""
SQLAlchemy ORM model for the periodicos table.
Used for table creation and type reference — queries use raw SQL (see queries.py).
"""

from sqlalchemy import Column, Integer, String, Index
from database import Base


class Periodico(Base):
    __tablename__ = "periodicos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issn = Column(String(20), nullable=False)
    titulo = Column(String(500), nullable=False)
    area = Column(String(200), nullable=False)
    estrato = Column(String(5), nullable=False)

    def __repr__(self) -> str:
        return f"<Periodico {self.issn} — {self.estrato}>"


# Índices para performance nas queries mais frequentes
Index("ix_periodicos_area", Periodico.area)
Index("ix_periodicos_estrato", Periodico.estrato)
Index("ix_periodicos_area_estrato", Periodico.area, Periodico.estrato)
