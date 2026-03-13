"""
Custom SQL queries — raw SQL via SQLAlchemy text() for performance-critical endpoints.
This module demonstrates intentional use of SQL beyond ORM abstractions:
  - Window functions (COUNT(*) OVER) for single-pass pagination
  - CASE WHEN for semantic ordering of estratos
  - ILIKE for case-insensitive text search
  - Composite filter building with parameterized inputs (no interpolation)
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional


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
    estrato: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 30,
) -> tuple[list[dict], int]:
    """
    Busca periódicos com filtros opcionais.

    Técnicas utilizadas:
    - Construção dinâmica de WHERE com parâmetros bind (seguro contra SQL injection)
    - ILIKE para busca case-insensitive em título e ISSN
    - COUNT(*) OVER() como window function: obtém o total na mesma query,
      sem um segundo round-trip ao banco
    - LIMIT/OFFSET para paginação server-side
    """
    conditions = []
    params: dict = {}

    if area:
        conditions.append("area = :area")
        params["area"] = area

    if estrato:
        conditions.append("estrato = :estrato")
        params["estrato"] = estrato

    if search:
        conditions.append("(titulo ILIKE :search OR issn ILIKE :search)")
        params["search"] = f"%{search}%"

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Window function: conta total sem query separada
    sql = text(f"""
        SELECT
            id,
            issn,
            titulo,
            area,
            estrato,
            COUNT(*) OVER() AS total_count
        FROM periodicos
        {where_clause}
        ORDER BY titulo
        LIMIT :limit OFFSET :offset
    """)

    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page

    rows = db.execute(sql, params).mappings().fetchall()

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
