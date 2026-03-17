#!/bin/sh
# entrypoint.sh — inicializa o banco se necessário, depois sobe o servidor.
# Só executa load_data.py quando a tabela 'periodicos' está vazia.
set -e

echo "▶ Verificando estado do banco de dados..."

ROW_COUNT=$(python - <<'EOF'
from database import engine
from models import Base
from sqlalchemy import text

# Garante que as tabelas existem antes de contar
Base.metadata.create_all(bind=engine)

with engine.connect() as c:
    print(c.execute(text("SELECT COUNT(*) FROM periodicos")).scalar())
EOF
)

if [ "$ROW_COUNT" -eq "0" ]; then
    echo "▶ Banco vazio — carregando dados iniciais..."
    python load_data.py
else
    echo "▶ Banco já possui $ROW_COUNT registros — pulando carga inicial."
fi

echo "▶ Iniciando servidor..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
