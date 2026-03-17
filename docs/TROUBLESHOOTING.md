# TROUBLESHOOTING.md — QUALIS CAPES

Guia completo de troubleshooting para problemas comuns durante desenvolvimento, testes e deploy.

## 📋 Índice

- [Problemas de Setup](#problemas-de-setup)
- [Problemas de Banco de Dados](#problemas-de-banco-de-dados)
- [Problemas de Backend](#problemas-de-backend)
- [Problemas de Frontend](#problemas-de-frontend)
- [Problemas de Docker](#problemas-de-docker)
- [Problemas de IA/Gemini](#problemas-de-igemini)
- [Problemas de Performance](#problemas-de-performance)
- [Problemas de Testes](#problemas-de-testes)

---

## Problemas de Setup

### ❌ "Comando `docker compose` não encontrado"

**Diagnóstico:**
```bash
docker --version      # Verificar Docker
docker compose version # Verificar Docker Compose
```

**Solução:**

**Linux:**
```bash
# Opção 1: Install latest docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Opção 2: Via package manager
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

**Mac:**
```bash
# Via Homebrew
brew install docker-compose

# Ou use Docker Desktop (incluso)
```

**Windows:**
- Instale [Docker Desktop para Windows](https://docs.docker.com/desktop/install/windows-install/)
- Inclui Docker Compose automaticamente

---

### ❌ "Erro de permissão: 'docker' requires elevated privileges"

**Solução (Linux):**
```bash
# Adicione seu usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Teste
docker ps
```

**⚠️ Aviso de segurança:** Isso permite que o usuário execute Docker sem `sudo` (risco de elevação de privilégio).

---

### ❌ "Git clone falhou — permissão negada"

**Problema:** Chave SSH não configurada.

**Solução:**
```bash
# Gerar chave SSH (se não tiver)
ssh-keygen -t ed25519 -C "seu-email@example.com"

# Copiar chave pública
cat ~/.ssh/id_ed25519.pub

# Adicionar em GitHub: Settings → SSH and GPG keys → New SSH key
# Colar a chave pública

# Testar
ssh -T git@github.com

# Clonar com SSH
git clone git@github.com:ronanpjr/qualis_capes.git
```

---

## Problemas de Banco de Dados

### ❌ "psycopg2.OperationalError: could not connect to server"

**Causa:** PostgreSQL não está rodando ou acessível.

**Diagnóstico:**
```bash
# Ver se container está rodando
docker compose ps

# Ver logs do postgres
docker compose logs postgres

# Testar conexão
docker compose exec postgres psql -U qualis_user -d qualis_db -c "SELECT 1"
```

**Solução:**

```bash
# 1. Certifique-se de estar no diretório raiz do projeto
cd /home/ronan/agora_sabemos

# 2. Suba o postgres
docker compose up -d postgres

# 3. Aguarde ~5s até estar saudável
docker compose exec postgres pg_isready -U qualis_user

# 4. Tente novamente
```

---

### ❌ "FATAL: database 'qualis_db' does not exist"

**Causa:** Banco não foi criado (docker-compose não criou automaticamente).

**Solução:**
```bash
# Opção 1: Recrear services (melhor)
docker compose down --volumes
docker compose up -d postgres
sleep 5

# Opção 2: Criar manualmente
docker compose exec postgres createdb -U qualis_user qualis_db

# Verificar
docker compose exec postgres psql -U qualis_user -d qualis_db -c "\dt"
```

---

### ❌ "relation 'periodicos' does not exist"

**Causa:** Tabelas não foram criadas (load_data.py não foi executado).

**Solução:**
```bash
# 1. Certifique-se de que backend está rodando
docker compose up -d backend

# 2. Execute o carregador de dados
docker compose exec backend python load_data.py

# 3. Verifique
docker compose exec postgres psql -U qualis_user -d qualis_db -c "SELECT COUNT(*) FROM periodicos;"
```

---

### ❌ "too many connections"

**Causa:** Pool de conexões esgotado.

**Solução:**

```python
# Em backend/database.py, aumentar pool size:
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Aumento de 10
    max_overflow=40,     # Aumento de 20
    pool_pre_ping=True,
)
```

Depois reinicie o backend:
```bash
docker compose restart backend
```

---

### ❌ "Erro ao carregar dados: 'No such file or directory: qualis_capes.xlsx'"

**Causa:** Arquivo XLSX não está no diretório `/backend/`.

**Solução:**
```bash
# Verificar arquivos no backend
ls -la backend/

# Se arquivo não existir:
# 1. Copie o arquivo fornecido:
cp ~/Downloads/qualis_capes.xlsx backend/

# 2. Ou ajuste o script load_data.py para apontar para o caminho correto:
# XLSX_FILE = "qualis_capes.xlsx"  (ou "./qualis_capes.xlsx" ou caminho absoluto)
```

---

## Problemas de Backend

### ❌ "ModuleNotFoundError: No module named 'fastapi'"

**Causa:** Dependências não instaladas.

**Solução:**

**Via Docker:**
```bash
docker compose up --build backend
```

**Manual:**
```bash
cd backend
pip install -r requirements.txt
```

---

### ❌ "GEMINI_API_KEY não configurada"

**Cause:** Variável de ambiente não definida.

**Diagnóstico:**
```bash
echo $GEMINI_API_KEY  # Mostrar valor (deve estar vazio se não configurada)
```

**Solução:**

```bash
# 1. Copie .env.example
cp .env.example .env

# 2. Edite .env e preencha:
GEMINI_API_KEY=sua_chave_aqui_xyz123...

# 3. Via Docker (automático):
docker compose up -d  # Lê .env automaticamente

# 4. Via manual:
export GEMINI_API_KEY="sua_chave_aqui"
uvicorn main:app --reload
```

**Obter chave:**
1. Acesse https://aistudio.google.com/apikey
2. Clique "Get API Key"
3. Copie a chave gerada
4. Cole em `.env`

---

### ❌ "ValueError: invalid literal for int() with base 10"

**Causa:** Query parameter de tipo errado (esperava int, recebeu string).

**Diagnóstico:**
```bash
# Verificar request
curl 'http://localhost:8000/api/periodicos?page=abc'  # ❌ Erro esperado

# Correto:
curl 'http://localhost:8000/api/periodicos?page=1'    # ✅ OK
```

**Solução:** Pydantic já valida automaticamente. Se erro persistir, verificar logs:

```bash
docker compose logs -f backend
```

---

### ❌ "HTTPException: 422 — Estratos inválidos"

**Causa:** Valor de estrato não reconhecido.

**Solução:**

```bash
# Valores válidos:
# A1, A2, A3, A4, B1, B2, B3, B4, C

# ✅ Correto:
curl 'http://localhost:8000/api/periodicos?estrato=A1'

# ❌ Incorreto:
curl 'http://localhost:8000/api/periodicos?estrato=B5'  # B5 não existe
curl 'http://localhost:8000/api/periodicos?estrato=a1'  # Minúscula
```

---

### ❌ "HTTPException: 503 — Serviço de IA temporariamente indisponível"

**Causa:** Gemini API não está respondendo (down, limite atingido, chave inválida).

**Solução:**

```bash
# 1. Verificar status do Gemini:
# https://status.cloud.google.com/

# 2. Validar chave API:
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts": [{"text": "Hello"}]}]}'

# 3. Verificar limite de requisições (Gemini tem rate limit):
# Espere 1 minuto se excedeu

# 4. Logs:
docker compose logs -f backend | grep -i gemini
```

---

### ❌ "Endpoint retorna vazio — nenhum resultado"

**Diagnóstico:**
```bash
# Verificar se dados foram carregados
docker compose exec postgres psql -U qualis_user -d qualis_db -c "SELECT COUNT(*) FROM periodicos;"

# Listar áreas disponíveis
curl http://localhost:8000/api/areas

# Tentar busca sem filtro
curl http://localhost:8000/api/periodicos?per_page=5
```

**Solução:**

```bash
# Se COUNT = 0, dados não foram carregados:
docker compose exec backend python load_data.py

# Se área não existe em lista:
curl http://localhost:8000/api/areas | jq '.' | grep "COMPUTACAO"

# Se digitou errado:
curl 'http://localhost:8000/api/periodicos?area=COMPUTACAO'  # ✅ OK
curl 'http://localhost:8000/api/periodicos?area=computacao'  # ❌ Erro
```

---

### ❌ "Rate limit exceeded — Too many requests"

**Causa:** Você fez muitas requisições rápido demais.

**Limites:**
- Geral: 60 req/min por IP
- Chat: 10 req/min por IP

**Solução:**

```bash
# Espere 60 segundos (o contador reseta)

# Ou mude IP (VPN, proxy, rede diferente)

# Ou customize limite em main.py:
@limiter.limit("120/minute")  # Novo limite
def search_periodicos(...): ...
```

---

## Problemas de Frontend

### ❌ "CORS error — Access to XMLHttpRequest blocked"

**Erro no console:**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/areas'
from origin 'http://localhost:5173' has been blocked by CORS policy:
```

**Causa:** Backend não reconhece origem do frontend.

**Solução:**

```python
# Em backend/main.py, verificar CORS:
origins = [
    "http://localhost:5173",  # ✅ Deve estar aqui
    "http://localhost:3000",
]

# Reinicie backend:
docker compose restart backend
```

---

### ❌ "ERR_CONNECTION_REFUSED — API não responde"

**Diagnóstico:**
```bash
# Verificar se API está rodando
docker compose ps | grep backend

# Testar endpoint
curl http://localhost:8000/health

# Ver logs
docker compose logs backend
```

**Solução:**

```bash
# 1. Suba o backend
docker compose up -d backend

# 2. Aguarde ~3s até estar saudável
sleep 3

# 3. Teste novamente
curl http://localhost:8000/health
```

---

### ❌ "VITE_API_URL não definida — API_URL is undefined"

**Diagnóstico:**
```bash
# Ver variáveis de ambiente no build
docker compose exec frontend env | grep VITE

# Ou verificar em .env.local
cat frontend/.env.local
```

**Solução:**

```bash
# Opção 1: Via .env.local
echo "VITE_API_URL=http://localhost:8000" > frontend/.env.local

# Opção 2: Via Docker build arg
docker compose build frontend --build-arg VITE_API_URL=http://localhost:8000

# Opção 3: Hardcode em api.js (desenvolvimento apenas)
const BASE_URL = "http://localhost:8000"
```

---

### ❌ "Gráfico de distribuição não aparece (vazio)"

**Causa:** Dados da distribuição vazios ou formato incorreto.

**Diagnóstico:**
```bash
curl 'http://localhost:8000/api/areas/COMPUTACAO/distribuicao' | jq '.'
```

**Solução:**

```bash
# 1. Verificar se área existe
curl http://localhost:8000/api/areas | jq '.' | grep COMPUTACAO

# 2. Verificar dados
docker compose exec postgres psql -U qualis_user -d qualis_db -c \
  "SELECT DISTINCT area FROM periodicos LIMIT 5;"

# 3. Se nenhuma área retorna, dados não foram carregados:
docker compose exec backend python load_data.py
```

---

### ❌ "Tabela de resultados não pagina corretamente"

**Causa:** Bug no componente de paginação.

**Diagnóstico:**
```bash
# Verificar resposta da API
curl 'http://localhost:8000/api/periodicos?page=1&per_page=10' | jq '.total_pages'
curl 'http://localhost:8000/api/periodicos?page=2&per_page=10' | jq '.items | length'
```

**Solução:**
- Abra DevTools (F12) → Console → procure erros JavaScript
- Verifique se `total_pages` é um número inteiro
- Limpe cache: Ctrl+Shift+Delete ou `docker compose down`

---

## Problemas de Docker

### ❌ "Docker daemon is not running"

**Causa:** Docker Desktop ou daemon não está iniciado.

**Solução:**

**Linux:**
```bash
sudo systemctl start docker
sudo systemctl status docker
```

**Mac/Windows:**
- Abra **Docker Desktop** (aplicação)
- Aguarde até que apareça "Docker is running"

---

### ❌ "No space left on device"

**Causa:** Disco cheio com imagens/containers Docker antigos.

**Solução:**

```bash
# Limpar
docker system prune -a --volumes  # ⚠️ Remove tudo

# Ou seletivo:
docker image prune -a   # Remove imagens não usadas
docker volume prune     # Remove volumes não usados
docker container prune  # Remove containers stopped

# Ver espaço usado
docker system df
```

---

### ❌ "Image build failed — Dockerfile not found"

**Causa:** Dockerfile não está no diretório correto.

**Verificação:**
```bash
ls -la backend/Dockerfile
ls -la frontend/Dockerfile
```

**Solução:**

```bash
# Assegure-se de que está no diretório raiz do projeto
cd /home/ronan/agora_sabemos

# Reconstrua
docker compose up --build -d
```

---

### ❌ "Port already in use — bind: address already in use"

**Problema:** Porta 5432, 8000 ou 5173 já está ocupada.

**Diagnóstico:**
```bash
# Ver processos usando portas
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
```

**Solução:**

**Opção 1: Parar serviço usando porta**
```bash
kill -9 <PID>
```

**Opção 2: Usar portas diferentes**
```yaml
# docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"  # PostgreSQL na 5433
  backend:
    ports:
      - "8001:8000"  # Backend na 8001
  frontend:
    ports:
      - "5174:80"    # Frontend na 5174
```

---

### ❌ "Container exits with code 1"

**Diagnóstico:**
```bash
# Ver logs
docker compose logs backend
docker compose logs postgres

# Ver status
docker compose ps
```

**Soluções comuns:**

```bash
# Erro de conexão BD
# → Adicionar healthcheck
# → Ordenar depends_on

# Erro de import
# → Verificar requirements.txt
# → Reconstruir: docker compose up --build

# Erro de permissão
# → Verificar volumes no docker-compose.yml
# → Ajustar permissions
```

---

## Problemas de IA/Gemini

### ❌ "Erro 403 — Permission denied for API"

**Causa:** Chave API inválida ou sem permissões.

**Solução:**

```bash
# 1. Validar chave
echo $GEMINI_API_KEY

# 2. Gerar nova chave em https://aistudio.google.com/apikey

# 3. Atualizar .env
GEMINI_API_KEY=nova_chave_aqui

# 4. Reiniciar backend
docker compose restart backend
```

---

### ❌ "Rate limit — Quota exceeded"

**Causa:** Gemini API tem limite de requisições (free tier = ~60 req/min).

**Solução:**

```bash
# Esperar 1 minuto
sleep 60

# Ou usar modelo mais rápido:
# Em chat.py, trocar de gemini-2.5-flash para outro

# Ou limitar requisições no backend:
@limiter.limit("5/minute")  # Reduzir a 5/min ao invés de 10
```

---

### ❌ "Chat retorna resposta vazia ou genérica"

**Causa:** Gemini não entendeu ou não executou a função corretamente.

**Diagnóstico:**
```bash
# Verificar logs
docker compose logs backend | grep -i chat

# Testar manualmente
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quantos periódicos tem?"}'
```

**Solução:**

```bash
# 1. Verificar se database está populado
docker compose exec postgres psql -U qualis_user -d qualis_db -c "SELECT COUNT(*) FROM periodicos;"

# 2. Testar função diretamente
curl 'http://localhost:8000/api/periodicos?per_page=5' | jq '.total'

# 3. Aumentar clareza da mensagem
# Ao invés de: "quantos tem?"
# Use: "Quantos periódicos A1 existem na área de COMPUTACAO?"
```

---

## Problemas de Performance

### ❌ "API lenta — requisição leva >2 segundos"

**Diagnóstico:**
```bash
# Medir latência
time curl 'http://localhost:8000/api/periodicos?per_page=100'

# Ver queries lentas no PostgreSQL
docker compose exec postgres psql -U qualis_user -d qualis_db -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Soluções:**

```bash
# 1. Aumentar per_page pode cache resultados
curl 'http://localhost:8000/api/periodicos?per_page=100'  # Vs 30

# 2. Adicionar índices em PostgreSQL
docker compose exec postgres psql -U qualis_user -d qualis_db -c \
  "CREATE INDEX IF NOT EXISTS ix_periodicos_titulo_trgm ON periodicos USING gist(titulo gist_trgm_ops);"

# 3. Implementar cache em queries simples
# Em queries.py, usar @lru_cache para get_areas()

# 4. Use Redis para cache distribuído (futuro)
```

---

### ❌ "Frontend lento — interface travada"

**Causa:** Bundle grande, sem debounce em buscas, componentes re-rendendo.

**Diagnóstico:**
```bash
# Ver tamanho do bundle
npm run build
du -sh frontend/dist

# Profiling no DevTools (F12 → Performance)
# Gravar interação → Analizar tempo de renderização
```

**Soluções:**

```bash
# 1. Verificar debounce está aplicado
# Em App.jsx, busca deve usar useDebounce(searchText, 300)

# 2. Lazy loading de imagens
<img loading="lazy" src="..." />

# 3. Code splitting
// import { component } = lazy(() => import("./Component"))

# 4. Minimizar re-renders
// Usar useMemo para dados que não mudam frequentemente
```

---

## Problemas de Testes

### ❌ "pytest: command not found"

**Solução:**
```bash
cd backend

# Via pip
pip install pytest

# Ou via requirements.txt
pip install -r requirements.txt

# Testar
pytest --version
```

---

### ❌ "FAILED tests/test_endpoints.py::test_list_areas"

**Diagnóstico:**
```bash
cd backend
pytest -v tests/test_endpoints.py::test_list_areas -s
```

**Causa comum:** Fixture de database não inicializando.

**Solução:**
```python
# Em conftest.py, verificar Base.metadata.create_all()
Base.metadata.create_all(bind=engine)

# Executar novamente
pytest -v --tb=short
```

---

### ❌ "Database lock — cannot lock database"

**Causa:** SQLite (testes) lock de múltiplos acessos.

**Solução:**
```python
# Em conftest.py, usar check_same_thread=False
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False}
)
```

---

## Checklist de Troubleshooting

Antes de desistir, tente:

- [ ] Reiniciar Docker: `docker compose restart`
- [ ] Remover containers/images: `docker compose down -v && docker system prune -a`
- [ ] Limpar cache: `docker compose build --no-cache`
- [ ] Verificar logs: `docker compose logs -f`
- [ ] Testar endpoint direto com `curl`
- [ ] Verificar variáveis de ambiente: `echo $VAR_NAME`
- [ ] Executar load_data.py: `docker compose exec backend python load_data.py`
- [ ] Verificar disco: `df -h`
- [ ] Verificar network: `docker network ls && docker network inspect agora_sabemos_default`

---

**Versão:** 1.0  
**Última atualização:** March 16, 2026
