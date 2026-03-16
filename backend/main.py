"""
FastAPI application — QUALIS CAPES API.

Endpoints:
  GET  /api/areas                      — lista todas as áreas de avaliação
  GET  /api/periodicos                 — busca periódicos (filtros + paginação)
  GET  /api/areas/{area}/distribuicao  — distribuição de estratos por área
  POST /api/chat                       — consulta em linguagem natural (Gemini)

Segurança:
  - Rate limiting via SlowAPI (slowapi)
  - Inputs validados com Pydantic
  - Queries parametrizadas (ver queries.py)
  - CORS restrito a origens conhecidas
"""

import math
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from typing import Annotated



import queries
from chat import handle_chat
from database import engine, get_db
from models import Base
from scalar_fastapi import get_scalar_api_reference
from schemas import (
    ChatRequest,
    ChatResponse,
    DistribuicaoResponse,
    PaginatedResponse,
    PeriodicoResponse,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria tabelas se não existirem (idempotente)
    Base.metadata.create_all(bind=engine)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="QUALIS CAPES API",
    description="API para consulta de classificação QUALIS de periódicos científicos.",
    version="1.0.0",
    docs_url=None,  # Disabled to use Scalar below
    redoc_url=None,
    lifespan=lifespan,
)

@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — origens explícitas conforme SECURITY_GUIDELINES.md
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Headers de segurança
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/areas", response_model=list[str], tags=["Áreas"])
@limiter.limit("60/minute")
def list_areas(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Lista todas as 50 áreas de avaliação disponíveis, ordenadas alfabeticamente."""
    areas = queries.get_areas(db)
    if not areas:
        raise HTTPException(status_code=404, detail="Nenhuma área encontrada.")
    return areas


@app.get("/api/periodicos", response_model=PaginatedResponse, tags=["Periódicos"])
@limiter.limit("60/minute")
def search_periodicos(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    area: Annotated[str | None, Query(max_length=200)] = None,
    estrato: Annotated[list[str] | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=200, strip_whitespace=True)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 30,
):
    """
    Busca periódicos com filtros opcionais.
    - **area**: filtra por área de avaliação (exact match)
    - **estrato**: filtra por classificação (A1, A2, A3, A4, B1, B2, B3, B4, C)
    - **search**: busca por título ou ISSN (case-insensitive)
    - **page** / **per_page**: paginação (máx 100 por página)
    """
    # Valida estrato se fornecido
    if estrato:
        invalidos = [e for e in estrato if e not in queries.VALID_ESTRATOS]
        if invalidos:
            raise HTTPException(
                status_code=422,
                detail=f"Estratos inválidos: {', '.join(invalidos)}. Use: {', '.join(sorted(queries.VALID_ESTRATOS))}",
            )

    items, total = queries.search_periodicos(
        db, area=area, estrato=estrato, search=search, page=page, per_page=per_page
    )

    return PaginatedResponse(
        items=[PeriodicoResponse(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total else 0,
    )


@app.get(
    "/api/areas/{area}/distribuicao",
    response_model=DistribuicaoResponse,
    tags=["Áreas"],
)
@limiter.limit("60/minute")
def get_distribuicao(request: Request, area: str, db: Annotated[Session, Depends(get_db)]):
    """
    Retorna a distribuição de estratos (contagem e percentual) para uma área específica.
    Ordenação semântica: A1 → C.
    """
    distribuicao = queries.get_distribuicao(db, area=area)
    if not distribuicao:
        raise HTTPException(
            status_code=404,
            detail=f"Área '{area}' não encontrada ou sem dados.",
        )

    total = sum(item["count"] for item in distribuicao)
    return DistribuicaoResponse(
        area=area,
        total=total,
        distribuicao=distribuicao,
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Consulta em linguagem natural via Google Gemini (function calling).
    O modelo interpreta a mensagem e aciona os endpoints corretos automaticamente.
    Rate-limited a 10 req/min por IP.
    """
    return await handle_chat(body.message, db)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}
