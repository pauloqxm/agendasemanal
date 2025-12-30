# agenda_igreja/config.py
import os
from urllib.parse import urlparse

def get_db_config() -> dict:
    db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
    if db_url:
        u = urlparse(db_url)
        return {
            "host": u.hostname,
            "database": u.path.lstrip("/"),
            "user": u.username,
            "password": u.password,
            "port": int(u.port or 5432),
            "sslmode": os.getenv("PGSSLMODE", "require"),
        }

    return {
        "host": os.getenv("PGHOST"),
        "database": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
        "port": int(os.getenv("PGPORT", "5432")),
        "sslmode": os.getenv("PGSSLMODE", "require"),
    }

def get_admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD", "admin123")
