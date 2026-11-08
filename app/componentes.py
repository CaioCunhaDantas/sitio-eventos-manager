"""Peças de interface reaproveitadas em várias telas."""

import streamlit as st

from database import cpf as cpf_util


def botao_com_confirmacao(chave: str, rotulo: str, pergunta: str, rotulo_sim: str,
                          icone: str | None = None) -> bool:
    """Botão que pede "Tem certeza?" antes de agir.

    1º clique: mostra a pergunta com "Sim" e "Não, voltar".
    Devolve True apenas quando a pessoa clica em "Sim".
    """
    marcador = f"confirmar_{chave}"
    if not st.session_state.get(marcador):
        if st.button(rotulo, key=f"pedir_{chave}", icon=icone):
            st.session_state[marcador] = True
            st.rerun()
        return False

    st.warning(pergunta, icon=":material/help:")
    col_sim, col_nao = st.columns(2)
    if col_sim.button(rotulo_sim, key=f"sim_{chave}", type="primary", width="stretch"):
        st.session_state[marcador] = False
        return True
    if col_nao.button("Não, voltar", key=f"nao_{chave}", width="stretch"):
        st.session_state[marcador] = False
        st.rerun()
    return False


def erros_da_reserva(hora_inicio: str, hora_fim: str, tipo_festa: str | None,
                     num_convidados: int | None, valor_total: float | None,
                     valor_sinal: float | None, completa: bool = True) -> list[str]:
    """Confere os dados antes de salvar e devolve as mensagens de erro (em português claro).

    completa=False (pré-reserva): tipo, convidados e valor podem ficar em branco.
    """
    erros = []
    if hora_inicio >= hora_fim:
        erros.append("O horário de fim precisa ser depois do horário de início.")
    if completa:
        if not tipo_festa or not tipo_festa.strip():
            erros.append("Escreva o tipo de festa (ex.: aniversário).")
        if not num_convidados:
            erros.append("Informe quantos convidados.")
        if not valor_total:
            erros.append("Informe o valor total da festa.")
    if valor_total and valor_sinal and valor_sinal > valor_total:
        erros.append("O sinal não pode ser maior que o valor total.")
    return erros


def campos_cadastro(chave: str, cliente: dict | None = None) -> tuple[str, str, str, str]:
    """CPF + endereço (rua e número / bairro / cidade), já preenchidos se houver.

    Devolve (cpf, endereco, bairro, cidade).
    """
    cliente = cliente or {}
    cpf = st.text_input("CPF", value=cpf_util.formatar(cliente.get("cpf")) if cliente.get("cpf")
                        else "", placeholder="000.000.000-00", key=f"{chave}_cpf")
    endereco = st.text_input("Endereço (rua e número)", value=cliente.get("endereco") or "",
                             key=f"{chave}_endereco")
    c1, c2 = st.columns(2)
    bairro = c1.text_input("Bairro", value=cliente.get("bairro") or "", key=f"{chave}_bairro")
    cidade = c2.text_input("Cidade", value=cliente.get("cidade") or "", key=f"{chave}_cidade")
    return cpf, endereco, bairro, cidade


def erros_do_cadastro(cpf: str | None, endereco: str | None, bairro: str | None,
                      cidade: str | None, obrigatorio: bool) -> list[str]:
    """CPF (se preenchido) precisa ser válido; na reserva completa, tudo é obrigatório."""
    erros = []
    if cpf and cpf.strip() and not cpf_util.valido(cpf):
        erros.append("CPF inválido. Confira os números (os dois últimos não batem).")
    if obrigatorio:
        if not (cpf and cpf.strip()):
            erros.append("Informe o CPF.")
        if not all(x and x.strip() for x in (endereco, bairro, cidade)):
            erros.append("Preencha o endereço completo: rua e número, bairro e cidade.")
    return erros


def guardar_aviso(texto: str) -> None:
    """Guarda uma mensagem de sucesso para mostrar depois do recarregamento da tela."""
    st.session_state["aviso"] = texto


def mostrar_aviso() -> None:
    texto = st.session_state.pop("aviso", None)
    if texto:
        st.success(texto, icon=":material/check_circle:")
