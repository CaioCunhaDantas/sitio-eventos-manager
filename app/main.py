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
from database.criar_banco import criar_banco
from database.usuarios import existe_usuario, verificar_senha

st.set_page_config(page_title="Sítio de Festas", page_icon=":material/cottage:", layout="centered")
aplicar_estilo()


@st.cache_resource  # roda só uma vez enquanto o sistema estiver aberto
def preparar_banco() -> None:
    criar_banco()


preparar_banco()

# Proteção contra "chute" de senha: depois de MAX_TENTATIVAS erradas seguidas,
# o login fica bloqueado por TEMPO_BLOQUEIO.
MAX_TENTATIVAS = 5
TEMPO_BLOQUEIO = timedelta(minutes=5)


@st.cache_resource
def tentativas_de_login() -> dict:
    """Contador compartilhado por TODAS as abas/navegadores (fica na memória do
    servidor). Se fosse por aba, bastaria abrir outra aba para tentar de novo."""
    return {"erros": 0, "bloqueado_ate": None}


def tela_login() -> None:
    st.title("Sítio de Festas")

    if not existe_usuario():
        st.warning(
            "Ainda não tem nenhuma senha cadastrada.  \n"
            "No terminal, rode: `py -m database.criar_usuario`"
        )
        return

    controle = tentativas_de_login()
    bloqueado_ate = controle["bloqueado_ate"]
    if bloqueado_ate and datetime.now() < bloqueado_ate:
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
            controle["erros"] = 0
            controle["bloqueado_ate"] = None
            st.session_state["usuario"] = nome
            st.rerun()  # recarrega a página, agora com o menu
        else:
            time.sleep(1)  # cada tentativa errada demora: chutar senhas fica lento
            controle["erros"] += 1
            if controle["erros"] >= MAX_TENTATIVAS:
                controle["erros"] = 0
                controle["bloqueado_ate"] = datetime.now() + TEMPO_BLOQUEIO
                st.rerun()
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
