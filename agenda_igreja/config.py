# agenda_igreja/config.py
import os
import streamlit as st


def get_db_config() -> dict:
    """
    Prioridade:
    1. Variáveis de ambiente (Railway)
    2. st.secrets (Streamlit Cloud / local)
    """

    # 1️⃣ Railway / ambiente
    if os.getenv("PGHOST"):
        return {
            "host": os.getenv("PGHOST"),
            "database": os.getenv("PGDATABASE"),
            "user": os.getenv("PGUSER"),
            "password": os.getenv("PGPASSWORD"),
            "port": int(os.getenv("PGPORT", "5432")),
            "sslmode": os.getenv("PGSSLMODE", "require"),
        }

    # 2️⃣ Streamlit secrets (só tenta se existir arquivo)
    try:
        secrets = st.secrets
        if "db" in secrets:
            db = secrets["db"]
            return {
                "host": db.get("host"),
                "database": db.get("database"),
                "user": db.get("user"),
                "password": db.get("password"),
                "port": int(db.get("port", 5432)),
                "sslmode": db.get("sslmode", "require"),
            }
    except Exception:
        pass

    # 3️⃣ fallback local
    return {
        "host": "localhost",
        "database": "postgres",
        "user": "postgres",
        "password": "",
        "port": 5432,
        "sslmode": "disable",
    }


def get_admin_password() -> str:
    # Railway / produção
    if os.getenv("ADMIN_PASSWORD"):
        return os.getenv("ADMIN_PASSWORD")

    # Streamlit secrets
    try:
        if "ADMIN_PASSWORD" in st.secrets:
            return str(st.secrets["ADMIN_PASSWORD"])
    except Exception:
        pass

    # fallback local
    return "admin123"
