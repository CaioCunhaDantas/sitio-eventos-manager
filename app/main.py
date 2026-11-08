"""Ponto de entrada do sistema.

Uso (na raiz do projeto):
    .venv\\Scripts\\streamlit run app/main.py
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# O Streamlit só enxerga a pasta app/. Esta linha adiciona a raiz do
# projeto ao caminho de importação, para "from database..." funcionar.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.estilo import aplicar_estilo
from app.protecao_login import ControleDeTentativas
from database.criar_banco import criar_banco
from database.usuarios import existe_usuario, verificar_senha

st.set_page_config(page_title="Sítio de Festas", page_icon=":material/cottage:", layout="centered")
aplicar_estilo()


@st.cache_resource  # roda só uma vez enquanto o sistema estiver aberto
def preparar_banco() -> None:
    criar_banco()


preparar_banco()


@st.cache_resource
def controle_de_tentativas() -> ControleDeTentativas:
    """Um controle só para o servidor inteiro (vale para todas as abas)."""
    return ControleDeTentativas(max_tentativas=5, tempo_bloqueio=timedelta(minutes=5))


def ip_do_visitante() -> str:
    """IP de quem está acessando.

    Na nuvem, o Caddy fica na frente do sistema e informa o IP real no
    cabeçalho X-Forwarded-For (ele descarta o valor que vier do visitante,
    então não dá para falsificar). Sem Caddy (PC de casa), usa o IP direto.
    """
    encaminhado = st.context.headers.get("X-Forwarded-For")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    ip = getattr(st.context, "ip_address", None)
    return ip if isinstance(ip, str) and ip else "local"


def tela_login() -> None:
    st.title("Sítio de Festas")

    if not existe_usuario():
        st.warning(
            "Ainda não tem nenhuma senha cadastrada.  \n"
            "No terminal, rode: `py -m database.criar_usuario`  \n"
            "(na nuvem: `docker compose exec app python -m database.criar_usuario`)"
        )
        return

    controle = controle_de_tentativas()
    ip = ip_do_visitante()
    bloqueado_ate = controle.bloqueado_ate(ip)
    if bloqueado_ate:
        minutos = max(1, round((bloqueado_ate - datetime.now()).total_seconds() / 60))
        st.error(f"Muitas senhas erradas seguidas. Espere {minutos} minuto(s) e tente de novo.",
                 icon=":material/lock_clock:")
        return

    # st.form: a senha só é conferida ao clicar em Entrar (ou apertar Enter)
    with st.form("login"):
        senha = st.text_input("Digite sua senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", width="stretch")

    if entrar:
        nome = verificar_senha(senha)
        if nome:
            controle.registrar_acerto(ip)
            st.session_state["usuario"] = nome
            st.rerun()  # recarrega a página, agora com o menu
        else:
            time.sleep(1)  # cada tentativa errada demora: chutar senhas fica lento
            if controle.registrar_erro(ip):
                st.rerun()  # acabou de bloquear: mostra o aviso de bloqueio
            st.error("Senha errada. Tente de novo.")

def sair() -> None:
    st.session_state.pop("usuario", None)
    st.rerun()


if "usuario" not in st.session_state:
    pagina = st.navigation([st.Page(tela_login, title="Entrar", icon=":material/lock:")])
else:
    # Ícones: Material Symbols (fonts.google.com/icons), escritos como :material/nome:
    pagina = st.navigation(
        [
            st.Page("paginas/calendario.py", title="Calendário",
                    icon=":material/calendar_month:", default=True),
            st.Page("paginas/nova_reserva.py", title="Nova reserva", icon=":material/add_circle:"),
            st.Page("paginas/clientes.py", title="Clientes", icon=":material/group:"),
            st.Page("paginas/pagamentos.py", title="Pagamentos", icon=":material/payments:"),
            st.Page(sair, title="Sair", icon=":material/logout:"),
        ],
        position="top",
    )

pagina.run()
