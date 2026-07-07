"""Estilos compartilhados do hub.

Fonte única de cores (variáveis CSS em :root) e do "chrome" comum (sidebar,
abas, tabelas admin, rodapé). Injetado uma vez por rerun em app.main(), em vez
de espalhado e duplicado por várias telas.

O CSS específico do grid de cards fica em views/_cards.py (injetado só nas telas
que mostram cards), porque usa seletores globais do Streamlit que não devem
vazar para os layouts de administração.
"""
from __future__ import annotations

import streamlit as st


# Paleta e tokens de layout — mude aqui para refletir em todo o app.
_ROOT_VARS = """
:root {
    --fgv-blue: #1f4e79;
    --fgv-blue-dark: #163a5c;
    --fgv-text: #1f2937;
    --fgv-muted: #6b7280;
    --fgv-muted-2: #94a3b8;
    --fgv-border: #e3e7ee;
    --fgv-bg-soft: #f4f6fa;
    --fgv-card-body-h: 196px;
}
"""

_SIDEBAR = """
.fgv-logo-wrap {
    display: flex; justify-content: center; align-items: center;
    padding: 4px 0 14px 0;
    border-bottom: 1px solid var(--fgv-border);
    margin-bottom: 14px;
}
.fgv-user-card {
    background: var(--fgv-bg-soft); border-radius: 10px;
    padding: 12px 14px; margin-bottom: 14px;
}
.fgv-user-card .welcome { font-size: 0.78rem; color: var(--fgv-muted); margin: 0 0 2px 0; }
.fgv-user-card .name    { font-size: 1.0rem;  color: var(--fgv-text); font-weight: 600; margin: 0; }
.fgv-user-card .email   { font-size: 0.82rem; color: #4b5563; margin: 6px 0 0 0; word-break: break-all; }
.fgv-user-card .role-badge {
    display: inline-block; margin-top: 8px;
    background: var(--fgv-blue); color: #fff;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 3px 10px; border-radius: 999px;
}
.fgv-user-card .role-badge.analista { background: #4b5d76; }
.fgv-nav-label {
    font-size: 0.72rem; color: var(--fgv-muted); letter-spacing: 0.5px;
    text-transform: uppercase; margin: 10px 0 4px 0;
}
"""

_TABS = """
div[data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 2px solid var(--fgv-border);
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--fgv-muted) !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    border-radius: 8px 8px 0 0 !important;
    letter-spacing: 0.5px;
}
button[data-baseweb="tab"]:hover {
    background: var(--fgv-bg-soft) !important;
    color: var(--fgv-blue) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--fgv-blue) !important;
    font-weight: 700 !important;
    border-bottom: 3px solid var(--fgv-blue) !important;
}
.empty-area { color: var(--fgv-muted-2); font-style: italic; padding: 1rem 0; }
"""

# Tabelas de administração (usuários e acessos) — classes compartilhadas.
_ADMIN_TABLE = """
.admin-table-header {
    background: var(--fgv-bg-soft); border-bottom: 2px solid var(--fgv-blue);
    padding: 8px 4px; border-radius: 6px 6px 0 0;
}
.admin-table-header span { color: var(--fgv-blue); font-weight: 700; font-size: 0.82rem;
    text-transform: uppercase; letter-spacing: 0.4px; }
.admin-meta { color: var(--fgv-muted-2); font-size: 0.72rem; margin-top: 2px; }
"""

_FOOTER = """
.fgv-footer {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    z-index: 999;
    background: #ffffff;
    border-top: 1px solid var(--fgv-border);
    padding: 8px 16px;
    text-align: center;
    color: var(--fgv-muted);
    font-size: 0.78rem;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
    box-shadow: 0 -1px 4px rgba(15, 30, 60, 0.04);
}
.fgv-footer .sep { color: #cbd5e1; font-weight: 400; }
/* espaco extra no final do conteudo para nao ficar atras do rodape fixo */
.block-container { padding-bottom: 4rem !important; }
@media (max-width: 640px) {
    .fgv-footer { font-size: 0.7rem; gap: 0.35rem; padding: 6px 10px; }
    .fgv-footer .sep { display: none; }
}
"""

_BASE_STYLES = f"<style>{_ROOT_VARS}{_SIDEBAR}{_TABS}{_ADMIN_TABLE}{_FOOTER}</style>"

HIDE_SIDEBAR = """
<style>
:root { --fgv-blue: #1f4e79; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }
section[data-testid="stSidebar"] + div { margin-left: 0 !important; }
.block-container { padding-top: 3rem; }
</style>
"""


def inject_base() -> None:
    """Injeta os estilos base (variáveis + chrome comum). Chamar 1x por rerun."""
    st.markdown(_BASE_STYLES, unsafe_allow_html=True)
