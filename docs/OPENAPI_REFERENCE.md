# OpenAPI Quick Reference

This file provides a quick visual reference of the QUALIS CAPES API specification.

## API Overview

```
Service:     QUALIS CAPES API
Title:       Consulta de Classificação QUALIS de Periódicos Científicos
Version:     1.0.0
Base URL:    http://localhost:8000
Format:      JSON (UTF-8)
Docs:        http://localhost:8000/docs (Scalar)
OpenAPI:     http://localhost:8000/openapi.json
```

## Endpoint Summary

```
┌─ ÁREAS ──────────────────────────────────────────────┐
│ GET  /api/areas                                       │  Lista ~50 áreas
│ GET  /api/areas/{area}/distribuicao                  │  Distribuição por estrato
└──────────────────────────────────────────────────────┘

┌─ PERIÓDICOS ─────────────────────────────────────────┐
│ GET  /api/periodicos?area=&estrato=&search=&page=   │  Busca avançada
└──────────────────────────────────────────────────────┘

┌─ CHAT (IA) ──────────────────────────────────────────┐
│ POST /api/chat                                        │  Linguagem natural
└──────────────────────────────────────────────────────┘

┌─ INFRA ──────────────────────────────────────────────┐
│ GET  /health                                          │  Health check
└──────────────────────────────────────────────────────┘
```

## Tag Categories

### 🏷️ Áreas
Endpoints para explorar áreas de avaliação CAPES:
- `GET /api/areas` - Lista todas as áreas
- `GET /api/areas/{area}/distribuicao` - Distribuição por estrato

### 🏷️ Periódicos
Endpoints para pesquisar periódicos:
- `GET /api/periodicos` - Busca com filtros e paginação

### 🏷️ Chat
Endpoints para consultas em IA:
- `POST /api/chat` - Linguagem natural com Gemini

### 🏷️ Infra
Endpoints de infraestrutura:
- `GET /health` - Verificação de disponibilidade

## HTTP Methods

| Método | Descrição | Endpoints |
|--------|-----------|-----------|
| GET | Recuperar dados (idempotente) | /api/areas, /api/periodicos, /api/areas/{area}/distribuicao, /health |
| POST | Submeter dados (não-idempotente) | /api/chat |

## Response Codes

| Código | Significado |
|--------|-------------|
| 200 | OK - Sucesso |
| 400 | Bad Request - Sintaxe inválida |
| 404 | Not Found - Recurso não existe |
| 422 | Unprocessable Entity - Validação falhou |
| 429 | Too Many Requests - Rate limit excedido |
| 503 | Service Unavailable - Erro de backend |

## Common Response Headers

```http
Content-Type: application/json; charset=utf-8
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Retry-After: <seconds>  (quando 429)
```

## Rate Limits

```
GET  /api/areas                        60 req/min
GET  /api/periodicos                   60 req/min
GET  /api/areas/{area}/distribuicao    60 req/min
POST /api/chat                         10 req/min  ⚠️ Limite reduzido
```

## Estratos de Classificação

| Estrato | Qualidade |
|---------|-----------|
| A1 | ⭐⭐⭐⭐⭐ Excelência Internacional |
| A2 | ⭐⭐⭐⭐ Muito Bom Nível |
| A3 | ⭐⭐⭐ Bom Nível |
| A4 | ⭐⭐ Nível Satisfatório |
| B1 | ⭐⭐ Bom (com restrições) |
| B2 | ⭐ Nível Satisfatório |
| B3 | · Nível Adequado |
| B4 | · Circulação Local |
| C | ✗ Descontinuado/Inadequado |

## CORS Configuration

```javascript
Allowed Origins:
  - http://localhost:5173  (frontend dev)
  - http://localhost:3000  (frontend alt)
  - ${PROD_ORIGIN}         (env variable)

Allowed Methods:
  - GET
  - POST

Allowed Headers:
  - Content-Type
```

## Security Features

✓ Rate limiting per IP  
✓ Input validation (Pydantic)  
✓ SQL injection prevention (ORM + parameterized)  
✓ CORS restrictions  
✓ Security headers  
✓ Audit logging  

## Example Request/Response

### Request

```bash
curl -X GET "http://localhost:8000/api/periodicos?area=Botânica&estrato=A1&page=1&per_page=10" \
  -H "Content-Type: application/json"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "issn": "0100-3941",
      "titulo": "Acta Botanica Brasilica",
      "area": "Botânica",
      "estrato": "A1"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 10,
  "total_pages": 2
}
```

## Common Operations

### 1. Get All Areas

```bash
GET /api/areas
```

### 2. Search Periodicos

```bash
GET /api/periodicos?area=Botânica&estrato=A1&estrato=A2
```

### 3. Get Distribution

```bash
GET /api/areas/Botânica/distribuicao
```

### 4. AI Query

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Quais periódicos de Botânica têm estrato A1?"
}
```

## Testing Endpoints

### Using curl

```bash
# Test all areas
curl http://localhost:8000/api/areas

# Test distribution
curl "http://localhost:8000/api/areas/Bot%C3%A2nica/distribuicao"

# Test search
curl "http://localhost:8000/api/periodicos?search=0100-3941"

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Mostrar periódicos A1 de Botânica"}'

# Test health
curl http://localhost:8000/health
```

### Using Scalar UI

```
Visit: http://localhost:8000/docs
```

All endpoints are interactive and can be tested directly from the UI.

## Related Documentation

- `docs/API_DOCUMENTATION.md` - Documentação completa com exemplos
- `backend/README.md` - Guia de setup e desenvolvimento
- `docs/ARCHITECTURE.md` - Arquitetura geral do sistema
- `docs/SECURITY_GUIDELINES.md` - Políticas de segurança
