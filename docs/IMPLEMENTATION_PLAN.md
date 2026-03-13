# QUALIS CAPES — Consulta de Classificação de Periódicos

Aplicação para consultar e analisar classificações QUALIS de periódicos científicos da CAPES, permitindo que coordenadores de pós-graduação filtrem por área de avaliação e estrato.

**Dados:** `classificacoes_publicadas_sucupira_teste.xlsx` — 171.111 registros, 50 áreas, 9 estratos (A1, A2, A3, A4, B1, B2, B3, B4, C).

**Stack:** FastAPI + PostgreSQL (Docker) | React + Vite

---

## Proposed Changes

### Infraestrutura — Docker Compose

#### [NEW] [docker-compose.yml](file:///home/ronan/agora_sabemos/docker-compose.yml)
Orquestra o banco PostgreSQL:
- **postgres**: `postgres:16-alpine`, porta `5432`, volume persistido em `pgdata`, database `qualis_db`, user `qualis_user`.

---

### Backend — FastAPI + PostgreSQL (Híbrido ORM + Raw SQL)

O backend usa **FastAPI** com **PostgreSQL** (via Docker). Abordagem **híbrida**: SQLAlchemy para definição de modelos e gerenciamento de sessão, **raw SQL** para queries de performance e demonstrar domínio de SQL.

#### [NEW] [load_data.py](file:///home/ronan/agora_sabemos/backend/load_data.py)
Script para ler o XLSX com `openpyxl` e popular o PostgreSQL. Usa batch insert com `executemany` para inserção eficiente. Cria a tabela `periodicos` com colunas: `id`, `issn`, `titulo`, `area`, `estrato`. Índices em `area`, `estrato`, e índice composto `(area, estrato)`.

#### [NEW] [database.py](file:///home/ronan/agora_sabemos/backend/database.py)
Configuração do SQLAlchemy (engine, session, Base). Conexão com PostgreSQL via `DATABASE_URL` (env var com fallback para `postgresql://qualis_user:qualis_pass@localhost:5432/qualis_db`).

#### [NEW] [models.py](file:///home/ronan/agora_sabemos/backend/models.py)
Model SQLAlchemy `Periodico` com campos: `id`, `issn`, `titulo`, `area`, `estrato`.

#### [NEW] [schemas.py](file:///home/ronan/agora_sabemos/backend/schemas.py)
Schemas Pydantic para respostas da API: `PeriodicoResponse`, `AreaResponse`, `DistribuicaoResponse`, `PaginatedResponse`.

#### [NEW] [queries.py](file:///home/ronan/agora_sabemos/backend/queries.py)
Queries SQL customizadas (raw SQL via `text()` do SQLAlchemy):
- **`get_areas_query()`** — `SELECT DISTINCT area FROM periodicos ORDER BY area` 
- **`search_periodicos_query()`** — Query dinâmica com `WHERE` condicional, `ILIKE` para busca por texto, `LIMIT/OFFSET` para paginação, `COUNT(*) OVER()` como window function para total sem query extra
- **`get_distribuicao_query()`** — `SELECT estrato, COUNT(*) ... GROUP BY estrato` com `ORDER BY` customizado usando `CASE WHEN` para ordenar A1→C

#### [NEW] [main.py](file:///home/ronan/agora_sabemos/backend/main.py)
Aplicação FastAPI com:
- **`GET /api/areas`** — Raw SQL: `SELECT DISTINCT ... ORDER BY`
- **`GET /api/periodicos?area=&estrato=&search=&page=&per_page=`** — Raw SQL: filtros dinâmicos, `ILIKE`, window function `COUNT(*) OVER()`, `LIMIT/OFFSET`
- **`GET /api/areas/{area}/distribuicao`** — Raw SQL: `GROUP BY` + `CASE WHEN` ordering
- CORS habilitado para `localhost:5173` (Vite dev server).
- Tratamento de erros com HTTPException.

#### [NEW] [requirements.txt](file:///home/ronan/agora_sabemos/backend/requirements.txt)
`fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `openpyxl`, `pydantic`.

---

### Frontend — React + Vite

Interface institucional e responsiva usando **React** com **Vite**. Design acadêmico seguindo o [design_guidelines.md](file:///home/ronan/.gemini/antigravity/brain/e7b886db-196d-49a4-baf8-91fdcd7404a3/design_guidelines.md) — paleta azul institucional, tipografia Merriweather+Inter, fundo claro, foco em dados.

#### [NEW] [frontend/](file:///home/ronan/agora_sabemos/frontend/)
Projeto Vite + React scaffolded com `create-vite`.

#### [NEW] [src/index.css](file:///home/ronan/agora_sabemos/frontend/src/index.css)
Design system com CSS variables: cores, espaçamentos, tipografia (Google Fonts — Inter), glassmorphism effects, animações. Dark theme como padrão.

#### [NEW] [src/App.jsx](file:///home/ronan/agora_sabemos/frontend/src/App.jsx)
Componente principal com layout: Header, Area Selector, Filters, Results Table, Distribution Panel.

#### [NEW] [src/components/AreaSelector.jsx](file:///home/ronan/agora_sabemos/frontend/src/components/AreaSelector.jsx)
Componente para seleção de área com campo de busca para filtrar as 50 áreas. Design com cards ou dropdown pesquisável.

#### [NEW] [src/components/ResultsTable.jsx](file:///home/ronan/agora_sabemos/frontend/src/components/ResultsTable.jsx)
Tabela de resultados com: título do periódico, ISSN, estrato (com badges coloridas). Paginação client-side conectada à API.

#### [NEW] [src/components/ClassificationFilter.jsx](file:///home/ronan/agora_sabemos/frontend/src/components/ClassificationFilter.jsx)
Filtro por classificação (A1–C) usando chip/toggle buttons. Permite selecionar um ou mais estratos.

#### [NEW] [src/components/DistributionPanel.jsx](file:///home/ronan/agora_sabemos/frontend/src/components/DistributionPanel.jsx)
Visualização da distribuição dos estratos na área selecionada. Inclui:
- Tabela de contagem por estrato
- Barra visual de distribuição (CSS puro, sem lib externa de gráficos)

#### [NEW] [src/api.js](file:///home/ronan/agora_sabemos/frontend/src/api.js)
Funções utilitárias para chamadas à API do backend (`fetch` wrapper).

---

### Diferencial — Chatbot com IA (Fase 2, após base pronta)

Integração com **Google Gemini** usando **function calling** para consultas em linguagem natural. O modelo recebe as definições dos endpoints como ferramentas e decide qual query executar.

**Fluxo:** Usuário digita → Backend envia ao Gemini com function definitions → Gemini retorna function call → Backend executa no PostgreSQL → Gemini formata resposta → Retorna ao usuário.

#### [NEW] [chat.py](file:///home/ronan/agora_sabemos/backend/chat.py)
- Definição das tools/functions para o Gemini (mapeando `search_periodicos`, `get_distribuicao`, `list_areas`)
- Lógica de function calling: recebe a resposta do Gemini, executa a query correspondente, re-envia resultado ao Gemini para formatação
- **`POST /api/chat`** — Recebe `{ "message": "..." }`, retorna `{ "response": "...", "data": [...] }`

#### [NEW] [src/components/ChatPanel.jsx](file:///home/ronan/agora_sabemos/frontend/src/components/ChatPanel.jsx)
- Painel de chat flutuante (canto inferior direito) com botão toggle
- Histórico de mensagens com bolhas estilizadas conforme design guidelines
- Exibe dados retornados (tabelas inline) quando relevante
- Sugestões de perguntas pré-definidas para onboarding

---

### Documentação

#### [NEW] [README.md](file:///home/ronan/agora_sabemos/README.md)
Documentação com:
- Descrição do projeto
- Decisões técnicas (por que PostgreSQL, abordagem híbrida ORM+SQL, FastAPI, React)
- Instruções de instalação e execução (Docker + backend + frontend)
- Screenshots
- Estrutura do projeto

---

## Decisões Técnicas

| Decisão | Justificativa |
|---|---|
| **PostgreSQL** via Docker | Demonstra domínio de banco relacional robusto, Docker Compose, e arquitetura de produção |
| **Híbrido ORM + Raw SQL** | ORM para definição de modelos, raw SQL para queries complexas — demonstra domínio de SQL (window functions, CASE WHEN, ILIKE) |
| **`COUNT(*) OVER()`** | Window function para obter total de registros na mesma query da paginação, evitando round-trip extra |
| **Gemini function calling** | Mais elegante que prompt engineering puro — o modelo escolhe qual endpoint chamar baseado na intenção do usuário |
| **Paginação server-side** | 171K registros é demais para enviar de uma vez |
| **CSS puro para charts** | Evita dependência pesada (Chart.js/D3) para uma visualização simples |

---

## Verification Plan

### Automated (API — via curl)
```bash
# 1. Listar áreas
curl http://localhost:8000/api/areas

# 2. Buscar periódicos de uma área
curl "http://localhost:8000/api/periodicos?area=COMPUTAÇÃO"

# 3. Filtrar por estrato  
curl "http://localhost:8000/api/periodicos?area=COMPUTAÇÃO&estrato=A1"

# 4. Buscar por texto
curl "http://localhost:8000/api/periodicos?search=IEEE&area=COMPUTAÇÃO"

# 5. Distribuição
curl "http://localhost:8000/api/areas/COMPUTAÇÃO/distribuicao"
```

### Visual (Frontend — via browser)
- Abrir `http://localhost:5173`
- Verificar seleção de área, tabela de resultados, filtros e distribuição
- Testar responsividade em diferentes tamanhos de tela

### Chatbot (Fase 2)
```bash
# Teste de linguagem natural
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quais são os periódicos A1 de Computação?"}'
```
- Verificar que retorna dados corretos + resposta formatada
- Testar edge cases: perguntas fora do escopo, áreas inexistentes
