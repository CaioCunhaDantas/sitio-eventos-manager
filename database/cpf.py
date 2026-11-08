"""CPF: limpeza, validação e formatação.

No banco o CPF fica só com os 11 números ('12345678909'); na tela,
formatado ('123.456.789-09').

Validação pelos dígitos verificadores (os 2 últimos números): são
calculados a partir dos 9 primeiros. Isso pega a maioria dos erros de
digitação (número trocado, faltando etc.).
"""


def limpar(texto: str | None) -> str:
    """'123.456.789-09' -> '12345678909' (tira pontos, traço e espaços)."""
    return "".join(c for c in (texto or "") if c.isdigit())


def _digito(numeros: str) -> int:
    # Multiplica cada número por um peso decrescente (10, 9, 8... ou 11, 10, 9...)
    peso_inicial = len(numeros) + 1
    soma = sum(int(n) * (peso_inicial - i) for i, n in enumerate(numeros))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def calcular_digitos(nove_primeiros: str) -> str:
    """'123456789' -> '09' (os dois dígitos verificadores)."""
    primeiro = _digito(nove_primeiros)
    segundo = _digito(nove_primeiros + str(primeiro))
    return f"{primeiro}{segundo}"


def valido(texto: str | None) -> bool:
    cpf = limpar(texto)
    if len(cpf) != 11 or cpf == cpf[0] * 11:  # 111.111.111-11 passa na conta, mas não existe
        return False
    return cpf[9:] == calcular_digitos(cpf[:9])


def formatar(cpf: str | None) -> str:
    """'12345678909' -> '123.456.789-09'"""
    cpf = limpar(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
