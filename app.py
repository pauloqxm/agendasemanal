import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, time

from agenda_igreja.db import test_db_connection
from agenda_igreja.auth import (
    init_auth,
    authenticate,
    has_role,
    create_user,
    list_users,
    set_user_active,
    reset_password
)
from agenda_igreja.events import (
    init_events,
    create_event,
    update_event,
    delete_event,
    get_event,
    list_events_between,
    list_event_logs
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
    page_title="Agenda ADTCE",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOGO_URL = "https://i.ibb.co/jZkYm687/logo-adtce.jpg"
IGREJA_NOME = "Igreja Assembleia de Deus Templo Central | Quixeramobim-CE"

# =========================
# Estado inicial
# =========================
def init_state():
    st.session_state.setdefault("auth_ok", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Agenda Pública")
    st.session_state.setdefault("edit_id", None)

# =========================
# Sidebar
# =========================
def sidebar():
    with st.sidebar:
        st.image(LOGO_URL, use_container_width=True)
        st.markdown(f"**{IGREJA_NOME}**")
        st.divider()

        ok, msg = test_db_connection()
        st.caption(msg)

        if st.session_state.auth_ok:
            user = st.session_state.user
            st.markdown(f"👤 **{user.get('nome')}**")
            st.caption(f"Perfil: {user.get('perfil')}")

            pages = ["Agenda Pública", "Agenda da Semana"]

            if has_role("ADMIN", "PASTOR", "DIRIGENTE", "SECRETARIO"):
                pages.append("Cadastrar Evento")

            if has_role("ADMIN", "PASTOR"):
                pages.append("Gerenciar Eventos")
                pages.append("Histórico")

            if has_role("ADMIN"):
                pages.append("Usuários")

            st.divider()
            st.session_state.page = st.radio("Navegação", pages)

            st.divider()
            if st.button("Sair", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        else:
            st.session_state.page = st.radio(
                "Navegação",
                ["Agenda Pública", "Login"]
            )

# =========================
# Login
# =========================
def page_login():
    st.markdown("## 🔐 Login")
    with st.form("login"):
        username = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        ok = st.form_submit_button("Entrar")

    if ok:
        success, user = authenticate(username, password)
        if success:
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
def week_bounds(ref):
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

# =========================
# Agenda Pública (somente leitura)
# =========================
def page_agenda_publica():
    st.markdown("## 📅 Agenda Pública")

    col1, col2 = st.columns(2)
    with col1:
        ref = st.date_input("Semana de referência", value=date.today())
    monday, sunday = week_bounds(ref)

    eventos = list_events_between(monday, sunday)

    if not eventos:
        st.info("Nenhum evento programado para esta semana.")
        return

    df = pd.DataFrame(eventos)
    df["Data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")
    df["Horário"] = df["horario"].astype(str).str[:5]
    df["Tipo"] = df.apply(lambda r: format_tipo(r.to_dict()), axis=1)

    st.markdown("### Programação")
    for tipo in TIPOS:
        bloco = df[df["tipo"] == tipo]
        if bloco.empty:
            continue

        st.markdown(f"### {tipo}")
        for _, r in bloco.iterrows():
            st.markdown(
                f"**{r['Data']} • {r['Horário']}**  \n"
                f"{r['Tipo']}  \n"
                f"📍 {r['congregacao']}"
            )
            st.divider()

# =========================
# Cadastro de Evento
# =========================
def page_cadastrar_evento():
    st.markdown("## ➕ Cadastro de Evento")

    user = st.session_state.user
    edit_id = st.session_state.edit_id
    ev = get_event(edit_id) if edit_id else {}

    def val(k, d=None): return ev.get(k, d)

    # Separação visual
    st.markdown("### 📌 Dados do Evento")

    col1, col2, col3 = st.columns(3)

    with col1:
        if user["perfil"] == "SECRETARIO":
            congregacao = st.selectbox(
                "🏛️ Congregação*",
                [user["congregacao_vinculada"]],
                index=0,
                disabled=True
            )
        else:
            congregacao = st.selectbox(
                "🏛️ Congregação*",
                CONGREGACOES,
                index=None,
                placeholder="Selecione a congregação"
            )

    with col2:
        tipo = st.selectbox(
            "📌 Tipo da agenda*",
            TIPOS,
            index=None,
            placeholder="Selecione o tipo"
        )

    with col3:
        subtipo = None
        turma_ebd = None
        if tipo == "Culto":
            subtipo = st.selectbox(
                "✨ Subtipo do culto",
                SUBTIPOS_CULTO,
                index=None,
                placeholder="Opcional"
            )
        elif tipo == "EBD":
            turma_ebd = st.selectbox(
                "📚 Turma EBD",
                TURMAS_EBD,
                index=None,
                placeholder="Selecione a turma"
            )

    col4, col5 = st.columns(2)
    with col4:
        data_evento = st.date_input("📅 Data*", value=val("data", date.today()))
    with col5:
        horario = st.time_input(
            "⏰ Horário*",
            value=val("horario", time(19, 0))
        )

    st.divider()
    st.markdown("### 👥 Equipe")

    dirigente1 = st.text_input("👤 Dirigente*", placeholder="Nome do dirigente")
    with st.expander("➕ Adicionar mais dirigentes"):
        dirigente2 = st.text_input("Dirigente 2")
        dirigente3 = st.text_input("Dirigente 3")

    portaria1 = st.text_input("🚪 Portaria*", placeholder="Responsável")
    with st.expander("➕ Adicionar mais portaria"):
        portaria2 = st.text_input("Portaria 2")
        portaria3 = st.text_input("Portaria 3")

    recepcao1 = st.text_input("🤝 Recepção*", placeholder="Responsável")
    with st.expander("➕ Adicionar mais recepção"):
        recepcao2 = st.text_input("Recepção 2")
        recepcao3 = st.text_input("Recepção 3")

    secretaria = st.text_input("🗂️ Secretaria", placeholder="Responsável")

    observacoes = st.text_area("📝 Observações")

    if st.button("Salvar evento", type="primary", use_container_width=True):
        if not congregacao or not tipo:
            st.error("Preencha os campos obrigatórios.")
            return

        payload = {
            "congregacao": congregacao,
            "tipo": tipo,
            "subtipo": subtipo,
            "turma_ebd": turma_ebd,
            "data": data_evento,
            "horario": horario,
            "dirigente1": dirigente1,
            "dirigente2": dirigente2,
            "dirigente3": dirigente3,
            "portaria1": portaria1,
            "portaria2": portaria2,
            "portaria3": portaria3,
            "recepcao1": recepcao1,
            "recepcao2": recepcao2,
            "recepcao3": recepcao3,
            "secretaria": secretaria,
            "observacoes": observacoes
        }

        if edit_id:
            update_event(edit_id, payload, usuario_id=user["id"])
            st.success("Evento atualizado.")
        else:
            create_event(payload, usuario_id=user["id"])
            st.success("Evento cadastrado.")

        st.session_state.page = "Agenda da Semana"
        st.session_state.edit_id = None
        st.rerun()

# =========================
# Gerenciar Eventos
# =========================
def page_gerenciar_eventos():
    st.markdown("## 🛠️ Gerenciar Eventos")

    col1, col2 = st.columns(2)
    with col1:
        ini = st.date_input("Data inicial", date.today() - timedelta(days=30))
    with col2:
        fim = st.date_input("Data final", date.today() + timedelta(days=60))

    eventos = list_events_between(ini, fim)
    if not eventos:
        st.info("Nenhum evento encontrado.")
        return

    df = pd.DataFrame(eventos)
    df["Data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")
    df["Horário"] = df["horario"].astype(str).str[:5]
    df["Tipo"] = df.apply(lambda r: format_tipo(r.to_dict()), axis=1)

    st.dataframe(df[["id","Data","Horário","congregacao","Tipo"]], hide_index=True)

    eid = st.selectbox("Selecione o evento pelo ID", df["id"].tolist())

    colA, colB = st.columns(2)
    with colA:
        if st.button("Editar"):
            st.session_state.edit_id = eid
            st.session_state.page = "Cadastrar Evento"
            st.rerun()
    with colB:
        if st.button("Excluir"):
            delete_event(eid, usuario_id=st.session_state.user["id"])
            st.success("Evento excluído.")
            st.rerun()

# =========================
# Histórico
# =========================
def page_historico():
    st.markdown("## 🧾 Histórico de Alterações")

    ini = date.today() - timedelta(days=30)
    fim = date.today() + timedelta(days=30)

    eventos = list_events_between(ini, fim)
    if not eventos:
        st.info("Sem registros.")
        return

    df = pd.DataFrame(eventos)
    df["label"] = df.apply(
        lambda r: f"#{r['id']} | {r['congregacao']} | {r['tipo']} | {r['data']}",
        axis=1
    )

    eid = st.selectbox(
        "Evento",
        df["id"].tolist(),
        format_func=lambda x: df.loc[df["id"]==x, "label"].values[0]
    )

    logs = list_event_logs(eid)
    if not logs:
        st.info("Sem histórico.")
        return

    for l in logs:
        st.markdown(f"**{l['acao']}** em {l['data_acao']}")
        st.json(l["depois"] or l["antes"])
        st.divider()

# =========================
# Usuários
# =========================
def page_usuarios():
    st.markdown("## 👥 Usuários")

    with st.expander("➕ Novo usuário", expanded=True):
        with st.form("novo_user"):
            nome = st.text_input("Nome")
            username = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["ADMIN","PASTOR","DIRIGENTE","SECRETARIO"], index=None)
            congregacao = None
            if perfil == "SECRETARIO":
                congregacao = st.selectbox("Congregação vinculada", CONGREGACOES, index=None)

            ok = st.form_submit_button("Salvar")
        if ok:
            create_user(nome, username, senha, perfil, congregacao)
            st.success("Usuário criado.")
            st.rerun()

    users = list_users()
    st.dataframe(pd.DataFrame(users), hide_index=True)

# =========================
# Main
# =========================
def main():
    init_state()
    init_auth()
    init_events()

    sidebar()

    page = st.session_state.page

    if page == "Login":
        page_login()
    elif page == "Agenda Pública":
        page_agenda_publica()
    elif page == "Agenda da Semana":
        page_agenda_publica()
    elif page == "Cadastrar Evento":
        page_cadastrar_evento()
    elif page == "Gerenciar Eventos":
        page_gerenciar_eventos()
    elif page == "Histórico":
        page_historico()
    elif page == "Usuários":
        page_usuarios()

if __name__ == "__main__":
    main()
