import os
import streamlit as st

def get_db_config() -> dict:
    # Preferir st.secrets (Railway/Streamlit Cloud)
    if hasattr(st, "secrets") and "db" in st.secrets:
        db = st.secrets["db"]
        return {
            "host": db.get("host"),
            "database": db.get("database"),
            "user": db.get("user"),
            "password": db.get("password"),
            "port": int(db.get("port", 5432)),
            "sslmode": db.get("sslmode", "require"),
        }

    # Fallback env vars
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "database": os.getenv("PGDATABASE", "postgres"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", ""),
        "port": int(os.getenv("PGPORT", "5432")),
        "sslmode": os.getenv("PGSSLMODE", "require"),
    }

def get_admin_password() -> str:
    if hasattr(st, "secrets") and "ADMIN_PASSWORD" in st.secrets:
        return str(st.secrets["ADMIN_PASSWORD"])
    return os.getenv("ADMIN_PASSWORD", "admin123")
