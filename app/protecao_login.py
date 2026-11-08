"""Proteção contra "chute" de senha, separada por IP.

Depois de `max_tentativas` senhas erradas seguidas vindas do MESMO IP,
esse IP fica bloqueado por `tempo_bloqueio`. Outros IPs não são afetados:
na internet aberta, um estranho errando a senha bloqueia só a si mesmo,
nunca a dona do sistema.

Não depende do Streamlit, então pode ser testado com unittest.
"""

import threading
from datetime import datetime, timedelta


class ControleDeTentativas:
    def __init__(self, max_tentativas: int = 5,
                 tempo_bloqueio: timedelta = timedelta(minutes=5)):
        self.max_tentativas = max_tentativas
        self.tempo_bloqueio = tempo_bloqueio
        self._por_ip: dict[str, dict] = {}
        # O Streamlit atende cada visitante numa thread; o Lock evita que duas
        # mexam no dicionário ao mesmo tempo.
        self._trava = threading.Lock()

    def bloqueado_ate(self, ip: str, agora: datetime | None = None) -> datetime | None:
        """Até quando esse IP está bloqueado (None = pode tentar)."""
        agora = agora or datetime.now()
        with self._trava:
            self._limpar(agora)
            dados = self._por_ip.get(ip)
            if dados and dados["bloqueado_ate"] and dados["bloqueado_ate"] > agora:
                return dados["bloqueado_ate"]
            return None

    def registrar_erro(self, ip: str, agora: datetime | None = None) -> bool:
        """Conta uma senha errada. Devolve True se este erro causou o bloqueio."""
        agora = agora or datetime.now()
        with self._trava:
            dados = self._por_ip.setdefault(ip, {"erros": 0, "bloqueado_ate": None})
            dados["erros"] += 1
            if dados["erros"] >= self.max_tentativas:
                dados["erros"] = 0
                dados["bloqueado_ate"] = agora + self.tempo_bloqueio
                return True
            return False

    def registrar_acerto(self, ip: str) -> None:
        with self._trava:
            self._por_ip.pop(ip, None)

    def _limpar(self, agora: datetime) -> None:
        """Esquece IPs cujo bloqueio já acabou (a lista não cresce para sempre)."""
        vencidos = [ip for ip, d in self._por_ip.items()
                    if d["bloqueado_ate"] and d["bloqueado_ate"] <= agora]
        for ip in vencidos:
            del self._por_ip[ip]
