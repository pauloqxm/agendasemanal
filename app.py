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
IGREJA_NOME = "Igreja Assembleia de Deus Templo Central | Quixeramobim-Ce"

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Agenda da Igreja",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar colapsada por padrão
)

# =========================
# Paleta de cores - Azul Escuro
# =========================
COLORS = {
    "primary": "#0A1F44",      # Azul escuro principal
    "secondary": "#1A365D",    # Azul escuro secundário
    "accent": "#2C5282",       # Azul médio
    "light": "#4A90E2",        # Azul claro
    "success": "#38A169",      # Verde
    "warning": "#D69E2E",      # Âmbar
    "danger": "#E53E3E",       # Vermelho
    "background": "#F7FAFC",   # Cinza muito claro
    "card": "#FFFFFF",         # Branco
    "text": "#1A202C",         # Cinza escuro
    "text_light": "#718096",   # Cinza médio
}

# =========================
# Estilo Moderno
# =========================
def apply_css():
    css = f"""
    <style>
    /* Configurações gerais */
    .block-container {{ 
        padding-top: 1rem; 
        padding-bottom: 2rem; 
    }}
    
    [data-testid="stSidebar"] {{ 
        background: linear-gradient(180deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-right: none;
    }}
    
    [data-testid="stSidebarNav"] {{
        padding-top: 2rem;
    }}
    
    /* Header fixo */
    .sticky-header {{
        position: sticky;
        top: 0;
        z-index: 100;
        background: white;
        border-bottom: 1px solid #E2E8F0;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
    }}
    
    /* Tabs modernas */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS['background']};
        padding: 8px;
        border-radius: 12px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        white-space: pre-wrap;
        border-radius: 8px;
        gap: 8px;
        padding: 8px 16px;
        background-color: transparent;
        color: {COLORS['text_light']};
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['primary']} !important;
        color: white !important;
        font-weight: 600;
    }}
    
    /* Cards modernos */
    .modern-card {{
        background: {COLORS['card']};
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        margin-bottom: 16px;
    }}
    
    .modern-card:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }}
    
    .event-card {{
        background: {COLORS['card']};
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
        border-left: 4px solid {COLORS['light']};
    }}
    
    /* Botões */
    .stButton > button {{
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
    }}
    
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        border: none;
    }}
    
    div[data-testid="stButton"] > button[kind="secondary"] {{
        background: white;
        color: {COLORS['primary']};
        border: 2px solid {COLORS['primary']};
    }}
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input {{
        border-radius: 10px;
        border: 2px solid #E2E8F0;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > div:focus,
    .stDateInput > div > div > input:focus {{
        border-color: {COLORS['light']};
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    }}
    
    /* Topbar */
    .topbar {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 25px rgba(10, 31, 68, 0.15);
    }}
    
    .topbar-content {{
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    
    .church-info {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .logo-wrap img {{
        width: 70px;
        height: 70px;
        border-radius: 14px;
        object-fit: cover;
        border: 3px solid rgba(255, 255, 255, 0.2);
    }}
    
    .church-text h1 {{
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0;
        color: white;
    }}
    
    .church-text p {{
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 4px 0 0 0;
        color: rgba(255, 255, 255, 0.9);
    }}
    
    /* Badges */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }}
    
    .badge-primary {{
        background: rgba(74, 144, 226, 0.1);
        color: {COLORS['light']};
    }}
    
    .badge-success {{
        background: rgba(56, 161, 105, 0.1);
        color: {COLORS['success']};
    }}
    
    .badge-warning {{
        background: rgba(214, 158, 46, 0.1);
        color: {COLORS['warning']};
    }}
    
    /* Page tabs */
    .page-tabs {{
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.5rem;
    }}
    
    .page-tab {{
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }}
    
    .page-tab:hover {{
        background: {COLORS['background']};
    }}
    
    .page-tab.active {{
        background: {COLORS['primary']};
        color: white;
    }}
    
    /* Status indicators */
    .status-indicator {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }}
    
    .status-online {{ background: {COLORS['success']}; }}
    .status-offline {{ background: {COLORS['danger']}; }}
    
    /* Divider */
    .divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
        margin: 1.5rem 0;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# =========================
# Componentes de UI
# =========================
def render_topbar():
    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-content">
            <div class="church-info">
              <div class="logo-wrap">
                <img src="{LOGO_URL}" />
              </div>
              <div class="church-text">
                <h1>{IGREJA_NOME}</h1>
                <p>Sistema de Gestão de Agenda</p>
              </div>
            </div>
            <div>
              <span class="badge badge-primary">
                <span class="status-indicator status-online"></span>
                Online
              </span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_page_tabs():
    """Renderiza as abas de página no topo"""
    # Páginas públicas sempre disponíveis
    if not st.session_state.auth_ok:
        pages = [
            {"id": "Agenda Pública", "label": "📅 Agenda Pública", "icon": "📅"},
            {"id": "Login", "label": "🔐 Login", "icon": "🔐"}
        ]
    else:
        pages = [
            {"id": "Agenda Pública", "label": "📅 Agenda Pública", "icon": "📅"},
            {"id": "Agenda da Semana", "label": "📊 Agenda da Semana", "icon": "📊"},
            {"id": "Cadastrar Evento", "label": "➕ Cadastrar Evento", "icon": "➕"},
            {"id": "Gerenciar Eventos", "label": "⚙️ Gerenciar Eventos", "icon": "⚙️"}
        ]
        
        if has_role("ADMIN"):
            pages.append({"id": "Usuários", "label": "👥 Usuários", "icon": "👥"})
    
    # Criar as abas usando colunas do Streamlit
    tab_cols = st.columns(len(pages))
    
    for idx, (col, page) in enumerate(zip(tab_cols, pages)):
        with col:
            is_active = st.session_state.page == page["id"]
            btn_type = "primary" if is_active else "secondary"
            
            if st.button(page["label"], key=f"tab_{page['id']}", 
                       type=btn_type, use_container_width=True):
                st.session_state.page = page["id"]
                st.rerun()

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

def _event_card(ev: dict):
    data_txt = _fmt_date_br(pd.to_datetime(ev["data"]).date() if ev.get("data") else date.today())
    hora_txt = _fmt_time_hhmm(ev.get("horario"))
    congreg = ev.get("congregacao") or ""

    tipo_txt = format_tipo(ev)
    subtipo = ev.get("subtipo") or ""
    turma = ev.get("turma_ebd") or ""

    # Criar badges
    badges = ""
    if subtipo:
        badges += f'<span class="badge badge-warning">🎯 {subtipo}</span>'
    if turma:
        badges += f'<span class="badge badge-success">📚 {turma}</span>'
    if ev.get("secretaria"):
        badges += f'<span class="badge badge-primary">📋 {ev.get("secretaria")}</span>'

    dirigentes = join_people(ev.get("dirigente1"), ev.get("dirigente2"), ev.get("dirigente3"))
    portaria = join_people(ev.get("portaria1"), ev.get("portaria2"), ev.get("portaria3"))
    recepcao = join_people(ev.get("recepcao1"), ev.get("recepcao2"), ev.get("recepcao3"))

    st.markdown(
        f"""
        <div class="event-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
              <div style="font-weight: 700; font-size: 1.1rem; color: {COLORS['primary']};">{tipo_txt}</div>
              <div style="font-size: 0.9rem; color: {COLORS['text_light']}; margin-top: 4px;">
                📅 {data_txt} • 🕒 {hora_txt} • 🏛️ {congreg}
              </div>
            </div>
            <div>
              {badges}
            </div>
          </div>
          
          <div style="margin: 12px 0;">
            <div style="font-size: 0.95rem; margin-bottom: 4px;">
              <span style="font-weight: 600; color: {COLORS['secondary']};">👤 Dirigentes:</span>
              <span style="color: {COLORS['text']}; margin-left: 8px;">{dirigentes or "Não informado"}</span>
            </div>
            <div style="font-size: 0.95rem; margin-bottom: 4px;">
              <span style="font-weight: 600; color: {COLORS['secondary']};">🚪 Portaria:</span>
              <span style="color: {COLORS['text']}; margin-left: 8px;">{portaria or "Não informado"}</span>
            </div>
            <div style="font-size: 0.95rem;">
              <span style="font-weight: 600; color: {COLORS['secondary']};">🤝 Recepção:</span>
              <span style="color: {COLORS['text']}; margin-left: 8px;">{recepcao or "Não informado"}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Sidebar Colapsada
# =========================
def sidebar():
    with st.sidebar:
        # Logo e título da sidebar
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 2rem;">
              <div style="margin-bottom: 1rem;">
                <img src="{LOGO_URL}" style="width: 60px; height: 60px; border-radius: 12px; border: 2px solid rgba(255,255,255,0.2);">
              </div>
              <div style="color: white; font-size: 0.9rem; font-weight: 600;">
                Agenda da Igreja
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Status do banco
        ok, msg = test_db_connection()
        if ok:
            st.markdown(
                f'<div style="color: #38A169; font-size: 0.8rem; text-align: center; margin-bottom: 1rem;">✓ {msg}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="color: #E53E3E; font-size: 0.8rem; text-align: center; margin-bottom: 1rem;">✗ {msg}</div>',
                unsafe_allow_html=True
            )
        
        st.divider()
        
        # Informações do usuário
        if st.session_state.auth_ok:
            user = st.session_state.user or {}
            st.markdown(
                f"""
                <div style="color: white; padding: 0.5rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin-bottom: 1rem;">
                  <div style="font-weight: 600; font-size: 0.9rem;">{user.get('nome') or user.get('username')}</div>
                  <div style="font-size: 0.8rem; opacity: 0.9;">Perfil: {user.get('perfil')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Botão de logout
            if st.button("🚪 Sair", use_container_width=True, type="secondary"):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()
        
        st.divider()
        
        # Botões de acesso rápido
        st.markdown('<div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.5rem;">Acesso Rápido</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅 Pública", use_container_width=True, type="secondary"):
                st.session_state.page = "Agenda Pública"
                st.rerun()
        
        with col2:
            if not st.session_state.auth_ok:
                if st.button("🔐 Login", use_container_width=True, type="secondary"):
                    st.session_state.page = "Login"
                    st.rerun()
            else:
                if st.button("📊 Semana", use_container_width=True, type="secondary"):
                    st.session_state.page = "Agenda da Semana"
                    st.rerun()

# =========================
# Login
# =========================
def page_login():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">🔐 Acesso ao Sistema</h2>
          <p style="color: {COLORS['text_light']}; margin-bottom: 1.5rem;">
            Área restrita para cadastro e gerenciamento da agenda
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.markdown('<div style="margin-bottom: 1.5rem;">', unsafe_allow_html=True)
                username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
                password = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
                st.markdown('</div>', unsafe_allow_html=True)
                
                submit = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
                
                if submit:
                    ok, user = authenticate(username.strip(), password)
                    if ok:
                        st.session_state.auth_ok = True
                        st.session_state.user = user
                        st.session_state.page = "Agenda da Semana"
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha inválidos.")
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            st.markdown(
                f"""
                <div style="text-align: center; color: {COLORS['text_light']}; font-size: 0.9rem;">
                  <p>Problemas com acesso? Entre em contato com o administrador.</p>
                  <button onclick="window.location.href='?page=Agenda Pública'" 
                          style="background: transparent; border: 2px solid {COLORS['primary']}; 
                                 color: {COLORS['primary']}; padding: 8px 16px; border-radius: 8px; 
                                 cursor: pointer; font-weight: 600; margin-top: 1rem;">
                    Voltar para Agenda Pública
                  </button>
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================
# Agenda Pública
# =========================
def page_agenda_publica():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">📅 Agenda Pública</h2>
          <p style="color: {COLORS['text_light']}; margin-bottom: 1.5rem;">
            Visualização pública dos eventos da igreja. Acesso livre sem necessidade de login.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Filtros em cards modernos
    with st.container():
        col1, col2, col3 = st.columns([1.2, 1, 0.8])
        with col1:
            with st.container():
                st.markdown('<div class="modern-card" style="padding: 1rem;">', unsafe_allow_html=True)
                ref = st.date_input("📆 Semana de referência", value=date.today(), format="DD/MM/YYYY")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            with st.container():
                st.markdown('<div class="modern-card" style="padding: 1rem;">', unsafe_allow_html=True)
                congregacao = st.selectbox("🏛️ Congregação", ["Todas"] + CONGREGACOES)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            with st.container():
                st.markdown('<div class="modern-card" style="padding: 1rem;">', unsafe_allow_html=True)
                modo = st.selectbox("👁️ Exibição", ["Cards", "Tabela"], index=0)
                st.markdown('</div>', unsafe_allow_html=True)
    
    monday, sunday = week_bounds(ref)
    
    # Card de resumo da semana
    st.markdown(
        f"""
        <div class="modern-card">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <h3 style="margin: 0; color: {COLORS['primary']};">📋 Resumo da Semana</h3>
              <p style="margin: 0.5rem 0 0 0; color: {COLORS['text_light']};">
                {_fmt_date_br(monday)} até {_fmt_date_br(sunday)}
              </p>
            </div>
            <span class="badge badge-primary">{congregacao}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    eventos = list_events_between(
        monday,
        sunday,
        congregacao=None if congregacao == "Todas" else congregacao,
        tipo=None
    )
    
    if not eventos:
        st.info("📭 Nenhum evento cadastrado nesta semana.")
        return
    
    df = pd.DataFrame(eventos)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)
    
    tab_culto, tab_ebd, tab_oracao, tab_ensaio = st.tabs(["🎵 Cultos", "📚 EBD", "🙏 Oração", "🎤 Ensaios"])
    
    def render_group(tipo_nome: str, container, icon: str):
        with container:
            sub = df[df["tipo"] == tipo_nome].copy()
            if sub.empty:
                st.info(f"{icon} Sem eventos deste tipo nesta semana.")
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
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "💾 Exportar em PNG",
                            data=png,
                            file_name=f"agenda_{tipo_nome.lower()}_{monday.strftime('%Y%m%d')}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            "📄 Exportar em CSV",
                            data=show.to_csv(index=False).encode('utf-8'),
                            file_name=f"agenda_{tipo_nome.lower()}_{monday.strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                return
            
            for _, r in sub.iterrows():
                _event_card(r.to_dict())
    
    render_group("Culto", tab_culto, "🎵")
    render_group("EBD", tab_ebd, "📚")
    render_group("Oração", tab_oracao, "🙏")
    render_group("Ensaio", tab_ensaio, "🎤")

# =========================
# Cadastro de Evento
# =========================
def page_cadastrar_evento():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">
            {'✏️ Editar Evento' if st.session_state.edit_id else '➕ Cadastrar Evento'}
          </h2>
          <p style="color: {COLORS['text_light']}; margin-bottom: 1.5rem;">
            {'Atualize as informações do evento' if st.session_state.edit_id else 'Preencha os dados para criar um novo evento'}
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    edit_id = st.session_state.edit_id
    ev = get_event(edit_id) if edit_id else None

    def val(key, default=None):
        if not ev:
            return default
        v = ev.get(key)
        return v if v is not None else default

    with st.container():
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="color: {COLORS["secondary"]};">📋 Dados do Evento</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)

        # Congregação (SECRETARIO só pode alterar a vinculada)
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
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Equipe do Evento
    with st.container():
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="color: {COLORS["secondary"]};">👥 Equipe do Evento</h3>', unsafe_allow_html=True)
        
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

        st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

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

        st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

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

        st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

        secretaria = st.text_input("🗂️ Secretaria", value=val("secretaria", "") or "", placeholder="Nome do responsável (opcional)")
        observacoes = st.text_area("📝 Observações", value=val("observacoes", "") or "", placeholder="Observações (opcional)", height=90)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Botões de ação
    col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
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
            st.success("✅ Evento atualizado com sucesso!")
        else:
            create_event(payload)
            st.success("✅ Evento cadastrado com sucesso!")

        st.session_state.edit_id = None
        st.session_state.page = "Agenda da Semana"
        st.rerun()

# =========================
# Agenda da Semana
# =========================
def page_agenda_semana():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">📊 Agenda da Semana</h2>
          <p style="color: {COLORS['text_light']}; margin-bottom: 1.5rem;">
            Visualização detalhada dos eventos da semana atual
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.container():
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
        st.info("📭 Nenhum evento cadastrado nesta semana.")
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
            "💾 Exportar agenda em PNG",
            data=png,
            file_name="agenda_semana.png",
            mime="image/png",
            use_container_width=True
        )

# =========================
# Gerenciar Eventos
# =========================
def page_gerenciar_eventos():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">⚙️ Gerenciar Eventos</h2>
          <p style="color: {COLORS['text_light']}; margin-bottom: 1.5rem;">
            Edite ou exclua eventos cadastrados no sistema
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            dt_ini = st.date_input("Data inicial", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
        with col2:
            dt_fim = st.date_input("Data final", value=date.today() + timedelta(days=60), format="DD/MM/YYYY")

    eventos = list_events_between(dt_ini, dt_fim)
    if not eventos:
        st.info("📭 Nenhum evento encontrado no período selecionado.")
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
        if st.button("✏️ Editar", use_container_width=True, type="primary"):
            st.session_state.edit_id = selected
            st.session_state.page = "Cadastrar Evento"
            st.rerun()
    with colB:
        if st.button("🗑️ Excluir", use_container_width=True, type="secondary"):
            delete_event(selected)
            st.success("✅ Evento excluído com sucesso!")
            st.rerun()

# =========================
# Usuários (ADMIN)
# =========================
def page_usuarios():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">👥 Gerenciar Usuários</h2>
          <p style="color: {COLORS['text_light']}; margin-bottom: 1.5rem;">
            Área administrativa para gerenciamento de acessos ao sistema
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if not has_role("ADMIN"):
        st.error("❌ Acesso negado. Esta área é somente para ADMIN.")
        return

    tab1, tab2 = st.tabs(["➕ Cadastrar usuário", "📋 Gerenciar usuários"])

    with tab1:
        st.markdown(
            f"""
            <div class="modern-card">
              <h3 style="color: {COLORS['secondary']};">Novo Usuário</h3>
              <p style="color: {COLORS['text_light']};">
                Crie um novo acesso. Para SECRETARIO, escolha a congregação vinculada.
              </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
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
                st.success("✅ Usuário criado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao criar usuário: {e}")

    with tab2:
        users = list_users()
        if not users:
            st.info("📭 Ainda não há usuários cadastrados.")
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
            if st.button("🔒 Desativar", use_container_width=True, type="secondary"):
                set_user_active(int(sel), False)
                st.success("✅ Usuário desativado!")
                st.rerun()
        with colB:
            if st.button("🔓 Ativar", use_container_width=True, type="secondary"):
                set_user_active(int(sel), True)
                st.success("✅ Usuário ativado!")
                st.rerun()
        with colC:
            nova = st.text_input("Nova senha (reset)", type="password", placeholder="Digite uma nova senha", key="nova_senha")
            if st.button("♻️ Resetar senha", use_container_width=True, type="secondary"):
                if not nova:
                    st.error("❌ Digite a nova senha.")
                else:
                    reset_password(int(sel), nova)
                    st.success("✅ Senha atualizada com sucesso!")
                    st.rerun()

# =========================
# Main
# =========================
def main():
    apply_css()
    init_state()
    init_auth()
    init_events()

    # Header
    render_topbar()
    render_page_tabs()

    sidebar()

    page = st.session_state.page

    if page == "Agenda Pública":
        page_agenda_publica()
        return

    if page == "Login":
        page_login()
        return

    if not st.session_state.auth_ok:
        st.warning("🔒 Você precisa estar logado para acessar esta área.")
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
