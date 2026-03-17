# ARCHITECTURE.md — QUALIS CAPES

Documento técnico detalhando a arquitetura, decisões de design e padrões de projeto.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Stack por Camada](#stack-por-camada)
- [Padrões de Código](#padrões-de-código)
- [Database Design](#database-design)
- [API Design](#api-design)
- [Frontend Architecture](#frontend-architecture)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)
- [Testing Strategy](#testing-strategy)

---

## Visão Geral

**QUALIS CAPES** é uma aplicação full-stack de **três camadas** (frontend, API, banco de dados) com integração de IA.

```
┌──────────────────────────┐
│     Frontend Layer       │  React 19 + Vite + Recharts
│    (SPA - React)         │
└────────────┬─────────────┘
             │ HTTP/REST + JSON
┌────────────▼─────────────┐
│    Backend Layer         │  Python 3.12 + FastAPI + Pydantic
│  (Stateless REST API)    │  SQLAlchemy ORM + Raw SQL
└────────────┬─────────────┘
             │ PostgreSQL Wire Protocol
┌────────────▼─────────────┐
│    Data Layer            │  PostgreSQL 16 + pg_trgm
│  (Relational Database)   │  171.111 registros, 50 áreas
└──────────────────────────┘
```

---

## Stack por Camada

### 🎨 Frontend

**Framework:** React 19 (composition, hooks)  
**Build Tool:** Vite 8  
**Styling:** CSS Vanilla (sem Tailwind/styled-components — simplicidade)  
**Charts:** Recharts 3.8 (gráficos acessíveis)  
**API Client:** Fetch API nativa

**Estrutura:**
```
frontend/
├── src/
│   ├── main.jsx              # Entry point
│   ├── App.jsx               # Root component (state management)
│   ├── index.css             # Global styles
│   ├── api.js                # API client (fetch wrapper)
│   └── components/
│       ├── AreaSelector.jsx      # Dropdown de áreas
│       ├── ClassificationFilter.jsx  # Filtro de estratos
│       ├── ResultsTable.jsx       # Tabela paginada
│       ├── DistributionPanel.jsx  # Gráfico de distribuição
│       └── ChatPanel.jsx          # Chat IA flutuante
├── index.html
├── vite.config.js
└── package.json
```

**Design System:**
- Paleta: 9 cores (primary, neutral, estratos semáforo)
- Tipografia: Merriweather (títulos), Inter (corpo)
- Tema: Light mode apenas (simplificação)
- Responsividade: Mobile-first, breakpoint 768px

---

### 🐍 Backend

**Framework:** FastAPI 0.115 (async, auto-docs, validation)  
**ORM:** SQLAlchemy 2.0 (models, sessions, types)  
**Validation:** Pydantic 2.11 (request/response schemas)  
**Rate Limiting:** SlowAPI (decorator-based)  
**IA Integration:** google-genai 1.8 (Gemini API client)  
**Logging:** Python stdlib logging module

**Estrutura:**
```
backend/
├── main.py              # FastAPI app + endpoints
├── database.py          # SQLAlchemy engine + session
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic schemas
├── queries.py           # SQL queries (raw + ORM)
├── chat.py              # Gemini integration + function calling
├── load_data.py         # XLSX → PostgreSQL loader
├── pytest.ini           # Pytest config
├── requirements.txt
└── tests/
    ├── conftest.py          # Fixtures
    ├── test_endpoints.py    # Integration tests (32)
    ├── test_queries.py      # Unit tests (20)
    └── __init__.py
```

**Key Modules:**

#### `main.py` — FastAPI App
- Configuração de CORS, security headers, rate limiting
- 4 endpoints RESTful + health check
- Middleware para logging e segurança
- Scalar docs (não Swagger)

#### `database.py` — SQLAlchemy Setup
- Engine: connection pooling (`pool_size=10, max_overflow=20`)
- SessionLocal: factory for DB sessions
- Dependency injection via `get_db()`

#### `models.py` — ORM Models
```python
class Periodico(Base):
    __tablename__ = "periodicos"
    id = Column(Integer, primary_key=True)
    issn = Column(String(20), unique=False, nullable=False)
    titulo = Column(String(500), nullable=False)
    area = Column(String(200), nullable=False)
    estrato = Column(String(5), nullable=False)
    
    # Índices para performance
    __table_args__ = (
        Index('ix_periodicos_area_estrato', 'area', 'estrato'),
        Index('ix_periodicos_titulo_trgm', 'titulo', postgresql_using='gist', postgresql_ops={'titulo': 'gist_trgm_ops'}),
    )
```

#### `queries.py` — Query Layer
Centraliza toda lógica de banco, hidrata para dicts (não ORM objects).

**Padrão 1: SQLAlchemy ORM (select/where/or_)**
```python
stmt = select(Periodico).where(and_(
    Periodico.area == area,
    or_(
        Periodico.titulo.ilike(f"%{search}%"),
        Periodico.issn.ilike(f"%{search}%"),
    ),
)).limit(per_page).offset((page - 1) * per_page)
```

**Padrão 2: Raw SQL com Parameterização**
```python
result = db.execute(
    text("SELECT DISTINCT area FROM periodicos ORDER BY area")
)
```

**Proteção:** Tudo usa parameterização (`:param`) — **zero SQL injection risk**.

#### `chat.py` — Gemini Integration
```python
# Define tools (endpoints como JSON schema)
TOOLS = [
    FunctionDeclaration(name="list_areas", ...),
    FunctionDeclaration(name="search_periodicos", ...),
    FunctionDeclaration(name="get_distribuicao", ...),
]

# Chat session com function calling
response = chat.send_message(user_message)
# Gemini responde com function call ou texto direto
while has_function_call:
    fc = extract_function_call(response)
    result = execute_function(fc.name, fc.args)
    response = chat.send_message(function_result)
```

**Fluxo:**
1. Usuário: "Quantos A1 em COMPUTAÇÃO?"
2. Backend envia ao Gemini: "user_message + tool_definitions"
3. Gemini responde: "I should call search_periodicos with area=COMPUTACAO, estrato=A1"
4. Backend executa no DB
5. Gemini formata resposta em português natural

---

### 🐘 PostgreSQL

**Schema:**
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
    INDEX ix_periodicos_titulo_trgm USING gist (titulo gist_trgm_ops)  -- Full-text search
);
```

**Extensions:**
```sql
CREATE EXTENSION pg_trgm;  -- Trigram for ILIKE performance
```

**Dados:**
- 171.111 linhas
- 50 áreas distintas
- Estratos: A1, A2, A3, A4, B1, B2, B3, B4, C

**Índices Estratégia:**
- `PK (id)`: Automático
- `area`: Filtragem comum
- `estrato`: Filtragem comum
- `area + estrato`: Combinação comum (composite)
- `titulo (trgm)`: Busca textual case-insensitive rápida

**Performance Targets:**
- Query sem filtros: < 100ms (paginada)
- Query com filtro de área: < 50ms
- Full-text search: < 150ms (com índice trgm)

---

## Padrões de Código

### 1. **Dependency Injection (FastAPI)**

```python
# Em main.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Uso
@app.get("/api/areas")
def list_areas(request: Request, db: Annotated[Session, Depends(get_db)]):
    return queries.get_areas(db)
```

**Benefício:** Sessão automática, rollback em erro, testável (override em testes).

---

### 2. **Pydantic Schemas para Validação**

```python
# schemas.py
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    
    @field_validator('message')
    def message_strip(cls, v):
        return v.strip()

# main.py
@app.post("/api/chat")
async def chat(body: ChatRequest, db: Session):
    # body.message já é validado, limpo e tipado
    return await handle_chat(body.message, db)
```

**Benefício:** Validação automática, erro 422 automático, docs Swagger/Scalar automáticos.

---

### 3. **Parametrização SQL**

```python
# ✅ Seguro (raw SQL)
result = db.execute(
    text("SELECT * FROM periodicos WHERE area = :area"),
    {"area": user_input}
)

# ✅ Seguro (ORM)
stmt = select(Periodico).where(Periodico.area == user_input)

# ❌ Inseguro (NÃO USADO)
# result = db.execute(text(f"SELECT * FROM periodicos WHERE area = '{user_input}'"))
```

---

### 4. **Error Handling com HTTPException**

```python
# Validação
if area not in valid_areas:
    raise HTTPException(
        status_code=422,
        detail=f"Área '{area}' não existe. Use: {', '.join(valid_areas[:5])}..."
    )

# Não encontrado
if not distribuicao:
    raise HTTPException(
        status_code=404,
        detail=f"Área '{area}' não encontrada."
    )

# Serviço indisponível
except Exception as e:
    raise HTTPException(
        status_code=503,
        detail="Serviço de IA temporariamente indisponível."
    )
```

**Benefício:** Respostas estruturadas, status codes semânticos, mensagens claras.

---

### 5. **Logging com Contexto**

```python
logger.info(f"GET /api/periodicos from {client_ip} - area={area}, estrato={estrato}")
logger.warning(f"Invalid area requested: {area}")
logger.error(f"Error in chat handler: {str(e)}")
logger.debug(f"Returned {len(items)} periodicos")
```

**Benefício:** Auditoria, debug em produção, tracing de requisições.

---

### 6. **Type Hints (Python + Pydantic)**

```python
def search_periodicos(
    db: Session,
    area: Optional[str] = None,
    estrato: Optional[list[str]] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 30,
) -> tuple[list[dict], int]:  # Tipo de retorno explícito
```

**Benefício:** Autocomplete, detecção de bugs estática, documentação viva.

---

## Database Design

### Normalização

**Grau:** 1NF (normalizado apenas o suficiente)

- ✅ **Sem repetição de dados:** Cada registro é único
- ✅ **Sem dependências parciais:** `area` é única função de `id`
- ❌ **Não 3NF:** `area` poderia ser tabela separada (mas overkill aqui)

### Índices

| Nome | Tipo | Uso | Performance |
|------|------|-----|------------|
| `id` | PK | SELECT por ID | O(1) |
| `area` | B-tree | Filtro por área | O(log n) |
| `estrato` | B-tree | Filtro por estrato | O(log n) |
| `area + estrato` | Composite B-tree | Filtro combinado | O(log n) |
| `titulo (trgm)` | GiST | ILIKE busca | O(log n) + distance ranking |

### Query Optimization

**Window Function para Paginação:**
```sql
-- 1 query em vez de 2
SELECT *, COUNT(*) OVER() as total_count
FROM periodicos
WHERE area = :area
LIMIT 30 OFFSET 0
```

**Índice GiST para ILIKE:**
```sql
CREATE INDEX ix_periodicos_titulo_trgm ON periodicos 
USING gist(titulo gist_trgm_ops);

-- Agora ILIKE é rápido em tabelas grandes
SELECT * FROM periodicos WHERE titulo ILIKE '%nature%'
```

---

## API Design

### Princípios RESTful

1. **Recursos:** `/api/areas`, `/api/periodicos`, `/api/areas/{area}/distribuicao`
2. **Métodos HTTP:** GET (leitura), POST (chat)
3. **Status Codes Semânticos:**
   - `200 OK` — Sucesso
   - `404 Not Found` — Recurso não existe
   - `422 Unprocessable Entity` — Validação falhou
   - `429 Too Many Requests` — Rate limit
   - `503 Service Unavailable` — Gemini API down

### Request/Response Format

**Request:**
```http
GET /api/periodicos?area=COMPUTACAO&estrato=A1&search=nature&page=1&per_page=30
```

**Response (200):**
```json
{
  "items": [...],
  "total": 5234,
  "page": 1,
  "per_page": 30,
  "total_pages": 175
}
```

**Response (422 — Validação):**
```json
{
  "detail": "Área 'COMPUTACO' não existe. Use: ADMINISTRAÇÃO, AGRONOMIA, ..."
}
```

### Versionamento

Não implementado (v1 é a única versão). Caso escalasse:

```http
GET /api/v1/periodicos
GET /api/v2/periodicos
```

---

## Frontend Architecture

### State Management

**Solução:** React Hooks (useState, useContext) — sem Redux (overkill)

```jsx
// App.jsx
const [selectedArea, setSelectedArea] = useState(null)
const [selectedEstratos, setSelectedEstratos] = useState([])
const [searchText, setSearchText] = useState('')
const [periodicos, setPeriodicos] = useState([])
const [currentPage, setCurrentPage] = useState(1)
```

### Component Hierarchy

```
App
├── AreaSelector
├── ClassificationFilter
├── ResultsTable
├── DistributionPanel
└── ChatPanel (flutuante)
```

**Props Drilling:** Aceitável aqui (árvore pequena). Caso escalasse, usaria Context.

### Data Fetching

**Hook customizado:** `useQualisData()`

```javascript
export function useQualisData() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const fetchPeriodicos = useCallback(async (filters) => {
    setLoading(true)
    try {
      const data = await getPeriodicos(filters)
      return data
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])
  
  return { fetchPeriodicos, loading, error }
}
```

### Debounce

```javascript
// useDebounce.js
export function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value)
  
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  
  return debouncedValue
}

// App.jsx — usar em busca de texto
const debouncedSearch = useDebounce(searchText, 300)
```

---

## Security Architecture

### Threat Model

| Ameaça | Mitigação | Implementação |
|--------|-----------|---|
| **SQL Injection** | Parameterização | `:param` em todas as queries |
| **Busca ILIKE Wildcard** | Escape de `%`, `_` | Sanitização em main.py |
| **Brute Force API** | Rate limiting | SlowAPI (60/min geral, 10/min chat) |
| **CSRF** | CORS restrito | Whitelist de origens |
| **Clickjacking** | X-Frame-Options | Middleware (DENY) |
| **Sniffing MIME** | X-Content-Type-Options | Middleware (nosniff) |
| **Gemini API Abuse** | Rate limit agressivo + try-catch | 10/min + erro tratado |
| **Secrets Exposure** | .env no .gitignore | .env.example fornecido |
| **Logging Sensível** | Apenas IP + parâmetros | Sem dados pessoais |

### CORS Configuration

```python
origins = [
    "http://localhost:5173",     # Dev frontend
    "http://localhost:3000",     # Alt dev
]
if PROD_ORIGIN:
    origins.append(PROD_ORIGIN)  # Produção

app.add_middleware(CORSMiddleware, allow_origins=origins)
```

### Rate Limiting Strategy

```python
limiter = Limiter(key_func=get_remote_address)

@limiter.limit("60/minute")      # Geral
def list_areas(...): ...

@limiter.limit("10/minute")      # Chat (API caída = caro)
async def chat(...): ...
```

---

## Performance Considerations

### Backend

| Métrica | Target | Atual | Notas |
|---------|--------|-------|-------|
| GET /api/areas | < 100ms | ~20ms | Candidato a cache |
| GET /api/periodicos (sem filtro) | < 500ms | ~80ms | Window function eficiente |
| GET /api/periodicos (com filtro) | < 200ms | ~50ms | Índices compostos |
| POST /api/chat | < 2s | ~1.5s | Gemini latency |

### Frontend

| Métrica | Target | Implementado |
|---------|--------|---|
| **Time to Interactive** | < 2s | ✅ Vite build, small bundle |
| **Largest Contentful Paint** | < 2.5s | ✅ No lazy loading needed (pequeno) |
| **Cumulative Layout Shift** | < 0.1 | ✅ Fixed layouts |
| **Bundle Size** | < 300KB | ✅ ~120KB (React + Recharts) |

### Otimizações

**Backend:**
- ✅ Connection pooling (`pool_size=10`)
- ✅ Window functions (uma query vs duas)
- ✅ Índices estratégicos
- ❌ Cache (candidato futuro — Redis)

**Frontend:**
- ✅ Code splitting (Vite)
- ✅ Hot module replacement (dev)
- ✅ Debounce em buscas
- ❌ Lazy loading (n ecessário — arquivo pequeno)

---

## Testing Strategy

### Unit Tests

**Arquivo:** `backend/tests/test_queries.py` (20 testes)

Testa **queries.py** isoladamente com fixtures de banco.

```python
def test_get_areas_returns_distinct_sorted(db):
    # Setup
    queries.insert_test_data(db)
    
    # Execute
    areas = queries.get_areas(db)
    
    # Assert
    assert len(areas) == len(set(areas))  # Distinct
    assert areas == sorted(areas)  # Sorted
```

### Integration Tests

**Arquivo:** `backend/tests/test_endpoints.py` (32 testes)

Testa **endpoints completos** com banco real (SQLite in-memory).

```python
def test_search_periodicos_with_area_filter(client, db):
    response = client.get("/api/periodicos?area=COMPUTACAO")
    assert response.status_code == 200
    data = response.json()
    assert all(p['area'] == 'COMPUTACAO' for p in data['items'])
```

### Test Database

```python
# conftest.py
@pytest.fixture
def db():
    # SQLite in-memory (rápido, isolado)
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    yield db
    db.close()
```

### Coverage

```bash
pytest --cov=backend --cov-report=html
```

**Target:** > 80% (queries.py em 100%, endpoints em 80%+)

### CI/CD (Futuro)

```yaml
# .github/workflows/test.yml
name: Test & Lint
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --cov
      - run: pylint backend/*.py
```

---

## Deployment

### Docker Compose (Desenvolvimento)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: qualis_user
      POSTGRES_PASSWORD: qualis_pass
      POSTGRES_DB: qualis_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "qualis_user"]
      interval: 2s
      timeout: 5s
      retries: 5
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://qualis_user:qualis_pass@postgres:5432/qualis_db
      GEMINI_API_KEY: ${GEMINI_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://backend:8000
```

### Produção (Recomendações)

- **App Server:** Gunicorn/Uvicorn (não dev server FastAPI)
- **Reverse Proxy:** Nginx (load balance, static files)
- **DB:** Managed PostgreSQL (RDS, Render, Railway)
- **Secrets:** Variáveis de ambiente (não .env)
- **Monitoring:** Datadog, New Relic, ou CloudWatch
- **Logging:** Centralized (ELK, Datadog, LogRocket)
- **Cache:** Redis para `/api/areas`
- **CDN:** Cloudflare para frontend estático

---

## Glossário

| Termo | Significado |
|-------|-----------|
| **Estrato** | Classificação QUALIS (A1–C) |
| **Área** | Campo de avaliação (COMPUTAÇÃO, BIOLOGIA, etc) |
| **Quadriênio** | Período de 4 anos (2021-2024) |
| **Window Function** | SQL: `COUNT(*) OVER()` — agregação sem GROUP BY |
| **pg_trgm** | PostgreSQL extension para trigram search (ILIKE rápido) |
| **Function Calling** | Gemini interpreta qual função chamar baseado na mensagem |
| **Rate Limiting** | Limite de requisições por IP/tempo (anti-DDoS, anti-abuse) |

---

**Versão:** 1.0  
**Última atualização:** March 16, 2026
