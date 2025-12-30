# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from agenda_igreja.db import test_db_connection
from agenda_igreja.auth import (
    init_auth,
    authenticate,
    has_role,
    create_user,
    list_users,
    set_user_active,
    reset_password,
    ROLES
)
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

LOGO_URL = "https://i.ibb.co/jZkYm687/logo-adtce.jpg"
IGREJA_NOME = "Igreja Assembleia de Deus Templo Centra | Quixeramobim-Ce"

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Agenda da Igreja",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"  # 1) Sidebar collapsed
)

# =========================
# Estilo (dark blue palette)
# =========================
def apply_css():
    st.markdown(
        """
        <style>
          :root{
            --bg0:#070B16;
            --bg1:#0B1022;
            --card:#0E1733;
            --card2:#0B132C;
            --stroke:rgba(255,255,255,0.10);
            --stroke2:rgba(255,255,255,0.16);
            --txt:#EAF0FF;
            --muted:rgba(234,240,255,0.72);
            --muted2:rgba(234,240,255,0.56);
            --brand:#1C4ED8;
            --brand2:#3B82F6;
            --good:#22C55E;
            --warn:#F59E0B;
            --bad:#EF4444;
            --shadow: 0 18px 55px rgba(0,0,0,0.35);
          }

          .stApp{
            background:
              radial-gradient(1000px 600px at 10% 0%, rgba(59,130,246,0.18), transparent 60%),
              radial-gradient(900px 600px at 100% 10%, rgba(28,78,216,0.22), transparent 55%),
              linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 100%);
            color: var(--txt);
          }

          .block-container{
            padding-top: 1.05rem;
            padding-bottom: 2rem;
            max-width: 1400px;
          }

          /* Sidebar */
          [data-testid="stSidebar"]{
            background: linear-gradient(180deg, rgba(14,23,51,0.92), rgba(11,16,34,0.92));
            border-right: 1px solid var(--stroke);
          }
          [data-testid="stSidebar"] *{
            color: var(--txt);
          }

          /* Inputs */
          .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
          .stDateInput input, .stTimeInput input{
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid var(--stroke) !important;
            color: var(--txt) !important;
            border-radius: 14px !important;
          }
          .stTextInput input::placeholder, .stTextArea textarea::placeholder{
            color: rgba(234,240,255,0.45) !important;
          }

          /* Buttons */
          .stButton > button{
            background: linear-gradient(135deg, rgba(28,78,216,0.95), rgba(59,130,246,0.95)) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: white !important;
            border-radius: 14px !important;
            padding: 0.7rem 1rem !important;
            font-weight: 800 !important;
            box-shadow: 0 12px 30px rgba(28,78,216,0.28);
            transition: transform .12s ease, filter .12s ease;
          }
          .stButton > button:hover{
            filter: brightness(1.06);
            transform: translateY(-1px);
          }

          /* Primary button (Streamlit type="primary") */
          button[kind="primary"]{
            background: linear-gradient(135deg, rgba(28,78,216,1), rgba(59,130,246,1)) !important;
          }

          /* Cards */
          .soft-card{
            background: linear-gradient(180deg, rgba(14,23,51,0.92), rgba(11,19,44,0.92));
            border: 1px solid var(--stroke);
            border-radius: 20px;
            padding: 16px;
            box-shadow: var(--shadow);
          }

          .topbar{
            background: linear-gradient(135deg, rgba(14,23,51,0.85), rgba(11,16,34,0.70));
            border: 1px solid var(--stroke);
            border-radius: 22px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: var(--shadow);
          }
          .topbar-row{
            display:flex;
            align-items:center;
            gap:14px;
          }
          .logo-wrap img{
            width: 62px;
            height: 62px;
            border-radius: 16px;
            object-fit: cover;
            border: 1px solid var(--stroke2);
          }
          .church-title{
            font-size: 1.05rem;
            font-weight: 900;
            margin: 0;
            line-height: 1.2;
            color: var(--txt);
          }
          .church-subtitle{
            font-size: 0.92rem;
            margin: 4px 0 0 0;
            color: var(--muted);
          }

          .chip{
            display:inline-block;
            padding: 0.2rem 0.62rem;
            border-radius: 999px;
            border: 1px solid var(--stroke);
            background: rgba(255,255,255,0.06);
            font-size: 0.78rem;
            font-weight: 800;
            margin-right: 6px;
            margin-bottom: 6px;
            color: rgba(234,240,255,0.92);
          }

          .event-card{
            background: linear-gradient(180deg, rgba(14,23,51,0.92), rgba(11,19,44,0.92));
            border: 1px solid var(--stroke);
            border-radius: 20px;
            padding: 14px;
            box-shadow: var(--shadow);
            margin-bottom: 10px;
          }
          .event-head{
            display:flex;
            justify-content: space-between;
            gap: 10px;
            align-items: baseline;
            margin-bottom: 6px;
          }
          .event-when{
            font-weight: 950;
            font-size: 0.96rem;
            color: rgba(234,240,255,0.95);
          }
          .event-where{
            font-weight: 850;
            font-size: 0.9rem;
            text-align: right;
            color: var(--muted);
          }
          .event-type{
            font-weight: 950;
            font-size: 1.06rem;
            margin: 6px 0 8px 0;
            color: rgba(234,240,255,0.98);
          }
          .event-people{
            font-size: 0.92rem;
            line-height: 1.35;
            color: rgba(234,240,255,0.92);
          }
          .muted{ color: var(--muted2); }
          .divider-soft{
            height: 1px;
            background: rgba(255,255,255,0.10);
            margin: 10px 0;
          }
          .section-title{
            font-size: 1.05rem;
            font-weight: 950;
            margin: 0;
            color: var(--txt);
          }
          .section-subtitle{
            margin: 6px 0 0 0;
            font-size: 0.92rem;
            color: var(--muted);
          }

          /* Segmented control (tabs no topo) */
          div[data-testid="stSegmentedControl"]{
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--stroke);
            border-radius: 18px;
            padding: 10px 10px;
            box-shadow: var(--shadow);
            margin-bottom: 14px;
          }
          div[data-testid="stSegmentedControl"] label{
            font-weight: 900 !important;
          }

          /* Dataframes */
          [data-testid="stDataFrame"]{
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--stroke);
            box-shadow: var(--shadow);
          }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_topbar():
    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-row">
            <div class="logo-wrap">
              <img src="{LOGO_URL}" />
            </div>
            <div>
              <p class="church-title">{IGREJA_NOME}</p>
              <p class="church-subtitle">Agenda semanal de eventos</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Estado inicial
# =========================
def init_state():
    st.session_state.setdefault("auth_ok", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Agenda Pública")
    st.session_state.setdefault("edit_id", None)

    st.session_state.setdefault("show_dirigentes_extra", False)
    st.session_state.setdefault("show_portaria_extra", False)
    st.session_state.setdefault("show_recepcao_extra", False)

# =========================
# Utilidades
# =========================
def week_bounds(ref: date):
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

def _fmt_date_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def _fmt_time_hhmm(t) -> str:
    try:
        return str(t)[:5]
    except Exception:
        return ""

def join_people(*args):
    return ", ".join([a for a in args if a])

def _chips(items):
    if not items:
        return ""
    return "".join([f"<span class='chip'>{x}</span>" for x in items if x])

def _event_card(ev: dict):
    data_txt = _fmt_date_br(pd.to_datetime(ev["data"]).date() if ev.get("data") else date.today())
    hora_txt = _fmt_time_hhmm(ev.get("horario"))
    congreg = ev.get("congregacao") or ""

    tipo_txt = format_tipo(ev)
    subtipo = ev.get("subtipo") or ""
    turma = ev.get("turma_ebd") or ""

    chips = []
    if subtipo:
        chips.append(f"Subtipo: {subtipo}")
    if turma:
        chips.append(f"Turma: {turma}")
    if ev.get("secretaria"):
        chips.append(f"Secretaria: {ev.get('secretaria')}")

    dirigentes = join_people(ev.get("dirigente1"), ev.get("dirigente2"), ev.get("dirigente3"))
    portaria = join_people(ev.get("portaria1"), ev.get("portaria2"), ev.get("portaria3"))
    recepcao = join_people(ev.get("recepcao1"), ev.get("recepcao2"), ev.get("recepcao3"))

    st.markdown(
        f"""
        <div class="event-card">
          <div class="event-head">
            <div class="event-when">{data_txt} • {hora_txt}</div>
            <div class="event-where">{congreg}</div>
          </div>
          <div class="event-type">{tipo_txt}</div>
          <div>{_chips(chips)}</div>
          <div class="divider-soft"></div>
          <div class="event-people">
            <div><b>Dirigentes:</b> <span class="muted">{dirigentes or "Não informado"}</span></div>
            <div><b>Portaria:</b> <span class="muted">{portaria or "Não informado"}</span></div>
            <div><b>Recepção:</b> <span class="muted">{recepcao or "Não informado"}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Sidebar (2) Botões Login e Agenda Pública
# =========================
def sidebar_quick_actions():
    with st.sidebar:
        st.markdown("### 📅 Agenda")

        ok, msg = test_db_connection()
        st.caption(msg)

        st.divider()

        # Botões pedidos
        colA, colB = st.columns(2)
        with colA:
            if st.button("Agenda Pública", use_container_width=True):
                st.session_state.page = "Agenda Pública"
                st.session_state.edit_id = None
                st.rerun()
        with colB:
            if st.button("Login", use_container_width=True):
                st.session_state.page = "Login"
                st.rerun()

        st.divider()

        if st.session_state.auth_ok:
            user = st.session_state.user or {}
            st.caption(f"Logado: {user.get('nome') or user.get('username')}")
            st.caption(f"Perfil: {user.get('perfil')}")
            if st.button("Sair", use_container_width=True):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()

        st.caption("Versão inicial da Agenda")

# =========================
# Top navigation (3) Abas no topo
# =========================
def top_nav():
    # Monta páginas disponíveis
    if st.session_state.auth_ok:
        pages = ["Agenda Pública", "Agenda da Semana", "Cadastrar Evento", "Gerenciar Eventos"]
        if has_role("ADMIN"):
            pages.append("Usuários")
    else:
        pages = ["Agenda Pública", "Login"]

    current = st.session_state.page if st.session_state.page in pages else pages[0]

    # Segmented control fica igual abas no topo, bem clean e moderno
    selected = st.segmented_control(
        label="",
        options=pages,
        default=current,
        selection_mode="single"
    )
    if selected and selected != st.session_state.page:
        st.session_state.page = selected
        st.session_state.edit_id = None
        st.rerun()

# =========================
# Login
# =========================
def page_login():
    st.markdown("## Login")
    st.write("Acesso restrito para cadastro e gerenciamento da agenda.")

    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="Seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Sua senha")
        submit = st.form_submit_button("Entrar", use_container_width=True)

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
# Agenda Pública (só leitura)
# =========================
def page_agenda_publica():
    st.markdown("## Agenda Pública")
    st.caption("Visualização pública. Sem edição.")

    colA, colB, colC = st.columns([1.1, 1.0, 0.9])
    with colA:
        ref = st.date_input("Semana de referência", value=date.today(), format="DD/MM/YYYY")
    monday, sunday = week_bounds(ref)

    with colB:
        congregacao = st.selectbox("Congregação", ["Todas"] + CONGREGACOES)
    with colC:
        modo = st.selectbox("Exibição", ["Cards", "Tabela"], index=0)

    eventos = list_events_between(
        monday,
        sunday,
        congregacao=None if congregacao == "Todas" else congregacao,
        tipo=None
    )

    st.markdown(
        f"<div class='soft-card'><b>Semana:</b> {_fmt_date_br(monday)} até {_fmt_date_br(sunday)}</div>",
        unsafe_allow_html=True
    )
    st.markdown("")

    if not eventos:
        st.info("Nenhum evento cadastrado nesta semana.")
        return

    df = pd.DataFrame(eventos)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    tab_culto, tab_ebd, tab_oracao, tab_ensaio = st.tabs(["Cultos", "EBD", "Oração", "Ensaios"])

    def render_group(tipo_nome: str, container):
        with container:
            sub = df[df["tipo"] == tipo_nome].copy()
            if sub.empty:
                st.info("Sem registros aqui nesta semana.")
                return

            if modo == "Tabela":
                view = sub.copy()
                view["Data"] = view["data"].apply(lambda x: x.strftime("%d/%m/%Y"))
                view["Horário"] = view["horario_txt"]
                view["Tipo"] = view.apply(lambda r: format_tipo(r.to_dict()), axis=1)

                view["Dirigentes"] = view.apply(
                    lambda r: join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3")), axis=1
                )
                view["Portaria"] = view.apply(
                    lambda r: join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3")), axis=1
                )
                view["Recepção"] = view.apply(
                    lambda r: join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3")), axis=1
                )

                show = view[["Data", "Horário", "congregacao", "Tipo", "Dirigentes", "Portaria", "Recepção", "secretaria"]]
                show = show.rename(columns={"congregacao": "Congregação", "secretaria": "Secretaria"})
                st.dataframe(show, use_container_width=True, hide_index=True)

                png = df_to_png_bytes(
                    show,
                    title=f"{tipo_nome} • {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"
                )
                if png:
                    st.download_button(
                        "Exportar esta aba em PNG",
                        data=png,
                        file_name=f"agenda_{tipo_nome.lower()}_{monday.strftime('%Y%m%d')}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                return

            for _, r in sub.iterrows():
                _event_card(r.to_dict())

    render_group("Culto", tab_culto)
    render_group("EBD", tab_ebd)
    render_group("Oração", tab_oracao)
    render_group("Ensaio", tab_ensaio)

# =========================
# Cadastro de Evento (Admin/Privado)
# =========================
def page_cadastrar_evento():
    st.markdown("## Cadastro de Evento")

    edit_id = st.session_state.edit_id
    ev = get_event(edit_id) if edit_id else None

    def val(key, default=None):
        if not ev:
            return default
        v = ev.get(key)
        return v if v is not None else default

    st.markdown(
        """
        <div class="soft-card">
          <p class="section-title">Dados do Evento</p>
          <p class="section-subtitle">Preencha as informações do evento. Os campos com * são obrigatórios.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("")

    col1, col2, col3 = st.columns(3)

    user = st.session_state.user or {}
    perfil = user.get("perfil")
    vinc = user.get("congregacao_vinculada")

    allowed_congregs = CONGREGACOES
    if perfil == "SECRETARIO" and vinc:
        allowed_congregs = [vinc]

    with col1:
        if ev and val("congregacao") in allowed_congregs:
            congregacao = st.selectbox(
                "🏛️ Congregação*",
                allowed_congregs,
                index=allowed_congregs.index(val("congregacao")),
                placeholder="Selecione a congregação"
            )
        else:
            congregacao = st.selectbox(
                "🏛️ Congregação*",
                allowed_congregs,
                index=None,
                placeholder="Selecione a congregação"
            )

    with col2:
        if ev and val("tipo") in TIPOS:
            tipo = st.selectbox(
                "📌 Tipo da agenda*",
                TIPOS,
                index=TIPOS.index(val("tipo")),
                placeholder="Escolha o tipo do evento"
            )
        else:
            tipo = st.selectbox(
                "📌 Tipo da agenda*",
                TIPOS,
                index=None,
                placeholder="Escolha o tipo do evento"
            )

    with col3:
        subtipo = None
        turma_ebd = None

        if (tipo == "Culto") or (ev and val("tipo") == "Culto" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "Culto":
                options = SUBTIPOS_CULTO
                current = val("subtipo")
                if ev and current in options:
                    subtipo = st.selectbox(
                        "✨ Subtipo do Culto",
                        options,
                        index=options.index(current),
                        placeholder="Selecione (opcional)"
                    )
                else:
                    subtipo = st.selectbox(
                        "✨ Subtipo do Culto",
                        options,
                        index=None,
                        placeholder="Selecione (opcional)"
                    )

        if (tipo == "EBD") or (ev and val("tipo") == "EBD" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "EBD":
                options = TURMAS_EBD
                current = val("turma_ebd")
                if ev and current in options:
                    turma_ebd = st.selectbox(
                        "📚 Turma da EBD*",
                        options,
                        index=options.index(current),
                        placeholder="Selecione a turma"
                    )
                else:
                    turma_ebd = st.selectbox(
                        "📚 Turma da EBD*",
                        options,
                        index=None,
                        placeholder="Selecione a turma"
                    )

    col4, col5 = st.columns(2)

    with col4:
        data_evento = st.date_input("📅 Data*", value=val("data", date.today()), format="DD/MM/YYYY")

    with col5:
        horario_default = datetime.strptime("19:00", "%H:%M").time()
        horario = st.time_input("🕖 Horário*", value=val("horario", horario_default))

    st.markdown(
        """
        <div class="soft-card" style="margin-top:14px;">
          <p class="section-title">Equipe do Evento</p>
          <p class="section-subtitle">Os campos 2 e 3 ficam ocultos. Clique no botão de adicionar se precisar.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("")

    st.markdown("### 👤 Dirigência")
    dirigente1 = st.text_input("👤 Dirigente", value=val("dirigente1", "") or "", placeholder="Nome do dirigente responsável")

    st.toggle("➕ Adicionar mais dirigentes", key="show_dirigentes_extra")
    if st.session_state.show_dirigentes_extra:
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dirigente2 = st.text_input("👥 Dirigente 2", value=val("dirigente2", "") or "", placeholder="Nome (opcional)")
        with col_d2:
            dirigente3 = st.text_input("👥 Dirigente 3", value=val("dirigente3", "") or "", placeholder="Nome (opcional)")
    else:
        dirigente2 = val("dirigente2", "") or ""
        dirigente3 = val("dirigente3", "") or ""

    st.markdown("<div class='divider-soft'></div>", unsafe_allow_html=True)

    st.markdown("### 🚪 Portaria")
    portaria1 = st.text_input("🚪 Portaria", value=val("portaria1", "") or "", placeholder="Nome do responsável pela portaria")

    st.toggle("➕ Adicionar mais na portaria", key="show_portaria_extra")
    if st.session_state.show_portaria_extra:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            portaria2 = st.text_input("🚪 Portaria 2", value=val("portaria2", "") or "", placeholder="Nome (opcional)")
        with col_p2:
            portaria3 = st.text_input("🚪 Portaria 3", value=val("portaria3", "") or "", placeholder="Nome (opcional)")
    else:
        portaria2 = val("portaria2", "") or ""
        portaria3 = val("portaria3", "") or ""

    st.markdown("<div class='divider-soft'></div>", unsafe_allow_html=True)

    st.markdown("### 🤝 Recepção")
    recepcao1 = st.text_input("🤝 Recepção", value=val("recepcao1", "") or "", placeholder="Nome do responsável pela recepção")

    st.toggle("➕ Adicionar mais na recepção", key="show_recepcao_extra")
    if st.session_state.show_recepcao_extra:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            recepcao2 = st.text_input("🤝 Recepção 2", value=val("recepcao2", "") or "", placeholder="Nome (opcional)")
        with col_r2:
            recepcao3 = st.text_input("🤝 Recepção 3", value=val("recepcao3", "") or "", placeholder="Nome (opcional)")
    else:
        recepcao2 = val("recepcao2", "") or ""
        recepcao3 = val("recepcao3", "") or ""

    st.markdown("<div class='divider-soft'></div>", unsafe_allow_html=True)

    secretaria = st.text_input("🗂️ Secretaria", value=val("secretaria", "") or "", placeholder="Nome do responsável (opcional)")
    observacoes = st.text_area("📝 Observações", value=val("observacoes", "") or "", placeholder="Observações (opcional)", height=90)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        salvar = st.button("💾 Salvar", type="primary", use_container_width=True)
    with col_s2:
        cancelar = st.button("↩️ Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.edit_id = None
        st.session_state.page = "Agenda da Semana"
        st.rerun()

    if salvar:
        if not congregacao:
            st.error("Selecione a Congregação.")
            return
        if not tipo:
            st.error("Selecione o Tipo da agenda.")
            return
        if tipo == "EBD" and not turma_ebd:
            st.error("Para EBD, selecione a Turma.")
            return

        payload = {
            "congregacao": congregacao,
            "tipo": tipo,
            "subtipo": (subtipo or None) if tipo == "Culto" else None,
            "turma_ebd": (turma_ebd or None) if tipo == "EBD" else None,
            "data": data_evento,
            "horario": horario,
            "dirigente1": (dirigente1 or "").strip() or None,
            "dirigente2": (dirigente2 or "").strip() or None,
            "dirigente3": (dirigente3 or "").strip() or None,
            "portaria1": (portaria1 or "").strip() or None,
            "portaria2": (portaria2 or "").strip() or None,
            "portaria3": (portaria3 or "").strip() or None,
            "recepcao1": (recepcao1 or "").strip() or None,
            "recepcao2": (recepcao2 or "").strip() or None,
            "recepcao3": (recepcao3 or "").strip() or None,
            "secretaria": (secretaria or "").strip() or None,
            "observacoes": (observacoes or "").strip() or None,
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
# Agenda da Semana (Privado)
# =========================
def page_agenda_semana():
    st.markdown("## Agenda da Semana")

    col1, col2, col3 = st.columns(3)
    with col1:
        ref = st.date_input("Semana de referência", value=date.today(), format="DD/MM/YYYY")
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

    df["Dirigente"] = df.apply(lambda r: join_people(r.dirigente1, r.dirigente2, r.dirigente3), axis=1)
    df["Portaria"] = df.apply(lambda r: join_people(r.portaria1, r.portaria2, r.portaria3), axis=1)
    df["Recepção"] = df.apply(lambda r: join_people(r.recepcao1, r.recepcao2, r.recepcao3), axis=1)

    view = df[["Data", "Horário", "congregacao", "Tipo", "Dirigente", "Portaria", "Recepção", "secretaria"]].rename(
        columns={"congregacao": "Congregação", "secretaria": "Secretaria"}
    )

    st.dataframe(view, use_container_width=True, hide_index=True)

    png = df_to_png_bytes(view, title=f"Agenda {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}")
    if png:
        st.download_button(
            "Exportar agenda em PNG",
            data=png,
            file_name="agenda_semana.png",
            mime="image/png",
            use_container_width=True
        )

# =========================
# Gerenciar Eventos (Privado)
# =========================
def page_gerenciar_eventos():
    st.markdown("## Gerenciar Eventos")

    col1, col2 = st.columns(2)
    with col1:
        dt_ini = st.date_input("Data inicial", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
    with col2:
        dt_fim = st.date_input("Data final", value=date.today() + timedelta(days=60), format="DD/MM/YYYY")

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
# Usuários (ADMIN)
# =========================
def page_usuarios():
    st.markdown("## Usuários")
    st.caption("Apenas administrador consegue cadastrar e gerenciar usuários.")

    if not has_role("ADMIN"):
        st.error("Acesso negado. Esta área é somente para ADMIN.")
        return

    tab1, tab2 = st.tabs(["Cadastrar usuário", "Gerenciar usuários"])

    with tab1:
        st.markdown(
            """
            <div class="soft-card">
              <p class="section-title">Novo Usuário</p>
              <p class="section-subtitle">Crie um novo acesso. Para SECRETARIO, escolha a congregação vinculada.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("")

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("👤 Nome*", placeholder="Nome completo")
        with col2:
            username = st.text_input("🆔 Usuário*", placeholder="Ex: joao.silva")

        col3, col4 = st.columns(2)
        with col3:
            senha = st.text_input("🔑 Senha*", type="password", placeholder="Defina uma senha")
        with col4:
            perfil = st.selectbox(
                "🎚️ Perfil*",
                ROLES,
                index=None,
                placeholder="Escolha o perfil"
            )

        congreg_vinc = None
        if perfil == "SECRETARIO":
            congreg_vinc = st.selectbox(
                "🏛️ Congregação vinculada*",
                CONGREGACOES,
                index=None,
                placeholder="Secretário só mexe nesta congregação"
            )

        if st.button("✅ Criar usuário", type="primary", use_container_width=True):
            if not nome.strip():
                st.error("Informe o nome.")
                return
            if not username.strip():
                st.error("Informe o usuário.")
                return
            if not senha:
                st.error("Informe a senha.")
                return
            if not perfil:
                st.error("Selecione o perfil.")
                return
            try:
                create_user(nome, username, senha, perfil, congreg_vinc)
                st.success("Usuário criado.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao criar usuário: {e}")

    with tab2:
        users = list_users()
        if not users:
            st.info("Ainda não há usuários cadastrados.")
            return

        df = pd.DataFrame(users)
        df["criado_em"] = pd.to_datetime(df["criado_em"]).dt.strftime("%d/%m/%Y %H:%M")
        df = df.rename(columns={
            "id": "ID",
            "username": "Usuário",
            "nome": "Nome",
            "perfil": "Perfil",
            "congregacao_vinculada": "Congregação Vinculada",
            "ativo": "Ativo",
            "criado_em": "Criado em",
        })

        st.dataframe(df, use_container_width=True, hide_index=True)

        ids = df["ID"].tolist()
        sel = st.selectbox("Selecione o usuário pelo ID", ids)

        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("🔒 Desativar", use_container_width=True):
                set_user_active(int(sel), False)
                st.success("Usuário desativado.")
                st.rerun()
        with colB:
            if st.button("🔓 Ativar", use_container_width=True):
                set_user_active(int(sel), True)
                st.success("Usuário ativado.")
                st.rerun()
        with colC:
            nova = st.text_input("Nova senha (reset)", type="password", placeholder="Digite uma nova senha")
            if st.button("♻️ Resetar senha", use_container_width=True):
                if not nova:
                    st.error("Digite a nova senha.")
                else:
                    reset_password(int(sel), nova)
                    st.success("Senha atualizada.")
                    st.rerun()

# =========================
# Main
# =========================
def main():
    apply_css()
    init_state()
    init_auth()
    init_events()

    render_topbar()

    # Sidebar enxuta com os botões pedidos
    sidebar_quick_actions()

    # Abas no topo (nav principal)
    top_nav()

    page = st.session_state.page

    if page == "Agenda Pública":
        page_agenda_publica()
        return

    if page == "Login":
        page_login()
        return

    if not st.session_state.auth_ok:
        st.warning("Você precisa estar logado para acessar esta área.")
        page_login()
        return

    if page == "Cadastrar Evento":
        page_cadastrar_evento()
    elif page == "Gerenciar Eventos":
        page_gerenciar_eventos()
    elif page == "Usuários":
        page_usuarios()
    else:
        page_agenda_semana()

if __name__ == "__main__":
    main()
