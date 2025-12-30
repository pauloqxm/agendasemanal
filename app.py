# app.py

import io
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import streamlit.components.v1 as components

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

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
# Paleta (fundo cinza claro, azul nos detalhes)
# =========================
COLORS = {
    "primary": "#0A1F44",
    "secondary": "#1A365D",
    "accent": "#2563EB",
    "accent2": "#1D4ED8",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    "background": "#F3F4F6",
    "card": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#111827",
    "text_light": "#6B7280",
}

# =========================
# Estilo
# =========================
def apply_css():
    css = f"""
    <style>
    .stApp {{
        background: {COLORS['background']};
    }}
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-right: none;
    }}

    /* Cards */
    .modern-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 14px;
    }}

    /* Topbar */
    .topbar {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
        color: white;
        box-shadow: 0 14px 30px rgba(10, 31, 68, 0.18);
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
        gap: 12px;
        min-width: 280px;
    }}
    .logo-wrap img {{
        width: 64px;
        height: 64px;
        border-radius: 14px;
        object-fit: cover;
        border: 3px solid rgba(255,255,255,0.18);
    }}
    .church-text h1 {{
        font-size: 1.2rem;
        font-weight: 800;
        margin: 0;
        color: white;
        line-height: 1.15;
    }}
    .church-text p {{
        font-size: 0.88rem;
        opacity: 0.9;
        margin: 4px 0 0 0;
    }}

    /* Botões */
    .stButton > button {{
        border-radius: 10px;
        font-weight: 700;
        transition: all 0.2s ease;
        padding-top: 0.58rem;
        padding-bottom: 0.58rem;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
    }}
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['accent2']} 0%, {COLORS['accent']} 100%);
        border: none;
    }}
    div[data-testid="stButton"] > button[kind="secondary"] {{
        background: white;
        color: {COLORS['primary']};
        border: 2px solid {COLORS['border']};
    }}

    /* Inputs */
    .stTextInput input,
    .stDateInput input,
    .stTimeInput input,
    .stTextArea textarea {{
        border-radius: 10px;
        border: 2px solid {COLORS['border']};
    }}
    .stTextInput input:focus,
    .stDateInput input:focus,
    .stTimeInput input:focus,
    .stTextArea textarea:focus {{
        border-color: {COLORS['accent']};
        box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
    }}

    /* Tabs padrão do Streamlit */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: rgba(255,255,255,0.65);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        border-radius: 10px;
        padding: 8px 14px;
        color: {COLORS['text_light']};
        font-weight: 700;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['primary']} !important;
        color: white !important;
    }}

    /* Event card */
    .event-card {{
        background: white;
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        border-left: 5px solid {COLORS['accent']};
    }}
    .event-day {{
        font-weight: 900;
        color: {COLORS['primary']};
        font-size: 0.85rem;
        text-transform: uppercase;
        margin-bottom: 6px;
        letter-spacing: 0.3px;
    }}
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.18rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 800;
        border: 1px solid rgba(0,0,0,0.06);
        background: rgba(37,99,235,0.10);
        color: {COLORS['accent2']};
        margin-left: 6px;
    }}

    /* A4 */
    .a4-wrap {{
        display:flex;
        justify-content:center;
        width: 100%;
    }}
    .a4-sheet {{
        width: 21cm;
        min-height: 29.7cm;
        background: white;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 12px 28px rgba(0,0,0,0.08);
        padding: 1.4cm 1.6cm;
        font-family: Arial, sans-serif;
        font-size: 10.2pt;
        line-height: 1.35;
    }}
    .a4-topline {{
        height: 6px;
        background: {COLORS['primary']};
        border-radius: 6px;
        margin-bottom: 12px;
    }}
    .a4-header {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 10px;
        margin-bottom: 10px;
    }}
    .a4-brand {{
        display:flex;
        align-items:center;
        gap: 10px;
    }}
    .a4-logo {{
        width: 46px;
        height: 46px;
        border-radius: 10px;
        object-fit: cover;
        border: 1px solid {COLORS['border']};
    }}
    .a4-title {{
        text-align:center;
        font-weight: 900;
        color: {COLORS['primary']};
        margin: 12px 0 10px 0;
        font-size: 11pt;
        letter-spacing: 0.3px;
    }}
    .a4-day {{
        margin-top: 12px;
        font-weight: 900;
        color: {COLORS['primary']};
        border-bottom: 1px solid {COLORS['border']};
        padding-bottom: 4px;
        text-transform: uppercase;
    }}
    .a4-item {{
        margin-top: 6px;
    }}
    .a4-dot {{
        color: {COLORS['accent2']};
        font-weight: 900;
        margin-right: 6px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

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
# Abas de navegação no topo (em botões)
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

    cols = st.columns(len(pages), vertical_alignment="center")
    for col, p in zip(cols, pages):
        with col:
            active = (st.session_state.page == p["id"])
            btn_type = "primary" if active else "secondary"
            if st.button(p["label"], key=f"nav_{p['id']}", type=btn_type, use_container_width=True):
                st.session_state.page = p["id"]
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

def weekday_pt_br(d: date) -> str:
    dias = ["SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO", "DOMINGO"]
    return dias[d.weekday()]

# =========================
# Card do evento (com dia da semana em destaque)
# =========================
def _event_card(ev: dict):
    d = pd.to_datetime(ev["data"]).date() if ev.get("data") else date.today()
    dia_sem = weekday_pt_br(d)
    data_txt = _fmt_date_br(d)
    hora_txt = _fmt_time_hhmm(ev.get("horario"))
    congreg = ev.get("congregacao") or ""
    tipo_txt = format_tipo(ev)

    dirigentes = join_people(ev.get("dirigente1"), ev.get("dirigente2"), ev.get("dirigente3"))
    portaria = join_people(ev.get("portaria1"), ev.get("portaria2"), ev.get("portaria3"))
    recepcao = join_people(ev.get("recepcao1"), ev.get("recepcao2"), ev.get("recepcao3"))

    badge_parts = []
    if ev.get("subtipo"):
        badge_parts.append(f"<span class='badge'>{ev.get('subtipo')}</span>")
    if ev.get("turma_ebd"):
        badge_parts.append(f"<span class='badge'>{ev.get('turma_ebd')}</span>")
    if ev.get("secretaria"):
        badge_parts.append(f"<span class='badge'>{ev.get('secretaria')}</span>")
    badges = "".join(badge_parts)

    st.markdown(
        f"""
        <div class="event-card">
          <div class="event-day">{dia_sem}</div>
          <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
            <div style="font-weight:900; color:{COLORS['primary']}; font-size:1.05rem;">{tipo_txt}</div>
            <div>{badges}</div>
          </div>
          <div style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700; font-size:0.9rem;">
            {data_txt} • {hora_txt} • {congreg}
          </div>
          <div style="margin-top:10px; color:{COLORS['text']}; font-size:0.95rem;">
            <div><b>Dirigentes</b> {dirigentes or "Não informado"}</div>
            <div><b>Portaria</b> {portaria or "Não informado"}</div>
            <div><b>Recepção</b> {recepcao or "Não informado"}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# A4 HTML
# =========================
def build_a4_html(eventos: list, monday: date, sunday: date, congregacao_label: str):
    periodo = f"{_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"

    if not eventos:
        return f"""
        <div class="a4-wrap">
          <div class="a4-sheet">
            <div class="a4-topline"></div>
            <div class="a4-header">
              <div class="a4-brand">
                <img class="a4-logo" src="{LOGO_URL}">
                <div>
                  <div style="font-weight:900; color:{COLORS['primary']}; font-size:9.6pt;">{IGREJA_NOME}</div>
                  <div style="color:{COLORS['text_light']}; font-weight:800; font-size:8.6pt;">Agenda semanal oficial</div>
                </div>
              </div>
              <div style="text-align:right; color:{COLORS['text_light']}; font-weight:900; font-size:8.6pt;">
                Congregação: {congregacao_label}
              </div>
            </div>
            <div class="a4-title">RODÍZIO SEMANAL – PERÍODO DE {periodo}</div>
            <div style="color:{COLORS['text_light']}; font-weight:700;">Nenhum evento cadastrado neste período.</div>
          </div>
        </div>
        """

    df = pd.DataFrame(eventos).copy()
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    parts = []
    parts.append(f"""
    <div class="a4-wrap">
      <div class="a4-sheet">
        <div class="a4-topline"></div>
        <div class="a4-header">
          <div class="a4-brand">
            <img class="a4-logo" src="{LOGO_URL}">
            <div>
              <div style="font-weight:900; color:{COLORS['primary']}; font-size:9.6pt;">{IGREJA_NOME}</div>
              <div style="color:{COLORS['text_light']}; font-weight:800; font-size:8.6pt;">Agenda semanal oficial</div>
            </div>
          </div>
          <div style="text-align:right; color:{COLORS['text_light']}; font-weight:900; font-size:8.6pt;">
            Congregação: {congregacao_label}
          </div>
        </div>
        <div class="a4-title">RODÍZIO SEMANAL – PERÍODO DE {periodo}</div>
    """)

    for d, sub in df.groupby("data"):
        parts.append(f"<div class='a4-day'>{weekday_pt_br(d)}</div>")

        for _, r in sub.iterrows():
            hora = (r.get("horario_txt") or "").strip()
            tipo_txt = format_tipo(r.to_dict())
            congreg = r.get("congregacao") or ""

            dirigentes = join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3"))
            portaria = join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3"))
            recepcao = join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3"))

            linhas = []
            linhas.append(f"<span class='a4-dot'>•</span> <b>{hora}</b> <b>{tipo_txt}</b> <span style='color:{COLORS['accent2']}; font-weight:900;'>({congreg})</span>")

            extra = []
            if dirigentes:
                extra.append(f"<b>Dirigentes</b> {dirigentes}")
            if portaria:
                extra.append(f"<b>Portaria</b> {portaria}")
            if recepcao:
                extra.append(f"<b>Recepção</b> {recepcao}")
            if r.get("secretaria"):
                extra.append(f"<b>Secretaria</b> {r.get('secretaria')}")
            if r.get("observacoes"):
                extra.append(f"<b>Obs</b> {r.get('observacoes')}")

            if extra:
                linhas.append("<br/>" + "<br/>".join(extra))

            parts.append(f"<div class='a4-item'>{''.join(linhas)}</div>")

    parts.append("</div></div>")
    return "".join(parts)

# =========================
# PDF A4 (ReportLab)
# =========================
def gerar_pdf_a4(eventos: list, monday: date, sunday: date, congregacao_label: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    x_left = 2.0 * cm
    y = h - 2.0 * cm

    c.setFillColorRGB(0.04, 0.12, 0.27)
    c.rect(x_left, y, w - (4.0 * cm), 0.18 * cm, stroke=0, fill=1)
    y -= 0.55 * cm

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_left, y, IGREJA_NOME[:85])

    c.setFont("Helvetica", 8.5)
    c.setFillColorRGB(0.35, 0.38, 0.42)
    c.drawRightString(w - 2.0 * cm, y, f"Congregação: {congregacao_label}")
    y -= 0.65 * cm

    c.setFillColorRGB(0.04, 0.12, 0.27)
    c.setFont("Helvetica-Bold", 10.2)
    c.drawCentredString(w / 2, y, f"RODÍZIO SEMANAL – PERÍODO DE {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}")
    y -= 0.75 * cm

    if not eventos:
        c.setFillColorRGB(0.35, 0.38, 0.42)
        c.setFont("Helvetica", 9)
        c.drawString(x_left, y, "Nenhum evento cadastrado neste período.")
        c.save()
        buf.seek(0)
        return buf.read()

    df = pd.DataFrame(eventos).copy()
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["horario_txt"] = df["horario"].astype(str).str[:5]
    df = df.sort_values(["data", "horario_txt", "congregacao"], ascending=True)

    c.setFillColorRGB(0, 0, 0)
    for d, sub in df.groupby("data"):
        if y < 3.0 * cm:
            c.showPage()
            y = h - 2.0 * cm

        c.setFillColorRGB(0.04, 0.12, 0.27)
        c.setFont("Helvetica-Bold", 9.6)
        c.drawString(x_left, y, weekday_pt_br(d))
        y -= 0.45 * cm

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        for _, r in sub.iterrows():
            if y < 2.2 * cm:
                c.showPage()
                y = h - 2.0 * cm

            hora = (r.get("horario_txt") or "").strip()
            tipo_txt = format_tipo(r.to_dict())
            congreg = r.get("congregacao") or ""

            line = f"• {hora}  {tipo_txt} ({congreg})"
            c.drawString(x_left, y, line[:115])
            y -= 0.42 * cm

            extras = []
            dirigentes = join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3"))
            portaria = join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3"))
            recepcao = join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3"))

            if dirigentes:
                extras.append(("Dirigentes", dirigentes))
            if portaria:
                extras.append(("Portaria", portaria))
            if recepcao:
                extras.append(("Recepção", recepcao))
            if r.get("secretaria"):
                extras.append(("Secretaria", str(r.get("secretaria"))))
            if r.get("observacoes"):
                extras.append(("Obs", str(r.get("observacoes"))))

            if extras:
                c.setFillColorRGB(0.35, 0.38, 0.42)
                c.setFont("Helvetica", 8.6)
                for label, val in extras:
                    if y < 2.2 * cm:
                        c.showPage()
                        y = h - 2.0 * cm
                    c.drawString(x_left + 0.55 * cm, y, f"{label}: {val}"[:125])
                    y -= 0.38 * cm
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica", 9)

        y -= 0.2 * cm

    c.save()
    buf.seek(0)
    return buf.read()

# =========================
# Sidebar
# =========================
def sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom: 1.2rem;">
              <img src="{LOGO_URL}" style="width:58px; height:58px; border-radius:12px; border:2px solid rgba(255,255,255,0.18); object-fit:cover;">
              <div style="margin-top:10px; color:white; font-weight:900;">Agenda da Igreja</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        ok, msg = test_db_connection()
        cor = "#22C55E" if ok else "#EF4444"
        st.markdown(
            f"<div style='text-align:center; font-weight:800; color:{cor}; font-size:0.85rem; margin-bottom: 0.7rem;'>{msg}</div>",
            unsafe_allow_html=True
        )
        st.divider()

        if st.session_state.auth_ok:
            user = st.session_state.user or {}
            st.markdown(
                f"""
                <div style="color:white; background: rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.15);
                            padding: 10px; border-radius: 12px; margin-bottom: 12px;">
                  <div style="font-weight:900;">{user.get('nome') or user.get('username')}</div>
                  <div style="opacity:0.9; font-weight:800; font-size:0.85rem;">Perfil {user.get('perfil')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Sair", type="secondary", use_container_width=True):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()

        st.divider()

        st.markdown("<div style='color:rgba(255,255,255,0.85); font-weight:900; margin-bottom: 8px;'>Acesso rápido</div>", unsafe_allow_html=True)
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
                if st.button("Agenda Semana", type="secondary", use_container_width=True):
                    st.session_state.page = "Agenda da Semana"
                    st.rerun()

# =========================
# Login
# =========================
def page_login():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="margin:0; color:{COLORS['primary']}; font-weight:900;">Acesso ao Sistema</h2>
          <p style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">Área restrita para cadastro e gerenciamento.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    colL, colC, colR = st.columns([1, 1.4, 1])
    with colC:
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
# Agenda Pública
# =========================
def page_agenda_publica():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="margin:0; color:{COLORS['primary']}; font-weight:900;">Agenda Pública</h2>
          <p style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">
            Visualização pública dos eventos. Acesso livre sem necessidade de login.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtros (sem quebrar layout)
    col1, col2, col3 = st.columns([1.2, 1.0, 0.9], vertical_alignment="top")

    with col1:
        st.markdown(
            f"<div class='modern-card' style='padding:14px;'><div style='font-weight:900; color:{COLORS['primary']}; margin-bottom:8px;'>Semana de referência</div>",
            unsafe_allow_html=True
        )
        ref = st.date_input("Semana de referência", value=date.today(), format="DD/MM/YYYY", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            f"<div class='modern-card' style='padding:14px;'><div style='font-weight:900; color:{COLORS['primary']}; margin-bottom:8px;'>Congregação</div>",
            unsafe_allow_html=True
        )
        congregacao = st.selectbox("Congregação", ["Todas"] + CONGREGACOES, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown(
            f"<div class='modern-card' style='padding:14px;'><div style='font-weight:900; color:{COLORS['primary']}; margin-bottom:8px;'>Exibição</div>",
            unsafe_allow_html=True
        )
        modo = st.selectbox("Exibição", ["Cards", "Tabela"], index=0, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    monday, sunday = week_bounds(ref)
    congreg_label = congregacao

    st.markdown(
        f"""
        <div class="modern-card">
          <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap;">
            <div>
              <div style="font-weight:900; color:{COLORS['primary']};">Resumo da Semana</div>
              <div style="margin-top:6px; color:{COLORS['text_light']}; font-weight:800;">{_fmt_date_br(monday)} até {_fmt_date_br(sunday)}</div>
            </div>
            <span class="badge">{congreg_label}</span>
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

    tab_todos, tab_culto, tab_ebd, tab_oracao, tab_ensaio = st.tabs(["Todos (A4)", "Cultos", "EBD", "Oração", "Ensaios"])

    # Aba Todos A4
    with tab_todos:
        st.markdown(
            f"""
            <div class="modern-card">
              <div style="font-weight:900; color:{COLORS['primary']};">Folha A4</div>
              <div style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">Pronta para imprimir ou mandar no WhatsApp.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        html = build_a4_html(eventos, monday, sunday, congregacao_label=congreg_label)
        components.html(html, height=980, scrolling=True)

        pdf_bytes = gerar_pdf_a4(eventos, monday, sunday, congregacao_label=congreg_label)
        st.download_button(
            "Baixar PDF",
            data=pdf_bytes,
            file_name=f"agenda_{monday.strftime('%Y%m%d')}_a_{sunday.strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    def render_group(tipo_nome: str, container):
        with container:
            sub = df[df["tipo"] == tipo_nome].copy()
            if sub.empty:
                st.info("Sem registros nesta semana.")
                return

            if modo == "Tabela":
                view = sub.copy()
                view["Data"] = view["data"].apply(lambda x: x.strftime("%d/%m/%Y"))
                view["Dia"] = view["data"].apply(lambda x: weekday_pt_br(x))
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
          <h2 style="margin:0; color:{COLORS['primary']}; font-weight:900;">Cadastro de Evento</h2>
          <p style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">Preencha as informações do evento.</p>
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
            congregacao = st.selectbox("Congregação", allowed_congregs, index=allowed_congregs.index(val("congregacao")))
        else:
            congregacao = st.selectbox("Congregação", allowed_congregs, index=None, placeholder="Selecione")

    with col2:
        if ev and val("tipo") in TIPOS:
            tipo = st.selectbox("Tipo", TIPOS, index=TIPOS.index(val("tipo")))
        else:
            tipo = st.selectbox("Tipo", TIPOS, index=None, placeholder="Selecione")

    with col3:
        subtipo = None
        turma_ebd = None

        if (tipo == "Culto") or (ev and val("tipo") == "Culto" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "Culto":
                options = SUBTIPOS_CULTO
                current = val("subtipo")
                subtipo = st.selectbox("Subtipo do Culto", options, index=options.index(current) if current in options else None, placeholder="Opcional")

        if (tipo == "EBD") or (ev and val("tipo") == "EBD" and tipo is None):
            tipo_eff = tipo or val("tipo")
            if tipo_eff == "EBD":
                options = TURMAS_EBD
                current = val("turma_ebd")
                turma_ebd = st.selectbox("Turma da EBD", options, index=options.index(current) if current in options else None, placeholder="Selecione")

    col4, col5 = st.columns(2)
    with col4:
        data_evento = st.date_input("Data", value=val("data", date.today()), format="DD/MM/YYYY")
    with col5:
        horario_default = datetime.strptime("19:00", "%H:%M").time()
        horario = st.time_input("Horário", value=val("horario", horario_default))

    st.markdown("<div class='modern-card'><b>Equipe do Evento</b></div>", unsafe_allow_html=True)

    dirigente1 = st.text_input("Dirigente", value=val("dirigente1", "") or "")
    st.toggle("Adicionar mais dirigentes", key="show_dirigentes_extra")
    if st.session_state.show_dirigentes_extra:
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dirigente2 = st.text_input("Dirigente 2", value=val("dirigente2", "") or "")
        with col_d2:
            dirigente3 = st.text_input("Dirigente 3", value=val("dirigente3", "") or "")
    else:
        dirigente2 = val("dirigente2", "") or ""
        dirigente3 = val("dirigente3", "") or ""

    portaria1 = st.text_input("Portaria", value=val("portaria1", "") or "")
    st.toggle("Adicionar mais na portaria", key="show_portaria_extra")
    if st.session_state.show_portaria_extra:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            portaria2 = st.text_input("Portaria 2", value=val("portaria2", "") or "")
        with col_p2:
            portaria3 = st.text_input("Portaria 3", value=val("portaria3", "") or "")
    else:
        portaria2 = val("portaria2", "") or ""
        portaria3 = val("portaria3", "") or ""

    recepcao1 = st.text_input("Recepção", value=val("recepcao1", "") or "")
    st.toggle("Adicionar mais na recepção", key="show_recepcao_extra")
    if st.session_state.show_recepcao_extra:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            recepcao2 = st.text_input("Recepção 2", value=val("recepcao2", "") or "")
        with col_r2:
            recepcao3 = st.text_input("Recepção 3", value=val("recepcao3", "") or "")
    else:
        recepcao2 = val("recepcao2", "") or ""
        recepcao3 = val("recepcao3", "") or ""

    secretaria = st.text_input("Secretaria", value=val("secretaria", "") or "")
    observacoes = st.text_area("Observações", value=val("observacoes", "") or "", height=90)

    c1, c2 = st.columns(2)
    with c1:
        salvar = st.button("Salvar", type="primary", use_container_width=True)
    with c2:
        cancelar = st.button("Cancelar", use_container_width=True)

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
# Agenda da Semana (Privado)
# =========================
def page_agenda_semana():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="margin:0; color:{COLORS['primary']}; font-weight:900;">Agenda da Semana</h2>
          <p style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">Visualização privada com filtros.</p>
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
# Gerenciar Eventos (Privado)
# =========================
def page_gerenciar_eventos():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="margin:0; color:{COLORS['primary']}; font-weight:900;">Gerenciar Eventos</h2>
          <p style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">Edite ou exclua eventos.</p>
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

# =========================
# Usuários (ADMIN)
# =========================
def page_usuarios():
    st.markdown(
        f"""
        <div class="modern-card">
          <h2 style="margin:0; color:{COLORS['primary']}; font-weight:900;">Usuários</h2>
          <p style="margin-top:6px; color:{COLORS['text_light']}; font-weight:700;">Cadastro e gestão de acessos.</p>
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
            nome = st.text_input("Nome", placeholder="Nome completo")
        with col2:
            username = st.text_input("Usuário", placeholder="Ex: joao.silva")

        col3, col4 = st.columns(2)
        with col3:
            senha = st.text_input("Senha", type="password", placeholder="Defina uma senha")
        with col4:
            perfil = st.selectbox("Perfil", ROLES, index=None, placeholder="Escolha")

        congreg_vinc = None
        if perfil == "SECRETARIO":
            congreg_vinc = st.selectbox("Congregação vinculada", CONGREGACOES, index=None, placeholder="Selecione")

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
            nova = st.text_input("Nova senha", type="password", placeholder="Digite a nova senha", key="nova_senha")
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
