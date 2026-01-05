# app.py
import io
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# PDF (A4)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
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
    list_events_between,
    users_audit_summary_with_ids
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
# Paleta de cores
# =========================
COLORS = {
    "primary": "#0A1F44",
    "secondary": "#1A365D",
    "accent": "#2C5282",
    "light": "#4A90E2",
    "success": "#38A169",
    "warning": "#D69E2E",
    "danger": "#E53E3E",
    "background": "#F7FAFC",
    "card": "#FFFFFF",
    "text": "#1A202C",
    "text_light": "#718096",
}

# =========================
# Estilo Moderno
# =========================
def apply_css():
    css = f"""
    <style>
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-right: none;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS['background']};
        padding: 8px;
        border-radius: 12px;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        white-space: nowrap;
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

    /* Cards */
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

    /* Destaque do dia da semana */
    .weekday-pill {{
        display: inline-flex;
        align-items: center;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.6px;
        background: rgba(74, 144, 226, 0.12);
        color: {COLORS['accent']};
        margin-bottom: 8px;
        text-transform: uppercase;
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

    /* Inputs como card */
    div[data-testid="stDateInput"],
    div[data-testid="stSelectbox"],
    div[data-testid="stTimeInput"],
    div[data-testid="stTextInput"],
    div[data-testid="stTextArea"] {{
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 16px;
      padding: 14px 14px 10px 14px;
      box-shadow: 0 6px 18px rgba(2, 6, 23, 0.06);
    }}

    div[data-testid="stDateInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stTimeInput"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label {{
      margin-bottom: 8px !important;
      font-weight: 600 !important;
      color: #1A202C !important;
    }}

    /* Topbar */
    .topbar {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-radius: 16px;
        padding: 0.5rem;
        margin: 2rem 0%;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 25px rgba(10, 31, 68, 0.15);
    }}

    .topbar-content {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }}

    .church-info {{
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 0;
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
        word-break: break-word;
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
        white-space: nowrap;
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

    .badge-muted {{
        background: rgba(2, 6, 23, 0.05);
        color: #334155;
    }}

    .status-indicator {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }}

    .status-online {{ background: {COLORS['success']}; }}
    .status-offline {{ background: {COLORS['danger']}; }}

    .divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
        margin: 1.5rem 0;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# =========================
# Helpers
# =========================
_WEEKDAYS_PT = {
    0: "SEGUNDA-FEIRA",
    1: "TERÇA-FEIRA",
    2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA",
    4: "SEXTA-FEIRA",
    5: "SÁBADO",
    6: "DOMINGO",
}

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
    return ", ".join([a for a in args if isinstance(a, str) and a.strip()])

def _weekday_label(d: date) -> str:
    try:
        return _WEEKDAYS_PT.get(d.weekday(), "")
    except Exception:
        return ""

def _html_escape(s: str) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

def _labels_dirigencia(tipo: str):
    t = (tipo or "").strip()
    if t == "Ensaio":
        return ("Regente", "Regentes")
    if t == "EBD":
        return ("Professor(a)", "Professores(as)")
    return ("Dirigente", "Dirigentes")

def _people_line_dyn(label_sing: str, label_plur: str, *names) -> str:
    val = join_people(*names)
    if not val:
        return ""
    qtd = len([n for n in names if isinstance(n, str) and n.strip()])
    label = label_sing if qtd == 1 else label_plur
    return f"{label}: {val}"

def df_to_pdf_bytes_a4(df: pd.DataFrame, title: str, subtitle: str):
    if df is None or df.empty:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(subtitle, styles["Normal"]))
    story.append(Spacer(1, 12))

    safe = df.fillna("").astype(str)
    data = [list(safe.columns)] + safe.values.tolist()

    table = Table(data, repeatRows=1, hAlign="LEFT")
    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),

        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),

        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    table.setStyle(table_style)
    story.append(table)

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf

# =========================
# PDF e PNG "Rodízio Semanal" (layout igual ao modelo da imagem)
# =========================
def agenda_todos_to_pdf_rodizio(
    subdf: pd.DataFrame,
    monday: date,
    sunday: date,
    congregacao_txt: str,
    return_png: bool = False
):
    if subdf is None or subdf.empty:
        return (None, None) if return_png else None

    def _try_fetch_logo_bytes(url: str):
        try:
            with urlopen(url, timeout=8) as r:
                return r.read()
        except Exception:
            return None

    def _fmt_hora_h(h):
        """
        '19:00' -> '19h'
        '19:30' -> '19h30'
        """
        if h is None:
            return ""
        s = str(h).strip()
        if not s:
            return ""
        s = s[:5]
        if ":" not in s:
            return s
        hh, mm = s.split(":", 1)
        hh = (hh or "").strip()
        mm = (mm or "").strip()
        if not hh:
            return ""
        if mm in ("", "00"):
            return f"{hh}h"
        return f"{hh}h{mm}"

    def _cat_from_tipo(row: dict) -> str:
        t = (row.get("tipo") or "").strip()
        if t:
            # tenta classificar pelo texto
            for cand in ["Culto", "EBD", "Ensaio", "Oração", "Escola Bíblica"]:
                if cand.lower() in t.lower():
                    return "EBD" if "escola bíblica" in t.lower() else cand
        txt = (format_tipo(row) or "").strip()
        for cand in ["Culto", "EBD", "Ensaio", "Oração", "Escola Bíblica"]:
            if cand.lower() in txt.lower():
                return "EBD" if "escola bíblica" in txt.lower() else cand
        return "Outros"

    def _tipo_resumo(row: dict) -> str:
        # Texto principal do item, tipo "Círculo de Oração", "Culto de Ensino", etc
        txt = (format_tipo(row) or row.get("tipo") or "").strip()
        return txt

    def _maybe_class_from_tipo(tipo_txt: str) -> str:
        """
        Tenta extrair classe da EBD do texto.
        Ex: "EBD - Maternal" -> "Maternal"
        """
        if not tipo_txt:
            return ""
        t = tipo_txt.strip()
        low = t.lower()
        # casos comuns
        known = ["maternal", "juniores", "jovens", "adultos", "adolescentes", "crianças"]
        for k in known:
            if k in low:
                # devolve com a primeira letra maiúscula
                return k.capitalize()
        # padrão com hífen
        if "-" in t:
            part = t.split("-", 1)[1].strip()
            if part:
                return part
        return ""

    def _people_join(*vals):
        ppl = []
        for v in vals:
            v = (v or "").strip()
            if v:
                ppl.append(v)
        return ", ".join(ppl)

    def _labels_dirigencia_for_row(row: dict, fallback_cat: str):
        # mantém sua lógica existente, só com fallback seguro
        try:
            lab_s, lab_p = _labels_dirigencia(row.get("tipo") or fallback_cat)
            return lab_s, lab_p
        except Exception:
            return "Dirigente", "Dirigentes"

    def _build_roles_inline(row: dict, fallback_cat: str) -> str:
        """
        Monta 'Dirigentes: Fulano e Sicrana - Regente: X - Portaria: Y - Recepção: Z'
        Somente o que existir.
        """
        parts = []

        lab_s, lab_p = _labels_dirigencia_for_row(row, fallback_cat)

        dirigentes = _people_line_dyn(
            lab_s, lab_p,
            row.get("dirigente1"), row.get("dirigente2"), row.get("dirigente3")
        )
        portaria = _people_line_dyn(
            "Portaria", "Portaria",
            row.get("portaria1"), row.get("portaria2"), row.get("portaria3")
        )
        recepcao = _people_line_dyn(
            "Recepção", "Recepção",
            row.get("recepcao1"), row.get("recepcao2"), row.get("recepcao3")
        )

        # Regente, se existir em algum lugar
        regente = (row.get("regente") or "").strip()
        if not regente:
            # muita gente usa secretaria como "regente" em ensaios, então tenta
            # mas sem forçar se for claramente outra coisa
            sec = (row.get("secretaria") or "").strip()
            if sec and "cong." not in sec.lower():
                regente = sec

        if dirigentes:
            parts.append(f"<b>{_html_escape(lab_p)}</b>: {_html_escape(dirigentes.split(':',1)[-1].strip()) if ':' in dirigentes else _html_escape(dirigentes)}")
        if regente:
            parts.append(f"<b>Regente</b>: {_html_escape(regente)}")
        if portaria:
            parts.append(f"<b>Portaria</b>: {_html_escape(portaria.split(':',1)[-1].strip()) if ':' in portaria else _html_escape(portaria)}")
        if recepcao:
            parts.append(f"<b>Recepção</b>: {_html_escape(recepcao.split(':',1)[-1].strip()) if ':' in recepcao else _html_escape(recepcao)}")

        return " - ".join([p for p in parts if p])

    # -------------------------
    # Pré-processamento
    # -------------------------
    dfp = subdf.copy()
    dfp["data"] = pd.to_datetime(dfp["data"]).dt.date
    dfp["horario_txt"] = dfp["horario"].astype(str).str[:5]
    dfp["hora_h"] = dfp["horario_txt"].apply(_fmt_hora_h)
    dfp["categoria"] = dfp.apply(lambda r: _cat_from_tipo(r.to_dict()), axis=1)
    dfp = dfp.sort_values(["data", "horario_txt", "categoria", "congregacao"], ascending=True)

    # -------------------------
    # Estilos (igual ao visual do modelo)
    # -------------------------
    base = getSampleStyleSheet()
    styles = {
        "h_title": ParagraphStyle(
            "h_title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=16,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=1,
            spaceAfter=3
        ),
        "h_sub": ParagraphStyle(
            "h_sub",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12.5,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=1,
            spaceAfter=10
        ),
        "bullet_line": ParagraphStyle(
            "bullet_line",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0f172a"),
            leftIndent=12,
            firstLineIndent=-10,
            spaceAfter=5
        ),
        "small_center": ParagraphStyle(
            "small_center",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#334155"),
            alignment=1,
            spaceAfter=6
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=11.2,
            textColor=colors.HexColor("#0f172a"),
            alignment=0
        ),
        "table_cell_center": ParagraphStyle(
            "table_cell_center",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=11.2,
            textColor=colors.HexColor("#0f172a"),
            alignment=1
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=11.2,
            textColor=colors.white,
            alignment=1
        ),
    }

    def _weekday_upper(d: date) -> str:
        # usa seu helper se existir, senão faz simples
        try:
            w = _weekday_label(d)
            return (w or "").upper()
        except Exception:
            dias = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]
            return dias[d.weekday()]

    def _line_for_row(row: dict) -> str:
        dia = _weekday_upper(row["data"])
        hora = (row.get("hora_h") or "").strip()
        tipo = _tipo_resumo(row) or ""
        roles = _build_roles_inline(row, row.get("categoria") or "")
        # congregação, quando existir, vai em negrito discreto no final
        congreg = (row.get("congregacao") or "").strip()

        dia_html = f"<u><b>{_html_escape(dia)}</b></u>"
        hora_html = f"{_html_escape(hora)}" if hora else ""
        tipo_html = _html_escape(tipo)

        # mesma pegada da imagem: "SEGUNDA, 18h: Texto - Dirigentes: ..."
        core = f"{dia_html}"
        if hora_html:
            core += f", {hora_html}: "
        else:
            core += ", "
        core += f"{tipo_html}"

        if roles:
            core += f" - {roles}"

        if congreg:
            core += f" <font color='#1e3a8a'><b>({ _html_escape(congreg) })</b></font>"

        return f"• {core}"

    def _build_ebd_table(df_ebd: pd.DataFrame, usable_w: float):
        """
        Tabela como no modelo: Classes | Professores | Lição (com Regente na primeira linha).
        Só monta se tiver pelo menos 2 linhas de classes detectáveis.
        """
        rows = []
        regente_global = ""

        for _, r in df_ebd.iterrows():
            row = r.to_dict()
            tipo_txt = _tipo_resumo(row)
            classe = (row.get("classe") or "").strip()
            if not classe:
                classe = _maybe_class_from_tipo(tipo_txt)

            professores = _people_join(row.get("professor1"), row.get("professor2"), row.get("professor3"))
            if not professores:
                # reaproveita dirigentes como professores, porque normalmente já está preenchido
                professores = _people_join(row.get("dirigente1"), row.get("dirigente2"), row.get("dirigente3"))

            licao = (row.get("licao") or "").strip()
            if not licao:
                licao = (row.get("observacoes") or "").strip()

            reg = (row.get("regente") or "").strip()
            if not reg:
                sec = (row.get("secretaria") or "").strip()
                if sec and "cong." not in sec.lower():
                    reg = sec
            if reg and not regente_global:
                regente_global = reg

            if classe or professores or licao:
                rows.append([
                    Paragraph(_html_escape(classe or ""), styles["table_cell"]),
                    Paragraph(_html_escape(professores or ""), styles["table_cell"]),
                    Paragraph(_html_escape(licao or ""), styles["table_cell"]),
                ])

        if len(rows) < 2:
            return None

        header = [
            Paragraph("Classes", styles["table_header"]),
            Paragraph("Professores", styles["table_header"]),
            Paragraph("Lição 01", styles["table_header"]),
        ]

        # primeira linha especial no bloco "Lição 01" com "Regente: X"
        if regente_global:
            # coloca no topo da coluna 3 (como no modelo)
            rows[0][2] = Paragraph(
                f"<b>Regente</b>: {_html_escape(regente_global)}<br/>{rows[0][2].text}",
                styles["table_cell"]
            )

        col1 = usable_w * 0.18
        col2 = usable_w * 0.37
        col3 = usable_w * 0.45

        t = Table([header] + rows, colWidths=[col1, col2, col3])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.black),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#0f172a")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),

            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    # -------------------------
    # Montagem do PDF
    # -------------------------
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.6 * cm,
        title="Rodízio Semanal"
    )

    page_w = A4[0]
    usable_w = page_w - (doc.leftMargin + doc.rightMargin)

    story = []

    # Logo pequeno no topo (opcional)
    logo_bytes = _try_fetch_logo_bytes(LOGO_URL)
    if logo_bytes:
        try:
            img = RLImage(io.BytesIO(logo_bytes))
            img.drawHeight = 1.8 * cm
            img.drawWidth = 1.8 * cm
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Spacer(1, 6))
        except Exception:
            pass

    story.append(Paragraph("RODÍZIO SEMANAL", styles["h_title"]))
    story.append(Paragraph(f"PERÍODO DE {_fmt_date_br(monday)} A {_fmt_date_br(sunday)}", styles["h_sub"]))
    if "IGREJA_NOME" in globals() and IGREJA_NOME:
        story.append(Paragraph(IGREJA_NOME, styles["small_center"]))
        story.append(Spacer(1, 4))

    # Lista por dia, no estilo do modelo
    df_in_period = dfp[(dfp["data"] >= monday) & (dfp["data"] <= sunday)].copy()
    if df_in_period.empty:
        return (None, None) if return_png else None

    # Se tiver EBD em múltiplas classes, a gente segura e joga a tabela no meio (como na imagem)
    df_ebd = df_in_period[df_in_period["categoria"] == "EBD"].copy()

    # Itens não-EBD em bullets
    df_main = df_in_period[df_in_period["categoria"] != "EBD"].copy()

    # bullets agrupados por dia
    for d, g in df_main.groupby("data", sort=True):
        for _, r in g.iterrows():
            story.append(Paragraph(_line_for_row(r.to_dict() | {"data": d}), styles["bullet_line"]))

        # ponto ideal para inserir a tabela (depois de QUARTA, se existir)
        if df_ebd is not None and not df_ebd.empty:
            # tenta encaixar após o dia da EBD, ou logo após a QUARTA
            has_ebd_today = (df_ebd["data"] == d).any()
            if has_ebd_today or _weekday_upper(d) == "QUARTA":
                t = _build_ebd_table(df_ebd[df_ebd["data"] == d] if has_ebd_today else df_ebd, usable_w)
                if t:
                    story.append(Spacer(1, 8))
                    story.append(t)
                    story.append(Spacer(1, 10))
                    # não repete a tabela depois
                    df_ebd = df_ebd.iloc[0:0]

    # Se sobrou EBD e não encaixou, joga no final
    if df_ebd is not None and not df_ebd.empty:
        t = _build_ebd_table(df_ebd, usable_w)
        if t:
            story.append(Spacer(1, 8))
            story.append(t)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()

    if not return_png:
        return pdf_bytes

    png_bytes = None
    try:
        import fitz  # PyMuPDF
        docp = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = docp.load_page(0)
        pix = page.get_pixmap(dpi=220)
        png_bytes = pix.tobytes("png")
        docp.close()
    except Exception:
        png_bytes = None

    return pdf_bytes, png_bytes



# =========================
# UI
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

def init_state():
    st.session_state.setdefault("auth_ok", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Agenda Pública")
    st.session_state.setdefault("edit_id", None)
    st.session_state.setdefault("cadastro_nonce", 0)

def render_page_tabs():
    if not st.session_state.auth_ok:
        pages = [
            {"id": "Agenda Pública", "label": "📅 Agenda Pública"},
            {"id": "Login", "label": "🔐 Login"}
        ]
    else:
        pages = [
            {"id": "Agenda Pública", "label": "📅 Agenda Pública"},
            {"id": "Agenda da Semana", "label": "📊 Agenda da Semana"},
            {"id": "Cadastrar Evento", "label": "➕ Cadastrar Evento"},
            {"id": "Gerenciar Eventos", "label": "⚙️ Gerenciar Eventos"}
        ]
        if has_role("ADMIN"):
            pages.append({"id": "Usuários", "label": "👥 Usuários"})

    tab_cols = st.columns(len(pages))
    for col, page in zip(tab_cols, pages):
        with col:
            is_active = st.session_state.page == page["id"]
            btn_type = "primary" if is_active else "secondary"
            if st.button(page["label"], key=f"tab_{page['id']}", type=btn_type, use_container_width=True):
                st.session_state.page = page["id"]
                st.rerun()

def _event_card(ev: dict):
    from html import escape

    d = pd.to_datetime(ev["data"]).date() if ev.get("data") else date.today()
    weekday_txt = escape(_weekday_label(d))

    data_txt = escape(_fmt_date_br(d))
    hora_txt = escape(_fmt_time_hhmm(ev.get("horario")))
    congreg = escape(ev.get("congregacao") or "")

    tipo_raw = (ev.get("tipo") or "").strip()
    tipo_txt = escape(format_tipo(ev) or "")
    subtipo = escape(ev.get("subtipo") or "")
    turma = escape(ev.get("turma_ebd") or "")

    badges = ""
    if ev.get("id") is not None:
        badges += f'<span class="badge badge-muted">🆔 {escape(str(ev.get("id")))}</span>'
    if subtipo:
        badges += f'<span class="badge badge-warning">🎯 {subtipo}</span>'
    if turma:
        badges += f'<span class="badge badge-success">📚 {turma}</span>'
    if ev.get("secretaria"):
        badges += f'<span class="badge badge-primary">📋 {escape(ev.get("secretaria") or "")}</span>'

    lab_s, lab_p = _labels_dirigencia(tipo_raw)
    label_equipes = lab_p  # no card, é lista

    dirigentes = escape(join_people(ev.get("dirigente1"), ev.get("dirigente2"), ev.get("dirigente3")) or "")
    portaria = escape(join_people(ev.get("portaria1"), ev.get("portaria2"), ev.get("portaria3")) or "")
    recepcao = escape(join_people(ev.get("recepcao1"), ev.get("recepcao2"), ev.get("recepcao3")) or "")

    obs = escape((ev.get("observacoes") or "").strip())
    obs_html = ""
    if obs:
        obs_html = f"""
        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px dashed #E2E8F0;">
          <div style="font-weight: 800; color: {COLORS['secondary']}; margin-bottom: 4px;">📝 Observações</div>
          <div style="color: {COLORS['text']}; font-size: 0.95rem; line-height: 1.35;">{obs}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="event-card">
          <div class="weekday-pill">{weekday_txt}</div>

          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px;">
            <div style="min-width:0;">
              <div style="font-weight:800; font-size:1.1rem; color:{COLORS['primary']};">{tipo_txt}</div>
              <div style="font-size:0.9rem; color:{COLORS['text_light']}; margin-top:4px;">
                📅 {data_txt} • 🕒 {hora_txt} • 🏛️ {congreg}
              </div>
            </div>
            <div style="text-align:right;">{badges}</div>
          </div>

          <div style="margin:12px 0;">
            <div style="font-size:0.95rem; margin-bottom:4px;">
              <span style="font-weight:700; color:{COLORS['secondary']};">👤 {escape(label_equipes)}</span>
              <span style="color:{COLORS['text']}; margin-left:8px;">{dirigentes or "Não informado"}</span>
            </div>
            <div style="font-size:0.95rem; margin-bottom:4px;">
              <span style="font-weight:700; color:{COLORS['secondary']};">🚪 Portaria</span>
              <span style="color:{COLORS['text']}; margin-left:8px;">{portaria or "Não informado"}</span>
            </div>
            <div style="font-size:0.95rem;">
              <span style="font-weight:700; color:{COLORS['secondary']};">🤝 Recepção</span>
              <span style="color:{COLORS['text']}; margin-left:8px;">{recepcao or "Não informado"}</span>
            </div>
          </div>

          {obs_html}
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

            if st.button("🚪 Sair", use_container_width=True, type="secondary"):
                st.session_state.auth_ok = False
                st.session_state.user = None
                st.session_state.edit_id = None
                st.session_state.page = "Agenda Pública"
                st.rerun()

        st.divider()

        st.markdown(
            '<div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.5rem;">Acesso Rápido</div>',
            unsafe_allow_html=True
        )

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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
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

    col1, col2, col3 = st.columns([1.2, 1, 0.8])
    with col1:
        ref = st.date_input("📆 Semana de referência", value=date.today(), format="DD/MM/YYYY")
    with col2:
        congregacao = st.selectbox("🏛️ Congregação", ["Todas"] + CONGREGACOES)
    with col3:
        modo = st.selectbox("👁️ Exibição", ["Cards", "Tabela"], index=0)

    monday, sunday = week_bounds(ref)

    st.markdown(
        f"""
        <div class="modern-card">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
            <div>
              <h3 style="margin: 0; color: {COLORS['primary']};">📋 Resumo da Semana</h3>
              <p style="margin: 0.5rem 0 0 0; color: {COLORS['text_light']};">
                {_fmt_date_br(monday)} - {_fmt_date_br(sunday)}
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

    tab_todos, tab_culto, tab_ebd, tab_oracao, tab_ensaio = st.tabs(
        ["📌 Todos", "🎵 Cultos", "📚 EBD", "🙏 Oração", "🎤 Ensaios"]
    )

    def make_table_view(subdf: pd.DataFrame) -> pd.DataFrame:
        view = subdf.copy()
        view["ID"] = view.get("id")
        view["Dia"] = view["data"].apply(lambda x: _weekday_label(x))
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

        view["Observações"] = view.get("observacoes", "").fillna("").astype(str)

        show = view[[
            "ID", "Dia", "Data", "Horário", "congregacao", "Tipo",
            "Dirigentes", "Portaria", "Recepção",
            "secretaria", "Observações"
        ]]
        show = show.rename(columns={"congregacao": "Congregação", "secretaria": "Secretaria"})
        return show

    def render_group(tipo_nome: str, container, icon: str):
        with container:
            sub = df if tipo_nome == "Todos" else df[df["tipo"] == tipo_nome].copy()

            if sub.empty:
                st.info(f"{icon} Sem eventos deste tipo nesta semana.")
                return

            if tipo_nome == "Todos":
                pdf_rodizio, png_rodizio = agenda_todos_to_pdf_rodizio(
                    subdf=sub,
                    monday=monday,
                    sunday=sunday,
                    congregacao_txt=congregacao,
                    return_png=True
                )

                c1, c2, c3 = st.columns([1, 1, 2])

                with c1:
                    if pdf_rodizio:
                        st.download_button(
                            "🧾 Baixar PDF",
                            data=pdf_rodizio,
                            file_name=f"rodizio_semanal_{monday.strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                with c2:
                    if png_rodizio:
                        st.download_button(
                            "🖼️ Baixar PNG",
                            data=png_rodizio,
                            file_name=f"rodizio_semanal_{monday.strftime('%Y%m%d')}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    else:
                        st.caption("Para liberar o PNG, instala PyMuPDF.")
                        st.code("pip install pymupdf", language="bash")

                with c3:
                    st.caption("Escolha um formato, PDF ou PNG, e baixe")

            if modo == "Tabela":
                show = make_table_view(sub)
                st.dataframe(show, use_container_width=True, hide_index=True)

                png = df_to_png_bytes(
                    show,
                    title=f"{tipo_nome} • {_fmt_date_br(monday)} a {_fmt_date_br(sunday)}"
                )
                colx, coly, colz = st.columns(3)
                with colx:
                    if png:
                        st.download_button(
                            "💾 Exportar em PNG",
                            data=png,
                            file_name=f"agenda_{tipo_nome.lower()}_{monday.strftime('%Y%m%d')}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                with coly:
                    st.download_button(
                        "📄 Exportar em CSV",
                        data=show.to_csv(index=False).encode("utf-8"),
                        file_name=f"agenda_{tipo_nome.lower()}_{monday.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                pdf_df = show.copy()
                pdf_df = pdf_df.rename(columns={"Dirigentes": "Dirig.", "Recepção": "Recep.", "Observações": "Obs."})
                title = "Agenda da Semana (A4)"
                subtitle = f"{IGREJA_NOME}<br/>{_fmt_date_br(monday)} - {_fmt_date_br(sunday)}<br/>Congregação: {congregacao}"
                pdf_bytes = df_to_pdf_bytes_a4(pdf_df, title=title, subtitle=subtitle)
                with colz:
                    if pdf_bytes:
                        st.download_button(
                            "🧾 Baixar PDF (Tabela A4)",
                            data=pdf_bytes,
                            file_name=f"agenda_tabela_a4_{monday.strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                return

            for _, r in sub.iterrows():
                _event_card(r.to_dict())

    render_group("Todos", tab_todos, "📌")
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

    nonce = f"edit_{edit_id}" if edit_id else f"new_{st.session_state.get('cadastro_nonce', 0)}"

    def k(name: str) -> str:
        return f"cad_{nonce}_{name}"

    def val(key, default=None):
        if not ev:
            return default
        v = ev.get(key)
        return v if v is not None else default

    with st.container():
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="color: {COLORS["secondary"]};">📋 Dados do Evento</h3>', unsafe_allow_html=True)

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
                    placeholder="Selecione a congregação",
                    key=k("congregacao")
                )
            else:
                congregacao = st.selectbox(
                    "🏛️ Congregação*",
                    allowed_congregs,
                    index=None,
                    placeholder="Selecione a congregação",
                    key=k("congregacao")
                )

        with col2:
            if ev and val("tipo") in TIPOS:
                tipo = st.selectbox(
                    "📌 Tipo da agenda*",
                    TIPOS,
                    index=TIPOS.index(val("tipo")),
                    placeholder="Escolha o tipo do evento",
                    key=k("tipo")
                )
            else:
                tipo = st.selectbox(
                    "📌 Tipo da agenda*",
                    TIPOS,
                    index=None,
                    placeholder="Escolha o tipo do evento",
                    key=k("tipo")
                )

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
                        placeholder="Selecione (opcional)",
                        key=k("subtipo")
                    )
                else:
                    subtipo = st.selectbox(
                        "✨ Subtipo do Culto",
                        options,
                        index=None,
                        placeholder="Selecione (opcional)",
                        key=k("subtipo")
                    )

            if tipo_eff == "EBD":
                options = TURMAS_EBD
                current = val("turma_ebd")
                if ev and current in options:
                    turma_ebd = st.selectbox(
                        "📚 Turma da EBD*",
                        options,
                        index=options.index(current),
                        placeholder="Selecione a turma",
                        key=k("turma_ebd")
                    )
                else:
                    turma_ebd = st.selectbox(
                        "📚 Turma da EBD*",
                        options,
                        index=None,
                        placeholder="Selecione a turma",
                        key=k("turma_ebd")
                    )

        col4, col5 = st.columns(2)
        with col4:
            data_evento = st.date_input(
                "📅 Data*",
                value=val("data", date.today()),
                format="DD/MM/YYYY",
                key=k("data")
            )
        with col5:
            horario_default = datetime.strptime("19:00", "%H:%M").time()
            horario = st.time_input(
                "🕖 Horário*",
                value=val("horario", horario_default),
                key=k("horario")
            )

        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="color: {COLORS["secondary"]};">👥 Equipe do Evento</h3>', unsafe_allow_html=True)

        tipo_eff_equipes = tipo or val("tipo")

        if tipo_eff_equipes == "Ensaio":
            titulo_secao = "### 🎼 Regência"
            label_base = "🎼 Regente"
            placeholder_base = "Nome do regente responsável"
            toggle_txt = "➕ Adicionar mais regentes"
            label_2 = "🎼 Regente 2"
            label_3 = "🎼 Regente 3"
        elif tipo_eff_equipes == "EBD":
            titulo_secao = "### 📚 Docência"
            label_base = "📚 Professor(a)"
            placeholder_base = "Nome do(a) professor(a) responsável"
            toggle_txt = "➕ Adicionar mais professores(as)"
            label_2 = "📚 Professor(a) 2"
            label_3 = "📚 Professor(a) 3"
        else:
            titulo_secao = "### 👤 Dirigência"
            label_base = "👤 Dirigente"
            placeholder_base = "Nome do dirigente responsável"
            toggle_txt = "➕ Adicionar mais dirigentes"
            label_2 = "👥 Dirigente 2"
            label_3 = "👥 Dirigente 3"

        st.markdown(titulo_secao)
        dirigente1 = st.text_input(
            label_base,
            value=val("dirigente1", "") or "",
            placeholder=placeholder_base,
            key=k("dirigente1")
        )

        show_dir = st.toggle(toggle_txt, key=k("show_dirigentes_extra"))
        if show_dir:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                dirigente2 = st.text_input(
                    label_2,
                    value=val("dirigente2", "") or "",
                    placeholder="Nome (opcional)",
                    key=k("dirigente2")
                )
            with col_d2:
                dirigente3 = st.text_input(
                    label_3,
                    value=val("dirigente3", "") or "",
                    placeholder="Nome (opcional)",
                    key=k("dirigente3")
                )
        else:
            dirigente2 = val("dirigente2", "") or ""
            dirigente3 = val("dirigente3", "") or ""

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### 🚪 Portaria")
        portaria1 = st.text_input(
            "🚪 Portaria",
            value=val("portaria1", "") or "",
            placeholder="Nome do responsável pela portaria",
            key=k("portaria1")
        )

        show_por = st.toggle("➕ Adicionar mais na portaria", key=k("show_portaria_extra"))
        if show_por:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                portaria2 = st.text_input(
                    "🚪 Portaria 2",
                    value=val("portaria2", "") or "",
                    placeholder="Nome (opcional)",
                    key=k("portaria2")
                )
            with col_p2:
                portaria3 = st.text_input(
                    "🚪 Portaria 3",
                    value=val("portaria3", "") or "",
                    placeholder="Nome (opcional)",
                    key=k("portaria3")
                )
        else:
            portaria2 = val("portaria2", "") or ""
            portaria3 = val("portaria3", "") or ""

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### 🤝 Recepção")
        recepcao1 = st.text_input(
            "🤝 Recepção",
            value=val("recepcao1", "") or "",
            placeholder="Nome do responsável pela recepção",
            key=k("recepcao1")
        )

        show_rec = st.toggle("➕ Adicionar mais na recepção", key=k("show_recepcao_extra"))
        if show_rec:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                recepcao2 = st.text_input(
                    "🤝 Recepção 2",
                    value=val("recepcao2", "") or "",
                    placeholder="Nome (opcional)",
                    key=k("recepcao2")
                )
            with col_r2:
                recepcao3 = st.text_input(
                    "🤝 Recepção 3",
                    value=val("recepcao3", "") or "",
                    placeholder="Nome (opcional)",
                    key=k("recepcao3")
                )
        else:
            recepcao2 = val("recepcao2", "") or ""
            recepcao3 = val("recepcao3", "") or ""

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        secretaria = st.text_input(
            "🗂️ Secretaria",
            value=val("secretaria", "") or "",
            placeholder="Nome do responsável (opcional)",
            key=k("secretaria")
        )
        observacoes = st.text_area(
            "📝 Observações",
            value=val("observacoes", "") or "",
            placeholder="Observações (opcional)",
            height=90,
            key=k("observacoes")
        )

        st.markdown('</div>', unsafe_allow_html=True)

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
        if (tipo == "EBD") and not turma_ebd:
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

        actor = (st.session_state.user or {}).get("username")

        if edit_id:
            update_event(edit_id, payload, actor_username=actor)
            st.success("✅ Evento atualizado com sucesso!")
            st.session_state.edit_id = None
            st.session_state.page = "Agenda da Semana"
            st.rerun()

        create_event(payload, actor_username=actor)
        st.success("✅ Evento cadastrado! Pode cadastrar o próximo.")

        st.session_state.edit_id = None
        st.session_state.page = "Cadastrar Evento"
        st.session_state.cadastro_nonce = st.session_state.get("cadastro_nonce", 0) + 1
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

    col1, col2, col3 = st.columns(3)
    with col1:
        ref = st.date_input("Semana de referência", value=date.today(), format="DD/MM/YYYY")
    monday, sunday = week_bounds(ref)

    with col2:
        congregacao = st.selectbox("Congregação", ["Todas"] + CONGREGACOES)
    with col3:
        tipo = st.selectbox("Tipo", ["Todos"] + TIPOS)

    st.caption(f"Período: {_fmt_date_br(monday)} - {_fmt_date_br(sunday)}")

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
    df["ID"] = df.get("id")
    df["Data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")
    df["Horário"] = df["horario"].astype(str).str[:5]
    df["Tipo"] = df.apply(lambda r: format_tipo(r.to_dict()), axis=1)

    df["Dirigente"] = df.apply(lambda r: join_people(r.get("dirigente1"), r.get("dirigente2"), r.get("dirigente3")), axis=1)
    df["Portaria"] = df.apply(lambda r: join_people(r.get("portaria1"), r.get("portaria2"), r.get("portaria3")), axis=1)
    df["Recepção"] = df.apply(lambda r: join_people(r.get("recepcao1"), r.get("recepcao2"), r.get("recepcao3")), axis=1)

    df["Observações"] = df.get("observacoes", "").fillna("").astype(str)

    view = df[[
        "ID", "Data", "Horário", "congregacao", "Tipo",
        "Dirigente", "Portaria", "Recepção",
        "secretaria", "Observações"
    ]].rename(columns={"congregacao": "Congregação", "secretaria": "Secretaria"})

    st.dataframe(view, use_container_width=True, hide_index=True)

    png = df_to_png_bytes(view, title=f"Agenda {_fmt_date_br(monday)} - {_fmt_date_br(sunday)}")
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
        df[["id", "Data", "Horário", "congregacao", "Tipo", "criado_por", "atualizado_por"]],
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

    tab1, tab2, tab3 = st.tabs(["➕ Cadastrar usuário", "📋 Gerenciar usuários", "📌 Resumo de ações"])

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
            congreg_vinc = st.selectbox("🏛️ Congregação vinculada*", CONGREGACOES, index=None)

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

    with tab3:
        audit = users_audit_summary_with_ids(limit_ids=12)
        if not audit:
            st.info("Sem dados de ações nos eventos ainda.")
        else:
            df_a = pd.DataFrame(audit)

            df_a["Última edição"] = pd.to_datetime(df_a["ultima_edicao"]).dt.strftime("%d/%m/%Y %H:%M")
            df_a.drop(columns=["ultima_edicao"], inplace=True)

            def _ids_to_text(v):
                if not isinstance(v, (list, tuple)) or len(v) == 0:
                    return ""
                return ", ".join([str(x) for x in v])

            df_a["IDs criados"] = df_a["ids_criados"].apply(_ids_to_text)
            df_a["IDs editados"] = df_a["ids_editados"].apply(_ids_to_text)

            df_a = df_a.rename(columns={
                "username": "Usuário",
                "criados": "Eventos criados",
                "editados": "Eventos editados",
            })

            st.dataframe(
                df_a[["Usuário", "Eventos criados", "IDs criados", "Eventos editados", "IDs editados", "Última edição"]],
                use_container_width=True,
                hide_index=True
            )

# =========================
# Rodapé
# =========================
def render_footer():
    st.markdown("---")
    st.markdown("""
    <style>
    .simple-footer {
        text-align: center;
        padding: 1rem 0;
        color: #555;
    }
    .simple-footer-logo {
        height: 50px;
        margin-bottom: 0.5rem;
    }
    .footer-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 0.3rem;
    }
    .footer-subtitle {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.8rem;
    }
    .footer-address {
        color: #777;
        font-size: 0.85rem;
        line-height: 1.4;
        margin-bottom: 0.8rem;
    }
    .footer-link {
        color: #2563eb;
        text-decoration: none;
        font-size: 0.85rem;
        transition: color 0.3s;
    }
    .footer-link:hover {
        color: #1d4ed8;
        text-decoration: underline;
    }
    .footer-copyright {
        color: #999;
        font-size: 0.8rem;
        border-top: 1px solid #eee;
        padding-top: 0.8rem;
        margin-top: 0.8rem;
    }
    </style>

    <div class="simple-footer">
        <img src="https://i.ibb.co/jZkYm687/logo-adtce.jpg" alt="Logo IADTC" class="simple-footer-logo">
        <div class="footer-title">Agenda da Igreja</div>
        <div class="footer-subtitle">Igreja Assembleia de Deus - Templo Central</div>
        <div class="footer-address">
            Rua Vereador José Franco, 70 • Centro<br>
            Quixeramobim, Ceará
        </div>
        <a href="https://gfinformaticace.com/" target="_blank" class="footer-link">
            Desenvolvido por GF INFORMÁTICA
        </a>
        <div class="footer-copyright">
            © 2026 • IADTC • Todos os direitos reservados
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        render_footer()
        return

    if page == "Login":
        page_login()
        render_footer()
        return

    if not st.session_state.auth_ok:
        st.warning("🔒 Você precisa estar logado para acessar esta área.")
        page_login()
        render_footer()
        return

    if page == "Cadastrar Evento":
        page_cadastrar_evento()
    elif page == "Gerenciar Eventos":
        page_gerenciar_eventos()
    elif page == "Usuários":
        page_usuarios()
    else:
        page_agenda_semana()

    render_footer()

if __name__ == "__main__":
    main()
