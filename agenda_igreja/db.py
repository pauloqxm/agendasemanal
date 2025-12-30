# agenda_igreja/db.py
import os
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2

SCHEMA = "bd_agenda"


def _get_db_config():
    # Railway pode expor URLs com nomes diferentes dependendo do setup
    candidates = [
        "DATABASE_PUBLIC_URL",
        "DATABASE_URL",
        "DATABASE_PRIVATE_URL",
        "DATABASE_URL_PUBLIC",
        "DATABASE_URL_PRIVATE",
        "POSTGRES_URL",
        "POSTGRES_PUBLIC_URL",
        "POSTGRES_PRIVATE_URL",
    ]

    db_url = None
    used_key = None
    for k in candidates:
        v = os.getenv(k)
        if v:
            db_url = v
            used_key = k
            break

    if not db_url:
        present = [k for k in candidates if os.getenv(k)]
        raise RuntimeError(
            "URL do banco não encontrada no serviço do app. "
            f"Testados: {', '.join(candidates)}. "
            f"Presentes: {present}."
        )

    u = urlparse(db_url)

    # debug opcional (sem vazar senha no log)
    # você pode comentar se não quiser
    # print(f"[DB] usando {used_key} host={u.hostname} db={u.path.lstrip('/')} port={u.port or 5432}")

    return {
        "used_key": used_key,
        "host": u.hostname,
        "dbname": u.path.lstrip("/"),
        "user": u.username,
        "password": u.password,
        "port": int(u.port or 5432),
        "sslmode": os.getenv("PGSSLMODE", "require"),
    }


@contextmanager
def get_db_connection():
    cfg = _get_db_config()
    conn = None
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            port=cfg["port"],
            sslmode=cfg["sslmode"],
            connect_timeout=10,
        )
        conn.autocommit = False

        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")
            cur.execute(f"SET search_path TO {SCHEMA}, public;")

        conn.commit()
        yield conn

    finally:
        if conn:
            conn.close()


def test_db_connection():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user;")
                db, user = cur.fetchone()
                cur.execute("SHOW search_path;")
                sp = cur.fetchone()[0]

        return True, f"✅ Banco OK. DB={db} USER={user} search_path={sp}"
    except Exception as e:
        return False, f"❌ Erro no banco: {e}"
