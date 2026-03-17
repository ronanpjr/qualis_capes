# API Documentation — QUALIS CAPES

Documentação completa da **REST API** para consulta de periódicos QUALIS CAPES.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Autenticação](#autenticação)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Áreas](#áreas)
  - [Periódicos](#periódicos)
  - [Chat (IA)](#chat-ia)
  - [Health Check](#health-check)
- [Modelos de Dados](#modelos-de-dados)
- [Códigos de Status](#códigos-de-status)
- [Exemplos de Uso](#exemplos-de-uso)
- [Tratamento de Erros](#tratamento-de-erros)
- [Segurança](#segurança)

---

## Visão Geral

A **QUALIS CAPES API** fornece acesso estruturado aos dados de classificação de ~7000 periódicos científicos brasileiros em ~50 áreas de avaliação.

### Base URL

```
http://localhost:8000  (desenvolvimento)
```

### Formato

- **Requisições**: JSON (POST) + Query Parameters (GET)
- **Respostas**: JSON UTF-8
- **Versionamento**: Via URL (`/api/v1/...` em futuras versões)

### Documentação Interativa

A documentação interativa está disponível em **3 formatos**:

1. **Scalar** (recomendado): `GET /docs`
2. **OpenAPI JSON**: `GET /openapi.json`
3. **Esta documentação**: `docs/API_DOCUMENTATION.md`

---

## Autenticação

Atualmente, a API **não requer autenticação**. Recomenda-se implementar em futuras versões:

- API Keys para clientes produtivos
- OAuth 2.0 para integração com sistemas CAPES

---

## Rate Limiting

Proteção contra abuso via **SlowAPI**. Limites por IP do cliente:

| Endpoint | Limite | Janela |
|----------|--------|--------|
| `GET /api/areas` | 60 | minuto |
| `GET /api/periodicos` | 60 | minuto |
| `GET /api/areas/{area}/distribuicao` | 60 | minuto |
| `POST /api/chat` | **10** | minuto |

**Resposta quando limite é excedido:**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45

{
  "detail": "rate limit exceeded: 10 per 1 minute"
}
```

---

## Endpoints

### Áreas

#### GET /api/areas

Lista todas as áreas de avaliação CAPES disponíveis.

**Parâmetros**: Nenhum

**Resposta (200 OK)**:

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
  "Ciência da Computação",
  "Ciência Política",
  "Ciências Ambientais",
  "Ciências Sociais Aplicadas",
  "Comunicação",
  "Dentística",
  "Dermatologia",
  "Economia",
  "Educação",
  "Educação Física",
  "Engenharia Aeronáutica",
  "Engenharia Civil",
  "Engenharia de Minas",
  "Engenharia de Produção",
  "Engenharia Elétrica",
  "Engenharia Mecânica",
  "Engenharia Química",
  "Ensino",
  "Entomologia",
  "Escultura",
  "Espaço",
  "Estatística",
  "Estética",
  "Ética",
  "Farmacologia",
  "Filosofia",
  "Física",
  "Fisioterapia e Terapia Ocupacional",
  "Fisiologia",
  "Fitotecnia",
  "Fonoaudiologia",
  "Fotografia",
  "Gastroenterologia",
  "Genética",
  "Geografia",
  "Geologia",
  "Geometria",
  "Geotecnia",
  "Ginecologia",
  "Hematologia",
  "Herpetologia",
  "Histologia",
  "História",
  "Homeopatia",
  "Imunologia",
  "Imunologia Clínica",
  "Inclusão Social",
  "Infectologia",
  "Informática na Educação",
  "Infraestrutura",
  "Inorgânica",
  "Integração Sensorial",
  "Interiores",
  "Iridologia",
  "Irrigação e Drenagem",
  "Isolamento Acústico",
  "Ixodologia"
]
```

**Erro (404 Not Found)**:

```json
{
  "detail": "Nenhuma área encontrada."
}
```

**Exemplo com curl**:

```bash
curl http://localhost:8000/api/areas
```

---

#### GET /api/areas/{area}/distribuicao

Retorna a distribuição de periódicos por estrato para uma área específica.

**Parâmetros**:

- `area` (path, obrigatório): Nome da área (ex: "Botânica", "Física")

**Resposta (200 OK)**:

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
    {
      "estrato": "A4",
      "count": 20,
      "percentual": 14.18
    },
    {
      "estrato": "B1",
      "count": 25,
      "percentual": 17.73
    },
    {
      "estrato": "B2",
      "count": 18,
      "percentual": 12.77
    },
    {
      "estrato": "B3",
      "count": 12,
      "percentual": 8.51
    },
    {
      "estrato": "B4",
      "count": 8,
      "percentual": 5.67
    },
    {
      "estrato": "C",
      "count": 3,
      "percentual": 2.13
    }
  ]
}
```

**Erro (404 Not Found)**:

```json
{
  "detail": "Área 'Zoologia' não encontrada ou sem dados."
}
```

**Exemplo com curl**:

```bash
curl "http://localhost:8000/api/areas/Bot%C3%A2nica/distribuicao"
```

---

### Periódicos

#### GET /api/periodicos

Busca periódicos com filtros avançados e paginação.

**Parâmetros** (todos opcionais):

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `area` | string | Area de avaliação (exact match) | - |
| `estrato` | list[string] | Um ou mais estratos (A1...C) | - |
| `search` | string | Busca por título ou ISSN | - |
| `page` | integer | Número da página (≥1) | 1 |
| `per_page` | integer | Itens por página (1-100) | 30 |

**Resposta (200 OK)**:

```json
{
  "items": [
    {
      "id": 1,
      "issn": "0100-3941",
      "titulo": "Acta Botanica Brasilica",
      "area": "Botânica",
      "estrato": "A1"
    },
    {
      "id": 2,
      "issn": "0100-4042",
      "titulo": "Acta Limnologica Brasiliensia",
      "area": "Botânica",
      "estrato": "A2"
    }
  ],
  "total": 141,
  "page": 1,
  "per_page": 30,
  "total_pages": 5
}
```

**Erro (422 Unprocessable Entity)** - Validação:

```json
{
  "detail": "Área 'Zoologia' não existe. Áreas disponíveis: Administração, Agronomia, Antropologia..."
}
```

**Exemplos com curl**:

```bash
# Listar todos os periódicos de Botânica
curl "http://localhost:8000/api/periodicos?area=Bot%C3%A2nica"

# Filtrar por estrato
curl "http://localhost:8000/api/periodicos?area=Bot%C3%A2nica&estrato=A1&estrato=A2"

# Buscar por ISSN
curl "http://localhost:8000/api/periodicos?search=0100-3941"

# Buscar por título (parcial)
curl "http://localhost:8000/api/periodicos?search=Acta"

# Combinado com paginação
curl "http://localhost:8000/api/periodicos?area=F%C3%ADsica&estrato=A1&page=2&per_page=50"
```

---

### Chat (IA)

#### POST /api/chat

Consulta em linguagem natural com integração Google Gemini.

**Body** (JSON):

```json
{
  "message": "Quais são os periódicos da área de Botânica com estrato A1 ou A2?"
}
```

**Resposta (200 OK)**:

```json
{
  "response": "Encontrei 30 periódicos da área de Botânica com estratificação A1 ou A2. Aqui estão alguns dos principais...",
  "data": [
    {
      "id": 1,
      "issn": "0100-3941",
      "titulo": "Acta Botanica Brasilica",
      "area": "Botânica",
      "estrato": "A1"
    },
    {
      "id": 15,
      "issn": "0100-5405",
      "titulo": "Brasileira de Botânica",
      "area": "Botânica",
      "estrato": "A2"
    }
  ],
  "action_taken": "search_periodicos"
}
```

**Rate Limit (429 Too Many Requests)**:

```
Limite: 10 requisições por minuto por IP
```

**Erro (503 Service Unavailable)** - Gemini indisponível:

```json
{
  "detail": "Serviço de IA temporariamente indisponível."
}
```

**Exemplos com curl**:

```bash
# Buscar periódicos de uma área
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quais periódicos de Botânica têm estrato A1?"}'

# Listar áreas
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Mostra todas as áreas disponíveis"}'

# Distribuição
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual é a distribuição de estratos em Física?"}'

# Buscar um periódico específico
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual é o estrato do periódico com ISSN 0100-3941?"}'
```

**Function Calling Automático**:

O Gemini escolhe automaticamente qual função chamar baseado na pergunta:

| Pergunta contém | Função invocada |
|-----------------|-----------------|
| "áreas", "lista", "todas" | `list_areas()` |
| "periódicos", "journals", "revistas", "estrato" | `search_periodicos()` |
| "distribuição", "percentual", "gráfico" | `get_distribuicao()` |

---

### Health Check

#### GET /health

Verificação simples de disponibilidade do servidor.

**Resposta (200 OK)**:

```json
{
  "status": "ok"
}
```

**Uso**: Monitoramento, load balancers, health checks em containers.

---

## Modelos de Dados

### PeriodicoResponse

```python
{
  "id": int,              # Identificador único
  "issn": str,            # ISSN (ex: "0100-3941")
  "titulo": str,          # Título da revista
  "area": str,            # Área de avaliação
  "estrato": str          # A1, A2, A3, A4, B1, B2, B3, B4, C
}
```

### PaginatedResponse

```python
{
  "items": list[PeriodicoResponse],
  "total": int,           # Total de itens (todos os filtros)
  "page": int,            # Página atual
  "per_page": int,        # Itens por página
  "total_pages": int      # Total de páginas
}
```

### DistribuicaoItem

```python
{
  "estrato": str,         # A1, A2, ..., C
  "count": int,           # Número de periódicos
  "percentual": float     # Porcentagem (0-100)
}
```

### DistribuicaoResponse

```python
{
  "area": str,                        # Nome da área
  "total": int,                       # Total de periódicos
  "distribuicao": list[DistribuicaoItem]
}
```

### ChatRequest

```python
{
  "message": str          # Pergunta em português (1-500 chars)
}
```

### ChatResponse

```python
{
  "response": str,        # Resposta do AI
  "data": list[dict],     # Dados estruturados (opcional)
  "action_taken": str     # Função invocada (opcional)
}
```

---

## Códigos de Status

| Status | Descrição |
|--------|-----------|
| **200 OK** | Requisição bem-sucedida |
| **400 Bad Request** | Erro na sintaxe da requisição |
| **404 Not Found** | Recurso não encontrado |
| **422 Unprocessable Entity** | Falha na validação de dados |
| **429 Too Many Requests** | Limite de taxa excedido |
| **503 Service Unavailable** | Serviço temporariamente indisponível |

---

## Exemplos de Uso

### 1. Descobrir áreas e explorar uma

```bash
# Passo 1: Listar todas as áreas
curl http://localhost:8000/api/areas

# Passo 2: Escolher "Botânica" e obter distribuição
curl "http://localhost:8000/api/areas/Bot%C3%A2nica/distribuicao"

# Passo 3: Ver periódicos A1 dessa área
curl "http://localhost:8000/api/periodicos?area=Bot%C3%A2nica&estrato=A1"
```

### 2. Buscar um periódico específico

```bash
# Por ISSN
curl "http://localhost:8000/api/periodicos?search=0100-3941"

# Por título (parcial)
curl "http://localhost:8000/api/periodicos?search=Acta"
```

### 3. Análise: periódicos de excelência por área

```bash
# Quantos A1 e A2 tem cada área?
for area in "Botânica" "Física" "Matemática"; do
  curl "http://localhost:8000/api/areas/$area/distribuicao" \
    | jq '.distribuicao | map(select(.estrato | IN("A1", "A2")) | .count) | add'
done
```

### 4. Consultas com IA (recomendado para usuários)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mostra os 10 periódicos mais bem avaliados de Botânica"
  }'
```

---

## Tratamento de Erros

### Exemplo: Área inválida

```bash
curl "http://localhost:8000/api/periodicos?area=INVALIDA"
```

**Resposta (422)**:

```json
{
  "detail": "Área 'INVALIDA' não existe. Áreas disponíveis: Administração, Agronomia, Antropologia..."
}
```

### Exemplo: Rate limit excedido

```bash
# Fazer 61 requisições em 1 minuto
for i in {1..61}; do
  curl http://localhost:8000/api/areas
done
```

**Resposta (429)**:

```json
{
  "detail": "rate limit exceeded: 60 per 1 minute"
}
```

---

## Segurança

### Proteções Implementadas

1. **Rate Limiting**: SlowAPI (por IP)
2. **Input Validation**: Pydantic (max_length, tipos)
3. **SQL Injection**: Queries parametrizadas (SQLAlchemy ORM)
4. **CORS**: Restrições explícitas (localhost + produção)
5. **Security Headers**: X-Content-Type-Options, X-Frame-Options
6. **Logging de Auditoria**: Todos os endpoints fazem log de IPs

### Recomendações Futuras

- [ ] Implementar API Keys
- [ ] OAuth 2.0 para aplicações parceiras
- [ ] HTTPS em produção (TLS 1.3+)
- [ ] Rate limiting por API Key (não apenas IP)
- [ ] WAF (Web Application Firewall) em produção
- [ ] Monitoramento com Sentry/DataDog

---

## Versioning

Atualmente em versão **1.0.0**. Futuras versões usarão:

```
GET /api/v1/areas          (v1)
GET /api/v2/areas          (v2, breaking changes)
```

Compatibilidade com v1 será mantida por pelo menos 12 meses.

---

## Support

Para dúvidas, bugs ou sugestões:

- Documentação: `docs/API_DOCUMENTATION.md`
- Issues: GitHub issues
- Segurança: Ver `docs/SECURITY_GUIDELINES.md`
