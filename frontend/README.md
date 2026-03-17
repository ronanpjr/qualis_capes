# Frontend — QUALIS CAPES

Interface React para consultar classificações QUALIS com filtros avançados, gráficos de distribuição e chat com IA.

## 📋 Índice

- [Estrutura](#estrutura)
- [Setup Local](#setup-local)
- [Desenvolvimento](#desenvolvimento)
- [Build & Deploy](#build--deploy)
- [Componentes](#componentes)
- [Hooks Customizados](#hooks-customizados)
- [Styling](#styling)
- [Responsividade](#responsividade)

---

## Estrutura

```
frontend/
├── src/
│   ├── main.jsx              # Entry point React
│   ├── App.jsx               # Root component (state management)
│   ├── index.css             # Global styles
│   ├── api.js                # API client (fetch wrapper)
│   ├── components/
│   │   ├── AreaSelector.jsx      # Dropdown áreas
│   │   ├── ClassificationFilter.jsx  # Chips estratos
│   │   ├── ResultsTable.jsx       # Tabela paginada
│   │   ├── DistributionPanel.jsx  # Gráfico (Recharts)
│   │   └── ChatPanel.jsx          # Chat IA flutuante
│   ├── hooks/
│   │   ├── useQualisData.js       # Hook de dados
│   │   └── useDebounce.js         # Hook debounce
│   └── assets/                    # Imagens, ícones
├── index.html               # HTML template
├── vite.config.js          # Vite config
├── eslint.config.js        # ESLint config
├── package.json
└── package-lock.json
```

---

## Setup Local

### 1. Dependências

```bash
cd frontend
npm install
```

### 2. Variáveis de Ambiente

```bash
# .env.local
VITE_API_URL=http://localhost:8000
```

### 3. Dev Server (Hot Reload)

```bash
npm run dev
```

Acesse: **http://localhost:5173**

---

## Desenvolvimento

### Dev Server

```bash
npm run dev
```

- Hot Module Replacement (HMR) automático
- Console mostra erros em tempo real
- Reload ao salvar arquivo

### Linting

```bash
npm run lint
npm run lint -- --fix  # Auto-fix issues
```

### Build

```bash
npm run build
# Gera dist/ otimizado
```

### Preview (Produção Local)

```bash
npm run build
npm run preview
```

---

## Build & Deploy

### Build Otimizado

```bash
npm run build
```

**Saída:** `dist/` pronto para deployment

**Includes:**
- Minificação CSS/JS
- Code splitting automático (Vite)
- Source maps para debug
- Assets otimizadas

### Deploy (Static Hosting)

**Opção 1: Docker (Recomendado)**
```bash
# Incluído em docker-compose.yml
docker compose up -d frontend
```

**Opção 2: Netlify**
```bash
npm run build
# Conectar pasta dist/ ao Netlify
```

**Opção 3: Vercel**
```bash
npm install -g vercel
vercel deploy
```

**Opção 4: GitHub Pages**
```bash
npm run build
# Commitar dist/ ou usar workflow
```

---

## Componentes

### 1. App.jsx — Root Component

**State Management:**
- `selectedArea` — Área selecionada
- `selectedEstratos` — Estratos (A1, A2, ...)
- `searchText` — Texto de busca
- `periodicos` — Resultados
- `currentPage` — Página atual
- `distribuicao` — Dados do gráfico
- `chatOpen` — Chat visível

---

### 2. AreaSelector.jsx — Dropdown

**Features:**
- Dropdown pesquisável
- 50 áreas
- Default: todos

---

### 3. ClassificationFilter.jsx — Chips

**Features:**
- Multi-select de estratos
- Chips visuais
- Toggle on/off

---

### 4. ResultsTable.jsx — Tabela Paginada

**Features:**
- Tabela desktop
- Cards mobile (responsivo)
- Paginação
- Sortable (futuro)

---

### 5. DistributionPanel.jsx — Gráfico

**Features:**
- Bar chart (Recharts)
- Contagem + percentual
- Responsivo

---

### 6. ChatPanel.jsx — Chat IA

**Features:**
- Botão flutuante
- Mensagens em tempo real
- Markdown support
- Histórico

---

## Hooks Customizados

### useQualisData.js

Fetch com loading/error:

```javascript
const { fetchPeriodicos, fetchDistribuicao, loading, error } = useQualisData()
```

### useDebounce.js

Debounce para search (300ms default):

```javascript
const debouncedSearch = useDebounce(searchText, 300)
```

---

## Styling

### Paleta (CSS Variables)

```
--primary-900: #0D1B3E (azul institucional)
--neutral-900: #1F2937 (texto)
--estrato-a1: #166534 (verde — A1/A2)
--estrato-b1: #CA8A04 (âmbar — B1)
--estrato-c: #6B7280 (cinza — C)
```

### CSS Organização

- `index.css` — Global
- Cada componente tem className própria
- Sem preprocessadores (vanilla CSS)

---

## Responsividade

### Breakpoint

```
Desktop: > 768px
Mobile: < 768px
```

### Layout

- **Desktop:** Header + Sidebar + Content
- **Mobile:** Header (stacked) + Content (full width)

---

## API Client

```javascript
import { getAreas, getPeriodicos, getDistribuicao } from './api'
```

**Features:**
- Timeout 10s
- CORS automático
- Error handling

---

## Performance

- ✅ Debounce (300ms)
- ✅ Paginação (server-side)
- ✅ Code splitting (Vite)
- ✅ Bundle ~120KB

---

**Versão:** 1.0  
**Última atualização:** March 16, 2026
