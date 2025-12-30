# app.py
import os
import sys

# Garante que o diretório do projeto esteja no PYTHONPATH (Docker/Railway)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from agenda_igreja.db import test_db_connection
from agenda_igreja.auth import init_auth, authenticate
from agenda_igreja.events import (
    init_events,
    create_event,
    update_event,
    delete_event,
    get_event,
    list_events_between
)
from agenda_igreja.ui import (
    CONGREGACOES,
    TIPOS,
    SUBTIPOS_CULTO,
    TURMAS_EBD,
    format_tipo,
    df_to_png_bytes
)

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Agenda da Igreja",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Estado inicial
# =========================
def init_state():
    st.session_state.setdefault("auth_ok", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Agenda da Semana")
    st.session_state.setdefault("edit_id", None)

# =========================
# Sidebar
# =========================
def sidebar():
    with st.sidebar:
        st.markdown("## 📅 Agenda da Igreja")

        ok, msg = test_db_connection()
        st.caption(msg)

        if st.session_state.auth_ok:
            user = st.session_state.user
            st.markdown(f"**Usuário:** {user.get('nome') or user.get('username')}")
            st.divider()

            pages = [
                "Agenda da Semana",
                "Cadastrar Evento",
                "Gerenciar Eventos"
            ]

            st.session_state.page = st.radio(
                "Navegação",
                pages,
                index=pages.index(st.session_state.page)
                if st.session_state.page in pages else 0
            )

            st.divider()
            if st.button("Sair"):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.page = "Login"
                st.rerun()
        else:
            st.session_state.page = "Login"

# =========================
# Login
# =========================
def page_login():
    st.markdown("# Login")
    st.write("Acesso restrito para cadastro e gerenciamento da agenda.")

    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        ok, user = authenticate(username.strip(), password)
        if ok:
            st.session_state.auth_ok = True
            st.session_state.user = user
            st.session_state.page = "Agenda da Semana"
            st.success("Login realizado com sucesso.")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# =========================
# Utilidades
# =========================
def week_bounds(ref: date):
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

# =========================
# Cadastro de Evento
# =========================
def page_cadastrar_evento():
    st.markdown("# Cadastro de Evento")

    edit_id = st.session_state.edit_id
    ev = get_event(edit_id) if edit_id else None

    def val(key, default=""):
        return ev.get(key) if ev and ev.get(key) is not None else default

    col1, col2, col3 = st.columns(3)

    with col1:
        congregacao = st.selectbox(
            "Congregação",
            CONGREGACOES,
            index=CONGREGACOES.index(val("congregacao", CONGREGACOES[0]))
        )

    with col2:
        tipo = st.selectbox(
            "Tipo da agenda",
            TIPOS,
            index=TIPOS.index(val("tipo", TIPOS[0]))
        )

    with col3:
        subtipo = ""
        turma_ebd = ""

        if tipo == "Culto":
            subtipo = st.selectbox(
                "Subtipo do Culto",
                [""] + SUBTIPOS_CULTO,
                index=([""] + SUBTIPOS_CULTO).index(val("subtipo", ""))
            )
        elif tipo == "EBD":
            turma_ebd = st.selectbox(
                "Turma da EBD",
                [""] + TURMAS_EBD,
                index=([""] + TURMAS_EBD).index(val("turma_ebd", ""))
            )

    col4, col5 = st.columns(2)
    with col4:
        data_evento = st.date_input("Data", value=val("data", date.today()))
    with col5:
        horario = st.time_input(
            "Horário",
            value=val("horario", datetime.now().time().replace(second=0, microsecond=0))
        )

    st.divider()
    st.markdown("## Equipe")

    dirigente1 = st.text_input("Dirigente", value=val("dirigente1"))
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dirigente2 = st.text_input("Dirigente 2", value=val("dirigente2"))
    with col_d2:
        dirigente3 = st.text_input("Dirigente 3", value=val("dirigente3"))

    st.divider()

    portaria1 = st.text_input("Portaria", value=val("portaria1"))
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        portaria2 = st.text_input("Portaria 2", value=val("portaria2"))
    with col_p2:
        portaria3 = st.text_input("Portaria 3", value=val("portaria3"))

    st.divider()

    recepcao1 = st.text_input("Recepção", value=val("recepcao1"))
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        recepcao2 = st.text_input("Recepção 2", value=val("recepcao2"))
    with col_r2:
        recepcao3 = st.text_input("Recepção 3", value=val("recepcao3"))

    st.divider()
    secretaria = st.text_input("Secretaria", value=val("secretaria"))
    observacoes = st.text_area("Observações", value=val("observacoes"), height=80)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        salvar = st.button("Salvar", type="primary", use_container_width=True)
    with col_s2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.edit_id = None
        st.session_state.page = "Agenda da Semana"
        st.rerun()

    if salvar:
        payload = {
            "congregacao": congregacao,
            "tipo": tipo,
            "subtipo": subtipo or None,
            "turma_ebd": turma_ebd or None,
            "data": data_evento,
            "horario": horario,
            "dirigente1": dirigente1 or None,
            "dirigente2": dirigente2 or None,
            "dirigente3": dirigente3 or None,
            "portaria1": portaria1 or None,
            "portaria2": portaria2 or None,
            "portaria3": portaria3 or None,
            "recepcao1": recepcao1 or None,
            "recepcao2": recepcao2 or None,
            "recepcao3": recepcao3 or None,
            "secretaria": secretaria or None,
            "observacoes": observacoes or None,
        }

        if edit_id:
            update_event(edit_id, payload)
            st.success("Evento atualizado.")
        else:
            create_event(payload)
            st.success("Evento cadastrado.")

        st.session_state.edit_id = None
        st.session_state.page = "Agenda da Semana"
        st.rerun()

# =========================
# Agenda da Semana
# =========================
def page_agenda_semana():
    st.markdown("# Agenda da Semana")

    col1, col2, col3 = st.columns(3)
    with col1:
        ref = st.date_input("Semana de referência", value=date.today())
    monday, sunday = week_bounds(ref)

    with col2:
        congregacao = st.selectbox("Congregação", ["Todas"] + CONGREGACOES)
    with col3:
        tipo = st.selectbox("Tipo", ["Todos"] + TIPOS)

    eventos = list_events_between(
        monday,
        sunday,
        congregacao=None if congregacao == "Todas" else congregacao,
        tipo=None if tipo == "Todos" else tipo
    )

    if not eventos:
        st.info("Nenhum evento cadastrado nesta semana.")
        return

    df = pd.DataFrame(eventos)
    df["Data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")
    df["Horário"] = df["horario"].astype(str).str[:5]
    df["Tipo"] = df.apply(lambda r: format_tipo(r.to_dict()), axis=1)

    def join_people(*args):
        return ", ".join([a for a in args if a])

    df["Dirigente"] = df.apply(lambda r: join_people(r.dirigente1, r.dirigente2, r.dirigente3), axis=1)
    df["Portaria"] = df.apply(lambda r: join_people(r.portaria1, r.portaria2, r.portaria3), axis=1)
    df["Recepção"] = df.apply(lambda r: join_people(r.recepcao1, r.recepcao2, r.recepcao3), axis=1)

    view = df[[
        "Data", "Horário", "congregacao", "Tipo",
        "Dirigente", "Portaria", "Recepção", "secretaria"
    ]].rename(columns={
        "congregacao": "Congregação",
        "secretaria": "Secretaria"
    })

    st.dataframe(view, use_container_width=True, hide_index=True)

    png = df_to_png_bytes(
        view,
        title=f"Agenda {monday.strftime('%d/%m/%Y')} a {sunday.strftime('%d/%m/%Y')}"
    )

    if png:
        st.download_button(
            "Exportar agenda em PNG",
            data=png,
            file_name="agenda_semana.png",
            mime="image/png",
            use_container_width=True
        )

# =========================
# Gerenciar Eventos
# =========================
def page_gerenciar_eventos():
    st.markdown("# Gerenciar Eventos")

    col1, col2 = st.columns(2)
    with col1:
        dt_ini = st.date_input("Data inicial", value=date.today() - timedelta(days=30))
    with col2:
        dt_fim = st.date_input("Data final", value=date.today() + timedelta(days=60))

    eventos = list_events_between(dt_ini, dt_fim)

    if not eventos:
        st.info("Nenhum evento encontrado.")
        return

    df = pd.DataFrame(eventos)
    df["Data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")
    df["Horário"] = df["horario"].astype(str).str[:5]
    df["Tipo"] = df.apply(lambda r: format_tipo(r.to_dict()), axis=1)

    st.dataframe(
        df[["id", "Data", "Horário", "congregacao", "Tipo"]],
        use_container_width=True,
        hide_index=True
    )

    selected = st.selectbox("Selecione o ID do evento", df["id"].tolist())

    colA, colB = st.columns(2)
    with colA:
        if st.button("Editar", use_container_width=True):
            st.session_state.edit_id = selected
            st.session_state.page = "Cadastrar Evento"
            st.rerun()
    with colB:
        if st.button("Excluir", use_container_width=True):
            delete_event(selected)
            st.success("Evento excluído.")
            st.rerun()

# =========================
# Main
# =========================
def main():
    init_state()
    init_auth()
    init_events()

    sidebar()

    if not st.session_state.auth_ok:
        page_login()
        return

    page = st.session_state.page

    if page == "Cadastrar Evento":
        page_cadastrar_evento()
    elif page == "Gerenciar Eventos":
        page_gerenciar_eventos()
    else:
        page_agenda_semana()

if __name__ == "__main__":
    main()
