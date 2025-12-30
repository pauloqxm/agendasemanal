from datetime import date
from .db import get_db_connection

def init_events():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id SERIAL PRIMARY KEY,

                    congregacao TEXT NOT NULL,

                    tipo TEXT NOT NULL,
                    subtipo TEXT,
                    turma_ebd TEXT,

                    data DATE NOT NULL,
                    horario TIME NOT NULL,

                    dirigente1 TEXT,
                    dirigente2 TEXT,
                    dirigente3 TEXT,

                    portaria1 TEXT,
                    portaria2 TEXT,
                    portaria3 TEXT,

                    recepcao1 TEXT,
                    recepcao2 TEXT,
                    recepcao3 TEXT,

                    secretaria TEXT,

                    observacoes TEXT,
                    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos (data);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_congregacao ON eventos (congregacao);")
        conn.commit()

def create_event(payload: dict):
    cols = list(payload.keys())
    vals = [payload[c] for c in cols]
    ph = ",".join(["%s"] * len(cols))
    col_sql = ",".join(cols)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"INSERT INTO eventos ({col_sql}) VALUES ({ph}) RETURNING id;", vals)
            new_id = cur.fetchone()[0]
        conn.commit()
    return new_id

def update_event(event_id: int, payload: dict):
    sets = ",".join([f"{k}=%s" for k in payload.keys()])
    vals = list(payload.values()) + [event_id]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE eventos SET {sets} WHERE id=%s;", vals)
        conn.commit()

def delete_event(event_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eventos WHERE id=%s;", (event_id,))
        conn.commit()

def get_event(event_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM eventos WHERE id=%s;", (event_id,))
            row = cur.fetchone()
            if not row:
                return None

            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))

def list_events_between(dt_ini: date, dt_fim: date, congregacao: str | None = None, tipo: str | None = None):
    where = ["data BETWEEN %s AND %s"]
    params = [dt_ini, dt_fim]

    if congregacao and congregacao != "Todas":
        where.append("congregacao=%s")
        params.append(congregacao)

    if tipo and tipo != "Todos":
        where.append("tipo=%s")
        params.append(tipo)

    sql = f"""
        SELECT *
        FROM eventos
        WHERE {" AND ".join(where)}
        ORDER BY data ASC, horario ASC, congregacao ASC;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
