from datetime import date

import streamlit as st

from app.componentes import (campos_cadastro, erros_da_reserva, erros_do_cadastro,
                             guardar_aviso, mostrar_aviso)
from app.formatacao import FORMAS_TEXTO, HORARIOS, data_extenso, para_centavos
from database import repositorio as repo

st.title("Nova reserva")
mostrar_aviso()

# Depois de salvar, a "versão" muda e todos os campos voltam a ficar vazios
# (cada campo tem a versão no nome da sua chave).
versao = st.session_state.setdefault("nova_reserva_versao", 0)


def chave(nome: str) -> str:
    return f"nr_{nome}_{versao}"


COMPLETA, PRE = "Reserva completa", "Pré-reserva (só guardar o dia)"
tipo_registro = st.radio(
    "O que você quer registrar?", [COMPLETA, PRE], horizontal=True, key=chave("registro"),
    help="Pré-reserva: o cliente demonstrou interesse, mas ainda não pagou o sinal. "
         "Basta o dia, o nome e o telefone. O resto você completa depois no Calendário.",
)
eh_pre = tipo_registro == PRE

# ---------- 1. Dia ----------
st.subheader("1. Qual o dia da festa?")
dia = st.date_input("Dia da festa", value=None, min_value=date.today(),
                    format="DD/MM/YYYY", key=chave("dia"))
ocupada = repo.reserva_na_data(dia) if dia else None
if dia and ocupada:
    st.error(f"{data_extenso(dia).capitalize()} já está ocupado: "
             f"**{ocupada['cliente']}** ({ocupada['tipo_festa'] or 'pré-reserva'}). "
             "Escolha outro dia.", icon=":material/event_busy:")
elif dia:
    st.success(f"{data_extenso(dia).capitalize()} está livre!", icon=":material/event_available:")

# ---------- 2. Cliente ----------
st.subheader("2. Quem vai alugar?")
clientes = repo.listar_clientes()
por_id = {c["id"]: c for c in clientes}
JA_VEIO, NOVO = "Já alugou antes", "Cliente novo"
modo = st.radio("Quem vai alugar?", [JA_VEIO, NOVO] if clientes else [NOVO],
                horizontal=True, label_visibility="collapsed", key=chave("modo"))

id_cliente = nome = telefone = email = None
cpf = endereco = bairro = cidade = None
precisa_cadastro = False  # mostra (e exige) CPF e endereço?

if modo == JA_VEIO:
    id_cliente = st.selectbox("Escolha o cliente", list(por_id),
                              format_func=lambda i: f"{por_id[i]['nome']} — {por_id[i]['telefone']}",
                              index=None, placeholder="Clique aqui e digite o nome",
                              key=chave("cliente"))
    # Cliente antigo sem CPF/endereço: na reserva completa, pede para completar
    if id_cliente and not eh_pre and not repo.cadastro_completo(por_id[id_cliente]):
        st.caption("Faltam dados no cadastro deste cliente (CPF ou endereço). Preencha abaixo:")
        precisa_cadastro = True
        cpf, endereco, bairro, cidade = campos_cadastro(chave(f"cad_{id_cliente}"),
                                                        por_id[id_cliente])
else:
    nome = st.text_input("Nome", key=chave("nome"))
    telefone = st.text_input("Telefone / WhatsApp", key=chave("telefone"))
    if not eh_pre:
        email = st.text_input("E-mail (se tiver)", key=chave("email"))
        precisa_cadastro = True
        cpf, endereco, bairro, cidade = campos_cadastro(chave("cad_novo"))

# ---------- 3 e 4. Festa e valores (só na reserva completa) ----------
hora_inicio, hora_fim = "09:00", "19:00"
tipo = convidados = valor_total = valor_sinal = forma = None
sinal_pago = False

if not eh_pre:
    st.subheader("3. Como vai ser a festa?")
    c1, c2 = st.columns(2)
    hora_inicio = c1.selectbox("Começa às", HORARIOS, index=0, key=chave("inicio"))
    hora_fim = c2.selectbox("Termina às", HORARIOS, index=len(HORARIOS) - 1, key=chave("fim"))
    tipo = st.text_input("Tipo de festa", placeholder="Ex.: aniversário de 15 anos",
                         key=chave("tipo"))
    convidados = st.number_input("Quantos convidados?", min_value=1, value=None, step=5,
                                 key=chave("convidados"))

    st.subheader("4. Valores")
    c3, c4 = st.columns(2)
    valor_total = c3.number_input("Valor total da festa (R$)", min_value=0.0, value=None,
                                  step=50.0, format="%.2f", key=chave("total"))
    valor_sinal = c4.number_input("Valor do sinal (R$)", min_value=0.0, value=None,
                                  step=50.0, format="%.2f", key=chave("sinal"))
    sinal_pago = st.checkbox("O sinal já foi pago", key=chave("sinal_pago"))
    if sinal_pago:
        forma = st.radio("Como o sinal foi pago?", list(FORMAS_TEXTO),
                         format_func=FORMAS_TEXTO.get, horizontal=True, key=chave("forma"))

obs = st.text_area("Observações (se precisar)", key=chave("obs"))

# ---------- Salvar ----------
rotulo = "Salvar pré-reserva" if eh_pre else "Salvar reserva"
if st.button(rotulo, type="primary", width="stretch", disabled=bool(ocupada),
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
    if precisa_cadastro:
        erros += erros_do_cadastro(cpf, endereco, bairro, cidade, obrigatorio=True)
    erros += erros_da_reserva(hora_inicio, hora_fim, tipo, convidados, valor_total,
                              valor_sinal, completa=not eh_pre)
    if sinal_pago and not valor_sinal:
        erros.append("Marcou que o sinal foi pago: informe o valor do sinal.")

    for erro in erros:
        st.error(erro)

    if not erros:
        try:
            if modo == NOVO:
                id_cliente = repo.criar_cliente(nome, telefone, email, None,
                                                endereco, bairro, cidade, cpf)
                nome_cliente = nome.strip()
            else:
                nome_cliente = por_id[id_cliente]["nome"]
                if precisa_cadastro:  # completa CPF/endereço do cliente antigo
                    repo.completar_cadastro(id_cliente, endereco, bairro, cidade, cpf)
            id_reserva = repo.criar_reserva(
                id_cliente, dia, hora_inicio, hora_fim, tipo, convidados,
                para_centavos(valor_total), para_centavos(valor_sinal) or 0, obs,
            )
            if sinal_pago:
                repo.registrar_pagamento(id_reserva, para_centavos(valor_sinal), date.today(),
                                         "sinal", forma)
        except repo.DataOcupadaError:
            st.error("Esse dia acabou de ser ocupado por outra festa. Escolha outro dia.",
                     icon=":material/event_busy:")
        except repo.CpfDuplicadoError as erro:
            st.error(f"Esse CPF já está cadastrado para **{erro.args[0]}**. "
                     "Se for a mesma pessoa, escolha \"Já alugou antes\".")
        else:
            st.session_state["nova_reserva_versao"] += 1
            if eh_pre:
                guardar_aviso(f"Pré-reserva de {nome_cliente} guardada para {data_extenso(dia)}. "
                              "Complete os dados no Calendário quando o cliente confirmar.")
            else:
                guardar_aviso(f"Festa de {nome_cliente} marcada para {data_extenso(dia)}.")
            st.rerun()
