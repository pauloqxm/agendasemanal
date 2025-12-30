# agenda_igreja/auth.py
import hashlib
import streamlit as st
from agenda_igreja.db import get_db_connection

ROLES = ["ADMIN", "PASTOR", "DIRIGENTE", "SECRETARIO"]

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def has_role(*roles) -> bool:
    user = st.session_state.get("user")
    return bool(user) and user.get("perfil") in roles

def init_auth():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL CHECK (perfil IN ('ADMIN','PASTOR','DIRIGENTE','SECRETARIO')),
                    congregacao_vinculada TEXT,
                    ativo BOOLEAN DEFAULT TRUE,
                    criado_em TIMESTAMP DEFAULT NOW()
                );
            """)

            # Cria admin padrão se não existir (troque a senha depois)
            cur.execute("SELECT COUNT(*) FROM usuarios WHERE perfil='ADMIN';")
            n_admin = cur.fetchone()[0]
            if n_admin == 0:
                cur.execute("""
                    INSERT INTO usuarios (username, nome, senha_hash, perfil, congregacao_vinculada, ativo)
                    VALUES (%s, %s, %s, 'ADMIN', NULL, TRUE)
                    ON CONFLICT (username) DO NOTHING;
                """, ("admin", "Administrador", _hash_password("admin123")))

        conn.commit()

def authenticate(username: str, password: str):
    u = (username or "").strip()
    p = (password or "")
    if not u or not p:
        return False, None

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, nome, senha_hash, perfil, congregacao_vinculada, ativo
                FROM usuarios
                WHERE username=%s
                LIMIT 1;
            """, (u,))
            row = cur.fetchone()

    if not row:
        return False, None

    user_id, uname, nome, senha_hash, perfil, congreg_vinc, ativo = row
    if not ativo:
        return False, None

    if _hash_password(p) != senha_hash:
        return False, None

    user = {
        "id": user_id,
        "username": uname,
        "nome": nome,
        "perfil": perfil,
        "congregacao_vinculada": congreg_vinc,
    }
    return True, user

def create_user(nome: str, username: str, senha: str, perfil: str, congregacao_vinculada: str | None):
    if perfil not in ROLES:
        raise ValueError("Perfil inválido.")

    if perfil == "SECRETARIO" and not congregacao_vinculada:
        raise ValueError("Secretário(a) precisa de congregação vinculada.")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usuarios (username, nome, senha_hash, perfil, congregacao_vinculada, ativo)
                VALUES (%s, %s, %s, %s, %s, TRUE);
            """, (
                username.strip(),
                nome.strip(),
                _hash_password(senha),
                perfil,
                congregacao_vinculada
            ))
        conn.commit()

def list_users():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, nome, perfil, congregacao_vinculada, ativo, criado_em
                FROM usuarios
                ORDER BY criado_em DESC;
            """)
            rows = cur.fetchall()

    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "username": r[1],
            "nome": r[2],
            "perfil": r[3],
            "congregacao_vinculada": r[4],
            "ativo": r[5],
            "criado_em": r[6],
        })
    return out

def set_user_active(user_id: int, ativo: bool):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET ativo=%s WHERE id=%s;", (ativo, user_id))
        conn.commit()

def reset_password(user_id: int, nova_senha: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET senha_hash=%s WHERE id=%s;", (_hash_password(nova_senha), user_id))
        conn.commit()
