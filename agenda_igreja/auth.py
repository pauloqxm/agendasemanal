# agenda_igreja/auth.py
import hashlib
import streamlit as st
from agenda_igreja.db import get_db_connection

ROLES = ["ADMIN", "PASTOR", "DIRIGENTE", "SECRETARIO"]


def _hash_password(pw: str) -> str:
    return hashlib.sha256((pw or "").encode("utf-8")).hexdigest()


def has_role(*roles) -> bool:
    user = st.session_state.get("user") or {}
    perfil = (user.get("perfil") or "").upper()
    wanted = [r.upper() for r in roles]
    return bool(perfil) and perfil in wanted


def _ensure_schema(cur):
    """
    Garante que a tabela e colunas existam, mesmo se o banco já tinha uma versão antiga.
    """

    # 1) Cria tabela mínima se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE
        );
    """)

    # 2) Migrações: adiciona colunas que podem faltar
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS perfil TEXT;")
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS congregacao_vinculada TEXT;")

    # timestamps: pode existir como criado_em ou data_cadastro em versões antigas
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW();")
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS data_cadastro TIMESTAMP DEFAULT NOW();")

    # 3) Normaliza valores nulos de perfil
    cur.execute("UPDATE usuarios SET perfil = COALESCE(perfil, 'DIRIGENTE') WHERE perfil IS NULL;")

    # 4) Tenta colocar regra de perfil (CHECK) sem quebrar se já existir
    # (Se já tiver constraint com nome diferente, a gente ignora)
    try:
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'usuarios_perfil_check'
                ) THEN
                    ALTER TABLE usuarios
                    ADD CONSTRAINT usuarios_perfil_check
                    CHECK (perfil IN ('ADMIN','PASTOR','DIRIGENTE','SECRETARIO'));
                END IF;
            END $$;
        """)
    except Exception:
        # Se der qualquer treta de constraint, segue o jogo. Melhor rodar do que quebrar.
        pass

    # 5) Define DEFAULT do perfil
    try:
        cur.execute("ALTER TABLE usuarios ALTER COLUMN perfil SET DEFAULT 'DIRIGENTE';")
    except Exception:
        pass


def init_auth():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            _ensure_schema(cur)

            # Cria admin padrão se não existir nenhum admin
            cur.execute("SELECT COUNT(*) FROM usuarios WHERE UPPER(perfil)='ADMIN';")
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
            # Seleciona com fallback de colunas
            cur.execute("""
                SELECT id, username, nome, senha_hash,
                       COALESCE(perfil,'DIRIGENTE') AS perfil,
                       congregacao_vinculada,
                       COALESCE(ativo, TRUE) AS ativo
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
        "perfil": (perfil or "DIRIGENTE"),
        "congregacao_vinculada": congreg_vinc,
    }
    return True, user


def create_user(nome: str, username: str, senha: str, perfil: str, congregacao_vinculada: str | None):
    perfil = (perfil or "").upper()
    if perfil not in ROLES:
        raise ValueError("Perfil inválido.")

    if perfil == "SECRETARIO" and not congregacao_vinculada:
        raise ValueError("Secretário(a) precisa de congregação vinculada.")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            _ensure_schema(cur)
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
            _ensure_schema(cur)
            # Usa o melhor timestamp disponível
            cur.execute("""
                SELECT id, username, nome,
                       COALESCE(perfil,'DIRIGENTE') AS perfil,
                       congregacao_vinculada,
                       COALESCE(ativo, TRUE) AS ativo,
                       COALESCE(criado_em, data_cadastro, NOW()) AS criado_em
                FROM usuarios
                ORDER BY COALESCE(criado_em, data_cadastro, NOW()) DESC;
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
            _ensure_schema(cur)
            cur.execute("UPDATE usuarios SET ativo=%s WHERE id=%s;", (ativo, user_id))
        conn.commit()


def reset_password(user_id: int, nova_senha: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            _ensure_schema(cur)
            cur.execute(
                "UPDATE usuarios SET senha_hash=%s WHERE id=%s;",
                (_hash_password(nova_senha), user_id)
            )
        conn.commit()
