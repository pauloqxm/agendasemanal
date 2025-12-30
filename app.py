# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, time as dtime

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
    initial_sidebar_state="expanded"
)

# =========================
# Estilo (visual mais profissional)
# =========================
def apply_css():
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px; }
          [data-testid="stSidebar"] { border-right: 1px solid rgba(0,0,0,0.06); }
          .soft-card {
            background: #ffffff;
            border: 1px solid rgba(0,0,0,0.06);
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
          }
          .topbar {
            background: linear-gradient(135deg, rgba(0,0,0,0.05), rgba(0,0,0,0.00));
            border: 1px solid rgba(0,0,0,0.06);
            border-radius: 20px;
            padding: 14px 16px;
            margin-bottom: 14px;
          }
          .topbar-row {
            display: flex;
            align-items: center;
            gap: 14px;
          }
          .logo-wrap img {
            width: 62px;
            height: 62px;
            border-radius: 16px;
            object-fit: cover;
            border: 1px solid rgba(0,0,0,0.08);
          }
          .church-title {
            font-size: 1.05rem;
            font-weight: 900;
            margin: 0;
            line-height: 1.2;
          }
          .church-subtitle {
            font-size: 0.9rem;
            opacity: 0.75;
            margin: 4px 0 0 0;
          }
          .chip {
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border-radius: 999px;
            border: 1px solid rgba(0,0,0,0.10);
            background: rgba(0,0,0,0.03);
            font-size: 0.78rem;
            font-weight: 800;
            margin-right: 6px;
            margin-bottom: 6px;
          }
          .event-card {
            background: #ffffff;
            border: 1px solid rgba(0,0,0,0.06);
            border-radius: 18px;
            padding: 14px 14px;
            box-shadow: 0 10px 28px rgba(0,0,0,0.06);
            margin-bottom: 10px;
          }
          .event-head {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            align-items: baseline;
            margin-bottom: 6px;
          }
          .event-when {
            font-weight: 900;
            font-size: 0.95rem;
          }
          .event-where {
            font-weight: 900;
            opacity: 0.8;
            font-size: 0.9rem;
            text-align: right;
          }
          .event-type {
            font-weight: 900;
            font-size: 1.05rem;
            margin: 6px 0 8px 0;
          }
          .event-people {
            font-size: 0.92rem;
            opacity: 0.92;
            line-height: 1.35;
          }
          .muted { opacity: 0.72; }
          .divider-soft { height: 1px; background: rgba(0,0,0,0.06); margin: 10px 0; }
          .section-title {
            font-size: 1.05rem;
            font-weight: 900;
            margin: 0;
          }
          .section-subtitle {
            opacity: 0.72;
            margin: 6px 0 0 0;
            font-size: 0.92rem;
          }
          .small-note {
            font-size: 0.85rem;
            opacity: 0.75;
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
# Helpers de permissão
# =========================
def current_user():
    return st.session_state.get("user") or {}

def user_role():
    return (current_user().get("perfil") or "").upper()

def user_congregacao_vinculada():
    return current_user().get("congregacao_vinculada")

def can_manage_events() -> bool:
    return st.session_state.get("auth_ok") and has_role("ADMIN", "PASTOR", "DIRIGENTE", "SECRETARIO")

def can_manage_users() -> bool:
    return st.session_state.get("auth_ok") and has_role("ADMIN")

def enforce_secretario_congregacao(selected_congregacao: str | None) -> bool:
    """
    Retorna True se permitido. Secretário só mexe na congregação vinculada.
    """
    if user_role() != "SECRETARIO":
        return True
    vinc = user_congregacao_vinculada()
    return bool(vinc) and (selected_congregacao == vinc)

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
    safe = [x for x in items if x]
    return "".join([f"<span class='chip'>{x}</span>" for x in safe])

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
# Sidebar
# =========================
def sidebar():
    with st.sidebar:
        st.markdown("## 📅 Agenda")

        ok, msg = test_db_connection()
        st.caption(msg)

        st.divider()

        if st.session_state.auth_ok:
            user = current_user()
            st.markdown(f"**Usuário:** {user.get('nome') or user.get('username')}")
            st.caption(f"Perfil: **{user_role() or '—'}**")

            if user_role() == "SECRETARIO":
                st.caption(f"Congregação vinculada: **{user_congregacao_vinculada() or '—'}**")

            pages = ["Agenda Pública", "Agenda da Semana", "Cadastrar Evento", "Gerenciar Eventos"]
            if can_manage_users():
                pages.append("Usuários")

            st.session_state.page = st.radio(
                "Navegação",
                pages,
                index=pages.index(st.session_state.page) if st.session_state.page in pages else 0
            )

            st.divider()
            if st.button("Sair", use_container_width=True):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()
        else:
            pages = ["Agenda Pública", "Login"]
            st.session_state.page = st.radio(
                "Navegação",
                pages,
                index=pages.index(st.session_state.page) if st.session_state.page in pages else 0
            )

        st.divider()
        st.caption("Agenda da Igreja • versão inicial")

# =========================
# Login
# =========================
def page_login():
    st.markdown("## Login")
    st.write("Acesso restrito para cadastro e gerenciamento da agenda.")

    with st.form("login_form"):
        username = st.text_input("👤 Usuário*", placeholder="Digite seu usuário")
        password = st.text_input("🔒 Senha*", type="password", placeholder="Digite sua senha")
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
            st.error("Usuário ou senha inválidos, ou conta inativa.")

# =========================
# Agenda Pública (só leitura)
# =========================
def page_agenda_publica():
    st.markdown("## Agenda Pública")
    st.caption("Visualização pública. Sem edição.")

    colA, colB, colC = st.columns([1.1, 1.0, 0.9])
    with colA:
        ref = st.date_input("📅 Semana de referência", value=date.today(), format="DD/MM/YYYY")
    monday, sunday = week_bounds(ref)

    with colB:
        congregacao = st.selectbox(
            "🏛️ Congregação",
            ["Todas"] + CONGREGACOES,
            index=0,
        )
    with colC:
        modo = st.selectbox("👀 Exibição", ["Cards", "Tabela"], index=0)

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
                        "📸 Exportar esta aba em PNG",
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
# Cadastro de Evento (Admin)
# =========================
def page_cadastrar_evento():
    st.markdown("## Cadastro de Evento")

    if not can_manage_events():
        st.error("Você não tem permissão para cadastrar/editar eventos.")
        return

    edit_id = st.session_state.edit_id
    ev = get_event(edit_id) if edit_id else None

    def val(key, default=None):
        if not ev:
            return default
        v = ev.get(key)
        return v if v is not None else default

    # Card topo
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

    # Se Secretário: congregação travada e validada
    secretario_vinc = user_congregacao_vinculada() if user_role() == "SECRETARIO" else None
    if user_role() == "SECRETARIO" and not secretario_vinc:
        st.error("Seu perfil é SECRETARIO, mas você não tem congregação vinculada. Peça ao ADMIN para ajustar.")
        return

    col1, col2, col3 = st.columns(3)

    # Congregação
    with col1:
        if user_role() == "SECRETARIO":
            # travado
            congregacao = st.selectbox(
                "🏛️ Congregação*",
                [secretario_vinc],
                index=0,
                disabled=True
            )
        else:
            if ev and val("congregacao") in CONGREGACOES:
                congregacao = st.selectbox(
                    "🏛️ Congregação*",
                    CONGREGACOES,
                    index=CONGREGACOES.index(val("congregacao")),
                    placeholder="Selecione a congregação"
                )
            else:
                congregacao = st.selectbox(
                    "🏛️ Congregação*",
                    CONGREGACOES,
                    index=None,
                    placeholder="Selecione a congregação"
                )

    # Tipo
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

    # Subtipo/Turma (dinâmico)
    with col3:
        subtipo = None
        turma_ebd = None

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

    # Data
    with col4:
        data_evento = st.date_input(
            "📅 Data*",
            value=val("data", date.today()),
            format="DD/MM/YYYY"
        )

    # Horário (default 19:00)
    with col5:
        horario_default = dtime(hour=19, minute=0)
        horario = st.time_input(
            "🕖 Horário*",
            value=val("horario", horario_default)
        )

    # Separação bonita entre evento e equipe
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

    # Dirigência
    st.markdown("### 👤 Dirigência")
    dirigente1 = st.text_input(
        "👤 Dirigente*",
        value=val("dirigente1", "") or "",
        placeholder="Nome do dirigente responsável"
    )

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

    # Portaria
    st.markdown("### 🚪 Portaria")
    portaria1 = st.text_input(
        "🚪 Portaria*",
        value=val("portaria1", "") or "",
        placeholder="Nome do responsável pela portaria"
    )

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

    # Recepção
    st.markdown("### 🤝 Recepção")
    recepcao1 = st.text_input(
        "🤝 Recepção*",
        value=val("recepcao1", "") or "",
        placeholder="Nome do responsável pela recepção"
    )

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

    secretaria = st.text_input(
        "🗂️ Secretaria",
        value=val("secretaria", "") or "",
        placeholder="Nome do responsável pela secretaria (opcional)"
    )
    observacoes = st.text_area(
        "📝 Observações",
        value=val("observacoes", "") or "",
        placeholder="Escreva observações importantes (opcional)",
        height=90
    )

    # trava de permissão do secretário no salvar/editar
    if user_role() == "SECRETARIO":
        if not enforce_secretario_congregacao(congregacao):
            st.error("Secretário(a) só pode operar a congregação vinculada.")
            return
        st.caption("🔒 Seu perfil é SECRETARIO. A congregação fica vinculada e não pode ser alterada.")

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
        # validações
        if not congregacao:
            st.error("Selecione a Congregação.")
            return
        if not tipo:
            st.error("Selecione o Tipo da agenda.")
            return
        if tipo_eff == "EBD" and not turma_ebd:
            st.error("Para EBD, selecione a Turma.")
            return
        if not data_evento:
            st.error("Selecione a Data.")
            return
        if not horario:
            st.error("Selecione o Horário.")
            return

        # Secretário: valida de novo
        if user_role() == "SECRETARIO" and not enforce_secretario_congregacao(congregacao):
            st.error("Secretário(a) só pode cadastrar/editar eventos da congregação vinculada.")
            return

        payload = {
            "congregacao": congregacao,
            "tipo": tipo_eff,
            "subtipo": (subtipo or None) if tipo_eff == "Culto" else None,
            "turma_ebd": (turma_ebd or None) if tipo_eff == "EBD" else None,
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

        # Se editando, Secretário só pode editar se evento for da congregação dele
        if edit_id and user_role() == "SECRETARIO":
            ev_db = get_event(edit_id)
            if ev_db and ev_db.get("congregacao") != secretario_vinc:
                st.error("Você não pode editar evento de outra congregação.")
                return

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
# Agenda da Semana (Admin)
# =========================
def page_agenda_semana():
    st.markdown("## Agenda da Semana")

    if not can_manage_events():
        st.info("Apenas usuários logados podem acessar esta área.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        ref = st.date_input("📅 Semana de referência", value=date.today(), format="DD/MM/YYYY")
    monday, sunday = week_bounds(ref)

    # Secretário: força congregação vinculada
    if user_role() == "SECRETARIO":
        congregacao = user_congregacao_vinculada()
        col2, col3 = st.columns(2)
        with col2:
            st.selectbox("🏛️ Congregação", [congregacao], index=0, disabled=True)
        with col3:
            tipo = st.selectbox("📌 Tipo", ["Todos"] + TIPOS, index=0)
    else:
        with col2:
            congregacao = st.selectbox("🏛️ Congregação", ["Todas"] + CONGREGACOES, index=0)
        with col3:
            tipo = st.selectbox("📌 Tipo", ["Todos"] + TIPOS, index=0)

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
        title=f"Agenda {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"
    )
    if png:
        st.download_button(
            "📸 Exportar agenda em PNG",
            data=png,
            file_name="agenda_semana.png",
            mime="image/png",
            use_container_width=True
        )

# =========================
# Gerenciar Eventos (Admin)
# =========================
def page_gerenciar_eventos():
    st.markdown("## Gerenciar Eventos")

    if not can_manage_events():
        st.error("Você não tem permissão para gerenciar eventos.")
        return

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        dt_ini = st.date_input("📅 Data inicial", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
    with col2:
        dt_fim = st.date_input("📅 Data final", value=date.today() + timedelta(days=60), format="DD/MM/YYYY")

    # Secretário: restringe por congregação vinculada
    if user_role() == "SECRETARIO":
        cong = user_congregacao_vinculada()
        with col3:
            st.selectbox("🏛️ Congregação", [cong], index=0, disabled=True)
        eventos = list_events_between(dt_ini, dt_fim, congregacao=cong, tipo=None)
    else:
        with col3:
            cong = st.selectbox("🏛️ Congregação", ["Todas"] + CONGREGACOES, index=0)
        eventos = list_events_between(dt_ini, dt_fim, congregacao=None if cong == "Todas" else cong, tipo=None)

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

    selected = st.selectbox("🧾 Selecione o ID do evento", df["id"].tolist())

    # Secretário: valida evento
    if user_role() == "SECRETARIO":
        ev = get_event(selected)
        if ev and ev.get("congregacao") != user_congregacao_vinculada():
            st.error("Esse evento não pertence à sua congregação. Você não pode mexer.")
            return

    colA, colB = st.columns(2)
    with colA:
        if st.button("✏️ Editar", use_container_width=True):
            st.session_state.edit_id = selected
            st.session_state.page = "Cadastrar Evento"
            st.rerun()
    with colB:
        if st.button("🗑️ Excluir", use_container_width=True):
            # Secretário: trava
            if user_role() == "SECRETARIO":
                ev = get_event(selected)
                if ev and ev.get("congregacao") != user_congregacao_vinculada():
                    st.error("Você não pode excluir evento de outra congregação.")
                    return
            delete_event(selected)
            st.success("Evento excluído.")
            st.rerun()

# =========================
# Usuários (ADMIN)
# =========================
def page_usuarios():
    st.markdown("## Usuários")

    if not can_manage_users():
        st.error("Apenas ADMIN pode gerenciar usuários.")
        return

    st.markdown(
        """
        <div class="soft-card">
          <p class="section-title">Gestão de Usuários</p>
          <p class="section-subtitle">Crie usuários, ative/desative e redefina senhas. Troque a senha do admin padrão.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("")

    tab1, tab2, tab3 = st.tabs(["➕ Criar usuário", "📋 Lista", "🔑 Reset senha"])

    with tab1:
        with st.form("form_create_user"):
            nome = st.text_input("👤 Nome*", placeholder="Nome completo")
            username = st.text_input("🆔 Username*", placeholder="Ex: joao.silva")
            senha = st.text_input("🔒 Senha*", type="password", placeholder="Defina uma senha")
            perfil = st.selectbox(
                "🎭 Perfil*",
                ["ADMIN", "PASTOR", "DIRIGENTE", "SECRETARIO"],
                index=None,
                placeholder="Escolha um perfil"
            )

            congreg_vinc = None
            if perfil == "SECRETARIO":
                congreg_vinc = st.selectbox(
                    "🏛️ Congregação vinculada*",
                    CONGREGACOES,
                    index=None,
                    placeholder="Escolha a congregação do secretário(a)"
                )

            submit = st.form_submit_button("Criar", use_container_width=True)

        if submit:
            try:
                if not nome or not username or not senha or not perfil:
                    st.error("Preencha Nome, Username, Senha e Perfil.")
                else:
                    create_user(nome, username, senha, perfil, congreg_vinc)
                    st.success("Usuário criado.")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao criar usuário: {e}")

    with tab2:
        users = list_users()
        if not users:
            st.info("Nenhum usuário encontrado.")
        else:
            dfu = pd.DataFrame(users)
            if "criado_em" in dfu.columns:
                dfu["criado_em"] = pd.to_datetime(dfu["criado_em"]).dt.strftime("%d/%m/%Y %H:%M")
            st.dataframe(dfu, use_container_width=True, hide_index=True)

            st.markdown("### ✅ Ativar / Desativar")
            ids = dfu["id"].tolist()
            uid = st.selectbox("Usuário (ID)", ids)
            ativo_atual = bool(dfu.loc[dfu["id"] == uid, "ativo"].iloc[0])

            colA, colB = st.columns(2)
            with colA:
                st.caption(f"Status atual: {'ATIVO' if ativo_atual else 'INATIVO'}")
            with colB:
                novo = st.selectbox("Novo status", [True, False], index=0 if ativo_atual else 1)

            if st.button("Atualizar status", use_container_width=True):
                try:
                    set_user_active(int(uid), bool(novo))
                    st.success("Status atualizado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with tab3:
        users = list_users()
        if not users:
            st.info("Nenhum usuário encontrado.")
        else:
            dfu = pd.DataFrame(users)
            options = [f"{r['id']} - {r['username']} ({r['perfil']})" for r in users]
            sel = st.selectbox("Selecione o usuário", options)
            user_id = int(sel.split(" - ")[0])

            nova = st.text_input("🔒 Nova senha*", type="password", placeholder="Digite a nova senha")
            if st.button("Resetar senha", use_container_width=True):
                if not nova:
                    st.error("Informe a nova senha.")
                else:
                    try:
                        reset_password(user_id, nova)
                        st.success("Senha atualizada.")
                    except Exception as e:
                        st.error(f"Erro: {e}")

# =========================
# Main
# =========================
def main():
    apply_css()
    init_state()

    # init DB structures
    init_auth()
    init_events()

    render_topbar()
    sidebar()

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

    # Rotas logadas
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
