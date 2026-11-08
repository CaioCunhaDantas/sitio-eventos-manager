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
