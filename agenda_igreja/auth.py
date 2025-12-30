import hashlib
from .db import get_db_connection
from .config import get_admin_password

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def init_auth():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    nome TEXT,
                    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                    ativo BOOLEAN NOT NULL DEFAULT TRUE,
                    data_cadastro TIMESTAMP NOT NULL DEFAULT NOW(),
                    ultimo_login TIMESTAMP
                );
            """)
        conn.commit()

    ensure_default_admin()

def ensure_default_admin():
    admin_pass = get_admin_password()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE username=%s;", ("admin",))
            row = cur.fetchone()
            if not row:
                cur.execute("""
                    INSERT INTO usuarios (username, senha_hash, nome, is_admin, ativo)
                    VALUES (%s, %s, %s, TRUE, TRUE);
                """, ("admin", _sha256(admin_pass), "Administrador"))
        conn.commit()

def authenticate(username: str, password: str):
    if not username or not password:
        return False, None

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, nome, is_admin, ativo, senha_hash
                FROM usuarios
                WHERE username=%s;
            """, (username,))
            u = cur.fetchone()

            if not u:
                return False, None
            if not u[4]:
                return False, None

            senha_hash = u[5]
            if _sha256(password) != senha_hash:
                return False, None

            cur.execute("UPDATE usuarios SET ultimo_login=NOW() WHERE id=%s;", (u[0],))
        conn.commit()

    user = {
        "id": u[0],
        "username": u[1],
        "nome": u[2],
        "is_admin": u[3],
    }
    return True, user
