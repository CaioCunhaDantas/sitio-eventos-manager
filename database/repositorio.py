"""Consultas e alterações no banco: clientes, reservas e pagamentos.

As telas nunca escrevem SQL: chamam estas funções. Assim todo o SQL
fica num lugar só e pode ser testado sem abrir a interface.

Valores em dinheiro entram e saem em CENTAVOS (int).
Datas entram como datetime.date e saem como texto 'AAAA-MM-DD'.
"""

import sqlite3
from contextlib import contextmanager
from datetime import date

from database.criar_banco import conectar


class DataOcupadaError(Exception):
    """Já existe uma festa (não cancelada) nessa data."""


@contextmanager
def _conexao():
    """Abre a conexão, faz commit se tudo der certo (ou rollback se der
    erro) e sempre fecha no final."""
    conexao = conectar()
    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def _lista(cursor) -> list[dict]:
    return [dict(linha) for linha in cursor.fetchall()]


def _um(cursor) -> dict | None:
    linha = cursor.fetchone()
    return dict(linha) if linha else None


def _vazio_para_none(texto: str | None) -> str | None:
    return texto.strip() if texto and texto.strip() else None


# ============================================================
# Clientes
# ============================================================

def listar_clientes(busca: str = "") -> list[dict]:
    termo = f"%{busca.strip()}%"
    with _conexao() as c:
        return _lista(c.execute(
            """
            SELECT * FROM cliente
            WHERE nome LIKE ? OR telefone LIKE ?
            ORDER BY nome COLLATE NOCASE
            """,
            (termo, termo),
        ))


def criar_cliente(nome: str, telefone: str, email: str | None = None,
                  observacoes: str | None = None) -> int:
    with _conexao() as c:
        cursor = c.execute(
            "INSERT INTO cliente (nome, telefone, email, observacoes) VALUES (?, ?, ?, ?)",
            (nome.strip(), telefone.strip(), _vazio_para_none(email),
             _vazio_para_none(observacoes)),
        )
        return cursor.lastrowid


def atualizar_cliente(id_cliente: int, nome: str, telefone: str,
                      email: str | None = None, observacoes: str | None = None) -> None:
    with _conexao() as c:
        c.execute(
            "UPDATE cliente SET nome = ?, telefone = ?, email = ?, observacoes = ? WHERE id = ?",
            (nome.strip(), telefone.strip(), _vazio_para_none(email),
             _vazio_para_none(observacoes), id_cliente),
        )


# ============================================================
# Reservas
# ============================================================

# Reserva + nome do cliente + situação financeira (da view de saldo)
_SELECT_RESERVA = """
    SELECT r.*, c.nome AS cliente, c.telefone,
           s.total_pago, s.saldo_devedor, s.sinal_pago
    FROM reserva r
    JOIN cliente c          ON c.id = r.id_cliente
    JOIN vw_saldo_reserva s ON s.id_reserva = r.id
"""


def _traduzir_conflito(erro: sqlite3.IntegrityError, data_festa: date) -> Exception:
    """Transforma o erro do índice único (uma festa por dia) num erro claro."""
    if "reserva.data_festa" in str(erro):
        return DataOcupadaError(data_festa)
    return erro


def criar_reserva(id_cliente: int, data_festa: date, hora_inicio: str, hora_fim: str,
                  tipo_festa: str, num_convidados: int, valor_total: int,
                  valor_sinal: int, observacoes: str | None = None) -> int:
    try:
        with _conexao() as c:
            cursor = c.execute(
                """
                INSERT INTO reserva (id_cliente, data_festa, hora_inicio, hora_fim,
                                     tipo_festa, num_convidados, valor_total,
                                     valor_sinal, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id_cliente, data_festa.isoformat(), hora_inicio, hora_fim,
                 tipo_festa.strip(), num_convidados, valor_total, valor_sinal,
                 _vazio_para_none(observacoes)),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as erro:
        raise _traduzir_conflito(erro, data_festa) from erro


def atualizar_reserva(id_reserva: int, data_festa: date, hora_inicio: str, hora_fim: str,
                      tipo_festa: str, num_convidados: int, valor_total: int,
                      valor_sinal: int, status: str, observacoes: str | None = None) -> None:
    try:
        with _conexao() as c:
            c.execute(
                """
                UPDATE reserva
                SET data_festa = ?, hora_inicio = ?, hora_fim = ?, tipo_festa = ?,
                    num_convidados = ?, valor_total = ?, valor_sinal = ?,
                    status = ?, observacoes = ?
                WHERE id = ?
                """,
                (data_festa.isoformat(), hora_inicio, hora_fim, tipo_festa.strip(),
                 num_convidados, valor_total, valor_sinal, status,
                 _vazio_para_none(observacoes), id_reserva),
            )
    except sqlite3.IntegrityError as erro:
        raise _traduzir_conflito(erro, data_festa) from erro


def cancelar_reserva(id_reserva: int) -> None:
    """Cancela (não apaga): o histórico fica guardado e a data é liberada."""
    with _conexao() as c:
        c.execute("UPDATE reserva SET status = 'cancelada' WHERE id = ?", (id_reserva,))


def reserva_na_data(data_festa: date) -> dict | None:
    """A festa (não cancelada) marcada nesse dia, ou None se o dia está livre."""
    with _conexao() as c:
        return _um(c.execute(
            _SELECT_RESERVA + " WHERE r.data_festa = ? AND r.status <> 'cancelada'",
            (data_festa.isoformat(),),
        ))


def reservas_do_periodo(inicio: date, fim: date) -> list[dict]:
    """Festas não canceladas entre inicio e fim (inclusive)."""
    with _conexao() as c:
        return _lista(c.execute(
            _SELECT_RESERVA + """
            WHERE r.data_festa BETWEEN ? AND ? AND r.status <> 'cancelada'
            ORDER BY r.data_festa
            """,
            (inicio.isoformat(), fim.isoformat()),
        ))


def reservas_ativas() -> list[dict]:
    """Todas as festas não canceladas, da mais próxima para a mais distante."""
    with _conexao() as c:
        return _lista(c.execute(
            _SELECT_RESERVA + " WHERE r.status <> 'cancelada' ORDER BY r.data_festa"
        ))


def reservas_do_cliente(id_cliente: int) -> list[dict]:
    with _conexao() as c:
        return _lista(c.execute(
            _SELECT_RESERVA + " WHERE r.id_cliente = ? ORDER BY r.data_festa DESC",
            (id_cliente,),
        ))


# ============================================================
# Pagamentos
# ============================================================

def registrar_pagamento(id_reserva: int, valor: int, data_pagamento: date, tipo: str,
                        forma_pagamento: str, observacao: str | None = None) -> int:
    """Registra o pagamento. Se for o sinal, a reserva passa a 'confirmada'.

    As duas alterações rodam na MESMA transação: ou as duas acontecem,
    ou nenhuma acontece.
    """
    with _conexao() as c:
        cursor = c.execute(
            """
            INSERT INTO pagamento (id_reserva, valor, data_pagamento, tipo,
                                   forma_pagamento, observacao)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id_reserva, valor, data_pagamento.isoformat(), tipo, forma_pagamento,
             _vazio_para_none(observacao)),
        )
        if tipo == "sinal":
            c.execute(
                "UPDATE reserva SET status = 'confirmada' WHERE id = ? AND status = 'pre_reserva'",
                (id_reserva,),
            )
        return cursor.lastrowid


def pagamentos_recentes(limite: int = 30) -> list[dict]:
    with _conexao() as c:
        return _lista(c.execute(
            """
            SELECT p.*, r.data_festa, c.nome AS cliente
            FROM pagamento p
            JOIN reserva r ON r.id = p.id_reserva
            JOIN cliente c ON c.id = r.id_cliente
            ORDER BY p.data_pagamento DESC, p.id DESC
            LIMIT ?
            """,
            (limite,),
        ))


def apagar_pagamento(id_pagamento: int) -> None:
    """Só para corrigir um pagamento lançado por engano."""
    with _conexao() as c:
        c.execute("DELETE FROM pagamento WHERE id = ?", (id_pagamento,))


def total_a_receber() -> int:
    """Soma do que falta receber de todas as festas não canceladas."""
    with _conexao() as c:
        linha = c.execute(
            """
            SELECT COALESCE(SUM(saldo_devedor), 0) AS total
            FROM vw_saldo_reserva
            WHERE status <> 'cancelada' AND saldo_devedor > 0
            """
        ).fetchone()
        return linha["total"]
