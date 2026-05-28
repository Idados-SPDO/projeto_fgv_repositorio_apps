"""Gerenciamento de aplicações/domínios (admin)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import areas as areas_mod
from .. import auth, db


# icone padrao usado em todos os cards
DEFAULT_ICON = "⚙️"  # engrenagem


def _guard() -> dict:
    user = auth.require_login()
    if not auth.is_admin():
        st.error("Acesso restrito a administradores.")
        st.stop()
    return user


def _new_app_form(me: dict) -> None:
    with st.expander("Nova aplicação", expanded=False):
        with st.form("create_app_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Nome da aplicação *")
                area = st.selectbox(
                    "Área *",
                    options=areas_mod.AREA_NAMES,
                    format_func=areas_mod.display_name,
                )
            with c2:
                url = st.text_input("URL *", placeholder="https://...")
                description = st.text_area("Descrição", height=120)

            submitted = st.form_submit_button("Cadastrar aplicação", type="primary")
            if submitted:
                if not all([name, area, url]):
                    st.error("Preencha nome, área e URL.")
                    return
                if not (url.startswith("http://") or url.startswith("https://")):
                    st.error("URL deve começar com http:// ou https://")
                    return
                db.create_application(
                    area=area,
                    name=name.strip(),
                    description=description.strip() or None,
                    url=url.strip(),
                    icon=DEFAULT_ICON,
                    created_by=me["id"],
                )
                st.success(f"Aplicação {name} cadastrada.")
                st.rerun()


def _edit_app_section(apps_df: pd.DataFrame) -> None:
    if apps_df.empty:
        return

    st.markdown("#### Editar aplicação")
    labels = {
        int(r["APP_ID"]): f"[{r['AREA']}] {r['NAME']}" for _, r in apps_df.iterrows()
    }
    target_id = st.selectbox(
        "Selecione uma aplicação",
        options=list(labels.keys()),
        format_func=lambda i: labels[i],
        key="edit_app_select",
    )
    row = apps_df[apps_df["APP_ID"] == target_id].iloc[0]

    with st.form(f"edit_app_form_{target_id}"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Nome", value=row["NAME"])
            area = st.selectbox(
                "Área",
                options=areas_mod.AREA_NAMES,
                index=areas_mod.AREA_NAMES.index(row["AREA"]) if row["AREA"] in areas_mod.AREA_NAMES else 0,
                format_func=areas_mod.display_name,
            )
            is_active = st.checkbox("Ativa", value=bool(row["IS_ACTIVE"]))
        with c2:
            url = st.text_input("URL", value=row["URL"])
            description = st.text_area("Descrição", value=row["DESCRIPTION"] or "", height=120)

        save = st.form_submit_button("Salvar alterações", type="primary")

    if save:
        if not (url.startswith("http://") or url.startswith("https://")):
            st.error("URL deve começar com http:// ou https://")
            return
        db.update_application(
            app_id=int(target_id),
            area=area,
            name=name.strip(),
            description=description.strip() or None,
            url=url.strip(),
            icon=row["ICON"] or DEFAULT_ICON,
            is_active=is_active,
        )
        st.success("Alterações salvas.")
        st.rerun()

    with st.popover("Excluir aplicação"):
        st.warning(f"Excluir definitivamente **{row['NAME']}**?")
        if st.button("Confirmar exclusão", key=f"del_app_{target_id}", type="primary"):
            db.delete_application(int(target_id))
            st.success("Aplicação excluída.")
            st.rerun()


def render() -> None:
    me = _guard()
    st.header("Gerenciar aplicações")
    st.caption("Cadastre ou edite os domínios das aplicações internas por área.")

    apps_df = db.list_applications(only_active=False)

    _new_app_form(me)
    st.divider()

    st.markdown("#### Aplicações cadastradas")
    if apps_df.empty:
        st.info("Nenhuma aplicação cadastrada ainda.")
        return

    display = apps_df.copy()
    display["IS_ACTIVE"] = display["IS_ACTIVE"].map({True: "Sim", False: "Não"})
    st.dataframe(
        display.rename(
            columns={
                "AREA": "Área",
                "NAME": "Nome",
                "DESCRIPTION": "Descrição",
                "URL": "URL",
                "IS_ACTIVE": "Ativa",
                "CREATED_AT": "Criada em",
                "UPDATED_AT": "Atualizada em",
            }
        ).drop(columns=["APP_ID", "CREATED_BY", "ICON"]),
        hide_index=True,
        use_container_width=True,
        column_config={"URL": st.column_config.LinkColumn("URL")},
    )

    st.divider()
    _edit_app_section(apps_df)
