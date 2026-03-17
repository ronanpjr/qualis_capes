# Backend — QUALIS CAPES

Aplicação FastAPI para consulta de periódicos QUALIS com integração de IA (Gemini).

## 📋 Índice

- [Estrutura](#estrutura)
- [Setup Local](#setup-local)
- [Executar](#executar)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Testes](#testes)
- [Debugging](#debugging)
- [Deployment](#deployment)

---

## Estrutura

```
backend/
├── main.py              # FastAPI app + endpoints + middleware
├── database.py          # SQLAlchemy engine + session
├── models.py            # ORM models (Periodico)
├── schemas.py           # Pydantic request/response models
├── queries.py           # SQL queries (ORM + raw)
├── chat.py              # Gemini integration + function calling
├── load_data.py         # XLSX loader script
├── requirements.txt
├── pytest.ini           # Pytest config
└── tests/
    ├── conftest.py          # Fixtures
    ├── test_endpoints.py    # Integration tests (32)
    ├── test_queries.py      # Unit tests (20)
    └── __init__.py
```

### Módulos

#### `main.py` — FastAPI Application

**Responsabilidades:**
- Definir endpoints REST
- Rate limiting via SlowAPI
- Security middleware (CORS, headers)
- Logging de auditoria
- Error handling

**Endpoints:**
- `GET /api/areas` — Listar áreas
- `GET /api/periodicos` — Buscar periódicos
- `GET /api/areas/{area}/distribuicao` — Distribuição
- `POST /api/chat` — Chat IA
- `GET /health` — Health check

---

#### `database.py` — Database Setup

```python
DATABASE_URL = "postgresql://..."
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Dependency injection para sessão de DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

#### `models.py` — ORM Models

```python
class Periodico(Base):
    __tablename__ = "periodicos"
    id = Column(Integer, primary_key=True)
    issn = Column(String(20), nullable=False)
    titulo = Column(String(500), nullable=False)
    area = Column(String(200), nullable=False)
    estrato = Column(String(5), nullable=False)
```

**Índices:**
- `area` — Filtragem
- `estrato` — Filtragem
- `area + estrato` — Combinação comum
- `titulo (trgm)` — Busca textual

---

#### `schemas.py` — Pydantic Models

Request/Response schemas com validação automática:

```python
class PeriodicoResponse(BaseModel):
    id: int
    issn: str
    titulo: str
    area: str
    estrato: str

class PaginatedResponse(BaseModel):
    items: list[PeriodicoResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)

class ChatResponse(BaseModel):
    response: str
    data: list[dict] | None = None
    action_taken: str | None = None
```

---

#### `queries.py` — SQL Layer

Centraliza queries para:
- **ORM queries** (select/where/or_) — type-safe
- **Raw SQL** (window functions, custom logic) — performante

```python
def get_areas(db: Session) -> list[str]:
    """Áreas distintas, ordenadas."""
    result = db.execute(text("SELECT DISTINCT area FROM periodicos ORDER BY area"))
    return [row[0] for row in result.fetchall()]

def search_periodicos(
    db: Session,
    area: Optional[str] = None,
    estrato: Optional[list[str]] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 30,
) -> tuple[list[dict], int]:
    """Busca com filtros + paginação (1 query via window function)."""
    filters = []
    if area:
        filters.append(Periodico.area == area)
    if estrato:
        filters.append(Periodico.estrato.in_(estrato))
    if search:
        search_pattern = f"%{search}%"
        filters.append(or_(
            Periodico.titulo.ilike(search_pattern),
            Periodico.issn.ilike(search_pattern)
        ))
    
    total_count = func.count().over()
    stmt = select(
        Periodico.id, Periodico.issn, Periodico.titulo,
        Periodico.area, Periodico.estrato,
        total_count.label("total_count")
    )
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(Periodico.titulo).limit(per_page).offset((page - 1) * per_page)
    
    rows = db.execute(stmt).mappings().fetchall()
    if not rows:
        return [], 0
    
    total = rows[0]["total_count"]
    items = [dict(row) for row in rows]
    return items, total
```

**Padrão:** Raw SQL parametrizado (`:param`) — **nunca string interpolation**.

---

#### `chat.py` — Gemini Integration

Usa **function calling** para interpreter mensagens em linguagem natural:

```python
TOOLS = [
    FunctionDeclaration(name="list_areas", ...),
    FunctionDeclaration(name="search_periodicos", ...),
    FunctionDeclaration(name="get_distribuicao", ...),
]

async def handle_chat(message: str, db: Session) -> ChatResponse:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    chat = client.chats.create(model="gemini-2.5-flash", tools=TOOLS, ...)
    
    response = chat.send_message(message)
    
    while fc := extract_function_call(response):
        result = execute_function(fc.name, fc.args, db)
        response = chat.send_message(FunctionResponse(name=fc.name, response=result))
    
    return ChatResponse(response=response.text, data=raw_data, action_taken=action_taken)
```

**Fluxo:**
1. Usuário: "Quantos A1 em COMPUTAÇÃO?"
2. Backend → Gemini: message + tool definitions
3. Gemini → Backend: "call search_periodicos(area=COMPUTACAO, estrato=A1)"
4. Backend executa, retorna resultado real
5. Gemini → Frontend: "Na área de COMPUTAÇÃO existem 245 A1..."

---

#### `load_data.py` — Data Loader

Script para carregar dados XLSX → PostgreSQL:

```bash
python load_data.py
```

**Steps:**
1. Cria tabela `periodicos` + índices
2. Lê arquivo `qualis_capes.xlsx`
3. Batch insert (5K registros/vez) com transação atômica
4. Verifica integridade (COUNT)

---

## Setup Local

### 1. Ambiente Virtual

```bash
cd backend
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Dependências

```bash
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente

```bash
# Copie template
cp ../.env.example .env

# Edite .env
POSTGRES_USER=qualis_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=qualis_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
GEMINI_API_KEY=your_gemini_key
```

### 4. Banco de Dados (opções)

**Opção A: PostgreSQL Local**
```bash
createdb qualis_db
```

**Opção B: PostgreSQL via Docker**
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_USER=qualis_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=qualis_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### 5. Carregar Dados

```bash
# Assegure-se que qualis_capes.xlsx está em backend/
python load_data.py
```

---

## Executar

### Dev Server (Hot Reload)

```bash
uvicorn main:app --reload --port 8000
```

Acesse:
- API: http://localhost:8000/api/areas
- Docs: http://localhost:8000/docs

### Produção

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Ou com Gunicorn:
```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## API Endpoints

### GET /api/areas

Lista todas as áreas.

**Response:**
```json
[
  "ADMINISTRAÇÃO PÚBLICA",
  "AGRONOMIA",
  "ANTROPOLOGIA",
  ...
]
```

---

### GET /api/periodicos

Busca periódicos com filtros opcionais.

**Query Parameters:**
- `area` (string): Filtra por área exata
- `estrato` (array): Filtra por estrato(s) — A1, A2, ..., C
- `search` (string): Busca em título ou ISSN
- `page` (int, default 1): Página
- `per_page` (int, default 30, max 100): Resultados por página

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "issn": "0010-4825",
      "titulo": "Nature",
      "area": "BIOLOGIA GERAL",
      "estrato": "A1"
    }
  ],
  "total": 5234,
  "page": 1,
  "per_page": 30,
  "total_pages": 175
}
```

---

### GET /api/areas/{area}/distribuicao

Distribuição de estratos para uma área.

**Response:**
```json
{
  "area": "COMPUTACAO",
  "total": 2341,
  "distribuicao": [
    {
      "estrato": "A1",
      "count": 245,
      "percentual": 10.47
    }
  ]
}
```

---

### POST /api/chat

Consulta em linguagem natural.

**Request:**
```json
{
  "message": "Quantos periódicos A1 tem em COMPUTAÇÃO?"
}
```

**Response:**
```json
{
  "response": "Na área de COMPUTAÇÃO existem 245 periódicos A1...",
  "data": [...],
  "action_taken": "search_periodicos"
}
```

**Rate Limit:** 10 req/min por IP

---

## Database Schema

### Table: periodicos

```sql
CREATE TABLE periodicos (
    id SERIAL PRIMARY KEY,
    issn VARCHAR(20) NOT NULL,
    titulo VARCHAR(500) NOT NULL,
    area VARCHAR(200) NOT NULL,
    estrato VARCHAR(5) NOT NULL,
    
    INDEX ix_periodicos_area,
    INDEX ix_periodicos_estrato,
    INDEX ix_periodicos_area_estrato,
    INDEX ix_periodicos_titulo_trgm USING gist(titulo gist_trgm_ops)
);
```

### Índices

| Nome | Coluna(s) | Tipo | Uso |
|------|-----------|------|-----|
| `id` | id | PK | Acesso por ID |
| `ix_periodicos_area` | area | B-tree | Filtro por área |
| `ix_periodicos_estrato` | estrato | B-tree | Filtro por estrato |
| `ix_periodicos_area_estrato` | area, estrato | Composite | Combinação |
| `ix_periodicos_titulo_trgm` | titulo | GiST | ILIKE rápido |

---

## Testes

### Executar Todos

```bash
pytest -v
```

### Executar por Tipo

```bash
# Integração (endpoints)
pytest -v tests/test_endpoints.py

# Unitários (queries)
pytest -v tests/test_queries.py

# Específico
pytest -v tests/test_endpoints.py::test_list_areas

# Com cobertura
pytest -v --cov=.
```

### Estrutura de Testes

**`conftest.py` — Fixtures:**
```python
@pytest.fixture
def db():
    """Banco in-memory isolado por teste."""
    engine = create_engine("sqlite:///:memory:", ...)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def client(db):
    """TestClient com DB override."""
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)
```

**`test_endpoints.py` — Integração (32 testes):**
- Health check
- GET /api/areas
- GET /api/periodicos (com/sem filtros)
- GET /api/areas/{area}/distribuicao
- POST /api/chat (validação, rate limit)

**`test_queries.py` — Unitários (20 testes):**
- get_areas: distinctness, sorting
- search_periodicos: filtros, paginação, busca
- get_distribuicao: contagem, percentual

### Coverage Target

- **Total:** >80%
- **Queries:** 100%
- **Endpoints:** 80%+

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"GET /api/periodicos from {client_ip} - area={area}")
logger.warning(f"Invalid area: {area}")
logger.error(f"Error: {str(e)}")
```

**Ver logs em runtime:**
```bash
docker compose logs -f backend
```

### SQL Debug

```python
# Em database.py
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    print(f"SQL: {statement}")
    print(f"Params: {parameters}")
```

### Testar Endpoint

```bash
curl 'http://localhost:8000/api/periodicos?area=COMPUTACAO&estrato=A1'

# Com headers
curl -H "Content-Type: application/json" \
     -X POST \
     -d '{"message":"test"}' \
     http://localhost:8000/api/chat
```

### Debugger (PyCharm/VSCode)

```python
# Em main.py, adicione breakpoint
import pdb; pdb.set_trace()

# Ou use debugger integrado do IDE
```

---

## Deployment

### Docker (Recomendado)

```bash
docker compose up -d backend
```

### Produção (Self-Hosted)

```bash
# 1. Build
pip install -r requirements.txt
python load_data.py

# 2. Rodar com Gunicorn
gunicorn main:app --workers 4 --bind 0.0.0.0:8000

# 3. Reverse proxy (nginx/apache) na frente

# 4. SSL (Let's Encrypt)

# 5. Monitoramento (Sentry, DataDog, etc)
```

### Produção (PaaS — Railway, Render, Heroku)

```bash
# Railway
railway add
railway up

# Render
git push  # Trigger auto-deploy

# Heroku
heroku create
git push heroku main
```

---

## Variáveis de Ambiente (Produção)

```bash
# Database
POSTGRES_USER=production_user
POSTGRES_PASSWORD=generate_strong_password
POSTGRES_DB=qualis_prod
POSTGRES_HOST=db.provider.com
POSTGRES_PORT=5432

# IA
GEMINI_API_KEY=prod_key_here

# CORS
PROD_ORIGIN=https://seu-dominio.com

# Logging
LOG_LEVEL=WARNING  # Menos verbose em prod
```

---

## Performance

### Benchmarks (Target)

| Operação | Target | Atual |
|----------|--------|-------|
| GET /api/areas | < 100ms | ~20ms ✅ |
| GET /api/periodicos (sem filtro) | < 500ms | ~80ms ✅ |
| GET /api/periodicos (com filtro) | < 200ms | ~50ms ✅ |
| POST /api/chat | < 2s | ~1.5s ✅ |

### Otimizações

- ✅ Connection pooling (pool_size=10)
- ✅ Window functions (1 query vs 2)
- ✅ Índices estratégicos
- ⏳ Cache com Redis (futuro)
- ⏳ Query optimization com EXPLAIN (futuro)

---

## Dependências

Ver `requirements.txt` para versão exata.

Principais:
- **fastapi==0.115** — Web framework
- **uvicorn==0.34** — ASGI server
- **sqlalchemy==2.0** — ORM
- **psycopg2-binary** — PostgreSQL driver
- **pydantic==2.11** — Validation
- **slowapi==0.1** — Rate limiting
- **google-genai==1.8** — Gemini API
- **pytest** — Testing
- **python-dotenv** — Env vars

---

**Versão:** 1.0  
**Última atualização:** March 16, 2026
