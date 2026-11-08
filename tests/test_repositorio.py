"""Testes da camada de banco.

Rodar (na raiz do projeto):
    py -m unittest -v

Cada teste usa um banco novo numa pasta temporária: o sitio.db real
nunca é tocado.
"""

import os
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

# Precisa vir ANTES de importar o pacote database, porque o caminho do
# banco é lido na importação.
_PASTA = tempfile.mkdtemp()
os.environ["SITIO_DB"] = str(Path(_PASTA) / "teste.db")

from database import repositorio as repo  # noqa: E402
from database.criar_banco import CAMINHO_BANCO, criar_banco  # noqa: E402

DIA = date(2030, 5, 18)


class TestRepositorio(unittest.TestCase):
    def setUp(self):
        CAMINHO_BANCO.unlink(missing_ok=True)
        criar_banco()
        self.cliente = repo.criar_cliente("Ana", "21999990000")

    def nova_reserva(self, dia=DIA, **extra):
        dados = dict(id_cliente=self.cliente, data_festa=dia, hora_inicio="10:00",
                     hora_fim="18:00", tipo_festa="Aniversário", num_convidados=80,
                     valor_total=300_000, valor_sinal=90_000)
        dados.update(extra)
        return repo.criar_reserva(**dados)

    # --- uma festa por dia ---
    def test_nao_permite_duas_festas_no_mesmo_dia(self):
        self.nova_reserva()
        with self.assertRaises(repo.DataOcupadaError):
            self.nova_reserva()

    def test_cancelar_libera_a_data(self):
        id_reserva = self.nova_reserva()
        repo.cancelar_reserva(id_reserva)
        self.assertIsNone(repo.reserva_na_data(DIA))
        self.nova_reserva()  # não pode dar erro

    def test_mudar_data_para_dia_ocupado_da_erro(self):
        self.nova_reserva()
        outra = self.nova_reserva(dia=date(2030, 5, 25))
        with self.assertRaises(repo.DataOcupadaError):
            repo.atualizar_reserva(outra, DIA, "10:00", "18:00", "X", 10,
                                   1000, 0, "pre_reserva")

    def test_horario_fora_do_funcionamento_da_erro(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.nova_reserva(hora_fim="20:00")

    # --- pagamentos e saldo ---
    def test_saldo_e_confirmacao_pelo_sinal(self):
        id_reserva = self.nova_reserva()
        self.assertEqual(repo.reserva_na_data(DIA)["status"], "pre_reserva")

        repo.registrar_pagamento(id_reserva, 90_000, DIA, "sinal", "pix")
        reserva = repo.reserva_na_data(DIA)
        self.assertEqual(reserva["status"], "confirmada")
        self.assertEqual(reserva["saldo_devedor"], 210_000)
        self.assertEqual(repo.total_a_receber(), 210_000)

    def test_apagar_pagamento_volta_o_saldo(self):
        id_reserva = self.nova_reserva()
        id_pag = repo.registrar_pagamento(id_reserva, 50_000, DIA, "parcela", "dinheiro")
        repo.apagar_pagamento(id_pag)
        self.assertEqual(repo.reserva_na_data(DIA)["saldo_devedor"], 300_000)

    def test_cancelada_nao_entra_no_a_receber(self):
        id_reserva = self.nova_reserva()
        repo.cancelar_reserva(id_reserva)
        self.assertEqual(repo.total_a_receber(), 0)

    # --- clientes ---
    def test_busca_de_cliente_por_nome_e_telefone(self):
        repo.criar_cliente("Bruno", "21888880000")
        self.assertEqual([c["nome"] for c in repo.listar_clientes("bru")], ["Bruno"])
        self.assertEqual([c["nome"] for c in repo.listar_clientes("9999")], ["Ana"])

    def test_atualizar_cliente(self):
        repo.atualizar_cliente(self.cliente, "Ana Maria", "21999990000", "ana@x.com")
        cliente = repo.listar_clientes("Ana")[0]
        self.assertEqual((cliente["nome"], cliente["email"]), ("Ana Maria", "ana@x.com"))


if __name__ == "__main__":
    unittest.main()
