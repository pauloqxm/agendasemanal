# agenda_igreja/db.py
import psycopg2
from contextlib import contextmanager
from .config import get_db_config

SCHEMA = "bd_agenda"

@contextmanager
def get_db_connection():
    config = get_db_config()

    conn = None
    try:
        conn = psycopg2.connect(
            host=config["host"],
            dbname=config["database"],
            user=config["user"],
            password=config["password"],
            port=config["port"],
            sslmode=config["sslmode"],
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
