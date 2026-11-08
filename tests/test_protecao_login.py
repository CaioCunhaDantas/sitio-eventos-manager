"""Testes do bloqueio de login por IP.

Rodar (na raiz do projeto):  py -m unittest -v
"""

import unittest
from datetime import datetime, timedelta

from app.protecao_login import ControleDeTentativas

AGORA = datetime(2030, 1, 1, 12, 0)


class TestProtecaoLogin(unittest.TestCase):
    def setUp(self):
        self.controle = ControleDeTentativas(max_tentativas=3,
                                             tempo_bloqueio=timedelta(minutes=5))

    def errar(self, ip, vezes):
        for _ in range(vezes):
            self.controle.registrar_erro(ip, AGORA)

    def test_bloqueia_depois_do_limite(self):
        self.errar("1.1.1.1", 2)
        self.assertIsNone(self.controle.bloqueado_ate("1.1.1.1", AGORA))
        self.assertTrue(self.controle.registrar_erro("1.1.1.1", AGORA))  # 3º erro
        self.assertEqual(self.controle.bloqueado_ate("1.1.1.1", AGORA),
                         AGORA + timedelta(minutes=5))

    def test_bloqueio_de_um_ip_nao_atinge_outro(self):
        self.errar("6.6.6.6", 3)  # estranho
        self.assertIsNotNone(self.controle.bloqueado_ate("6.6.6.6", AGORA))
        self.assertIsNone(self.controle.bloqueado_ate("2.2.2.2", AGORA))  # a dona entra

    def test_bloqueio_acaba_depois_do_tempo(self):
        self.errar("1.1.1.1", 3)
        depois = AGORA + timedelta(minutes=6)
        self.assertIsNone(self.controle.bloqueado_ate("1.1.1.1", depois))

    def test_acerto_zera_os_erros(self):
        self.errar("1.1.1.1", 2)
        self.controle.registrar_acerto("1.1.1.1")
        self.errar("1.1.1.1", 2)  # recomeçou a contagem: 2 < 3
        self.assertIsNone(self.controle.bloqueado_ate("1.1.1.1", AGORA))


if __name__ == "__main__":
    unittest.main()
