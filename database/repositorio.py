"""Consultas e alterações no banco: clientes, reservas e pagamentos.

As telas nunca escrevem SQL: chamam estas funções. Assim todo o SQL
fica num lugar só e pode ser testado sem abrir a interface.

Valores em dinheiro entram e saem em CENTAVOS (int).
Datas entram como datetime.date e saem como texto 'AAAA-MM-DD'.
"""

import sqlite3
from contextlib import contextmanager
from datetime import date

from database import cpf as cpf_util
from database.criar_banco import conectar


class DataOcupadaError(Exception):
    """Já existe uma festa (não cancelada) nessa data."""


class DadosIncompletosError(Exception):
    """Pré-reserva sem tipo/convidados/valor: não pode receber pagamento nem ser confirmada."""


class CpfInvalidoError(Exception):
    """CPF com dígitos verificadores errados (provável erro de digitação)."""


class CpfDuplicadoError(Exception):
    """Já existe um cliente com esse CPF. args[0] = nome dele."""


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

def _preparar_cpf(cpf: str | None) -> str | None:
    """Vazio -> None; senão confere os dígitos e devolve só os 11 números."""
    if not cpf or not cpf.strip():
        return None
    if not cpf_util.valido(cpf):
        raise CpfInvalidoError(cpf)
    return cpf_util.limpar(cpf)


def _erro_cpf_duplicado(c: sqlite3.Connection, cpf: str) -> CpfDuplicadoError:
    dono = c.execute("SELECT nome FROM cliente WHERE cpf = ?", (cpf,)).fetchone()
    return CpfDuplicadoError(dono["nome"] if dono else "outro cliente")


def listar_clientes(busca: str = "") -> list[dict]:
    termo = f"%{busca.strip()}%"
    # Busca por CPF funciona com ou sem pontuação ("123.456" ou "123456")
    termo_cpf = f"%{cpf_util.limpar(busca)}%" if cpf_util.limpar(busca) else termo
    with _conexao() as c:
        return _lista(c.execute(
            """
            SELECT * FROM cliente
            WHERE nome LIKE ? OR telefone LIKE ? OR bairro LIKE ? OR cidade LIKE ?
                  OR cpf LIKE ?
            ORDER BY nome COLLATE NOCASE
            """,
            (termo, termo, termo, termo, termo_cpf),
        ))


def criar_cliente(nome: str, telefone: str, email: str | None = None,
                  observacoes: str | None = None, endereco: str | None = None,
                  bairro: str | None = None, cidade: str | None = None,
                  cpf: str | None = None) -> int:
    cpf_limpo = _preparar_cpf(cpf)
    with _conexao() as c:
        try:
            cursor = c.execute(
                """
                INSERT INTO cliente (nome, telefone, email, observacoes, endereco,
                                     bairro, cidade, cpf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nome.strip(), telefone.strip(), _vazio_para_none(email),
                 _vazio_para_none(observacoes), _vazio_para_none(endereco),
                 _vazio_para_none(bairro), _vazio_para_none(cidade), cpf_limpo),
            )
        except sqlite3.IntegrityError as erro:
            if "cliente.cpf" in str(erro):
                raise _erro_cpf_duplicado(c, cpf_limpo) from erro
            raise
        return cursor.lastrowid


def atualizar_cliente(id_cliente: int, nome: str, telefone: str,
                      email: str | None = None, observacoes: str | None = None,
                      endereco: str | None = None, bairro: str | None = None,
                      cidade: str | None = None, cpf: str | None = None) -> None:
    cpf_limpo = _preparar_cpf(cpf)
    with _conexao() as c:
        try:
            c.execute(
                """
                UPDATE cliente
                SET nome = ?, telefone = ?, email = ?, observacoes = ?,
                    endereco = ?, bairro = ?, cidade = ?, cpf = ?
                WHERE id = ?
                """,
                (nome.strip(), telefone.strip(), _vazio_para_none(email),
                 _vazio_para_none(observacoes), _vazio_para_none(endereco),
                 _vazio_para_none(bairro), _vazio_para_none(cidade), cpf_limpo, id_cliente),
            )
        except sqlite3.IntegrityError as erro:
            if "cliente.cpf" in str(erro):
                raise _erro_cpf_duplicado(c, cpf_limpo) from erro
            raise


def completar_cadastro(id_cliente: int, endereco: str, bairro: str, cidade: str,
                       cpf: str) -> None:
    """Preenche só endereço e CPF (usado na Nova reserva), sem tocar nos outros campos."""
    cpf_limpo = _preparar_cpf(cpf)
    with _conexao() as c:
        try:
            c.execute(
                "UPDATE cliente SET endereco = ?, bairro = ?, cidade = ?, cpf = ? WHERE id = ?",
                (_vazio_para_none(endereco), _vazio_para_none(bairro),
                 _vazio_para_none(cidade), cpf_limpo, id_cliente),
            )
        except sqlite3.IntegrityError as erro:
            if "cliente.cpf" in str(erro):
                raise _erro_cpf_duplicado(c, cpf_limpo) from erro
            raise


def endereco_completo(cliente: dict) -> bool:
    return all(cliente.get(campo) for campo in ("endereco", "bairro", "cidade"))


def cadastro_completo(cliente: dict) -> bool:
    """Tem tudo o que a reserva completa exige: endereço e CPF."""
    return endereco_completo(cliente) and bool(cliente.get("cpf"))


# ============================================================
# Reservas
# ============================================================

# Reserva + nome do cliente + situação financeira (da view de saldo)
_SELECT_RESERVA = """
    SELECT r.*, c.nome AS cliente, c.telefone, c.endereco, c.bairro, c.cidade,
           s.total_pago, s.saldo_devedor, s.sinal_pago
    FROM reserva r
    JOIN cliente c          ON c.id = r.id_cliente
    JOIN vw_saldo_reserva s ON s.id_reserva = r.id
"""


def _traduzir_erro(erro: sqlite3.IntegrityError, data_festa: date | None = None) -> Exception:
    """Transforma erros do banco em erros claros para a tela."""
    mensagem = str(erro)
    if "reserva.data_festa" in mensagem:           # índice único: uma festa por dia
        return DataOcupadaError(data_festa)
    if "reserva_sem_dados_completos" in mensagem:  # trigger do pagamento
        return DadosIncompletosError()
    if "status = 'pre_reserva'" in mensagem:       # CHECK de dados obrigatórios
        return DadosIncompletosError()
    return erro


def criar_reserva(id_cliente: int, data_festa: date, hora_inicio: str = "09:00",
                  hora_fim: str = "19:00", tipo_festa: str | None = None,
                  num_convidados: int | None = None, valor_total: int | None = None,
                  valor_sinal: int = 0, observacoes: str | None = None) -> int:
    """Cria a reserva como 'pre_reserva' (sem sinal pago).

    Pré-reserva só com o dia: deixe tipo_festa, num_convidados e
    valor_total como None; eles podem ser completados depois.
    """
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
                 _vazio_para_none(tipo_festa), num_convidados, valor_total, valor_sinal,
                 _vazio_para_none(observacoes)),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as erro:
        raise _traduzir_erro(erro, data_festa) from erro


def atualizar_reserva(id_reserva: int, data_festa: date, hora_inicio: str, hora_fim: str,
                      tipo_festa: str | None, num_convidados: int | None,
                      valor_total: int | None, valor_sinal: int, status: str,
                      observacoes: str | None = None) -> None:
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
                (data_festa.isoformat(), hora_inicio, hora_fim, _vazio_para_none(tipo_festa),
                 num_convidados, valor_total, valor_sinal, status,
                 _vazio_para_none(observacoes), id_reserva),
            )
    except sqlite3.IntegrityError as erro:
        raise _traduzir_erro(erro, data_festa) from erro


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
    try:
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
                    "UPDATE reserva SET status = 'confirmada' "
                    "WHERE id = ? AND status = 'pre_reserva'",
                    (id_reserva,),
                )
            return cursor.lastrowid
    except sqlite3.IntegrityError as erro:
        raise _traduzir_erro(erro) from erro


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
