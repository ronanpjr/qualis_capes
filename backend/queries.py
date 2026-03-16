"""
Custom SQL queries — raw SQL via SQLAlchemy text() for performance-critical endpoints.
This module demonstrates intentional use of SQL beyond ORM abstractions:
  - Window functions (COUNT(*) OVER) for single-pass pagination
  - CASE WHEN for semantic ordering of estratos
  - ILIKE for case-insensitive text search
  - Composite filter building with parameterized inputs (no interpolation)
"""

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.orm import Session
from typing import Optional

from models import Periodico


# Ordem canônica dos estratos (A1 mais alto → C mais baixo)
ESTRATO_ORDER = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B1": 5, "B2": 6, "B3": 7, "B4": 8, "C": 9}

VALID_ESTRATOS = set(ESTRATO_ORDER.keys())


def get_areas(db: Session) -> list[str]:
    """
    Lista todas as áreas distintas, ordenadas alfabeticamente.
    Raw SQL: SELECT DISTINCT com ORDER BY — simplesmente mais direto que ORM aqui.
    """
    result = db.execute(
        text("SELECT DISTINCT area FROM periodicos ORDER BY area")
    )
    return [row[0] for row in result.fetchall()]


def search_periodicos(
    db: Session,
    area: Optional[str] = None,
    estrato: Optional[list[str]] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 30,
) -> tuple[list[dict], int]:
    """
    Busca periódicos com filtros opcionais usando SQLAlchemy Expression Language.

    Técnicas utilizadas:
    - SQLAlchemy select().where() para construção dinâmica segura de queries
    - Proteção automática contra SQL injection via parameterização
    - ilike() para busca case-insensitive em título e ISSN
    - Window function COUNT(*) OVER() para obter total sem query separada
    - LIMIT/OFFSET para paginação server-side
    """
    # Construir filtros dinamicamente usando Expression Language
    filters = []

    if area:
        filters.append(Periodico.area == area)

    if estrato:
        filters.append(Periodico.estrato.in_(estrato))

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Periodico.titulo.ilike(search_pattern),
                Periodico.issn.ilike(search_pattern)
            )
        )

    # Construir query com Expression Language
    # Usar window function para contar total em uma única query
    total_count = func.count().over()
    stmt = select(
        Periodico.id,
        Periodico.issn,
        Periodico.titulo,
        Periodico.area,
        Periodico.estrato,
        total_count.label("total_count")
    )

    # Aplicar filtros usando and_(*filters) se houver filtros
    if filters:
        stmt = stmt.where(and_(*filters))

    # Aplicar ordenação e paginação
    stmt = stmt.order_by(Periodico.titulo).limit(per_page).offset((page - 1) * per_page)

    rows = db.execute(stmt).mappings().fetchall()

    if not rows:
        return [], 0

    total = rows[0]["total_count"]
    items = [
        {
            "id": row["id"],
            "issn": row["issn"],
            "titulo": row["titulo"],
            "area": row["area"],
            "estrato": row["estrato"],
        }
        for row in rows
    ]
    return items, total


def get_distribuicao(db: Session, area: str) -> list[dict]:
    """
    Distribuição de estratos para uma área específica.

    Técnicas utilizadas:
    - GROUP BY estrato com COUNT(*)
    - CASE WHEN para ordenação semântica (A1=1 ... C=9),
      já que ORDER BY estrato alfabético daria ordem errada (A1, A2, B1... mas também C antes de B)
    - Cálculo de percentual via SUM() OVER() (window function)
    """
    sql = text("""
        SELECT
            estrato,
            COUNT(*) AS count,
            ROUND(
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(),
                2
            ) AS percentual
        FROM periodicos
        WHERE area = :area
        GROUP BY estrato
        ORDER BY
            CASE estrato
                WHEN 'A1' THEN 1
                WHEN 'A2' THEN 2
                WHEN 'A3' THEN 3
                WHEN 'A4' THEN 4
                WHEN 'B1' THEN 5
                WHEN 'B2' THEN 6
                WHEN 'B3' THEN 7
                WHEN 'B4' THEN 8
                WHEN 'C'  THEN 9
                ELSE 10
            END
    """)

    rows = db.execute(sql, {"area": area}).mappings().fetchall()
    return [
        {
            "estrato": row["estrato"],
            "count": row["count"],
            "percentual": float(row["percentual"]),
        }
        for row in rows
    ]
