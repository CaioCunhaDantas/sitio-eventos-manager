"""Cria o arquivo do banco SQLite a partir de database/schema.sql.

Uso (na raiz do projeto):
    py -m database.criar_banco

Pode rodar mais de uma vez sem perigo: o schema usa
"CREATE ... IF NOT EXISTS", então nada que já existe é apagado.
Bancos de versões antigas são atualizados pelas migrações.
"""

import os
import sqlite3
from pathlib import Path

from database.migracoes import MIGRACOES, VERSAO_ATUAL

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
    """Cria o banco (se não existir) ou atualiza um banco antigo para a versão atual.

    1. Banco antigo (já tem tabelas, versão menor): roda as migrações em ordem.
    2. Depois roda o schema.sql: num banco novo cria tudo; num banco já
       atualizado não faz nada (tudo é "IF NOT EXISTS").
    """
    conexao = conectar(caminho_banco)
    try:
        versao = conexao.execute("PRAGMA user_version").fetchone()[0]
        ja_tem_tabelas = conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'cliente'"
        ).fetchone() is not None

        if ja_tem_tabelas:
            # Bancos criados antes do controle de versão ficaram com 0: são a versão 1
            for destino in range(max(versao, 1) + 1, VERSAO_ATUAL + 1):
                conexao.executescript(MIGRACOES[destino])

        conexao.executescript(CAMINHO_SCHEMA.read_text(encoding="utf-8"))
        conexao.execute(f"PRAGMA user_version = {VERSAO_ATUAL}")
        conexao.commit()
    finally:
        conexao.close()


if __name__ == "__main__":
    criar_banco()
    print(f"Banco pronto em: {CAMINHO_BANCO}")
