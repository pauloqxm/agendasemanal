# agenda_igreja/config.py
import os
from urllib.parse import urlparse

def get_db_config() -> dict:
    # Railway usa DATABASE_PUBLIC_URL
    db_url = os.getenv("DATABASE_PUBLIC_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_PUBLIC_URL não encontrada. "
            "Verifique as variáveis do serviço no Railway."
        )

    u = urlparse(db_url)

    return {
        "host": u.hostname,
        "database": u.path.lstrip("/"),
        "user": u.username,
        "password": u.password,
        "port": int(u.port or 5432),
        "sslmode": os.getenv("PGSSLMODE", "require"),
    }

def get_admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD", "admin123")
