# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from io import BytesIO
import urllib.request

# ReportLab (PDF)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

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
    initial_sidebar_state="collapsed"
)

# =========================
# Paleta (cinza claro + azul)
# =========================
COLORS = {
    "primary": "#0A1F44",       # azul escuro
    "secondary": "#12315F",
    "accent": "#2563EB",        # azul vivo para foco/CTAs
    "light": "#E8F0FF",
    "bg": "#F3F4F6",            # cinza claro
    "card": "#FFFFFF",
    "text": "#0F172A",
    "muted": "#64748B",
    "border": "#E5E7EB",
    "success": "#16A34A",
    "danger": "#DC2626",
    "warning": "#D97706"
}

# =========================
# CSS (moderno, sem pílulas vazias)
# =========================
def apply_css():
    css = f"""
    <style>
    /* App background */
    .stApp {{
        background: {COLORS['bg']};
    }}

    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-right: none;
    }}

    /* Topbar */
    .topbar {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 18px;
        padding: 18px 18px;
        box-shadow: 0 10px 25px rgba(2, 6, 23, 0.06);
        margin-bottom: 14px;
    }}
    .topbar-row {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 16px;
        flex-wrap: wrap;
    }}
    .brand {{
        display:flex;
        align-items:center;
        gap: 12px;
        min-width: 280px;
    }}
    .brand img {{
        width: 58px;
        height: 58px;
        border-radius: 14px;
        object-fit: cover;
        border: 1px solid {COLORS['border']};
    }}
    .brand-title {{
        font-weight: 900;
        font-size: 1.2rem;
        color: {COLORS['primary']};
        margin:0;
        line-height:1.15;
    }}
    .brand-sub {{
        color: {COLORS['muted']};
        margin: 4px 0 0 0;
        font-weight: 600;
        font-size: 0.92rem;
    }}
    .status-pill {{
        display:inline-flex;
        align-items:center;
        gap: 8px;
        background: {COLORS['light']};
        border: 1px solid rgba(37,99,235,0.25);
        color: {COLORS['primary']};
        padding: 8px 12px;
        border-radius: 999px;
        font-weight: 800;
        font-size: 0.85rem;
        white-space: nowrap;
    }}
    .dot {{
        width: 9px;
        height: 9px;
        border-radius: 999px;
        background: {COLORS['success']};
        box-shadow: 0 0 0 3px rgba(22,163,74,0.12);
    }}

    /* Page tabs (top nav buttons) */
    .page-tabs-wrap {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 18px;
        padding: 12px;
        box-shadow: 0 10px 25px rgba(2, 6, 23, 0.05);
        margin-bottom: 14px;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 900 !important;
        transition: all .2s ease !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
    }}
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%) !important;
        border: none !important;
        color: white !important;
    }}
    div[data-testid="stButton"] > button[kind="secondary"] {{
        background: white !important;
        color: {COLORS['primary']} !important;
        border: 2px solid rgba(10,31,68,0.18) !important;
    }}

    /* Modern card */
    .modern-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 10px 25px rgba(2, 6, 23, 0.06);
        margin-bottom: 12px;
    }}
    .card-title {{
        margin: 0;
        font-size: 1.35rem;
        font-weight: 950;
        color: {COLORS['primary']};
    }}
    .card-sub {{
        margin: 8px 0 0 0;
        color: {COLORS['muted']};
        font-weight: 600;
    }}

    /* Filtros: estiliza o container real dos widgets (sem “pílula vazia”) */
    .filter-label {{
        font-weight: 950;
        color: {COLORS['primary']};
        margin-bottom: 8px;
        font-size: 0.96rem;
        display:flex;
        align-items:center;
        gap: 8px;
    }}
    div[data-testid="stDateInput"],
    div[data-testid="stSelectbox"] {{
        background: #FFFFFF;
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 12px 12px 10px 12px;
        box-shadow: 0 8px 18px rgba(2, 6, 23, 0.06);
    }}
    div[data-testid="stDateInput"] > div,
    div[data-testid="stSelectbox"] > div {{
        padding: 0 !important;
        margin: 0 !important;
    }}
    div[data-testid="stDateInput"] input {{
        border-radius: 12px !important;
        border: 2px solid {COLORS['border']} !important;
        padding: 12px 12px !important;
        font-weight: 900 !important;
        background: #F8FAFC !important;
    }}
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        border-radius: 12px !important;
        border: 2px solid {COLORS['border']} !important;
        background: #F8FAFC !important;
    }}
    div[data-testid="stDateInput"] input:focus {{
        border-color: {COLORS['accent']} !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    }}
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {{
        border-color: {COLORS['accent']} !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    }}

    /* Streamlit tabs (Cultos/EBD/Oração/Ensaios) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        padding: 8px;
        border-radius: 16px;
        box-shadow: 0 8px 18px rgba(2, 6, 23, 0.05);
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 900;
        color: {COLORS['muted']};
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['primary']} !important;
        color: white !important;
    }}

    /* Event cards */
    .event-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 22px rgba(2, 6, 23, 0.06);
        margin-bottom: 12px;
        border-left: 5px solid {COLORS['accent']};
    }}
    .weekday-line {{
        font-weight: 1000;
        letter-spacing: .5px;
        color: {COLORS['primary']};
        text-transform: uppercase;
        font-size: 0.86rem;
        margin-bottom: 6px;
    }}

    /* A4 preview */
    .a4-wrap {{
        display:flex;
        justify-content:center;
        margin-top: 8px;
    }}
    .a4-page {{
        width: 794px; /* ~A4 at 96dpi */
        min-height: 1123px;
        background: white;
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        box-shadow: 0 15px 35px rgba(2,6,23,0.10);
        padding: 28px 30px;
        position: relative;
    }}
    .a4-header {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 16px;
        border-bottom: 3px solid {COLORS['primary']};
        padding-bottom: 12px;
        margin-bottom: 12px;
    }}
    .a4-brand {{
        display:flex;
        align-items:center;
        gap: 12px;
    }}
    .a4-brand img {{
        width: 54px;
        height: 54px;
        border-radius: 12px;
        object-fit: cover;
        border: 1px solid {COLORS['border']};
    }}
    .a4-igreja {{
        font-weight: 950;
        color: {COLORS['primary']};
        margin: 0;
        line-height: 1.15;
        font-size: 0.98rem;
    }}
    .a4-sub {{
        margin: 4px 0 0 0;
        color: {COLORS['muted']};
        font-weight: 700;
        font-size: 0.85rem;
    }}
    .a4-right {{
        text-align:right;
        color: {COLORS['muted']};
        font-weight: 800;
        font-size: 0.85rem;
    }}
    .a4-title {{
        text-align:center;
        font-weight: 1000;
        color: {COLORS['primary']};
        margin: 12px 0 14px 0;
        letter-spacing: .6px;
    }}
    .a4-day {{
        margin-top: 14px;
        font-weight: 1000;
        color: {COLORS['primary']};
        text-transform: uppercase;
        font-size: 0.92rem;
    }}
    .a4-item {{
        margin-top: 6px;
        padding-left: 12px;
        border-left: 3px solid rgba(10,31,68,0.18);
        color: {COLORS['text']};
        font-weight: 650;
        font-size: 0.9rem;
        line-height: 1.35;
    }}
    .a4-meta {{
        color: {COLORS['muted']};
        font-weight: 700;
        font-size: 0.86rem;
        margin-top: 2px;
    }}

    @media (max-width: 900px) {{
        .a4-page {{
            width: 100%;
            border-radius: 14px;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# =========================
# Helpers
# =========================
def init_state():
    st.session_state.setdefault("auth_ok", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Agenda Pública")
    st.session_state.setdefault("edit_id", None)
    st.session_state.setdefault("show_dirigentes_extra", False)
    st.session_state.setdefault("show_portaria_extra", False)
    st.session_state.setdefault("show_recepcao_extra", False)

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

def weekday_pt(d: date) -> str:
    # Monday=0
    names = ["SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO", "DOMINGO"]
    try:
        return names[d.weekday()]
    except Exception:
        return ""

def safe_upper(s: str) -> str:
    return (s or "").strip().upper()

def render_topbar():
    ok, msg = test_db_connection()
    status = "Online" if ok else "Offline"
    dot_color = COLORS["success"] if ok else COLORS["danger"]
    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-row">
            <div class="brand">
              <img src="{LOGO_URL}" />
              <div>
                <p class="brand-title">{IGREJA_NOME}</p>
                <p class="brand-sub">Agenda semanal de eventos</p>
              </div>
            </div>
            <div class="status-pill">
              <span class="dot" style="background:{dot_color}; box-shadow: 0 0 0 3px rgba(22,163,74,0.12);"></span>
              {status}
              <span style="opacity:.7;">{msg}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_page_tabs():
    # Páginas
    if not st.session_state.auth_ok:
        pages = [
            {"id": "Agenda Pública", "label": "📅 Agenda Pública"},
            {"id": "Login", "label": "🔐 Login"},
        ]
    else:
        pages = [
            {"id": "Agenda Pública", "label": "📅 Agenda Pública"},
            {"id": "Agenda da Semana", "label": "📊 Agenda da Semana"},
            {"id": "Cadastrar Evento", "label": "➕ Cadastrar Evento"},
            {"id": "Gerenciar Eventos", "label": "⚙️ Gerenciar Eventos"},
        ]
        if has_role("ADMIN"):
            pages.append({"id": "Usuários", "label": "👥 Usuários"})

    st.markdown('<div class="page-tabs-wrap">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for col, p in zip(cols, pages):
        with col:
            is_active = st.session_state.page == p["id"]
            btn_type = "primary" if is_active else "secondary"
            if st.button(p["label"], type=btn_type, use_container_width=True, key=f"top_{p['id']}"):
                st.session_state.page = p["id"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        # header sidebar
        st.markdown(
            f"""
            <div style="text-align:center; padding: 14px 10px 10px 10px;">
              <img src="{LOGO_URL}" style="width:58px; height:58px; border-radius:14px; border:2px solid rgba(255,255,255,0.15); object-fit:cover;">
              <div style="margin-top:10px; color:white; font-weight:950;">Agenda</div>
              <div style="color:rgba(255,255,255,0.75); font-weight:700; font-size:.82rem;">Acesso rápido</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # Botões pedidos: Login e Agenda Pública
        if st.button("📅 Agenda Pública", use_container_width=True, type="secondary"):
            st.session_state.page = "Agenda Pública"
            st.rerun()

        if not st.session_state.auth_ok:
            if st.button("🔐 Login", use_container_width=True, type="secondary"):
                st.session_state.page = "Login"
                st.rerun()
        else:
            user = st.session_state.user or {}
            st.markdown(
                f"""
                <div style="margin-top:10px; padding:10px; border-radius:12px; background: rgba(255,255,255,0.10); color:white;">
                  <div style="font-weight:950;">{user.get('nome') or user.get('username')}</div>
                  <div style="opacity:.85; font-weight:800; font-size:.85rem;">Perfil: {user.get('perfil')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("🚪 Sair", use_container_width=True, type="secondary"):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()

        st.divider()
        st.caption("Versão • Agenda Igreja")


# =========================
# Event Card (com dia da semana em destaque)
# =========================
def _event_card(ev: dict):
    d = pd.to_datetime(ev["data"]).date() if ev.get("data") else date.today()
    data_txt = _fmt_date_br(d)
    dia_semana = weekday_pt(d)
    hora_txt = _fmt_time_hhmm(ev.get("horario"))
    congreg = ev.get("congregacao") or ""

    tipo_txt = format_tipo(ev)
    subtipo = ev.get("subtipo") or ""
    turma = ev.get("turma_ebd") or ""

    badges = ""
    if subtipo:
        badges += f'<span style="display:inline-block;background:rgba(217,119,6,0.10); color:{COLORS["warning"]}; border:1px solid rgba(217,119,6,0.25); padding:4px 10px; border-radius:999px; font-weight:900; font-size:.75rem; margin-left:6px;">🎯 {subtipo}</span>'
    if turma:
        badges += f'<span style="display:inline-block;background:rgba(22,163,74,0.10); color:{COLORS["success"]}; border:1px solid rgba(22,163,74,0.25); padding:4px 10px; border-radius:999px; font-weight:900; font-size:.75rem; margin-left:6px;">📚 {turma}</span>'
    if ev.get("secretaria"):
        badges += f'<span style="display:inline-block;background:rgba(37,99,235,0.10); color:{COLORS["accent"]}; border:1px solid rgba(37,99,235,0.25); padding:4px 10px; border-radius:999px; font-weight:900; font-size:.75rem; margin-left:6px;">📋 {ev.get("secretaria")}</span>'

    dirigentes = join_people(ev.get("dirigente1"), ev.get("dirigente2"), ev.get("dirigente3"))
    portaria = join_people(ev.get("portaria1"), ev.get("portaria2"), ev.get("portaria3"))
    recepcao = join_people(ev.get("recepcao1"), ev.get("recepcao2"), ev.get("recepcao3"))

    st.markdown(
        f"""
        <div class="event-card">
          <div class="weekday-line">{dia_semana}</div>

          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;">
            <div>
              <div style="font-weight:1000; font-size:1.08rem; color:{COLORS['primary']};">{tipo_txt}</div>
              <div style="font-size:.92rem; color:{COLORS['muted']}; font-weight:800; margin-top:4px;">
                📅 {data_txt} • 🕒 {hora_txt} • 🏛️ {congreg}
              </div>
            </div>
            <div style="text-align:right;">
              {badges}
            </div>
          </div>

          <div style="margin-top:12px; color:{COLORS['text']}; font-weight:700;">
            <div style="margin-bottom:4px;"><span style="font-weight:1000; color:{COLORS['secondary']};">👤 Dirigentes:</span> <span style="color:{COLORS['text']}; font-weight:750;">{dirigentes or "Não informado"}</span></div>
            <div style="margin-bottom:4px;"><span style="font-weight:1000; color:{COLORS['secondary']};">🚪 Portaria:</span> <span style="color:{COLORS['text']}; font-weight:750;">{portaria or "Não informado"}</span></div>
            <div><span style="font-weight:1000; color:{COLORS['secondary']};">🤝 Recepção:</span> <span style="color:{COLORS['text']}; font-weight:750;">{recepcao or "Não informado"}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# PDF A4 (ReportLab)
# =========================
def build_a4_pdf(eventos_df: pd.DataFrame, monday: date, sunday: date, congregacao: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    primary = HexColor(COLORS["primary"])
    muted = HexColor(COLORS["muted"])
    text = HexColor(COLORS["text"])

    # header line
    c.setStrokeColor(primary)
    c.setLineWidth(3)
    c.line(1.6*cm, h-2.2*cm, w-1.6*cm, h-2.2*cm)

    # Logo (tentativa via URL)
    logo_drawn = False
    try:
        with urllib.request.urlopen(LOGO_URL, timeout=5) as r:
            img_bytes = r.read()
        img_stream = BytesIO(img_bytes)
        c.drawImage(img_stream, 1.6*cm, h-2.0*cm-1.4*cm, width=1.4*cm, height=1.4*cm, mask='auto')
        logo_drawn = True
    except Exception:
        logo_drawn = False

    # Igreja + meta
    x_text = 3.2*cm if logo_drawn else 1.6*cm
    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x_text, h-1.55*cm, IGREJA_NOME)

    c.setFillColor(muted)
    c.setFont("Helvetica", 8.2)
    c.drawString(x_text, h-1.95*cm, "Agenda semanal oficial")

    c.setFillColor(muted)
    c.setFont("Helvetica-Bold", 8.2)
    c.drawRightString(w-1.6*cm, h-1.60*cm, f"Congregação: {congregacao}")

    # Title
    periodo = f"RODÍZIO SEMANAL - PERÍODO DE {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"
    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 10.2)
    c.drawCentredString(w/2, h-3.0*cm, periodo)

    y = h - 3.6*cm
    left = 1.9*cm
    right = w - 1.9*cm

    # Organiza por dia
    if eventos_df.empty:
        c.setFillColor(text)
        c.setFont("Helvetica", 10)
        c.drawString(left, y, "Nenhum evento cadastrado nesta semana.")
        c.showPage()
        c.save()
        return buf.getvalue()

    eventos_df = eventos_df.copy()
    eventos_df["data_dt"] = pd.to_datetime(eventos_df["data"]).dt.date
    eventos_df["horario_txt"] = eventos_df["horario"].astype(str).str[:5]
    eventos_df = eventos_df.sort_values(["data_dt", "horario_txt", "congregacao"])

    grouped = eventos_df.groupby("data_dt")

    for d, sub in grouped:
        # new page if needed
        if y < 3.0*cm:
            c.showPage()
            y = h - 2.0*cm

        # Day title
        c.setFillColor(primary)
        c.setFont("Helvetica-Bold", 9.7)
        c.drawString(left, y, f"• {weekday_pt(d)}")
        y -= 0.55*cm

        # items
        for _, r in sub.iterrows():
            if y < 3.0*cm:
                c.showPage()
                y = h - 2.0*cm

            hora = str(r.get("horario"))[:5] if pd.notna(r.get("horario")) else ""
            tipo = format_tipo(r.to_dict())
            cong = r.get("congregacao") or ""
            dirigentes = join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3"))
            portaria = join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3"))
            recepcao = join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3"))

            line1 = f"{hora}: {tipo} ({cong})"
            line2_parts = []
            if dirigentes:
                line2_parts.append(f"Dirigentes: {dirigentes}")
            if portaria:
                line2_parts.append(f"Portaria: {portaria}")
            if recepcao:
                line2_parts.append(f"Recepção: {recepcao}")
            line2 = "  |  ".join(line2_parts) if line2_parts else ""

            c.setFillColor(text)
            c.setFont("Helvetica-Bold", 9.0)
            c.drawString(left+0.6*cm, y, line1)
            y -= 0.45*cm

            if line2:
                c.setFillColor(muted)
                c.setFont("Helvetica", 8.3)
                # quebra manual simples se passar do limite
                max_chars = 110
                chunks = [line2[i:i+max_chars] for i in range(0, len(line2), max_chars)]
                for chunk in chunks:
                    if y < 3.0*cm:
                        c.showPage()
                        y = h - 2.0*cm
                    c.drawString(left+0.9*cm, y, chunk)
                    y -= 0.42*cm
            y -= 0.20*cm

        y -= 0.25*cm

    c.showPage()
    c.save()
    return buf.getvalue()


# =========================
# Pages
# =========================
def page_login():
    st.markdown(
        f"""
        <div class="modern-card">
          <p class="card-title">🔐 Login</p>
          <p class="card-sub">Acesso restrito para cadastro e gerenciamento da agenda.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    colA, colB, colC = st.columns([1, 1.2, 1])
    with colB:
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

def page_agenda_publica():
    st.markdown(
        f"""
        <div class="modern-card">
          <p class="card-title">📅 Agenda Pública</p>
          <p class="card-sub">Visualização pública dos eventos da igreja. Acesso livre sem necessidade de login.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # filtros (sem div vazia)
    col1, col2, col3 = st.columns([1.2, 1, 0.9])
    with col1:
        st.markdown("<div class='filter-label'>📆 Semana de referência</div>", unsafe_allow_html=True)
        ref = st.date_input("Semana de referência", value=date.today(), format="DD/MM/YYYY", label_visibility="collapsed")
    with col2:
        st.markdown("<div class='filter-label'>🏛️ Congregação</div>", unsafe_allow_html=True)
        congregacao = st.selectbox("Congregação", ["Todas"] + CONGREGACOES, label_visibility="collapsed")
    with col3:
        st.markdown("<div class='filter-label'>👁️ Exibição</div>", unsafe_allow_html=True)
        modo = st.selectbox("Exibição", ["Cards", "Tabela"], index=0, label_visibility="collapsed")

    monday, sunday = week_bounds(ref)

    st.markdown(
        f"""
        <div class="modern-card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">
            <div>
              <div style="font-weight:1000; color:{COLORS['primary']}; font-size:1.05rem;">📋 Resumo da Semana</div>
              <div style="margin-top:6px; color:{COLORS['muted']}; font-weight:850;">{_fmt_date_br(monday)} até {_fmt_date_br(sunday)}</div>
            </div>
            <div style="display:inline-block;background:{COLORS['light']}; border:1px solid rgba(37,99,235,0.25); color:{COLORS['primary']}; padding:8px 12px; border-radius:999px; font-weight:950;">
              {congregacao}
            </div>
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
        st.info("Nenhum evento cadastrado nesta semana.")
        return

    df = pd.DataFrame(eventos)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    # Abas: Todos A4 + tipos
    tab_all, tab_culto, tab_ebd, tab_oracao, tab_ensaio = st.tabs(["🧾 Todos (A4)", "🎵 Cultos", "📚 EBD", "🙏 Oração", "🎤 Ensaios"])

    def render_group_cards(tipo_nome: str, container):
        with container:
            sub = df[df["tipo"] == tipo_nome].copy()
            if sub.empty:
                st.info("Sem registros aqui nesta semana.")
                return

            if modo == "Tabela":
                view = sub.copy()
                view["Data"] = view["data"].apply(lambda x: x.strftime("%d/%m/%Y"))
                view["Dia"] = view["data"].apply(lambda x: weekday_pt(x))
                view["Horário"] = view["horario_txt"]
                view["Tipo"] = view.apply(lambda r: format_tipo(r.to_dict()), axis=1)
                view["Dirigentes"] = view.apply(lambda r: join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3")), axis=1)
                view["Portaria"] = view.apply(lambda r: join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3")), axis=1)
                view["Recepção"] = view.apply(lambda r: join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3")), axis=1)

                show = view[["Dia", "Data", "Horário", "congregacao", "Tipo", "Dirigentes", "Portaria", "Recepção", "secretaria"]]
                show = show.rename(columns={"congregacao": "Congregação", "secretaria": "Secretaria"})
                st.dataframe(show, use_container_width=True, hide_index=True)

                png = df_to_png_bytes(show, title=f"{tipo_nome} • {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}")
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

    # A4: Todos (preview + PDF)
    with tab_all:
        st.markdown(
            f"""
            <div class="modern-card">
              <div style="font-weight:1000; color:{COLORS['primary']}; font-size:1.05rem;">Folha A4</div>
              <div style="margin-top:6px; color:{COLORS['muted']}; font-weight:850;">Pronta para imprimir ou mandar no WhatsApp.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Preview A4 em HTML
        df_a4 = df.copy()
        if congregacao != "Todas":
            cong_label = congregacao
        else:
            cong_label = "Todas"

        # Agrupa por dia
        groups = []
        for d, sub in df_a4.groupby("data"):
            sub = sub.sort_values(["horario_txt", "congregacao"])
            items_html = ""
            for _, r in sub.iterrows():
                hora = r.get("horario_txt") or ""
                tipo = format_tipo(r.to_dict())
                cong = r.get("congregacao") or ""
                dirigentes = join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3"))
                portaria = join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3"))
                recepcao = join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3"))

                meta_parts = []
                if dirigentes:
                    meta_parts.append(f"<b>Dirigentes:</b> {dirigentes}")
                if portaria:
                    meta_parts.append(f"<b>Portaria:</b> {portaria}")
                if recepcao:
                    meta_parts.append(f"<b>Recepção:</b> {recepcao}")
                meta = "  |  ".join(meta_parts) if meta_parts else "—"

                items_html += f"""
                <div class="a4-item">
                  <div><b>{hora}</b>: <b>{tipo}</b> <span style="color:{COLORS['muted']}; font-weight:800;">({cong})</span></div>
                  <div class="a4-meta">{meta}</div>
                </div>
                """

            groups.append(
                f"""
                <div class="a4-day">• {weekday_pt(d)}</div>
                {items_html}
                """
            )

        periodo = f"RODÍZIO SEMANAL - PERÍODO DE {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"
        html_a4 = f"""
        <div class="a4-wrap">
          <div class="a4-page">
            <div class="a4-header">
              <div class="a4-brand">
                <img src="{LOGO_URL}" />
                <div>
                  <p class="a4-igreja">{IGREJA_NOME}</p>
                  <p class="a4-sub">Agenda semanal oficial</p>
                </div>
              </div>
              <div class="a4-right">
                Congregação: {cong_label}
              </div>
            </div>

            <div class="a4-title">{periodo}</div>
            {''.join(groups)}
          </div>
        </div>
        """
        st.markdown(html_a4, unsafe_allow_html=True)

        # PDF download
        pdf_bytes = build_a4_pdf(
            eventos_df=df_a4 if congregacao == "Todas" else df_a4[df_a4["congregacao"] == congregacao],
            monday=monday,
            sunday=sunday,
            congregacao=cong_label
        )
        st.download_button(
            "📄 Baixar PDF (A4)",
            data=pdf_bytes,
            file_name=f"rodizio_{monday.strftime('%Y%m%d')}_{sunday.strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    render_group_cards("Culto", tab_culto)
    render_group_cards("EBD", tab_ebd)
    render_group_cards("Oração", tab_oracao)
    render_group_cards("Ensaio", tab_ensaio)


def page_cadastrar_evento():
    st.markdown(
        f"""
        <div class="modern-card">
          <p class="card-title">{'✏️ Editar Evento' if st.session_state.edit_id else '➕ Cadastrar Evento'}</p>
          <p class="card-sub">Preencha as informações do evento. Os campos com * são obrigatórios.</p>
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

    col1, col2, col3 = st.columns(3)

    user = st.session_state.user or {}
    perfil = user.get("perfil")
    vinc = user.get("congregacao_vinculada")

    allowed_congregs = CONGREGACOES
    if perfil == "SECRETARIO" and vinc:
        allowed_congregs = [vinc]

    with col1:
        if ev and val("congregacao") in allowed_congregs:
            congregacao = st.selectbox("🏛️ Congregação*", allowed_congregs, index=allowed_congregs.index(val("congregacao")))
        else:
            congregacao = st.selectbox("🏛️ Congregação*", allowed_congregs, index=None, placeholder="Selecione")

    with col2:
        if ev and val("tipo") in TIPOS:
            tipo = st.selectbox("📌 Tipo da agenda*", TIPOS, index=TIPOS.index(val("tipo")))
        else:
            tipo = st.selectbox("📌 Tipo da agenda*", TIPOS, index=None, placeholder="Selecione")

    with col3:
        subtipo = None
        turma_ebd = None

        if (tipo == "Culto") or (ev and val("tipo") == "Culto" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "Culto":
                options = SUBTIPOS_CULTO
                current = val("subtipo")
                if ev and current in options:
                    subtipo = st.selectbox("✨ Subtipo do Culto", options, index=options.index(current))
                else:
                    subtipo = st.selectbox("✨ Subtipo do Culto", options, index=None, placeholder="Opcional")

        if (tipo == "EBD") or (ev and val("tipo") == "EBD" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "EBD":
                options = TURMAS_EBD
                current = val("turma_ebd")
                if ev and current in options:
                    turma_ebd = st.selectbox("📚 Turma da EBD*", options, index=options.index(current))
                else:
                    turma_ebd = st.selectbox("📚 Turma da EBD*", options, index=None, placeholder="Selecione")

    col4, col5 = st.columns(2)
    with col4:
        data_evento = st.date_input("📅 Data*", value=val("data", date.today()), format="DD/MM/YYYY")
    with col5:
        horario_default = datetime.strptime("19:00", "%H:%M").time()
        horario = st.time_input("🕖 Horário*", value=val("horario", horario_default))

    st.markdown("### 👥 Equipe do Evento")

    st.markdown("#### 👤 Dirigência")
    dirigente1 = st.text_input("👤 Dirigente", value=val("dirigente1", "") or "")
    st.toggle("➕ Adicionar mais dirigentes", key="show_dirigentes_extra")
    if st.session_state.show_dirigentes_extra:
        c1, c2 = st.columns(2)
        with c1:
            dirigente2 = st.text_input("👥 Dirigente 2", value=val("dirigente2", "") or "")
        with c2:
            dirigente3 = st.text_input("👥 Dirigente 3", value=val("dirigente3", "") or "")
    else:
        dirigente2 = val("dirigente2", "") or ""
        dirigente3 = val("dirigente3", "") or ""

    st.markdown("#### 🚪 Portaria")
    portaria1 = st.text_input("🚪 Portaria", value=val("portaria1", "") or "")
    st.toggle("➕ Adicionar mais na portaria", key="show_portaria_extra")
    if st.session_state.show_portaria_extra:
        c1, c2 = st.columns(2)
        with c1:
            portaria2 = st.text_input("🚪 Portaria 2", value=val("portaria2", "") or "")
        with c2:
            portaria3 = st.text_input("🚪 Portaria 3", value=val("portaria3", "") or "")
    else:
        portaria2 = val("portaria2", "") or ""
        portaria3 = val("portaria3", "") or ""

    st.markdown("#### 🤝 Recepção")
    recepcao1 = st.text_input("🤝 Recepção", value=val("recepcao1", "") or "")
    st.toggle("➕ Adicionar mais na recepção", key="show_recepcao_extra")
    if st.session_state.show_recepcao_extra:
        c1, c2 = st.columns(2)
        with c1:
            recepcao2 = st.text_input("🤝 Recepção 2", value=val("recepcao2", "") or "")
        with c2:
            recepcao3 = st.text_input("🤝 Recepção 3", value=val("recepcao3", "") or "")
    else:
        recepcao2 = val("recepcao2", "") or ""
        recepcao3 = val("recepcao3", "") or ""

    secretaria = st.text_input("🗂️ Secretaria", value=val("secretaria", "") or "")
    observacoes = st.text_area("📝 Observações", value=val("observacoes", "") or "", height=90)

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


def page_agenda_semana():
    st.markdown(
        f"""
        <div class="modern-card">
          <p class="card-title">📊 Agenda da Semana</p>
          <p class="card-sub">Área interna para consulta e exportação.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

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
    df["Dia"] = pd.to_datetime(df["data"]).dt.date.apply(weekday_pt)
    df["Horário"] = df["horario"].astype(str).str[:5]
    df["Tipo"] = df.apply(lambda r: format_tipo(r.to_dict()), axis=1)

    df["Dirigente"] = df.apply(lambda r: join_people(r.dirigente1, r.dirigente2, r.dirigente3), axis=1)
    df["Portaria"] = df.apply(lambda r: join_people(r.portaria1, r.portaria2, r.portaria3), axis=1)
    df["Recepção"] = df.apply(lambda r: join_people(r.recepcao1, r.recepcao2, r.recepcao3), axis=1)

    view = df[["Dia", "Data", "Horário", "congregacao", "Tipo", "Dirigente", "Portaria", "Recepção", "secretaria"]].rename(
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


def page_gerenciar_eventos():
    st.markdown(
        f"""
        <div class="modern-card">
          <p class="card-title">⚙️ Gerenciar Eventos</p>
          <p class="card-sub">Editar ou excluir registros.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

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

    st.dataframe(df[["id", "Data", "Horário", "congregacao", "Tipo"]], use_container_width=True, hide_index=True)

    selected = st.selectbox("Selecione o ID do evento", df["id"].tolist())
    colA, colB = st.columns(2)
    with colA:
        if st.button("Editar", type="primary", use_container_width=True):
            st.session_state.edit_id = selected
            st.session_state.page = "Cadastrar Evento"
            st.rerun()
    with colB:
        if st.button("Excluir", type="secondary", use_container_width=True):
            delete_event(selected)
            st.success("Evento excluído.")
            st.rerun()


def page_usuarios():
    st.markdown(
        f"""
        <div class="modern-card">
          <p class="card-title">👥 Usuários</p>
          <p class="card-sub">Somente ADMIN pode cadastrar e gerenciar usuários.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not has_role("ADMIN"):
        st.error("Acesso negado. Esta área é somente para ADMIN.")
        return

    tab1, tab2 = st.tabs(["➕ Cadastrar usuário", "📋 Gerenciar usuários"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("👤 Nome*", placeholder="Nome completo")
        with col2:
            username = st.text_input("🆔 Usuário*", placeholder="Ex: joao.silva")

        col3, col4 = st.columns(2)
        with col3:
            senha = st.text_input("🔑 Senha*", type="password", placeholder="Defina uma senha")
        with col4:
            perfil = st.selectbox("🎚️ Perfil*", ROLES, index=None, placeholder="Escolha o perfil")

        congreg_vinc = None
        if perfil == "SECRETARIO":
            congreg_vinc = st.selectbox("🏛️ Congregação vinculada*", CONGREGACOES, index=None, placeholder="Selecione")

        if st.button("Criar usuário", type="primary", use_container_width=True):
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
            if st.button("Desativar", type="secondary", use_container_width=True):
                set_user_active(int(sel), False)
                st.success("Usuário desativado.")
                st.rerun()
        with colB:
            if st.button("Ativar", type="secondary", use_container_width=True):
                set_user_active(int(sel), True)
                st.success("Usuário ativado.")
                st.rerun()
        with colC:
            nova = st.text_input("Nova senha (reset)", type="password", placeholder="Digite uma nova senha", key="nova_senha")
            if st.button("Resetar senha", type="secondary", use_container_width=True):
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
