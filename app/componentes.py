"""Peças de interface reaproveitadas em várias telas."""

import streamlit as st


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


def campos_endereco(chave: str, cliente: dict | None = None) -> tuple[str, str, str]:
    """Os 3 campos de endereço (rua e número / bairro / cidade), já preenchidos se houver."""
    cliente = cliente or {}
    endereco = st.text_input("Endereço (rua e número)", value=cliente.get("endereco") or "",
                             key=f"{chave}_endereco")
    c1, c2 = st.columns(2)
    bairro = c1.text_input("Bairro", value=cliente.get("bairro") or "", key=f"{chave}_bairro")
    cidade = c2.text_input("Cidade", value=cliente.get("cidade") or "", key=f"{chave}_cidade")
    return endereco, bairro, cidade


def guardar_aviso(texto: str) -> None:
    """Guarda uma mensagem de sucesso para mostrar depois do recarregamento da tela."""
    st.session_state["aviso"] = texto


def mostrar_aviso() -> None:
    texto = st.session_state.pop("aviso", None)
    if texto:
        st.success(texto, icon=":material/check_circle:")
