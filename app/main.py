"""Ponto de entrada do sistema.

Uso (na raiz do projeto):
    .venv\\Scripts\\streamlit run app/main.py
"""

import sys
from pathlib import Path

# O Streamlit só enxerga a pasta app/. Esta linha adiciona a raiz do
# projeto ao caminho de importação, para "from database..." funcionar.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.estilo import aplicar_estilo
from database.criar_banco import criar_banco
from database.usuarios import existe_usuario, verificar_senha

st.set_page_config(page_title="Sítio de Festas", page_icon="🏡", layout="centered")
aplicar_estilo()


@st.cache_resource  # roda só uma vez enquanto o sistema estiver aberto
def preparar_banco() -> None:
    criar_banco()


preparar_banco()


def tela_login() -> None:
    st.title("🏡 Sítio de Festas")

    if not existe_usuario():
        st.warning(
            "Ainda não tem nenhuma senha cadastrada.  \n"
            "No terminal, rode: `py -m database.criar_usuario`"
        )
        return

    # st.form: a senha só é conferida ao clicar em Entrar (ou apertar Enter)
    with st.form("login"):
        senha = st.text_input("Digite sua senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if entrar:
        nome = verificar_senha(senha)
        if nome:
            st.session_state["usuario"] = nome
            st.rerun()  # recarrega a página, agora com o menu
        else:
            st.error("Senha errada. Tente de novo.")


def sair() -> None:
    st.session_state.pop("usuario", None)
    st.rerun()


if "usuario" not in st.session_state:
    pagina = st.navigation([st.Page(tela_login, title="Entrar", icon="🔑")])
else:
    pagina = st.navigation(
        [
            st.Page("paginas/calendario.py", title="Calendário", icon="📅", default=True),
            st.Page("paginas/nova_reserva.py", title="Nova reserva", icon="➕"),
            st.Page("paginas/clientes.py", title="Clientes", icon="👥"),
            st.Page("paginas/pagamentos.py", title="Pagamentos", icon="💰"),
            st.Page(sair, title="Sair", icon="🚪"),
        ],
        position="top",
    )

pagina.run()
