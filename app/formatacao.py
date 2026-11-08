"""Conversões para mostrar dados do jeito brasileiro (R$, datas, textos)."""

from datetime import date

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
# date.weekday(): 0 = segunda ... 6 = domingo
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

STATUS_TEXTO = {
    "pre_reserva": "Pré-reserva (sem sinal)",
    "confirmada": "Confirmada",
    "realizada": "Já aconteceu",
    "cancelada": "Cancelada",
}
TIPOS_TEXTO = {"sinal": "Sinal", "parcela": "Parcela", "quitacao": "Pagamento final"}
FORMAS_TEXTO = {
    "pix": "Pix",
    "dinheiro": "Dinheiro",
    "cartao_credito": "Cartão de crédito",
    "cartao_debito": "Cartão de débito",
    "transferencia": "Transferência",
}

# Horários permitidos (o sítio funciona das 09:00 às 19:00), de meia em meia hora
HORARIOS = [f"{h:02d}:{m:02d}" for h in range(9, 20) for m in (0, 30)
            if not (h == 19 and m == 30)]


def dados_completos(reserva: dict) -> bool:
    """Pré-reserva incompleta = ainda sem tipo de festa, convidados ou valor."""
    return all(reserva.get(campo) is not None
               for campo in ("tipo_festa", "num_convidados", "valor_total"))


def situacao_pagamento(reserva: dict) -> str:
    """'pre_reserva' (faltam dados), 'quitada' (nada falta),
    'sem_sinal' (nada pago) ou 'falta' (pagou parte)."""
    if not dados_completos(reserva):
        return "pre_reserva"
    if reserva["saldo_devedor"] <= 0:
        return "quitada"
    if reserva["total_pago"] == 0:
        return "sem_sinal"
    return "falta"


def texto_situacao(reserva: dict) -> str:
    """Texto curto para o calendário e listas: 'Quitada', 'Falta R$ ...' ou 'Pré-reserva'."""
    situacao = situacao_pagamento(reserva)
    if situacao == "pre_reserva":
        return "Pré-reserva"
    if situacao == "quitada":
        return "Quitada"
    return f"Falta {reais(reserva['saldo_devedor'])}"


def reais(centavos: int | None) -> str:
    """150050 -> 'R$ 1.500,50'   (None -> '—', valor ainda não combinado)"""
    if centavos is None:
        return "—"
    texto = f"{centavos / 100:,.2f}"                       # '1,500.50'
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def para_centavos(valor_em_reais: float | None) -> int | None:
    """1500.5 -> 150050 (round evita 1500.5*100 = 150049.99999). Vazio -> None."""
    if valor_em_reais is None:
        return None
    return round(valor_em_reais * 100)


def endereco_texto(cliente: dict) -> str | None:
    """'Rua A, 10 — Tijuca, Rio de Janeiro' (ou None se não tiver nada)."""
    partes = [cliente.get("endereco"),
              ", ".join(p for p in (cliente.get("bairro"), cliente.get("cidade")) if p)]
    texto = " — ".join(p for p in partes if p)
    return texto or None


def para_data(valor: str | date) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(valor)


def data_curta(valor: str | date) -> str:
    """'2026-12-20' -> '20/12/2026'"""
    return para_data(valor).strftime("%d/%m/%Y")


def data_com_dia_semana(valor: str | date) -> str:
    """'2026-12-20' -> '20/12 (domingo)'"""
    d = para_data(valor)
    return f"{d:%d/%m} ({DIAS_SEMANA[d.weekday()]})"


def data_extenso(valor: str | date) -> str:
    """'2026-12-20' -> 'domingo, 20 de dezembro de 2026'"""
    d = para_data(valor)
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"
