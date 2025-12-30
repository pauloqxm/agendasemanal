from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt

CONGREGACOES = [
    "Sede",
    "Conjunto Esperança",
    "Rodoviária",
    "Pompéia",
    "Sabonete",
    "Depósito",
]

TIPOS = ["Culto", "Oração", "Ensaio", "EBD"]

SUBTIPOS_CULTO = [
    "Santa Ceia",
    "Missões",
    "Jovens",
    "Família",
    "Crianças",
    "Senhoras",
    "Ação de Graças",
    "Campal",
    "Em residência",
    "Cruzada",
    "Louvor e adoração",
]

TURMAS_EBD = ["Jardim de Infância", "Pré-adolescentes", "Adultos"]

def format_tipo(row: dict) -> str:
    t = row.get("tipo") or ""
    st = row.get("subtipo") or ""
    turma = row.get("turma_ebd") or ""
    if t == "Culto" and st:
        return f"{t} - {st}"
    if t == "EBD" and turma:
        return f"{t} - {turma}"
    return t

def df_to_png_bytes(df: pd.DataFrame, title: str):
    if df is None or df.empty:
        return None

    fig = plt.figure(figsize=(14, max(3, 0.5 + 0.35 * len(df))))
    ax = plt.gca()
    ax.axis("off")
    plt.title(title)

    tbl = plt.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.4)

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
