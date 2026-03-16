# QUALIS CAPES — Consulta de Classificação de Periódicos

Ferramenta para consultar e analisar classificações QUALIS de periódicos científicos da CAPES, permitindo que coordenadores de pós-graduação filtrem por área de avaliação e estrato.

> **Dados:** Classificação de Periódicos — Quadriênio 2021-2024 (Plataforma Sucupira)

*Nota: O enunciado mencionava a escala antiga (com B5), porém, para refletir fielmente a base de dados oficial do quadriênio 2021-2024 fornecida, o sistema foi adaptado para a escala atual (A1-A4, B1-B4, C).*

---

## 🏗️ Stack

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy + Raw SQL |
| **Banco de Dados** | PostgreSQL 16 (Docker) |
| **Frontend** | React 18 · Vite |
| **IA** | Google Gemini (function calling) |
| **Infra** | Docker Compose |

---

## 📋 Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.12+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) e npm
- Chave de API do [Google Gemini](https://aistudio.google.com/apikey) (para o chatbot)

---

## 🚀 Setup

Você pode rodar o projeto inteiramente via Docker (Recomendado) ou manualmente.

### Opção 1: Via Docker (Recomendado)

A infraestrutura completa (Banco de Dados, Backend FastAPI e Frontend Vite) está configurada no `docker-compose`.

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd agora_sabemos

# 2. Configure as variáveis de ambiente (necessário para a chave da Gemini API)
cp .env.example .env
# Edite o arquivo .env e adicione sua GEMINI_API_KEY

# 3. Suba todos os serviços
docker compose up --build -d

# 4. Popule o banco de dados com a planilha Excel fornecida
docker compose exec backend python load_data.py
```

Acesse **http://localhost:5173** no navegador. O backend estará disponível em `http://localhost:8000`.

---

### Opção 2: Setup Manual

Caso prefira rodar os serviços individualmente na sua máquina:

#### 1. Banco de dados
Suba apenas o banco de dados usando o docker-compose (ou use uma instância PostgreSQL local configurando o `.env`):
```bash
docker compose up -d postgres
```

#### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Carregar dados do XLSX para o PostgreSQL
python load_data.py

# Iniciar o servidor
uvicorn main:app --reload --port 8000
```

#### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Acesse **http://localhost:5173** no navegador.

---

## 📡 API Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/areas` | Lista todas as áreas de avaliação |
| `GET` | `/api/periodicos?area=&estrato=&search=&page=&per_page=` | Busca periódicos com filtros |
| `GET` | `/api/areas/{area}/distribuicao` | Distribuição de estratos por área |
| `POST` | `/api/chat` | Consulta em linguagem natural (Gemini) |

---

## 🏛️ Decisões Técnicas

### Por que PostgreSQL?
Embora SQLite fosse suficiente para ~171K registros, PostgreSQL foi escolhido para demonstrar domínio de banco relacional robusto e arquitetura de produção com Docker Compose.

### Por que Híbrido ORM + Raw SQL?
SQLAlchemy é usado para definição de modelos e gerenciamento de sessão. **Queries SQL customizadas** são usadas em endpoints de performance:
- `COUNT(*) OVER()` — Window function para paginação eficiente (evita query extra)
- `CASE WHEN` — Ordenação customizada de estratos (A1 → C)
- `ILIKE` — Busca textual case-insensitive

### Por que Gemini Function Calling?
Ao invés de prompt engineering simples, usamos function calling — o modelo recebe as definições dos endpoints como ferramentas e decide qual executar baseado na intenção do usuário.

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte de testes unitários para a API (localizada em `backend/tests/`).
Para rodá-los:

```bash
cd backend
pytest -v
```

---

## ⏳ O que eu faria diferente com mais tempo

- **CI/CD Automatizado:** Criaria pipelines no GitHub Actions para rodar o linting, formatação e os testes (Pytest) automaticamente a cada pull request.
- **Testes no Frontend:** Utilizaria o Vitest e a React Testing Library para adicionar cobertura de testes aos componentes React, e Cypress para testes end-to-end (E2E).
- **Cache de Queries no Backend:** Integraria o Redis ou cache na memória (ex. `functools.lru_cache`) para as consultas de `/api/areas` e distribuições, uma vez que são dados de pouquíssima mutabilidade.
- **Migrations:** Utilizaria o Alembic para versionamento do esquema de banco de dados, caso as tabelas ficassem mais complexas ao longo do tempo.
- **Paginação Dinâmica e Melhorias de Busca:** Melhoraria a UX adicionando "infinite scroll" à tabela e implementando o Text Search do Postgres (com dicionários pt-br) ao longo de mais colunas para lidar com plurais e sinônimos.

---

## 📁 Estrutura do Projeto

```
agora_sabemos/
├── backend/
│   ├── main.py              # Aplicação FastAPI
│   ├── database.py          # Configuração SQLAlchemy
│   ├── models.py            # Modelos do banco
│   ├── schemas.py           # Schemas Pydantic
│   ├── queries.py           # Queries SQL customizadas
│   ├── chat.py              # Integração Gemini
│   ├── load_data.py         # Script de carga de dados
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── index.css
│   │   └── components/
│   │       ├── AreaSelector.jsx
│   │       ├── ResultsTable.jsx
│   │       ├── ClassificationFilter.jsx
│   │       ├── DistributionPanel.jsx
│   │       └── ChatPanel.jsx
│   └── package.json
├── docker-compose.yml
├── .env.example
├── DESIGN_GUIDELINES.md
├── SECURITY_GUIDELINES.md
└── README.md
```

---

## 📄 Licença

Projeto acadêmico — uso educacional.
