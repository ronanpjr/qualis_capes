# QUALIS CAPES - Consulta de Periódicos

## Planning
- [x] Inspect QUALIS data file structure
- [x] Create Python venv
- [x] Write implementation plan
- [x] Write design guidelines
- [x] Get user approval on plan

## Backend (FastAPI)
- [ ] Project setup (dependencies, structure)
- [ ] Data loading script (XLSX → SQLite)
- [ ] Database models and connection
- [ ] API endpoints:
  - [ ] `GET /api/areas` — list all areas
  - [ ] `GET /api/periodicos` — search by area, filter by estrato, pagination
  - [ ] `GET /api/areas/{area}/distribuicao` — distribution stats
- [ ] Error handling and CORS

## Frontend (React + Vite)
- [ ] Project scaffolding (Vite + React)
- [ ] Design system (CSS variables, global styles)
- [ ] Components:
  - [ ] Area selector (search/filter)
  - [ ] Results table with pagination
  - [ ] Classification filter
  - [ ] Distribution chart/table
  - [ ] Header/layout
- [ ] API integration
- [ ] Responsive design and polish

## Fase 2 — Chatbot Gemini
- [ ] Backend: `chat.py` com function calling
- [ ] Backend: endpoint `POST /api/chat`
- [ ] Frontend: `ChatPanel.jsx` com UI de chat
- [ ] Testes e verificação

## Documentation
- [ ] README.md with setup instructions
- [ ] Technical decisions documentation

## Verification
- [ ] Backend API tests (curl/httpie)
- [ ] Frontend visual verification (browser)
- [ ] Full integration test
