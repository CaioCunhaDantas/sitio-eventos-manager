import calendar
from datetime import date
from html import escape

import streamlit as st

from app.componentes import (botao_com_confirmacao, erros_da_reserva, guardar_aviso,
                             mostrar_aviso)
from app.formatacao import (HORARIOS, MESES, STATUS_TEXTO, dados_completos,
                            data_com_dia_semana, data_extenso, endereco_texto,
                            para_centavos, para_data, reais, situacao_pagamento,
                            texto_situacao)
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
.cal .festa .valor { display: block; font-weight: 600; }
.cal .festa.pre_reserva { background: #FFFFFF; color: #5F6553; border: 1px dashed #8A9078; }
/* Cores por situação do pagamento */
.cal .festa.quitada   { background: #556B2F; color: #FFFFFF; }
.cal .festa.falta     { background: #FBF0D5; color: #5A4510; border-left: 3px solid #C8961E; }
.cal .festa.sem_sinal { background: #F8E1D7; color: #6B2E17; border-left: 3px solid #C0603A; }
.cal td.passado .festa { opacity: 0.6; }
/* Sábado e domingo com fundo levemente destacado */
.cal td.fds { background: #F7F9F1; }
.cal th.fds { color: #556B2F; }
.legenda { display: flex; flex-wrap: wrap; gap: 20px; font-size: 0.8rem; color: #6B7160;
           margin-top: 10px; }
.legenda span::before { content: ""; display: inline-block; width: 10px; height: 10px;
                        border-radius: 50%; margin-right: 6px; }
.legenda .l-quitada::before   { background: #556B2F; }
.legenda .l-falta::before     { background: #C8961E; }
.legenda .l-sem_sinal::before { background: #C0603A; }
.legenda .l-pre_reserva::before { background: #FFFFFF; box-shadow: inset 0 0 0 1px #8A9078; }
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


def escolher_mes_ano() -> None:
    """Chamada quando a pessoa troca o mês ou o ano nos seletores.

    Converte a escolha em deslocamento a partir de hoje (o mesmo formato
    usado pelas setas), assim tudo continua andando junto com o mês atual.
    """
    hoje = date.today()
    escolhido = st.session_state["sel_ano"] * 12 + st.session_state["sel_mes"] - 1
    st.session_state["desloc_mes"] = escolhido - (hoje.year * 12 + hoje.month - 1)


def anos_disponiveis(ano_exibido: int) -> list[int]:
    """De 2 anos atrás até 5 anos à frente (sempre incluindo o ano exibido)."""
    hoje = date.today()
    primeiro = min(hoje.year - 2, ano_exibido)
    ultimo = max(hoje.year + 5, ano_exibido)
    return list(range(primeiro, ultimo + 1))


def html_celula(dia: date, mes: int, hoje: date, reserva: dict | None) -> str:
    classes = []
    if dia.weekday() >= 5:  # 5 = sábado, 6 = domingo
        classes.append("fds")
    if dia.month != mes:
        classes.append("fora")
    if dia < hoje:
        classes.append("passado")
    if dia == hoje:
        classes.append("hoje")

    conteudo = ""
    if reserva:
        situacao = situacao_pagamento(reserva)
        # chr(160) = espaço que não quebra linha: "R$" e o número ficam sempre juntos
        valor = texto_situacao(reserva).replace("R$ ", "R$" + chr(160))
        tipo = f"{escape(reserva['tipo_festa'])}<br>" if reserva["tipo_festa"] else ""
        # escape(): impede que um nome com "<" ou ">" quebre o HTML
        conteudo = (f'<div class="festa {situacao}"><b>{escape(reserva["cliente"])}</b><br>'
                    f'{tipo}<span class="valor">{valor}</span></div>')
    return f'<td class="{" ".join(classes)}"><span class="num">{dia.day}</span>{conteudo}</td>'


@st.fragment(run_every="2m")  # redesenha sozinho a cada 2 minutos
def calendario_do_mes() -> None:
    hoje = date.today()
    ano, mes = mes_exibido()
    # Semanas começando na segunda (firstweekday=0), incluindo dias do mês anterior/seguinte
    semanas = calendar.Calendar(firstweekday=0).monthdatescalendar(ano, mes)
    reservas = {r["data_festa"]: r
                for r in repo.reservas_do_periodo(semanas[0][0], semanas[-1][-1])}

    do_mes = [r for r in reservas.values() if para_data(r["data_festa"]).month == mes]
    livres = sum(1 for semana in semanas for d in semana
                 if d.month == mes and d >= hoje and d.isoformat() not in reservas)

    titulo, hoje_col = st.columns([3, 1.2], vertical_alignment="center")
    titulo.subheader(f"{MESES[mes - 1].capitalize()} de {ano}")
    if (ano, mes) != (hoje.year, hoje.month):
        # Dentro do fragmento, o botão só recarregaria o calendário;
        # st.rerun() recarrega a tela toda (seletores e lista de festas juntos).
        if hoje_col.button("Hoje", icon=":material/today:", width="stretch"):
            mudar_mes(0)
            st.rerun()

    m1, m2, m3 = st.columns(3)
    m1.metric("Festas", len(do_mes), border=True, help="Festas marcadas neste mês")
    m2.metric("Dias livres", livres, border=True, help="Dias deste mês, de hoje em diante, sem festa")
    # "or 0": pré-reserva sem valor combinado ainda não tem saldo
    a_receber_no_mes = sum(r["saldo_devedor"] or 0 for r in do_mes)
    m3.metric("A receber", reais(a_receber_no_mes), border=True,
              help="Quanto ainda falta receber das festas deste mês")

    cabecalho = "".join(
        f'<th class="fds">{d}</th>' if d in ("Sáb", "Dom") else f"<th>{d}</th>"
        for d in ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    )
    linhas = "".join(
        "<tr>" + "".join(html_celula(d, mes, hoje, reservas.get(d.isoformat())) for d in semana) + "</tr>"
        for semana in semanas
    )
    st.html(
        CSS_CALENDARIO
        + f'<table class="cal"><thead><tr>{cabecalho}</tr></thead><tbody>{linhas}</tbody></table>'
        + '<div class="legenda"><span class="l-quitada">Quitada</span>'
          '<span class="l-falta">Sinal pago, falta o resto</span>'
          '<span class="l-sem_sinal">Nada pago ainda</span>'
          '<span class="l-pre_reserva">Pré-reserva (faltam dados)</span></div>'
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
        tipo = st.text_input("Tipo de festa", value=r["tipo_festa"] or "")
        convidados = st.number_input("Convidados", min_value=1, value=r["num_convidados"], step=5)
        c3, c4 = st.columns(2)
        valor_total = c3.number_input(
            "Valor total (R$)", min_value=0.0, step=50.0, format="%.2f",
            value=r["valor_total"] / 100 if r["valor_total"] is not None else None)
        valor_sinal = c4.number_input("Valor do sinal (R$)", min_value=0.0, step=50.0, format="%.2f",
                                      value=r["valor_sinal"] / 100)
        status = st.selectbox("Situação", status_editaveis, format_func=STATUS_TEXTO.get,
                              index=status_editaveis.index(r["status"])
                              if r["status"] in status_editaveis else 0)
        obs = st.text_area("Observações", value=r["observacoes"] or "")
        salvar = st.form_submit_button("Salvar alterações", type="primary", width="stretch",
                                       icon=":material/check:")

    if salvar:
        # Na pré-reserva os dados da festa podem ficar em branco
        erros = erros_da_reserva(hora_inicio, hora_fim, tipo, convidados, valor_total,
                                 valor_sinal, completa=(status != "pre_reserva"))
        for erro in erros:
            st.error(erro)
        if not erros:
            try:
                repo.atualizar_reserva(r["id"], dia, hora_inicio, hora_fim, tipo, convidados,
                                       para_centavos(valor_total),
                                       para_centavos(valor_sinal) or 0, status, obs)
            except repo.DataOcupadaError:
                st.error(f"{data_extenso(dia).capitalize()} já tem outra festa. Escolha outro dia.",
                         icon=":material/event_busy:")
            except repo.DadosIncompletosError:
                st.error("Para sair da pré-reserva, preencha tipo de festa, convidados e valor.")
            else:
                guardar_aviso("Alterações salvas!")
                st.rerun()


def detalhes_da_festa(r: dict) -> None:
    if not dados_completos(r):
        st.info("Pré-reserva: o dia está guardado, mas faltam os dados da festa "
                "(tipo, convidados e valor). Complete em **Alterar dados desta festa**.",
                icon=":material/pending:")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Horário**  \n{r['hora_inicio']} às {r['hora_fim']}")
    c2.markdown(f"**Convidados**  \n{r['num_convidados'] or '—'}")
    c3.markdown(f"**Telefone**  \n{r['telefone']}")
    endereco = endereco_texto(r)
    st.markdown(f"**Endereço do cliente:** {endereco}" if endereco
                else "**Endereço do cliente:** não cadastrado (complete na tela Clientes)")
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

# Os seletores sempre mostram o mês exibido: o valor é colocado no
# session_state ANTES de o seletor ser desenhado (por isso não usamos index=).
ano_atual_exibido, mes_atual_exibido = mes_exibido()
st.session_state["sel_mes"] = mes_atual_exibido
st.session_state["sel_ano"] = ano_atual_exibido

b_ant, s_mes, s_ano, b_prox = st.columns([0.7, 2, 1.4, 0.7], vertical_alignment="bottom")
# Setas só com ícone (o texto aparece ao passar o mouse, pelo help=)
b_ant.button("", icon=":material/chevron_left:", help="Mês anterior", on_click=mudar_mes,
             args=(-1,), width="stretch")
s_mes.selectbox("Mês", list(range(1, 13)), format_func=lambda m: MESES[m - 1].capitalize(),
                key="sel_mes", on_change=escolher_mes_ano)
s_ano.selectbox("Ano", anos_disponiveis(ano_atual_exibido), key="sel_ano",
                on_change=escolher_mes_ano)
b_prox.button("", icon=":material/chevron_right:", help="Próximo mês", on_click=mudar_mes,
              args=(1,), width="stretch")

calendario_do_mes()

ano, mes = mes_exibido()
inicio = date(ano, mes, 1)
fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
festas = repo.reservas_do_periodo(inicio, fim)

st.subheader(f"Festas de {MESES[mes - 1]}")
if not festas:
    st.info("Nenhuma festa marcada neste mês.")
for r in festas:
    icone = {"quitada": ":material/check_circle:", "falta": ":material/hourglass_top:",
             "sem_sinal": ":material/schedule:",
             "pre_reserva": ":material/pending:"}[situacao_pagamento(r)]
    tipo = f"{r['tipo_festa']} · " if r["tipo_festa"] else ""
    with st.expander(f"{data_com_dia_semana(r['data_festa'])} — {r['cliente']} — "
                     f"{tipo}{texto_situacao(r).lower()}", icon=icone):
        detalhes_da_festa(r)
