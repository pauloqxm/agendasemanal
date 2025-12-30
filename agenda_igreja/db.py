import psycopg2
from psycopg2.extras import RealDictCursor
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
            database=config["database"],
            user=config["user"],
            password=config["password"],
            port=config["port"],
            sslmode=config.get("sslmode", "require"),
            connect_timeout=10,
        )
        conn.autocommit = False

        # garante schema e search_path
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
                cur.execute("SELECT version();")
                v = cur.fetchone()
                return True, f"✅ Conectado ao PostgreSQL: {v[0]}"
    except Exception as e:
        return False, f"❌ Falha na conexão: {str(e)}"
