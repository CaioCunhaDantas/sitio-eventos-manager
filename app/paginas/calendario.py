import calendar
from datetime import date
from html import escape

import streamlit as st

from app.componentes import (botao_com_confirmacao, erros_da_reserva, guardar_aviso,
                             mostrar_aviso)
from app.formatacao import (HORARIOS, MESES, STATUS_TEXTO, data_com_dia_semana,
                            data_extenso, para_centavos, para_data, reais)
from database import repositorio as repo

CSS_CALENDARIO = """
<style>
.cal { width: 100%; border-collapse: collapse; table-layout: fixed; }
.cal th { color: #8A9078; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
          text-transform: uppercase; text-align: left; padding: 0 8px 8px; }
.cal td { border-top: 1px solid #E6E9DF; height: 92px; vertical-align: top;
          padding: 6px; overflow: hidden; }
.cal .num { display: inline-flex; align-items: center; justify-content: center;
            width: 1.9em; height: 1.9em; border-radius: 50%;
            font-size: 0.95rem; color: #3A4030; }
.cal td.hoje .num { background: #556B2F; color: #FFFFFF; font-weight: 600; }
.cal td.passado .num { color: #A7AD9A; }
.cal td.fora .num { color: #D3D7C9; }
.cal td.fora .festa { display: none; }
.cal .festa { margin-top: 4px; padding: 4px 6px; border-radius: 6px; font-size: 0.78rem;
              line-height: 1.2; overflow-wrap: anywhere; }
.cal .festa b { font-weight: 600; }
.cal .festa.confirmada { background: #556B2F; color: #FFFFFF; }
.cal .festa.aguardando { background: #EEF1E6; color: #3A4030; border-left: 3px solid #556B2F; }
.cal td.passado .festa { opacity: 0.55; }
.legenda { display: flex; flex-wrap: wrap; gap: 20px; font-size: 0.8rem; color: #6B7160;
           margin-top: 10px; }
.legenda span::before { content: ""; display: inline-block; width: 10px; height: 10px;
                        border-radius: 50%; margin-right: 6px; }
.legenda .l-confirmada::before { background: #556B2F; }
.legenda .l-aguardando::before { background: #EEF1E6; box-shadow: inset 0 0 0 2px #556B2F; }
</style>
"""


def mes_exibido() -> tuple[int, int]:
    """Mês atual + o deslocamento escolhido nas setas.

    Guardamos só o deslocamento (ex.: +1 = próximo mês), nunca o mês fixo.
    Por isso, quando o mês vira, o calendário vira junto, sozinho.
    """
    hoje = date.today()
    meses_desde_ano_zero = hoje.year * 12 + (hoje.month - 1) + st.session_state.get("desloc_mes", 0)
    return meses_desde_ano_zero // 12, meses_desde_ano_zero % 12 + 1


def mudar_mes(delta: int) -> None:
    if delta == 0:
        st.session_state["desloc_mes"] = 0
    else:
        st.session_state["desloc_mes"] = st.session_state.get("desloc_mes", 0) + delta


def html_celula(dia: date, mes: int, hoje: date, reserva: dict | None) -> str:
    classes = []
    if dia.month != mes:
        classes.append("fora")
    if dia < hoje:
        classes.append("passado")
    if dia == hoje:
        classes.append("hoje")

    conteudo = ""
    if reserva:
        tipo = "aguardando" if reserva["status"] == "pre_reserva" else "confirmada"
        # escape(): impede que um nome com "<" ou ">" quebre o HTML
        conteudo = (f'<div class="festa {tipo}"><b>{escape(reserva["cliente"])}</b><br>'
                    f'{escape(reserva["tipo_festa"])}</div>')
    return f'<td class="{" ".join(classes)}"><span class="num">{dia.day}</span>{conteudo}</td>'


@st.fragment(run_every="2m")  # redesenha sozinho a cada 2 minutos
def calendario_do_mes() -> None:
    hoje = date.today()
    ano, mes = mes_exibido()
    # Semanas começando no domingo, incluindo dias do mês anterior/seguinte
    semanas = calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes)
    reservas = {r["data_festa"]: r
                for r in repo.reservas_do_periodo(semanas[0][0], semanas[-1][-1])}

    do_mes = [r for r in reservas.values() if para_data(r["data_festa"]).month == mes]
    livres = sum(1 for semana in semanas for d in semana
                 if d.month == mes and d >= hoje and d.isoformat() not in reservas)

    st.subheader(f"{MESES[mes - 1].capitalize()} de {ano}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Festas no mês", len(do_mes), border=True)
    m2.metric("Dias livres no mês", livres, border=True)
    m3.metric("Falta receber (total)", reais(repo.total_a_receber()), border=True)

    cabecalho = "".join(f"<th>{d}</th>" for d in ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"])
    linhas = "".join(
        "<tr>" + "".join(html_celula(d, mes, hoje, reservas.get(d.isoformat())) for d in semana) + "</tr>"
        for semana in semanas
    )
    st.html(
        CSS_CALENDARIO
        + f'<table class="cal"><thead><tr>{cabecalho}</tr></thead><tbody>{linhas}</tbody></table>'
        + '<div class="legenda"><span class="l-confirmada">Festa confirmada</span>'
          '<span class="l-aguardando">Aguardando sinal</span></div>'
    )


def formulario_alterar(r: dict) -> None:
    status_editaveis = ["pre_reserva", "confirmada", "realizada"]
    with st.form(f"alterar_reserva_{r['id']}"):
        dia = st.date_input("Dia da festa", value=para_data(r["data_festa"]), format="DD/MM/YYYY")
        c1, c2 = st.columns(2)
        hora_inicio = c1.selectbox("Começa às", HORARIOS, index=HORARIOS.index(r["hora_inicio"])
                                   if r["hora_inicio"] in HORARIOS else 0)
        hora_fim = c2.selectbox("Termina às", HORARIOS, index=HORARIOS.index(r["hora_fim"])
                                if r["hora_fim"] in HORARIOS else len(HORARIOS) - 1)
        tipo = st.text_input("Tipo de festa", value=r["tipo_festa"])
        convidados = st.number_input("Convidados", min_value=1, value=r["num_convidados"], step=5)
        c3, c4 = st.columns(2)
        valor_total = c3.number_input("Valor total (R$)", min_value=0.0, step=50.0, format="%.2f",
                                      value=r["valor_total"] / 100)
        valor_sinal = c4.number_input("Valor do sinal (R$)", min_value=0.0, step=50.0, format="%.2f",
                                      value=r["valor_sinal"] / 100)
        status = st.selectbox("Situação", status_editaveis, format_func=STATUS_TEXTO.get,
                              index=status_editaveis.index(r["status"])
                              if r["status"] in status_editaveis else 0)
        obs = st.text_area("Observações", value=r["observacoes"] or "")
        salvar = st.form_submit_button("Salvar alterações", type="primary", width="stretch",
                                       icon=":material/check:")

    if salvar:
        erros = erros_da_reserva(hora_inicio, hora_fim, tipo, convidados, valor_total, valor_sinal)
        for erro in erros:
            st.error(erro)
        if not erros:
            try:
                repo.atualizar_reserva(r["id"], dia, hora_inicio, hora_fim, tipo, convidados,
                                       para_centavos(valor_total), para_centavos(valor_sinal),
                                       status, obs)
            except repo.DataOcupadaError:
                st.error(f"{data_extenso(dia).capitalize()} já tem outra festa. Escolha outro dia.",
                         icon=":material/event_busy:")
            else:
                guardar_aviso("Alterações salvas!")
                st.rerun()


def detalhes_da_festa(r: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Horário**  \n{r['hora_inicio']} às {r['hora_fim']}")
    c2.markdown(f"**Convidados**  \n{r['num_convidados']}")
    c3.markdown(f"**Telefone**  \n{r['telefone']}")
    c4, c5, c6 = st.columns(3)
    c4.markdown(f"**Valor da festa**  \n{reais(r['valor_total'])}")
    c5.markdown(f"**Já pago**  \n{reais(r['total_pago'])}")
    c6.markdown(f"**Falta pagar**  \n{reais(r['saldo_devedor'])}")
    st.markdown(f"**Situação:** {STATUS_TEXTO[r['status']]}")
    if r["observacoes"]:
        st.markdown(f"**Observações:** {r['observacoes']}")

    if st.toggle("Alterar dados desta festa", key=f"toggle_alterar_{r['id']}"):
        formulario_alterar(r)

    if botao_com_confirmacao(
        chave=f"cancelar_{r['id']}",
        rotulo="Cancelar esta festa",
        pergunta=(f"Tem certeza que quer cancelar a festa de {r['cliente']} "
                  f"em {data_extenso(r['data_festa'])}? O dia vai ficar livre de novo."),
        rotulo_sim="Sim, cancelar a festa",
        icone=":material/event_busy:",
    ):
        repo.cancelar_reserva(r["id"])
        guardar_aviso(f"Festa de {r['cliente']} cancelada. O dia ficou livre.")
        st.rerun()


# ------------------------- Tela -------------------------
st.title("Calendário")
mostrar_aviso()

b1, b2, b3 = st.columns(3)
b1.button("Mês anterior", icon=":material/chevron_left:", on_click=mudar_mes, args=(-1,),
          width="stretch")
b2.button("Voltar para hoje", icon=":material/today:", on_click=mudar_mes, args=(0,),
          width="stretch")
b3.button("Próximo mês", icon=":material/chevron_right:", on_click=mudar_mes, args=(1,),
          width="stretch")

calendario_do_mes()

ano, mes = mes_exibido()
inicio = date(ano, mes, 1)
fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
festas = repo.reservas_do_periodo(inicio, fim)

st.subheader(f"Festas de {MESES[mes - 1]}")
if not festas:
    st.info("Nenhuma festa marcada neste mês.")
for r in festas:
    icone = ":material/schedule:" if r["status"] == "pre_reserva" else ":material/event_available:"
    with st.expander(f"{data_com_dia_semana(r['data_festa'])} — {r['cliente']} — {r['tipo_festa']}",
                     icon=icone):
        detalhes_da_festa(r)
