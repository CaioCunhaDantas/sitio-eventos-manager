from datetime import date

import pandas as pd
import streamlit as st

from app.componentes import botao_com_confirmacao, guardar_aviso, mostrar_aviso
from app.formatacao import (FORMAS_TEXTO, STATUS_TEXTO, TIPOS_TEXTO, data_curta,
                            para_centavos, para_data, reais)
from database import repositorio as repo

st.title("Pagamentos")
mostrar_aviso()

hoje = date.today()
ativas = repo.reservas_ativas()
# Pré-reserva sem valor combinado não tem saldo (None): fica fora daqui
devendo = [r for r in ativas if r["saldo_devedor"] is not None and r["saldo_devedor"] > 0]
sem_valor = [r for r in ativas if r["valor_total"] is None]
por_id = {r["id"]: r for r in devendo}
versao = st.session_state.setdefault("pagamento_versao", 0)


def tipo_automatico(reserva: dict, valor: int) -> str:
    """Primeiro pagamento = sinal; o que quita o saldo = final; o resto = parcela."""
    if reserva["total_pago"] == 0:
        return "sinal"
    if valor >= reserva["saldo_devedor"]:
        return "quitacao"
    return "parcela"


# ---------- Registrar ----------
st.subheader("Registrar um pagamento")
if sem_valor:
    nomes = ", ".join(f"{r['cliente']} ({data_curta(r['data_festa'])})" for r in sem_valor)
    st.caption(f"Pré-reservas sem valor combinado não aparecem aqui: {nomes}. "
               "Complete os dados delas no Calendário para poder receber o sinal.")
if not devendo:
    st.info("Nenhuma festa com pagamento pendente.", icon=":material/check_circle:")
else:
    id_reserva = st.selectbox(
        "De qual festa?", list(por_id),
        format_func=lambda i: (f"{data_curta(por_id[i]['data_festa'])} — {por_id[i]['cliente']} "
                               f"— falta {reais(por_id[i]['saldo_devedor'])}"),
        index=None, placeholder="Clique aqui e escolha a festa", key=f"pg_reserva_{versao}",
    )
    if id_reserva:
        r = por_id[id_reserva]
        m1, m2, m3 = st.columns(3)
        m1.metric("Valor da festa", reais(r["valor_total"]))
        m2.metric("Já pago", reais(r["total_pago"]))
        m3.metric("Falta pagar", reais(r["saldo_devedor"]))

        valor = st.number_input("Quanto foi pago agora? (R$)", min_value=0.0, step=50.0,
                                format="%.2f", value=r["saldo_devedor"] / 100,
                                key=f"pg_valor_{versao}_{id_reserva}")
        forma = st.radio("Como foi pago?", list(FORMAS_TEXTO), format_func=FORMAS_TEXTO.get,
                         horizontal=True, key=f"pg_forma_{versao}")
        dia = st.date_input("Quando foi pago?", value=hoje, max_value=hoje, format="DD/MM/YYYY",
                            key=f"pg_dia_{versao}")
        tipo = tipo_automatico(r, para_centavos(valor))
        st.caption(f"Vai ficar registrado como: **{TIPOS_TEXTO[tipo]}**")

        if st.button("Salvar pagamento", type="primary", width="stretch", icon=":material/check:"):
            centavos = para_centavos(valor)
            if centavos <= 0:
                st.error("Informe o valor pago.")
            elif centavos > r["saldo_devedor"]:
                st.error(f"O valor é maior do que falta pagar ({reais(r['saldo_devedor'])}).")
            else:
                repo.registrar_pagamento(id_reserva, centavos, dia, tipo, forma)
                st.session_state["pagamento_versao"] += 1
                guardar_aviso(f"Pagamento de {reais(centavos)} de {r['cliente']} registrado!")
                st.rerun()

# ---------- Quem deve ----------
st.subheader("Quem ainda deve")
if devendo:
    # Pandas monta a tabela; st.dataframe mostra com rolagem e ordenação
    tabela = pd.DataFrame([
        {
            "Dia da festa": data_curta(r["data_festa"]),
            "Cliente": r["cliente"],
            "Telefone": r["telefone"],
            "Valor da festa": reais(r["valor_total"]),
            "Já pago": reais(r["total_pago"]),
            "Falta": reais(r["saldo_devedor"]),
            "Situação": ("Atrasado: festa já passou" if para_data(r["data_festa"]) < hoje
                         else STATUS_TEXTO[r["status"]]),
        }
        for r in devendo
    ])
    st.dataframe(tabela, hide_index=True, width="stretch")
    st.markdown(f"**Total a receber: {reais(sum(r['saldo_devedor'] for r in devendo))}**")
else:
    st.info("Ninguém está devendo.")

# ---------- Histórico ----------
with st.expander("Últimos pagamentos recebidos", icon=":material/history:"):
    pagamentos = repo.pagamentos_recentes()
    if not pagamentos:
        st.markdown("_Nenhum pagamento registrado ainda._")
    for p in pagamentos:
        with st.container(border=True):
            st.markdown(
                f"**{reais(p['valor'])}** — {p['cliente']} (festa de {data_curta(p['data_festa'])})  \n"
                f"{TIPOS_TEXTO[p['tipo']]} · {FORMAS_TEXTO[p['forma_pagamento']]} · "
                f"pago em {data_curta(p['data_pagamento'])}"
            )
            if botao_com_confirmacao(
                chave=f"apagar_pagamento_{p['id']}",
                rotulo="Apagar (lançado por engano)",
                pergunta=(f"Apagar o pagamento de {reais(p['valor'])} de {p['cliente']}? "
                          "Faça isso só se ele foi registrado por engano."),
                rotulo_sim="Sim, apagar",
                icone=":material/delete:",
            ):
                repo.apagar_pagamento(p["id"])
                guardar_aviso("Pagamento apagado.")
                st.rerun()
