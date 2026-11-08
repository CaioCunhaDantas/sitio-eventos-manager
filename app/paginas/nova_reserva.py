from datetime import date

import streamlit as st

from app.componentes import erros_da_reserva, guardar_aviso, mostrar_aviso
from app.formatacao import FORMAS_TEXTO, HORARIOS, data_extenso, para_centavos
from database import repositorio as repo

st.title("Nova reserva")
mostrar_aviso()

# Depois de salvar, a "versão" muda e todos os campos voltam a ficar vazios
# (cada campo tem a versão no nome da sua chave).
versao = st.session_state.setdefault("nova_reserva_versao", 0)


def chave(nome: str) -> str:
    return f"nr_{nome}_{versao}"


# ---------- 1. Dia ----------
st.subheader("1. Qual o dia da festa?")
dia = st.date_input("Dia da festa", value=None, min_value=date.today(),
                    format="DD/MM/YYYY", key=chave("dia"))
ocupada = repo.reserva_na_data(dia) if dia else None
if dia and ocupada:
    st.error(f"{data_extenso(dia).capitalize()} já está ocupado: festa de "
             f"**{ocupada['cliente']}** ({ocupada['tipo_festa']}). Escolha outro dia.",
             icon=":material/event_busy:")
elif dia:
    st.success(f"{data_extenso(dia).capitalize()} está livre!", icon=":material/event_available:")

# ---------- 2. Cliente ----------
st.subheader("2. Quem vai alugar?")
clientes = repo.listar_clientes()
JA_VEIO, NOVO = "Já alugou antes", "Cliente novo"
modo = st.radio("Quem vai alugar?", [JA_VEIO, NOVO] if clientes else [NOVO],
                horizontal=True, label_visibility="collapsed", key=chave("modo"))

id_cliente = nome = telefone = email = None
if modo == JA_VEIO:
    nomes = {c["id"]: f"{c['nome']} — {c['telefone']}" for c in clientes}
    id_cliente = st.selectbox("Escolha o cliente", list(nomes), format_func=nomes.get,
                              index=None, placeholder="Clique aqui e digite o nome",
                              key=chave("cliente"))
else:
    nome = st.text_input("Nome", key=chave("nome"))
    telefone = st.text_input("Telefone / WhatsApp", key=chave("telefone"))
    email = st.text_input("E-mail (se tiver)", key=chave("email"))

# ---------- 3. Festa ----------
st.subheader("3. Como vai ser a festa?")
c1, c2 = st.columns(2)
hora_inicio = c1.selectbox("Começa às", HORARIOS, index=0, key=chave("inicio"))
hora_fim = c2.selectbox("Termina às", HORARIOS, index=len(HORARIOS) - 1, key=chave("fim"))
tipo = st.text_input("Tipo de festa", placeholder="Ex.: aniversário de 15 anos",
                     key=chave("tipo"))
convidados = st.number_input("Quantos convidados?", min_value=1, value=None, step=5,
                             key=chave("convidados"))

# ---------- 4. Valores ----------
st.subheader("4. Valores")
c3, c4 = st.columns(2)
valor_total = c3.number_input("Valor total da festa (R$)", min_value=0.0, value=None,
                              step=50.0, format="%.2f", key=chave("total"))
valor_sinal = c4.number_input("Valor do sinal (R$)", min_value=0.0, value=None,
                              step=50.0, format="%.2f", key=chave("sinal"))
sinal_pago = st.checkbox("O sinal já foi pago", key=chave("sinal_pago"))
forma = None
if sinal_pago:
    forma = st.radio("Como o sinal foi pago?", list(FORMAS_TEXTO), format_func=FORMAS_TEXTO.get,
                     horizontal=True, key=chave("forma"))
obs = st.text_area("Observações (se precisar)", key=chave("obs"))

# ---------- Salvar ----------
if st.button("Salvar reserva", type="primary", width="stretch", disabled=bool(ocupada),
             icon=":material/check:"):
    erros = []
    if not dia:
        erros.append("Escolha o dia da festa.")
    if modo == JA_VEIO and not id_cliente:
        erros.append("Escolha quem vai alugar.")
    if modo == NOVO and not (nome and nome.strip()):
        erros.append("Escreva o nome de quem vai alugar.")
    if modo == NOVO and not (telefone and telefone.strip()):
        erros.append("Escreva o telefone de quem vai alugar.")
    erros += erros_da_reserva(hora_inicio, hora_fim, tipo, convidados, valor_total, valor_sinal)
    if sinal_pago and not valor_sinal:
        erros.append("Marcou que o sinal foi pago: informe o valor do sinal.")

    for erro in erros:
        st.error(erro)

    if not erros:
        try:
            if modo == NOVO:
                id_cliente = repo.criar_cliente(nome, telefone, email)
            id_reserva = repo.criar_reserva(
                id_cliente, dia, hora_inicio, hora_fim, tipo, convidados,
                para_centavos(valor_total), para_centavos(valor_sinal or 0), obs,
            )
            if sinal_pago:
                repo.registrar_pagamento(id_reserva, para_centavos(valor_sinal), date.today(),
                                         "sinal", forma)
        except repo.DataOcupadaError:
            st.error("Esse dia acabou de ser ocupado por outra festa. Escolha outro dia.",
                     icon=":material/event_busy:")
        else:
            nome_cliente = nome if modo == NOVO else nomes[id_cliente].split(" — ")[0]
            st.session_state["nova_reserva_versao"] += 1
            guardar_aviso(f"Festa de {nome_cliente} marcada para {data_extenso(dia)}.")
            st.rerun()
