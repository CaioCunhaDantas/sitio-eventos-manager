"""Cria um banco de DEMONSTRAÇÃO (database/demo.db) com dados fictícios.

Serve para testar e mostrar o sistema sem mexer no banco de verdade
(sitio.db). As datas são calculadas a partir de hoje, então o mês atual
sempre tem festas para ver.

Uso (na raiz do projeto):
    py -m database.dados_exemplo
    $env:SITIO_DB = "database/demo.db"; .\\.venv\\Scripts\\streamlit run app/main.py

Login da demonstração: a senha é SENHA_DEMO, logo abaixo.
"""

import os
from datetime import date, timedelta
from pathlib import Path

CAMINHO_DEMO = Path(__file__).resolve().parent / "demo.db"
SENHA_DEMO = "demo1234"  # só vale para o demo.db, nunca use no banco real

# Precisa vir antes de importar os módulos do banco (eles leem SITIO_DB ao importar)
os.environ["SITIO_DB"] = str(CAMINHO_DEMO)

from database import repositorio as repo  # noqa: E402
from database.criar_banco import criar_banco  # noqa: E402
from database.usuarios import definir_senha  # noqa: E402


def main() -> None:
    CAMINHO_DEMO.unlink(missing_ok=True)  # recomeça do zero a cada execução
    criar_banco(CAMINHO_DEMO)
    definir_senha("Demonstração", SENHA_DEMO)

    hoje = date.today()
    ana = repo.criar_cliente("Ana Souza", "21 99999-0000", observacoes="Indicação da vizinha")
    bruno = repo.criar_cliente("Bruno Lima", "21 98888-1111", "bruno@exemplo.com")
    carla = repo.criar_cliente("Carla Mendes", "21 97777-2222")
    daniel = repo.criar_cliente("Daniel Rocha", "21 96666-3333")

    # Festa que já passou e ainda tem saldo (aparece como atrasada)
    r1 = repo.criar_reserva(carla, hoje - timedelta(days=6), "12:00", "18:00", "Batizado",
                            60, 250_000, 75_000)
    repo.registrar_pagamento(r1, 75_000, hoje - timedelta(days=40), "sinal", "dinheiro")

    # Festa confirmada (sinal pago)
    r2 = repo.criar_reserva(ana, hoje + timedelta(days=5), "10:00", "18:00",
                            "Aniversário de 15 anos", 120, 450_000, 135_000)
    repo.registrar_pagamento(r2, 135_000, hoje - timedelta(days=20), "sinal", "pix")

    # Festa aguardando sinal
    repo.criar_reserva(bruno, hoje + timedelta(days=12), "09:00", "19:00", "Casamento",
                       200, 800_000, 240_000)

    # Festa já quitada (sinal + pagamento final)
    r3 = repo.criar_reserva(daniel, hoje + timedelta(days=8), "11:00", "17:00", "Chá de bebê",
                            40, 180_000, 54_000)
    repo.registrar_pagamento(r3, 54_000, hoje - timedelta(days=30), "sinal", "pix")
    repo.registrar_pagamento(r3, 126_000, hoje - timedelta(days=2), "quitacao", "pix")

    # Festa no mês seguinte
    repo.criar_reserva(ana, hoje + timedelta(days=35), "10:00", "17:00", "Confraternização",
                       50, 300_000, 90_000)

    print(f"Banco de demonstração criado em: {CAMINHO_DEMO}")


if __name__ == "__main__":
    main()
