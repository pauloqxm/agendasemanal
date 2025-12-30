# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from io import BytesIO
from urllib.request import urlopen

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

# PDF (A4)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

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
# Paleta
# =========================
COLORS = {
    "primary": "#0A1F44",
    "secondary": "#1A365D",
    "accent": "#2C5282",
    "light": "#4A90E2",
    "success": "#38A169",
    "warning": "#D69E2E",
    "danger": "#E53E3E",
    "background": "#F2F4F8",   # cinza claro geral
    "card": "#FFFFFF",
    "text": "#1A202C",
    "text_light": "#718096",
    "border": "#E2E8F0",
}

# =========================
# CSS
# =========================
def apply_css():
    css = f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background: {COLORS['background']} !important;
    }}

    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-right: none;
    }}

    /* Topbar */
    .topbar {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
        color: white;
        box-shadow: 0 10px 25px rgba(10, 31, 68, 0.14);
    }}
    .topbar-content {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
    }}
    .church-info {{
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 280px;
    }}
    .logo-wrap img {{
        width: 64px;
        height: 64px;
        border-radius: 14px;
        object-fit: cover;
        border: 3px solid rgba(255,255,255,0.20);
        background: rgba(255,255,255,0.08);
    }}
    .church-text h1 {{
        font-size: 1.15rem;
        font-weight: 800;
        margin: 0;
        color: white;
        line-height: 1.2;
    }}
    .church-text p {{
        font-size: 0.9rem;
        opacity: 0.92;
        margin: 4px 0 0 0;
        color: rgba(255,255,255,0.92);
    }}

    /* Cards */
    .modern-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 14px;
    }}

    .event-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        padding: 14px 14px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06);
        margin-bottom: 12px;
        border-left: 5px solid {COLORS['light']};
    }}

    /* Botões */
    .stButton > button {{
        border-radius: 10px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease;
        min-height: 42px;
        padding: 0.55rem 0.9rem !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1.1 !important;
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
        border: 2px solid {COLORS['border']} !important;
    }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover {{
        border-color: {COLORS['light']} !important;
    }}

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stDateInput input {{
        border-radius: 10px !important;
        border: 2px solid {COLORS['border']} !important;
    }}

    /* Tabs (conteúdo) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: transparent;
        padding: 4px;
        border-radius: 12px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        border-radius: 10px;
        padding: 8px 14px;
        background: white;
        border: 1px solid {COLORS['border']};
        color: {COLORS['text_light']};
        font-weight: 700;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['primary']} !important;
        color: white !important;
        border-color: {COLORS['primary']} !important;
    }}

    /* Badge */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 800;
        margin-left: 8px;
        background: rgba(74, 144, 226, 0.10);
        color: {COLORS['accent']};
        border: 1px solid rgba(74, 144, 226, 0.18);
        white-space: nowrap;
    }}

    /* A4 Preview */
    .a4-sheet {{
        width: 210mm;
        min-height: 297mm;
        background: white;
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        margin: 14px auto;
        padding: 14mm 14mm;
    }}
    .a4-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        border-bottom: 2px solid rgba(10, 31, 68, 0.15);
        padding-bottom: 8px;
        margin-bottom: 12px;
    }}
    .a4-title {{
        font-size: 12pt;
        font-weight: 900;
        color: {COLORS['primary']};
        text-align: center;
        margin: 0;
    }}
    .a4-sub {{
        font-size: 9pt;
        color: {COLORS['text_light']};
        margin: 4px 0 0 0;
        text-align: center;
        font-weight: 600;
    }}
    .a4-day {{
        margin-top: 10px;
        font-size: 10pt;
        font-weight: 900;
        color: {COLORS['primary']};
        text-transform: uppercase;
    }}
    .a4-item {{
        margin: 6px 0 0 0;
        font-size: 9.5pt;
        color: {COLORS['text']};
        line-height: 1.35;
    }}
    .a4-dot {{
        color: {COLORS['accent']};
        font-weight: 900;
        margin-right: 6px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# =========================
# Estado
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

def weekday_pt_br(d: date) -> str:
    # date.weekday(): 0=segunda ... 6=domingo
    nomes = [
        "SEGUNDA-FEIRA",
        "TERÇA-FEIRA",
        "QUARTA-FEIRA",
        "QUINTA-FEIRA",
        "SEXTA-FEIRA",
        "SÁBADO",
        "DOMINGO",
    ]
    try:
        return nomes[d.weekday()]
    except Exception:
        return ""

def safe_fetch_logo_bytes(url: str) -> BytesIO | None:
    try:
        with urlopen(url, timeout=6) as r:
            data = r.read()
        bio = BytesIO(data)
        bio.seek(0)
        return bio
    except Exception:
        return None

# =========================
# Topbar
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
              <span class="badge">Online</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Abas topo (páginas)
# =========================
def render_page_tabs():
    if not st.session_state.auth_ok:
        pages = [
            {"id": "Agenda Pública", "label": "Agenda Pública"},
            {"id": "Login", "label": "Login"},
        ]
    else:
        pages = [
            {"id": "Agenda Pública", "label": "Agenda Pública"},
            {"id": "Agenda da Semana", "label": "Agenda da Semana"},
            {"id": "Cadastrar Evento", "label": "Cadastrar Evento"},
            {"id": "Gerenciar Eventos", "label": "Gerenciar Eventos"},
        ]
        if has_role("ADMIN"):
            pages.append({"id": "Usuários", "label": "Usuários"})

    cols = st.columns(len(pages))
    for col, p in zip(cols, pages):
        with col:
            active = (st.session_state.page == p["id"])
            btype = "primary" if active else "secondary"
            if st.button(p["label"], key=f"page_{p['id']}", type=btype, use_container_width=True):
                st.session_state.page = p["id"]
                st.rerun()

# =========================
# Card de evento (com DIA DA SEMANA)
# =========================
def _event_card(ev: dict):
    d = pd.to_datetime(ev["data"]).date() if ev.get("data") else date.today()
    dia_semana = weekday_pt_br(d)

    data_txt = _fmt_date_br(d)
    hora_txt = _fmt_time_hhmm(ev.get("horario"))
    congreg = ev.get("congregacao") or ""

    tipo_txt = format_tipo(ev)
    subtipo = ev.get("subtipo") or ""
    turma = ev.get("turma_ebd") or ""

    badges = ""
    if subtipo:
        badges += f'<span class="badge">🎯 {subtipo}</span>'
    if turma:
        badges += f'<span class="badge">📚 {turma}</span>'
    if ev.get("secretaria"):
        badges += f'<span class="badge">📋 {ev.get("secretaria")}</span>'

    dirigentes = join_people(ev.get("dirigente1"), ev.get("dirigente2"), ev.get("dirigente3"))
    portaria = join_people(ev.get("portaria1"), ev.get("portaria2"), ev.get("portaria3"))
    recepcao = join_people(ev.get("recepcao1"), ev.get("recepcao2"), ev.get("recepcao3"))

    st.markdown(
        f"""
        <div class="event-card">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
            <div style="flex:1;">
              <div style="font-weight:900; color:{COLORS['primary']}; font-size:0.95rem; letter-spacing:0.4px;">
                {dia_semana}
              </div>
              <div style="font-weight:900; font-size:1.08rem; color:{COLORS['primary']}; margin-top:2px;">
                {tipo_txt}
              </div>
              <div style="font-size:0.92rem; color:{COLORS['text_light']}; margin-top:4px; font-weight:700;">
                📅 {data_txt} • 🕒 {hora_txt} • 🏛️ {congreg}
              </div>
            </div>
            <div style="text-align:right;">
              {badges}
            </div>
          </div>

          <div style="margin-top:12px; font-size:0.95rem; line-height:1.45;">
            <div><b style="color:{COLORS['secondary']};">👤 Dirigentes:</b> {dirigentes or "Não informado"}</div>
            <div><b style="color:{COLORS['secondary']};">🚪 Portaria:</b> {portaria or "Não informado"}</div>
            <div><b style="color:{COLORS['secondary']};">🤝 Recepção:</b> {recepcao or "Não informado"}</div>
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
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom: 1.2rem;">
              <img src="{LOGO_URL}" style="width:54px; height:54px; border-radius:12px; border:2px solid rgba(255,255,255,0.20);">
              <div style="color:white; font-weight:800; margin-top:0.6rem;">Agenda</div>
              <div style="color:rgba(255,255,255,0.85); font-size:0.85rem;">Painel rápido</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        ok, msg = test_db_connection()
        color = COLORS["success"] if ok else COLORS["danger"]
        st.markdown(
            f"<div style='text-align:center; color:{color}; font-weight:800; font-size:0.85rem; margin-bottom:0.8rem;'>{msg}</div>",
            unsafe_allow_html=True
        )

        st.divider()

        if st.session_state.auth_ok:
            user = st.session_state.user or {}
            st.markdown(
                f"""
                <div style="color:white; padding:0.7rem; background:rgba(255,255,255,0.10); border-radius:12px;">
                  <div style="font-weight:900;">{user.get('nome') or user.get('username')}</div>
                  <div style="opacity:0.9; font-size:0.85rem;">Perfil: {user.get('perfil')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("")
            if st.button("Sair", type="secondary", use_container_width=True):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()
        else:
            st.caption("Acesso público liberado.")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Agenda Pública", type="secondary", use_container_width=True):
                st.session_state.page = "Agenda Pública"
                st.rerun()
        with c2:
            if not st.session_state.auth_ok:
                if st.button("Login", type="secondary", use_container_width=True):
                    st.session_state.page = "Login"
                    st.rerun()
            else:
                if st.button("Semana", type="secondary", use_container_width=True):
                    st.session_state.page = "Agenda da Semana"
                    st.rerun()

# =========================
# PDF A4 (Todos)
# =========================
def build_pdf_a4(events: list[dict], monday: date, sunday: date, congregacao_label: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.6*cm,
        rightMargin=1.6*cm,
        topMargin=1.3*cm,
        bottomMargin=1.3*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Normal"],
        fontSize=12,
        leading=14,
        textColor=rl_colors.HexColor(COLORS["primary"]),
        alignment=1,
        fontName="Helvetica-Bold"
    )
    sub_style = ParagraphStyle(
        "sub",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=rl_colors.HexColor("#334155"),
        alignment=1,
        fontName="Helvetica"
    )
    day_style = ParagraphStyle(
        "day",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        textColor=rl_colors.HexColor(COLORS["primary"]),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=4
    )
    item_style = ParagraphStyle(
        "item",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=12,
        textColor=rl_colors.HexColor("#0f172a"),
        fontName="Helvetica"
    )

    story = []

    # Header table (logo + textos)
    logo_bio = safe_fetch_logo_bytes(LOGO_URL)
    logo = None
    if logo_bio:
        try:
            logo = Image(logo_bio, width=2.2*cm, height=2.2*cm)
        except Exception:
            logo = None

    header_left = logo if logo else Paragraph("", styles["Normal"])
    header_mid = Paragraph(
        f"<b>{IGREJA_NOME}</b><br/><font size='8'>Agenda semanal oficial</font>",
        ParagraphStyle(
            "hmid",
            parent=styles["Normal"],
            alignment=1,
            textColor=rl_colors.HexColor(COLORS["primary"]),
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=11
        )
    )
    header_right = Paragraph("", styles["Normal"])

    t = Table([[header_left, header_mid, header_right]], colWidths=[2.6*cm, 12.0*cm, 2.6*cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (0,0), "LEFT"),
        ("ALIGN", (1,0), (1,0), "CENTER"),
        ("ALIGN", (2,0), (2,0), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    periodo = f"{_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"
    story.append(Paragraph(f"RODÍZIO SEMANAL – PERÍODO DE {periodo}", title_style))
    story.append(Paragraph(f"{congregacao_label}", sub_style))
    story.append(Spacer(1, 10))

    if not events:
        story.append(Paragraph("Nenhum evento cadastrado neste período.", item_style))
        doc.build(story)
        buf.seek(0)
        return buf.read()

    df = pd.DataFrame(events).copy()
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    # Agrupar por dia
    for d, sub in df.groupby("data"):
        dia_sem = weekday_pt_br(d)
        story.append(Paragraph(dia_sem, day_style))

        for _, r in sub.iterrows():
            hora = (str(r.get("horario"))[:5] if r.get("horario") else "")
            congreg = r.get("congregacao") or ""
            tipo_txt = format_tipo(r.to_dict())

            dirigentes = join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3"))
            portaria = join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3"))
            recepcao = join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3"))

            parts = []
            parts.append(f"<b>{hora}:</b> {tipo_txt} <font color='{COLORS['accent']}'><b>{congreg}</b></font>")
            if dirigentes:
                parts.append(f"Dirigentes: {dirigentes}")
            if portaria:
                parts.append(f"Portaria: {portaria}")
            if recepcao:
                parts.append(f"Recepção: {recepcao}")
            if r.get("secretaria"):
                parts.append(f"Secretaria: {r.get('secretaria')}")
            if r.get("observacoes"):
                parts.append(f"Obs: {r.get('observacoes')}")

            line = " <br/> ".join(parts)
            story.append(Paragraph(f"<font color='{COLORS['accent']}'><b>•</b></font> {line}", item_style))

        story.append(Spacer(1, 6))

    doc.build(story)
    buf.seek(0)
    return buf.read()

def render_a4_preview(events: list[dict], monday: date, sunday: date, congregacao_label: str):
    periodo = f"{_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"

    if not events:
        st.markdown(
            f"""
            <div class="a4-sheet">
              <div class="a4-header">
                <div style="display:flex; align-items:center; gap:10px;">
                  <img src="{LOGO_URL}" style="width:46px; height:46px; border-radius:10px; border:1px solid {COLORS['border']}; object-fit:cover;">
                  <div>
                    <div style="font-weight:900; color:{COLORS['primary']}; font-size:9.5pt;">{IGREJA_NOME}</div>
                    <div style="color:{COLORS['text_light']}; font-size:8.5pt; font-weight:700;">Agenda semanal oficial</div>
                  </div>
                </div>
                <div style="text-align:right; font-size:8.5pt; color:{COLORS['text_light']}; font-weight:800;">
                  {congregacao_label}
                </div>
              </div>
              <p class="a4-title">RODÍZIO SEMANAL – PERÍODO DE {periodo}</p>
              <p class="a4-sub">Nenhum evento cadastrado neste período.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    df = pd.DataFrame(events).copy()
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    html_parts = []
    html_parts.append(f"""
        <div class="a4-sheet">
          <div class="a4-header">
            <div style="display:flex; align-items:center; gap:10px;">
              <img src="{LOGO_URL}" style="width:46px; height:46px; border-radius:10px; border:1px solid {COLORS['border']}; object-fit:cover;">
              <div>
                <div style="font-weight:900; color:{COLORS['primary']}; font-size:9.5pt;">{IGREJA_NOME}</div>
                <div style="color:{COLORS['text_light']}; font-size:8.5pt; font-weight:700;">Agenda semanal oficial</div>
              </div>
            </div>
            <div style="text-align:right; font-size:8.5pt; color:{COLORS['text_light']}; font-weight:800;">
              {congregacao_label}
            </div>
          </div>

          <p class="a4-title">RODÍZIO SEMANAL – PERÍODO DE {periodo}</p>
    """)

    for d, sub in df.groupby("data"):
        dia_sem = weekday_pt_br(d)
        html_parts.append(f"<div class='a4-day'>{dia_sem}</div>")

        for _, r in sub.iterrows():
            hora = r.get("horario_txt") or ""
            tipo_txt = format_tipo(r.to_dict())
            congreg = r.get("congregacao") or ""

            dirigentes = join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3"))
            portaria = join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3"))
            recepcao = join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3"))

            linha = f"<b>{hora}:</b> <b>{tipo_txt}</b> <span style='color:{COLORS['accent']}; font-weight:900;'>({congreg})</span>"
            extras = []
            if dirigentes:
                extras.append(f"<b>Dirigentes:</b> {dirigentes}")
            if portaria:
                extras.append(f"<b>Portaria:</b> {portaria}")
            if recepcao:
                extras.append(f"<b>Recepção:</b> {recepcao}")
            if r.get("secretaria"):
                extras.append(f"<b>Secretaria:</b> {r.get('secretaria')}")
            if r.get("observacoes"):
                extras.append(f"<b>Obs:</b> {r.get('observacoes')}")

            extra_txt = ("<br/>".join(extras)) if extras else ""
            html_parts.append(
                f"""
                <div class="a4-item">
                  <span class="a4-dot">•</span> {linha}
                  {"<br/>" + extra_txt if extra_txt else ""}
                </div>
                """
            )

    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)

# =========================
# Login
# =========================
def page_login():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color:{COLORS['primary']}; margin:0;">Acesso ao Sistema</h2>
          <p style="color:{COLORS['text_light']}; margin:6px 0 0 0; font-weight:700;">
            Área restrita para cadastro e gerenciamento da agenda.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)

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
# Agenda Pública
# =========================
def page_agenda_publica():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color:{COLORS['primary']}; margin:0;">Agenda Pública</h2>
          <p style="color:{COLORS['text_light']}; margin:6px 0 0 0; font-weight:700;">
            Visualização pública dos eventos. Acesso livre sem necessidade de login.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtros (sem “blocos brancos” soltos)
    c1, c2, c3 = st.columns([1.2, 1.0, 0.9])

    with c1:
        st.markdown("<div class='modern-card' style='padding:14px;'>"
                    "<div style='font-weight:900; color:"+COLORS["primary"]+"; margin-bottom:8px;'>Semana de referência</div>",
                    unsafe_allow_html=True)
        ref = st.date_input("Semana de referência", value=date.today(), format="DD/MM/YYYY", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='modern-card' style='padding:14px;'>"
                    "<div style='font-weight:900; color:"+COLORS["primary"]+"; margin-bottom:8px;'>Congregação</div>",
                    unsafe_allow_html=True)
        congregacao = st.selectbox("Congregação", ["Todas"] + CONGREGACOES, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='modern-card' style='padding:14px;'>"
                    "<div style='font-weight:900; color:"+COLORS["primary"]+"; margin-bottom:8px;'>Exibição</div>",
                    unsafe_allow_html=True)
        modo = st.selectbox("Exibição", ["Cards", "Tabela"], index=0, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    monday, sunday = week_bounds(ref)

    eventos = list_events_between(
        monday,
        sunday,
        congregacao=None if congregacao == "Todas" else congregacao,
        tipo=None
    )

    congreg_label = "Todas as congregações" if congregacao == "Todas" else f"Congregação: {congregacao}"

    st.markdown(
        f"""
        <div class="modern-card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
            <div>
              <div style="font-weight:900; color:{COLORS['primary']}; font-size:1.02rem;">Resumo da Semana</div>
              <div style="color:{COLORS['text_light']}; font-weight:800; margin-top:4px;">
                {_fmt_date_br(monday)} até {_fmt_date_br(sunday)}
              </div>
            </div>
            <span class="badge">{congregacao}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Tabs (inclui TODOS A4)
    tab_todos, tab_culto, tab_ebd, tab_oracao, tab_ensaio = st.tabs(
        ["🗓️ Todos (A4)", "🎵 Cultos", "📚 EBD", "🙏 Oração", "🎤 Ensaios"]
    )

    # TODOS (A4) com PDF
    with tab_todos:
        st.markdown(
            f"""
            <div class="modern-card">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
                <div>
                  <div style="font-weight:900; color:{COLORS['primary']}; font-size:1.05rem;">Folha A4</div>
                  <div style="color:{COLORS['text_light']}; font-weight:800; margin-top:4px;">
                    Pronta para imprimir ou mandar no WhatsApp.
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Preview A4
        render_a4_preview(eventos, monday, sunday, congreg_label)

        # PDF
        pdf_bytes = build_pdf_a4(eventos, monday, sunday, congreg_label)
        st.download_button(
            "Baixar PDF (A4)",
            data=pdf_bytes,
            file_name=f"rodizio_semanal_{monday.strftime('%Y%m%d')}_{sunday.strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # Se não tem eventos, as outras abas só avisam
    if not eventos:
        with tab_culto:
            st.info("Nenhum evento cadastrado nesta semana.")
        with tab_ebd:
            st.info("Nenhum evento cadastrado nesta semana.")
        with tab_oracao:
            st.info("Nenhum evento cadastrado nesta semana.")
        with tab_ensaio:
            st.info("Nenhum evento cadastrado nesta semana.")
        return

    df = pd.DataFrame(eventos)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    def render_group(tipo_nome: str, container):
        with container:
            sub = df[df["tipo"] == tipo_nome].copy()
            if sub.empty:
                st.info("Sem registros aqui nesta semana.")
                return

            if modo == "Tabela":
                view = sub.copy()
                view["Data"] = view["data"].apply(lambda x: x.strftime("%d/%m/%Y"))
                view["Dia"] = view["data"].apply(weekday_pt_br)
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

                show = view[["Dia", "Data", "Horário", "congregacao", "Tipo", "Dirigentes", "Portaria", "Recepção", "secretaria"]]
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
# Cadastro de Evento
# =========================
def page_cadastrar_evento():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color:{COLORS['primary']}; margin:0;">
            {"Editar Evento" if st.session_state.edit_id else "Cadastrar Evento"}
          </h2>
          <p style="color:{COLORS['text_light']}; margin:6px 0 0 0; font-weight:700;">
            Preencha as informações do evento.
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

    col1, col2, col3 = st.columns(3)

    user = st.session_state.user or {}
    perfil = user.get("perfil")
    vinc = user.get("congregacao_vinculada")

    allowed_congregs = CONGREGACOES
    if perfil == "SECRETARIO" and vinc:
        allowed_congregs = [vinc]

    with col1:
        if ev and val("congregacao") in allowed_congregs:
            congregacao = st.selectbox("Congregação*", allowed_congregs, index=allowed_congregs.index(val("congregacao")))
        else:
            congregacao = st.selectbox("Congregação*", allowed_congregs, index=None, placeholder="Selecione")

    with col2:
        if ev and val("tipo") in TIPOS:
            tipo = st.selectbox("Tipo*", TIPOS, index=TIPOS.index(val("tipo")))
        else:
            tipo = st.selectbox("Tipo*", TIPOS, index=None, placeholder="Selecione")

    with col3:
        subtipo = None
        turma_ebd = None

        if (tipo == "Culto") or (ev and val("tipo") == "Culto" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "Culto":
                options = SUBTIPOS_CULTO
                current = val("subtipo")
                subtipo = st.selectbox("Subtipo do Culto", options, index=options.index(current) if (ev and current in options) else None)

        if (tipo == "EBD") or (ev and val("tipo") == "EBD" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "EBD":
                options = TURMAS_EBD
                current = val("turma_ebd")
                turma_ebd = st.selectbox("Turma da EBD*", options, index=options.index(current) if (ev and current in options) else None)

    col4, col5 = st.columns(2)
    with col4:
        data_evento = st.date_input("Data*", value=val("data", date.today()), format="DD/MM/YYYY")
    with col5:
        horario_default = datetime.strptime("19:00", "%H:%M").time()
        horario = st.time_input("Horário*", value=val("horario", horario_default))

    st.markdown("<div class='modern-card'><b>Equipe do Evento</b></div>", unsafe_allow_html=True)

    dirigente1 = st.text_input("Dirigente", value=val("dirigente1", "") or "")
    st.toggle("Adicionar mais dirigentes", key="show_dirigentes_extra")
    if st.session_state.show_dirigentes_extra:
        d1, d2 = st.columns(2)
        with d1:
            dirigente2 = st.text_input("Dirigente 2", value=val("dirigente2", "") or "")
        with d2:
            dirigente3 = st.text_input("Dirigente 3", value=val("dirigente3", "") or "")
    else:
        dirigente2 = val("dirigente2", "") or ""
        dirigente3 = val("dirigente3", "") or ""

    portaria1 = st.text_input("Portaria", value=val("portaria1", "") or "")
    st.toggle("Adicionar mais na portaria", key="show_portaria_extra")
    if st.session_state.show_portaria_extra:
        p1, p2 = st.columns(2)
        with p1:
            portaria2 = st.text_input("Portaria 2", value=val("portaria2", "") or "")
        with p2:
            portaria3 = st.text_input("Portaria 3", value=val("portaria3", "") or "")
    else:
        portaria2 = val("portaria2", "") or ""
        portaria3 = val("portaria3", "") or ""

    recepcao1 = st.text_input("Recepção", value=val("recepcao1", "") or "")
    st.toggle("Adicionar mais na recepção", key="show_recepcao_extra")
    if st.session_state.show_recepcao_extra:
        r1, r2 = st.columns(2)
        with r1:
            recepcao2 = st.text_input("Recepção 2", value=val("recepcao2", "") or "")
        with r2:
            recepcao3 = st.text_input("Recepção 3", value=val("recepcao3", "") or "")
    else:
        recepcao2 = val("recepcao2", "") or ""
        recepcao3 = val("recepcao3", "") or ""

    secretaria = st.text_input("Secretaria", value=val("secretaria", "") or "")
    observacoes = st.text_area("Observações", value=val("observacoes", "") or "", height=90)

    b1, b2 = st.columns(2)
    with b1:
        salvar = st.button("Salvar", type="primary", use_container_width=True)
    with b2:
        cancelar = st.button("Cancelar", type="secondary", use_container_width=True)

    if cancelar:
        st.session_state.edit_id = None
        st.session_state.page = "Agenda da Semana"
        st.rerun()

    if salvar:
        if not congregacao:
            st.error("Selecione a Congregação.")
            return
        if not tipo:
            st.error("Selecione o Tipo.")
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
# Agenda da Semana
# =========================
def page_agenda_semana():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color:{COLORS['primary']}; margin:0;">Agenda da Semana</h2>
          <p style="color:{COLORS['text_light']}; margin:6px 0 0 0; font-weight:700;">
            Visualização detalhada para equipe.
          </p>
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
    df["Dia"] = pd.to_datetime(df["data"]).dt.date.apply(weekday_pt_br)
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

# =========================
# Gerenciar Eventos
# =========================
def page_gerenciar_eventos():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color:{COLORS['primary']}; margin:0;">Gerenciar Eventos</h2>
          <p style="color:{COLORS['text_light']}; margin:6px 0 0 0; font-weight:700;">
            Editar ou excluir eventos cadastrados.
          </p>
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

    a, b = st.columns(2)
    with a:
        if st.button("Editar", type="primary", use_container_width=True):
            st.session_state.edit_id = selected
            st.session_state.page = "Cadastrar Evento"
            st.rerun()
    with b:
        if st.button("Excluir", type="secondary", use_container_width=True):
            delete_event(selected)
            st.success("Evento excluído.")
            st.rerun()

# =========================
# Usuários
# =========================
def page_usuarios():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="color:{COLORS['primary']}; margin:0;">Usuários</h2>
          <p style="color:{COLORS['text_light']}; margin:6px 0 0 0; font-weight:700;">
            Área administrativa de acessos.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not has_role("ADMIN"):
        st.error("Acesso negado. Esta área é somente para ADMIN.")
        return

    tab1, tab2 = st.tabs(["Cadastrar usuário", "Gerenciar usuários"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome*", placeholder="Nome completo")
        with col2:
            username = st.text_input("Usuário*", placeholder="Ex: joao.silva")

        col3, col4 = st.columns(2)
        with col3:
            senha = st.text_input("Senha*", type="password")
        with col4:
            perfil = st.selectbox("Perfil*", ROLES, index=None, placeholder="Escolha o perfil")

        congreg_vinc = None
        if perfil == "SECRETARIO":
            congreg_vinc = st.selectbox("Congregação vinculada*", CONGREGACOES, index=None)

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
            create_user(nome, username, senha, perfil, congreg_vinc)
            st.success("Usuário criado.")
            st.rerun()

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

        cA, cB, cC = st.columns(3)
        with cA:
            if st.button("Desativar", use_container_width=True, type="secondary"):
                set_user_active(int(sel), False)
                st.success("Usuário desativado.")
                st.rerun()
        with cB:
            if st.button("Ativar", use_container_width=True, type="secondary"):
                set_user_active(int(sel), True)
                st.success("Usuário ativado.")
                st.rerun()
        with cC:
            nova = st.text_input("Nova senha", type="password", key="nova_senha_admin")
            if st.button("Resetar senha", use_container_width=True, type="secondary"):
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
