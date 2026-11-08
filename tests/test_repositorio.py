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

    def test_endereco_do_cliente_e_busca_por_bairro(self):
        repo.criar_cliente("Bruno", "2188", endereco="Rua A, 10", bairro="Tijuca",
                           cidade="Rio de Janeiro")
        bruno = repo.listar_clientes("tijuca")[0]
        self.assertEqual(bruno["nome"], "Bruno")
        self.assertTrue(repo.endereco_completo(bruno))
        self.assertFalse(repo.endereco_completo(repo.listar_clientes("Ana")[0]))

    # --- CPF ---
    def test_cpf_valido_e_guardado_so_com_numeros(self):
        id_bruno = repo.criar_cliente("Bruno", "2188", cpf="529.982.247-25")
        bruno = repo.listar_clientes("529.982")[0]  # busca com pontuação
        self.assertEqual((bruno["id"], bruno["cpf"]), (id_bruno, "52998224725"))

    def test_cpf_com_digito_errado_e_recusado(self):
        with self.assertRaises(repo.CpfInvalidoError):
            repo.criar_cliente("Bruno", "2188", cpf="529.982.247-26")
        with self.assertRaises(repo.CpfInvalidoError):
            repo.criar_cliente("Bruno", "2188", cpf="111.111.111-11")

    def test_cpf_repetido_diz_quem_ja_tem(self):
        repo.criar_cliente("Bruno", "2188", cpf="52998224725")
        with self.assertRaises(repo.CpfDuplicadoError) as erro:
            repo.criar_cliente("Carlos", "2177", cpf="529.982.247-25")
        self.assertEqual(erro.exception.args[0], "Bruno")

    def test_completar_cadastro_nao_apaga_outros_dados(self):
        repo.atualizar_cliente(self.cliente, "Ana", "21999990000", "ana@x.com", "VIP")
        repo.completar_cadastro(self.cliente, "Rua A, 1", "Centro", "Rio", "52998224725")
        ana = repo.listar_clientes("Ana")[0]
        self.assertEqual((ana["email"], ana["observacoes"]), ("ana@x.com", "VIP"))
        self.assertTrue(repo.cadastro_completo(ana))

    # --- pré-reserva ---
    def test_pre_reserva_so_com_o_dia_segura_a_data(self):
        repo.criar_reserva(self.cliente, DIA)  # sem tipo, convidados nem valor
        pre = repo.reserva_na_data(DIA)
        self.assertEqual(pre["status"], "pre_reserva")
        self.assertIsNone(pre["valor_total"])
        with self.assertRaises(repo.DataOcupadaError):
            self.nova_reserva()

    def test_pre_reserva_incompleta_nao_recebe_pagamento(self):
        id_pre = repo.criar_reserva(self.cliente, DIA)
        with self.assertRaises(repo.DadosIncompletosError):
            repo.registrar_pagamento(id_pre, 10_000, DIA, "sinal", "pix")

    def test_pre_reserva_incompleta_nao_pode_ser_confirmada(self):
        id_pre = repo.criar_reserva(self.cliente, DIA)
        with self.assertRaises(repo.DadosIncompletosError):
            repo.atualizar_reserva(id_pre, DIA, "09:00", "19:00", None, None, None, 0,
                                   "confirmada")

    def test_completar_pre_reserva_e_pagar_sinal(self):
        id_pre = repo.criar_reserva(self.cliente, DIA)
        repo.atualizar_reserva(id_pre, DIA, "10:00", "18:00", "Casamento", 100,
                               500_000, 150_000, "pre_reserva")
        repo.registrar_pagamento(id_pre, 150_000, DIA, "sinal", "pix")
        self.assertEqual(repo.reserva_na_data(DIA)["status"], "confirmada")
        self.assertEqual(repo.total_a_receber(), 350_000)


class TestBackup(unittest.TestCase):
    def test_backup_copia_os_dados_e_mantem_so_os_mais_recentes(self):
        from database.backup import fazer_backup

        CAMINHO_BANCO.unlink(missing_ok=True)
        criar_banco()
        repo.criar_cliente("Ana", "2199")
        pasta = Path(tempfile.mkdtemp())
        for i in range(3):  # simula backups antigos
            (pasta / f"sitio_2000-01-0{i + 1}_000000.db").write_bytes(b"")

        criado = fazer_backup(pasta, manter=2)

        copia = sqlite3.connect(criado)
        self.assertEqual(copia.execute("SELECT nome FROM cliente").fetchone()[0], "Ana")
        copia.close()
        restantes = sorted(p.name for p in pasta.glob("sitio_*.db"))
        self.assertEqual(len(restantes), 2)
        self.assertIn(criado.name, restantes)  # o novo nunca é apagado


class TestMigracao(unittest.TestCase):
    """Um banco criado na versão 1 precisa ser atualizado sem perder dados."""

    def test_banco_v1_e_migrado_para_versao_atual(self):
        from database.migracoes import VERSAO_ATUAL

        CAMINHO_BANCO.unlink(missing_ok=True)
        schema_v1 = (Path(__file__).parent / "schema_v1.sql").read_text(encoding="utf-8")
        antigo = sqlite3.connect(CAMINHO_BANCO)
        antigo.executescript(schema_v1)
        antigo.execute("INSERT INTO cliente (nome, telefone) VALUES ('Ana', '2199')")
        antigo.execute(
            "INSERT INTO reserva (id_cliente, data_festa, hora_inicio, hora_fim, tipo_festa,"
            " num_convidados, valor_total, valor_sinal, status)"
            " VALUES (1, '2030-05-18', '10:00', '18:00', 'X', 10, 1000, 0, 'confirmada')"
        )
        antigo.execute("INSERT INTO pagamento (id_reserva, valor, data_pagamento, tipo,"
                       " forma_pagamento) VALUES (1, 500, '2030-01-01', 'sinal', 'pix')")
        antigo.commit()
        antigo.close()

        criar_banco()  # deve aplicar a migração

        conexao = sqlite3.connect(CAMINHO_BANCO)
        self.assertEqual(conexao.execute("PRAGMA user_version").fetchone()[0], VERSAO_ATUAL)
        self.assertEqual(conexao.execute("PRAGMA foreign_key_check").fetchall(), [])
        conexao.close()

        reserva = repo.reserva_na_data(DIA)
        self.assertEqual((reserva["cliente"], reserva["total_pago"]), ("Ana", 500))
        # Colunas novas existem e a pré-reserva incompleta passou a ser aceita
        repo.criar_cliente("Bruno", "2188", bairro="Centro", cpf="52998224725")
        repo.criar_reserva(1, date(2030, 6, 1))
        # A regra de uma festa por dia continua valendo depois da migração
        with self.assertRaises(repo.DataOcupadaError):
            repo.criar_reserva(1, DIA)


if __name__ == "__main__":
    unittest.main()
