"""Logo e rodape compartilhados entre as telas."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "fgv_ibre.png"
DEVELOPER_NAME = "Felipe Fortunato"
APP_NAME = "Repositório de Aplicações FGV IBRE"
CREATED_AT = "28/05/2026"


@st.cache_data(show_spinner=False)
def _logo_data_uri() -> str | None:
    if not LOGO_PATH.exists():
        return None
    data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def logo_html(*, height_px: int = 48, fallback_text: str = "FGV IBRE") -> str:
    """Retorna um <img> com o logo ou um placeholder textual."""
    uri = _logo_data_uri()
    if uri:
        return (
            f"<img src='{uri}' alt='FGV IBRE' "
            f"style='height:{height_px}px;width:auto;display:block;' />"
        )
    return (
        "<div style='display:inline-block;font-weight:800;letter-spacing:2px;"
        f"font-size:{max(int(height_px * 0.45), 16)}px;color:#1f4e79;"
        "padding:6px 14px;border:2px solid #1f4e79;border-radius:8px;'>"
        f"{fallback_text}</div>"
    )


def render_footer() -> None:
    # o CSS de .fgv-footer vive em src/styles.py (injetado uma vez em app.main)
    st.markdown(
        f"""
        <div class='fgv-footer'>
            <span>Desenvolvido por <b>{DEVELOPER_NAME}</b></span>
            <span class='sep'>|</span>
            <span>{APP_NAME}</span>
            <span class='sep'>|</span>
            <span>Criado em {CREATED_AT}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
