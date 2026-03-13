# Security Guidelines — QUALIS CAPES

> Consultar antes de implementar qualquer endpoint ou manipulação de dados.

---

## 1. Contexto de Ameaça

Dados QUALIS são **públicos** — não há informação sensível. O foco de segurança é:
- Prevenir abuso da API (especialmente o endpoint Gemini)
- Impedir SQL injection
- Proteger secrets (API keys)
- Garantir integridade da aplicação

**Autenticação:** ❌ Não aplicável. Dados públicos, ferramenta de consulta.

---

## 2. SQL Injection

Risco real — usamos raw SQL. **Regras:**

```python
# ✅ CORRETO — parametrizado
text("SELECT * FROM periodicos WHERE area = :area"), {"area": user_input}

# ❌ PROIBIDO — interpolação direta
text(f"SELECT * FROM periodicos WHERE area = '{user_input}'")
```

- **Todo** input do usuário DEVE passar por parâmetros bind (`:param`)
- Nunca concatenar/interpolar strings em queries SQL
- SQLAlchemy `text()` com dicionário de parâmetros sempre

---

## 3. Validação de Input

| Input | Validação |
|---|---|
| `area` | Verificar se existe nas áreas cadastradas (whitelist) |
| `estrato` | Enum: A1, A2, A3, A4, B1, B2, B3, B4, C |
| `search` | Strip whitespace, limitar a 200 chars |
| `page`, `per_page` | Inteiros positivos, `per_page` ≤ 100 |
| `message` (chat) | Strip whitespace, limitar a 500 chars |

Usar **Pydantic** `Query()` com constraints nos endpoints FastAPI.

---

## 4. Rate Limiting

Essencial para o endpoint `/api/chat` (custo de API Gemini):

- `/api/chat`: **10 req/min** por IP
- Demais endpoints: **60 req/min** por IP
- Usar `slowapi` (wrapper do `limits` para FastAPI)

---

## 5. Secrets

- API key do Gemini em **variável de ambiente** (`GEMINI_API_KEY`)
- Credenciais do PostgreSQL em **variável de ambiente** ou `docker-compose.yml` (dev only)
- **`.env`** no `.gitignore` — nunca committar
- Fornecer `.env.example` como template

---

## 6. CORS

```python
# Apenas origens necessárias
origins = [
    "http://localhost:5173",  # Vite dev
    "http://localhost:3000",  # fallback
]
```

Nunca usar `allow_origins=["*"]` em produção.

---

## 7. Headers de Segurança

Adicionar via middleware ou responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

---

## 8. Checklist Pré-Commit

- [ ] Nenhuma string interpolada em queries SQL?
- [ ] Inputs validados com Pydantic?
- [ ] API keys em variáveis de ambiente?
- [ ] `.env` no `.gitignore`?
- [ ] CORS restrito a origens específicas?
