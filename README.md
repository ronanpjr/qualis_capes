# QUALIS CAPES — Consulta de Classificação de Periódicos

Ferramenta para consultar e analisar classificações QUALIS de periódicos científicos da CAPES, permitindo que coordenadores de pós-graduação filtrem por área de avaliação e estrato.

> **Dados:** Classificação de Periódicos — Quadriênio 2021-2024 (Plataforma Sucupira)

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

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd agora_sabemos
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

### 3. Subir o banco de dados

```bash
docker compose up -d
```

### 4. Backend

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

### 5. Frontend

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
