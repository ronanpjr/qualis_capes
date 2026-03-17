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
  - Logging de auditoria em todos os endpoints
"""

import logging
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

# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler para console
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
    description="""
    ## API para Consulta de Classificação QUALIS CAPES

    A **QUALIS CAPES** é a classificação de periódicos utilizada pelo sistema
    de avaliação de programas de pós-graduação no Brasil. Este API fornece
    acesso estruturado aos dados de classificação de ~7000 periódicos científicos
    em ~50 áreas de avaliação.

    ### Funcionalidades Principais

    - **Listar Áreas**: Recupere todas as 50 áreas de avaliação disponíveis
    - **Pesquisar Periódicos**: Busque por área, estrato, título ou ISSN com paginação
    - **Distribuição por Estrato**: Veja como os periódicos estão distribuídos em cada área
    - **Consulta em IA**: Consulte usando linguagem natural (Google Gemini)

    ### Estratos de Classificação

    | Estrato | Descrição |
    |---------|-----------|
    | **A1** | Melhor classificação (periódicos de excelência internacional) |
    | **A2** | Periódicos de muito bom nível |
    | **A3** | Periódicos de bom nível |
    | **A4** | Periódicos de nível satisfatório |
    | **B1** | Periódicos de bom nível (com restrições) |
    | **B2** | Periódicos de nível satisfatório |
    | **B3** | Periódicos de nível adequado |
    | **B4** | Periódicos com circulação local |
    | **C** | Periódicos descontinuados ou inadequados |

    ### Segurança e Rate Limiting

    - Rate limiting por IP para proteger o serviço
    - Validação rigorosa de inputs com Pydantic
    - Queries parametrizadas contra SQL injection
    - CORS restrito a origens configuradas
    - Logging de auditoria em todos os endpoints

    ### Documentação Interativa

    Utilize o Scalar (esta interface) para explorar e testar todos os endpoints.
    """,
    version="1.0.0",
    docs_url=None,  # Disabled to use Scalar below
    redoc_url=None,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Áreas",
            "description": """
            Endpoints para consultar áreas de avaliação CAPES.

            Áreas são categorias de conhecimento utilizadas pelo sistema CAPES
            para avaliar periódicos científicos. Existem aproximadamente 50 áreas,
            indo desde Humanas até Exatas e Saúde.
            """,
        },
        {
            "name": "Periódicos",
            "description": """
            Endpoints para pesquisar periódicos científicos no banco QUALIS.

            Permite buscas com múltiplos filtros: área, estrato, título/ISSN.
            Suporta paginação para resultados em grandes volumes.
            """,
        },
        {
            "name": "Chat",
            "description": """
            Consultas em linguagem natural via AI (Google Gemini).

            Interpreta mensagens em português e executa as operações apropriadas
            automaticamente usando function calling. Ideal para usuários que
            preferem consultas conversacionais.
            """,
        },
        {
            "name": "Infra",
            "description": "Endpoints de infraestrutura e health checks.",
        },
    ],
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
PROD_ORIGIN = os.getenv("PROD_ORIGIN")
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
if PROD_ORIGIN:
    origins.append(PROD_ORIGIN)

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
    """
    ## Lista todas as áreas de avaliação CAPES

    Retorna uma lista alfabética de todas as ~50 áreas de avaliação disponíveis
    no banco de dados QUALIS CAPES.

    ### Rate Limiting
    - Limite: 60 requisições por minuto por IP
    - Tipo: por endereço IP do cliente

    ### Respostas Esperadas

    **200 OK** - Lista de áreas com sucesso
    ```json
    [
        "Administração",
        "Agronomia",
        "Antropologia",
        "Arqueologia",
        "Artes",
        "Astronomia",
        "Biologia Geral",
        "Bioquímica",
        "Biotecnologia",
        "Botânica",
        ...
    ]
    ```

    **404 Not Found** - Nenhuma área encontrada na base de dados

    ### Uso Típico

    Use este endpoint primeiro para:
    1. Descobrir quais áreas estão disponíveis
    2. Validar o nome de uma área antes de outras buscas
    3. Construir filtros dinâmicos na interface do usuário
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"GET /api/areas - client: {client_ip}")
    areas = queries.get_areas(db)
    if not areas:
        raise HTTPException(status_code=404, detail="Nenhuma área encontrada.")
    logger.debug(f"/api/areas - response: {len(areas)} items")
    return areas


@app.get("/api/periodicos", response_model=PaginatedResponse, tags=["Periódicos"])
@limiter.limit("60/minute")
def search_periodicos(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    area: Annotated[str | None, Query(
        max_length=200,
        description="Filtra por uma área de avaliação específica (exact match)"
    )] = None,
    estrato: Annotated[list[str] | None, Query(
        description="Filtra por um ou mais estratos: A1, A2, A3, A4, B1, B2, B3, B4, C"
    )] = None,
    search: Annotated[str | None, Query(
        max_length=200,
        strip_whitespace=True,
        description="Busca full-text no título ou ISSN (case-insensitive)"
    )] = None,
    page: Annotated[int, Query(
        ge=1,
        description="Número da página (começando em 1)"
    )] = 1,
    per_page: Annotated[int, Query(
        ge=1,
        le=100,
        description="Itens por página (máximo 100)"
    )] = 30,
):
    """
    ## Busca periódicos com filtros avançados

    Permite pesquisar o banco de periódicos QUALIS com múltiplos critérios
    simultâneos. Suporta paginação para grandes volumes de resultados.

    ### Parâmetros

    - **area**: Filtra por área de avaliação específica (ex: "Botânica", "Física")
    - **estrato**: Lista de estratos para filtrar (ex: A1, A2, B1)
    - **search**: Busca por título ou ISSN da revista
    - **page**: Número da página (padrão: 1)
    - **per_page**: Itens por página, máximo 100 (padrão: 30)

    ### Exemplos de Uso

    #### Buscar todos os periódicos de Botânica
    ```
    GET /api/periodicos?area=Botânica
    ```

    #### Buscar periódicos A1 e A2 de uma área
    ```
    GET /api/periodicos?area=Física&estrato=A1&estrato=A2
    ```

    #### Buscar um periódico específico por ISSN
    ```
    GET /api/periodicos?search=0100-3941
    ```

    #### Busca combinada com paginação
    ```
    GET /api/periodicos?area=Botânica&estrato=A1&page=2&per_page=50
    ```

    ### Rate Limiting
    - Limite: 60 requisições por minuto por IP

    ### Validações

    - Se **area** for fornecida, deve ser uma área válida do banco
    - Se **estrato** for fornecido, cada item deve ser um dos estratos válidos
    - **per_page** máximo de 100 itens

    ### Respostas

    **200 OK** - Resultados encontrados (pode estar vazio)

    **422 Unprocessable Entity** - Validação falhou (área ou estrato inválido)
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"GET /api/periodicos - client: {client_ip}")
    
    # Valida área se fornecida
    if area:
        valid_areas = queries.get_areas(db)
        if area not in valid_areas:
            logger.warning(f"/api/periodicos - validation failed: invalid area")
            raise HTTPException(
                status_code=422,
                detail=f"Área '{area}' não existe. Áreas disponíveis: {', '.join(sorted(valid_areas)[:5])}...",
            )

    # Valida estrato se fornecido
    if estrato:
        invalidos = [e for e in estrato if e not in queries.VALID_ESTRATOS]
        if invalidos:
            logger.warning(f"/api/periodicos - validation failed: invalid estrato")
            raise HTTPException(
                status_code=422,
                detail=f"Estratos inválidos: {', '.join(invalidos)}. Use: {', '.join(sorted(queries.VALID_ESTRATOS))}",
            )

    # Sanitiza busca: escapar wildcards ILIKE
    sanitized_search = None
    if search:
        sanitized_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    items, total = queries.search_periodicos(
        db, area=area, estrato=estrato, search=sanitized_search, page=page, per_page=per_page
    )

    logger.debug(f"/api/periodicos - response: {len(items)} items, total: {total}")
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
def get_distribuicao(
    request: Request,
    area: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    ## Distribuição de estratos por área

    Retorna a distribuição completa de periódicos de uma área de avaliação,
    dividida por estrato (A1 até C). Útil para análises e visualizações.

    ### Parâmetros

    - **area**: Nome da área de avaliação (use /api/areas para obter a lista)

    ### Exemplos de Uso

    #### Distribuição de Botânica
    ```
    GET /api/areas/Botânica/distribuicao
    ```

    #### Distribuição de Física
    ```
    GET /api/areas/Física/distribuicao
    ```

    ### Rate Limiting
    - Limite: 60 requisições por minuto por IP

    ### Respostas

    **200 OK** - Distribuição encontrada

    Exemplo:
    ```json
    {
        "area": "Botânica",
        "total": 141,
        "distribuicao": [
            {
                "estrato": "A1",
                "count": 12,
                "percentual": 8.51
            },
            {
                "estrato": "A2",
                "count": 18,
                "percentual": 12.77
            },
            {
                "estrato": "A3",
                "count": 15,
                "percentual": 10.64
            },
            ...
        ]
    }
    ```

    **404 Not Found** - Área não encontrada ou sem dados

    ### Ordenação

    Os estratos são retornados em ordem semântica de qualidade:
    A1 → A2 → A3 → A4 → B1 → B2 → B3 → B4 → C

    ### Uso Típico

    - Criar gráficos de distribuição por área
    - Entender o percentual de periódicos A1/A2 em uma área
    - Comparar a qualidade relativa entre áreas
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"GET /api/areas/{{area}}/distribuicao - client: {client_ip}")
    
    distribuicao = queries.get_distribuicao(db, area=area)
    if not distribuicao:
        logger.warning(f"/api/areas/{{area}}/distribuicao - area not found")
        raise HTTPException(
            status_code=404,
            detail=f"Área '{area}' não encontrada ou sem dados.",
        )

    total = sum(item["count"] for item in distribuicao)
    logger.debug(f"/api/areas/{{area}}/distribuicao - response: total={total}")
    return DistribuicaoResponse(
        area=area,
        total=total,
        distribuicao=distribuicao,
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("10/minute")
def chat(
    request: Request,
    body: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    ## Consulta em linguagem natural com IA

    Permite consultar o banco QUALIS usando linguagem natural em português.
    O modelo Google Gemini interpreta a pergunta e executa as operações
    apropriadas automaticamente usando function calling.

    ### Endpoint de IA com Function Calling

    Este endpoint utiliza a capacidade de **function calling** do Gemini:
    1. Recebe uma pergunta em português
    2. O modelo analisa a pergunta
    3. O modelo chama automaticamente as funções apropriadas:
       - `list_areas()` - para listar áreas
       - `search_periodicos()` - para buscar periódicos
       - `get_distribuicao()` - para distribuições
    4. Retorna os dados estruturados + resposta em linguagem natural

    ### Rate Limiting
    - Limite: 10 requisições por minuto por IP
    - Limite mais restritivo que outros endpoints (proteção de API)

    ### Exemplos de Perguntas

    #### Buscar periódicos de uma área
    ```
    "Quais são os periódicos da área de Botânica com estrato A1 ou A2?"
    ```

    #### Listar áreas disponíveis
    ```
    "Mostra todas as áreas de avaliação disponíveis"
    ```

    #### Distribuição por estrato
    ```
    "Qual é a distribuição de estratos em Física?"
    ```

    #### Buscar um periódico específico
    ```
    "Procuro a revista Acta Botanica Brasilica, qual é sua classificação?"
    ```

    ### Parâmetros

    - **message**: Pergunta em português (1-500 caracteres)

    ### Respostas

    **200 OK** - Consulta processada com sucesso

    Exemplo:
    ```json
    {
        "response": "Encontrei 12 periódicos com estrato A1 em Botânica. Os principais são...",
        "data": [
            {
                "id": 1,
                "issn": "0100-3941",
                "titulo": "Acta Botanica Brasilica",
                "area": "Botânica",
                "estrato": "A1"
            },
            ...
        ],
        "action_taken": "search_periodicos"
    }
    ```

    **503 Service Unavailable** - Serviço de IA indisponível (erro de conexão com Gemini)

    ### Campos da Resposta

    - **response**: Resposta em linguagem natural gerada pelo Gemini
    - **data**: Dados estruturados retornados pela função invocada (se houver)
    - **action_taken**: Nome da função/endpoint que foi invocado

    ### Limitações

    - Suporta apenas perguntas em português
    - Máximo 500 caracteres por pergunta
    - Rate limit reduzido (10/min) para proteção de API
    - Dependente da disponibilidade do Google Gemini

    ### Comportamento

    - Se o modelo não conseguir interpretar a pergunta, retorna uma resposta genérica
    - Se uma busca não encontrar resultados, informa claramente
    - Sempre retorna dados estruturados quando disponíveis
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"POST /api/chat - client: {client_ip}")
    
    try:
        result = handle_chat(body.message, db)
        logger.debug(f"/api/chat - response: action={result.action_taken}")
        return result
    except Exception as e:
        logger.error(f"/api/chat - handler error: {type(e).__name__}")
        raise HTTPException(status_code=503, detail="Serviço de IA temporariamente indisponível.")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Infra"], response_model=dict)
def health():
    """
    Health check endpoint.
    
    Simples verificação de que o servidor está operacional.
    Retorna um status OK se o serviço está disponível.
    
    **200 OK** - Servidor está saudável
    
    Uso típico: monitoramento de disponibilidade, load balancers, health checks.
    """
    return {"status": "ok"}
