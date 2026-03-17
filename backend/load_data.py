"""
Script de carga de dados — XLSX → PostgreSQL.

Lê o arquivo classificacoes_publicadas_sucupira_teste.xlsx e insere todos os
registros na tabela periodicos usando batch insert com psycopg2 diretamente
(via engine.raw_connection) para máxima performance com ~171K linhas.

Uso:
    cd backend
    source venv/bin/activate
    python load_data.py [--xlsx /caminho/para/arquivo.xlsx]

Dentro do Docker, o arquivo é montado em /app/classificacoes_publicadas_sucupira_teste.xlsx
como volume read-only e carregado automaticamente pelo entrypoint.sh quando o banco está vazio.
"""

import argparse
import os
import sys
import time
from pathlib import Path

import openpyxl
from sqlalchemy import text

from database import engine
from models import Base


BATCH_SIZE = 5_000
DEFAULT_XLSX = Path(os.getenv("XLSX_PATH", str(Path(__file__).parent / "classificacoes_publicadas_sucupira_teste.xlsx")))


def create_tables():
    """Cria a tabela e os índices se não existirem."""
    print("▶ Criando tabelas e índices...")
    Base.metadata.create_all(bind=engine)

    # Índice de busca textual para ILIKE em título (pg_trgm)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_periodicos_titulo_trgm
            ON periodicos USING gin (titulo gin_trgm_ops)
        """))
        conn.commit()
    print("  ✓ Tabelas e índices criados.")


def load_xlsx(xlsx_path: Path) -> list[tuple]:
    """Lê o XLSX e retorna lista de tuplas (issn, titulo, area, estrato)."""
    print(f"▶ Lendo {xlsx_path.name}...")
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["RelatorioQualis"]

    rows = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        issn, titulo, area, estrato = row
        if not all([issn, titulo, area, estrato]):
            continue  # pula linhas incompletas
        rows.append((
            str(issn).strip(),
            str(titulo).strip(),
            str(area).strip(),
            str(estrato).strip(),
        ))

    wb.close()
    print(f"  ✓ {len(rows):,} registros lidos.")
    return rows


def insert_data(rows: list[tuple]):
    """Inserção em batch usando raw connection com transação atômica.

    Técnica:
    - engine.begin() cria uma transação automática com rollback em caso de erro
    - Se qualquer INSERT falhar, TRUNCATE é revertido automaticamente
    - Commits por batch (~5K registros) para balance entre segurança e performance
    """
    print(f"▶ Inserindo {len(rows):,} registros em batches de {BATCH_SIZE:,}...")

    start = time.time()
    total_inserted = 0

    # engine.begin() cria uma transação com rollback automático em caso de exceção
    with engine.begin() as conn:
        # Limpa dados existentes dentro da transação (para rollback atômico)
        conn.execute(text("TRUNCATE TABLE periodicos RESTART IDENTITY"))

        raw_conn = conn.connection.driver_connection
        cursor = raw_conn.cursor()

        try:
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                cursor.executemany(
                    "INSERT INTO periodicos (issn, titulo, area, estrato) VALUES (%s, %s, %s, %s)",
                    batch,
                )
                total_inserted += len(batch)
                elapsed = time.time() - start
                print(f"  {total_inserted:,}/{len(rows):,} ({elapsed:.1f}s)", end="\r")
        finally:
            cursor.close()
            # Conexão será fechada automaticamente ao sair do contexto

    elapsed = time.time() - start
    print(f"\n  ✓ {total_inserted:,} registros inseridos em {elapsed:.2f}s.")


def verify(expected: int):
    """Verifica contagem final no banco."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM periodicos"))
        count = result.scalar()

    if count == expected:
        print(f"  ✓ Verificação OK: {count:,} registros no banco.")
    else:
        print(f"  ⚠ Atenção: esperado {expected:,}, encontrado {count:,}.")


def main():
    parser = argparse.ArgumentParser(description="Carga de dados QUALIS → PostgreSQL")
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=DEFAULT_XLSX,
        help="Caminho para o arquivo XLSX",
    )
    args = parser.parse_args()

    if not args.xlsx.exists():
        print(f"❌ Arquivo não encontrado: {args.xlsx}")
        sys.exit(1)

    print("=" * 50)
    print("  QUALIS CAPES — Carga de Dados")
    print("=" * 50)

    create_tables()
    rows = load_xlsx(args.xlsx)
    insert_data(rows)
    verify(len(rows))

    print("\n✅ Carga concluída! Banco pronto para uso.")


if __name__ == "__main__":
    main()
