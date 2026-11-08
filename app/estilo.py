"""Aparência: letras e botões grandes, pensado para quem tem pouca prática com computador."""

import streamlit as st

CSS = """
<style>
/* Botões grandes e fáceis de acertar (vale para todos os botões) */
button[data-testid^="stBaseButton"] {
    padding: 0.7rem 1.5rem;
    min-height: 3.2rem;
}
button[data-testid^="stBaseButton"] p {
    font-size: 1.3rem;
}
/* Área central mais larga, para o calendário caber com folga */
[data-testid="stMainBlockContainer"] {
    max-width: 1100px;
}
/* Menu do topo com letra grande */
[data-testid="stTopNavLink"] p,
[data-testid="stTopNavLink"] span {
    font-size: 1.25rem !important;
}
/* Número dos cartões (ex.: "Falta receber") um pouco menor, para caber inteiro */
[data-testid="stMetricValue"] > div {
    font-size: 1.5rem;
}
/* Celular: o menu do topo vira um botão no canto. Escreve "Menu" ao lado
   do ícone para ficar claro onde tocar. */
button[data-testid="stExpandSidebarButton"] {
    width: auto !important;
    padding: 0.3rem 0.7rem !important;
    border: 1px solid #D5DCC2 !important;
    border-radius: 8px !important;
}
button[data-testid="stExpandSidebarButton"]::after {
    content: "Menu";
    font-size: 1.05rem;
    margin-left: 0.4rem;
    color: #2E3324;
}
/* Menu lateral (celular) com letra grande e espaço para o dedo */
[data-testid="stSidebarNavLink"] {
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stSidebarNavLink"] span {
    font-size: 1.25rem !important;
}
/* Títulos mais leves */
h1 { font-weight: 600 !important; letter-spacing: -0.01em; }
h2, h3 { font-weight: 600 !important; }
/* Campos de texto com letra grande */
input, textarea {
    font-size: 1.3rem !important;
}
label p {
    font-size: 1.2rem !important;
}
</style>
"""


def aplicar_estilo() -> None:
    st.html(CSS)
