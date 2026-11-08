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
