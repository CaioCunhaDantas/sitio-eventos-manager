"""Cria o arquivo do banco SQLite a partir de database/schema.sql.

Uso (na raiz do projeto):
    py database/criar_banco.py

Pode rodar mais de uma vez sem perigo: o schema usa
"CREATE ... IF NOT EXISTS", então nada que já existe é apagado.
"""

import os
import sqlite3
from pathlib import Path

PASTA_DATABASE = Path(__file__).resolve().parent
CAMINHO_SCHEMA = PASTA_DATABASE / "schema.sql"
# A variável de ambiente SITIO_DB permite usar outro arquivo (ex.: em testes)
CAMINHO_BANCO = Path(os.environ.get("SITIO_DB", PASTA_DATABASE / "sitio.db"))


def conectar(caminho_banco: Path = CAMINHO_BANCO) -> sqlite3.Connection:
    """Abre uma conexão com as chaves estrangeiras ligadas.

    No SQLite, a checagem de chave estrangeira vem DESLIGADA e precisa
    ser ativada em cada conexão. Por isso toda conexão do sistema deve
    passar por esta função.
    """
    conexao = sqlite3.connect(caminho_banco)
    conexao.row_factory = sqlite3.Row  # permite ler colunas pelo nome: linha["nome"]
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


def criar_banco(caminho_banco: Path = CAMINHO_BANCO) -> None:
    """Executa o schema.sql no banco indicado (cria o arquivo se não existir)."""
    schema = CAMINHO_SCHEMA.read_text(encoding="utf-8")
    with conectar(caminho_banco) as conexao:
        conexao.executescript(schema)
    conexao.close()


if __name__ == "__main__":
    criar_banco()
    print(f"Banco pronto em: {CAMINHO_BANCO}")
