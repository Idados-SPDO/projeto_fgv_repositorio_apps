"""Renderização compartilhada do card de aplicação com botão de favorito.

O grid é um @st.fragment: favoritar/desfavoritar re-executa só o grid (rerun com
scope="fragment"), sem recarregar a página inteira. As cores usam as variáveis
CSS definidas em src/styles.py (--fgv-*). O CSS do card é injetado pelas telas
que mostram cards (home/favorites), não globalmente, porque usa seletores
globais do Streamlit que não devem afetar os layouts de administração.
"""
from __future__ import annotations

import html as html_mod
from typing import Callable, Optional

import pandas as pd
import streamlit as st

from .. import areas as areas_mod
from .. import db


CARD_CSS = """
<style>
/* container do card (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border: 1px solid var(--fgv-border) !important;
    box-shadow: 0 1px 2px rgba(15, 30, 60, 0.04);
    transition: box-shadow 0.12s ease, border-color 0.12s ease;
    height: 100%;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 18px rgba(15, 30, 60, 0.10);
    border-color: #c7d2e3 !important;
}
/* colunas do grid esticam para a mesma altura da linha */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}
.fgv-card-icon { font-size: 1.9rem; line-height: 1; padding-top: 4px; }

/* corpo do card: coluna flex de altura fixa -> cards uniformes */
.fgv-card-body {
    display: flex;
    flex-direction: column;
    height: var(--fgv-card-body-h);
}
.fgv-card-title {
    font-size: 1.05rem; font-weight: 600; color: var(--fgv-text);
    margin: 4px 0 4px 0; flex: 0 0 auto;
}
/* descrição rola quando maior que o espaço disponível */
.fgv-card-desc-wrap {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    margin-bottom: 8px;
}
.fgv-card-desc { font-size: 0.88rem; color: var(--fgv-muted); margin: 0; }
.fgv-card-desc-wrap::-webkit-scrollbar { width: 6px; }
.fgv-card-desc-wrap::-webkit-scrollbar-thumb {
    background: #d5dbe6; border-radius: 3px;
}
.fgv-card-area {
    font-size: 0.82rem; color: var(--fgv-blue); font-weight: 600;
    margin: 0 0 10px 0; flex: 0 0 auto;
}
.fgv-card-area b { font-weight: 700; }

/* área de ações: botão sempre no rodapé e centralizado */
.fgv-card-actions {
    flex: 0 0 auto;
    display: flex;
    justify-content: center;
    margin-top: auto;
}
.fgv-card-actions form { margin: 0; padding: 0; }
.fgv-card-open {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: var(--fgv-blue);
    color: #fff !important;
    text-decoration: none !important;
    padding: 9px 22px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    line-height: 1.1;
    cursor: pointer;
    border: none;
}
.fgv-card-open:hover { background: var(--fgv-blue-dark); }
</style>
"""


def _open_button_html(
    app_url: str,
    access_token: str | None,
    uid: str,
    app_id: int,
    app_name: str,
    refresh_token: str | None = None,
) -> str:
    """Gera o HTML do botão 'Abrir'.

    Se houver um access_token e a app for a url-updater (APP_ID=801),
    usa um formulário POST oculto para enviar o JWT ao endpoint /auth-login
    do app destino (SSO via Nginx sidecar). O refresh_token, se disponível,
    vai junto para o sidecar poder renovar a sessão sozinho quando o access
    token expirar, sem precisar que o usuário volte ao hub.
    Caso contrário, usa um link direto (fallback).
    """
    safe_url = html_mod.escape(app_url, quote=True)
    aria = html_mod.escape(f"Abrir {app_name}", quote=True)

    if not access_token or app_id != 801:
        return (
            f"<a class='fgv-card-open' href='{safe_url}' target='_blank' "
            f"rel='noopener' aria-label='{aria}' title='{aria}'>Abrir &nbsp;&rsaquo;</a>"
        )

    safe_token = html_mod.escape(access_token, quote=True)
    auth_url = f"{safe_url.rstrip('/')}/auth-login"
    form_id = f"sso_form_{uid}"

    refresh_field = ""
    if refresh_token:
        safe_refresh = html_mod.escape(refresh_token, quote=True)
        refresh_field = f"<input type='hidden' name='refresh_token' value='{safe_refresh}'>"

    return (
        f"<form id='{form_id}' method='POST' action='{auth_url}' target='_blank'>"
        f"<input type='hidden' name='token' value='{safe_token}'>"
        f"{refresh_field}"
        f"<button type='submit' class='fgv-card-open' aria-label='{aria}'>Abrir &nbsp;&rsaquo;</button>"
        f"</form>"
    )


def render_card(
    app: pd.Series,
    *,
    fav_ids: set[int],
    user_id: int,
    context: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> None:
    """Renderiza um card de aplicação dentro de um st.container."""
    app_id = int(app["APP_ID"])
    is_fav = app_id in fav_ids
    icon = html_mod.escape(str(app["ICON"] or "⚙️"))
    name = str(app["NAME"])

    with st.container(border=True):
        head_l, head_r = st.columns([4, 1])
        with head_l:
            st.markdown(
                f"<div class='fgv-card-icon'>{icon}</div>",
                unsafe_allow_html=True,
            )
        with head_r:
            label = "⭐" if is_fav else "☆"
            if st.button(
                label,
                key=f"fav_{context}_{app_id}",
                help="Desfavoritar" if is_fav else "Favoritar",
                use_container_width=True,
            ):
                db.toggle_favorite(user_id, app_id)
                # rerun só do fragmento do grid (não da página inteira)
                st.rerun(scope="fragment")

        safe_name = html_mod.escape(name)
        desc_html = ""
        if app["DESCRIPTION"]:
            safe_desc = html_mod.escape(str(app["DESCRIPTION"]))
            desc_html = f"<p class='fgv-card-desc'>{safe_desc}</p>"

        btn_html = _open_button_html(
            app["URL"],
            access_token,
            uid=f"{context}_{app_id}",
            app_id=app_id,
            app_name=name,
            refresh_token=refresh_token,
        )

        st.markdown(
            f"""
            <div class='fgv-card-body'>
                <p class='fgv-card-title'>{safe_name}</p>
                <div class='fgv-card-desc-wrap'>{desc_html}</div>
                <p class='fgv-card-area'><b>Área:</b> {areas_mod.display_name(app['AREA'])}</p>
                <div class='fgv-card-actions'>{btn_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


@st.fragment
def render_grid(
    *,
    fetch: Callable[[], Optional[pd.DataFrame]],
    user_id: int,
    context: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
    cols: int = 3,
    empty_message: str | None = None,
) -> None:
    """Renderiza um grid de cards (cols por linha) como fragmento isolado.

    `fetch` devolve o DataFrame de apps a exibir; é chamado a cada execução do
    fragmento, então após favoritar/desfavoritar (rerun de fragmento) os dados
    e o estado das estrelas refletem a mudança sem recarregar a página. Os
    favoritos (`fav_ids`) são relidos aqui (query cacheada + invalidada no toggle).
    """
    apps = fetch()
    if apps is None or apps.empty:
        if empty_message:
            st.info(empty_message)
        return

    fav_ids = db.list_favorite_app_ids(user_id)
    rows = [apps.iloc[i : i + cols] for i in range(0, len(apps), cols)]
    for i, row in enumerate(rows):
        columns = st.columns(cols, gap="medium")
        for col, (_, app) in zip(columns, row.iterrows()):
            with col:
                render_card(
                    app,
                    fav_ids=fav_ids,
                    user_id=user_id,
                    context=f"{context}_{i}",
                    access_token=access_token,
                    refresh_token=refresh_token,
                )
