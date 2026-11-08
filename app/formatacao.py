"""Conversões para mostrar dados do jeito brasileiro (R$, datas, textos)."""

from datetime import date

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
# date.weekday(): 0 = segunda ... 6 = domingo
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

STATUS_TEXTO = {
    "pre_reserva": "Aguardando sinal",
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


def reais(centavos: int) -> str:
    """150050 -> 'R$ 1.500,50'"""
    texto = f"{centavos / 100:,.2f}"                       # '1,500.50'
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def para_centavos(valor_em_reais: float) -> int:
    """1500.5 -> 150050 (round evita 1500.5*100 = 150049.99999)"""
    return round(valor_em_reais * 100)


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
