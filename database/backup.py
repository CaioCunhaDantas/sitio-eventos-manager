"""Backup do banco: copia o sitio.db para uma pasta, com data e hora no nome.

Uso (na raiz do projeto):
    py -m database.backup                      # salva em backups/
    py -m database.backup "C:\\Users\\voce\\OneDrive\\Backups Sitio"

Por que não copiar o arquivo direto (Copy-Item)? Se o sistema estiver
gravando naquele instante, a cópia pode sair corrompida. A função
backup() do SQLite copia de forma consistente mesmo com o banco em uso.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from database.criar_banco import CAMINHO_BANCO

PASTA_PADRAO = CAMINHO_BANCO.parent.parent / "backups"
MANTER = 60  # quantos backups guardar (os mais antigos são apagados)


def fazer_backup(pasta_destino: Path = PASTA_PADRAO, manter: int = MANTER,
                 caminho_banco: Path = CAMINHO_BANCO) -> Path | None:
    """Cria um backup e apaga os mais antigos. Devolve o caminho do backup criado."""
    if not caminho_banco.exists():
        print(f"Banco não encontrado em {caminho_banco}. Nada a fazer.")
        return None

    pasta_destino.mkdir(parents=True, exist_ok=True)
    destino = pasta_destino / f"sitio_{datetime.now():%Y-%m-%d_%H%M%S}.db"

    origem = sqlite3.connect(caminho_banco)
    copia = sqlite3.connect(destino)
    try:
        origem.backup(copia)  # cópia consistente, mesmo com o sistema aberto
    finally:
        copia.close()
        origem.close()

    # Mantém só os N mais recentes (o nome começa com a data, então ordenar = ordem cronológica)
    antigos = sorted(pasta_destino.glob("sitio_*.db"))[:-manter]
    for arquivo in antigos:
        arquivo.unlink()

    return destino


if __name__ == "__main__":
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else PASTA_PADRAO
    criado = fazer_backup(pasta)
    if criado:
        print(f"Backup criado: {criado}")
