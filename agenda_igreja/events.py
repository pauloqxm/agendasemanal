# agenda_igreja/events.py
import json
from datetime import date
from agenda_igreja.db import get_db_connection

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
                    criado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS eventos_log (
                    id SERIAL PRIMARY KEY,
                    evento_id INTEGER,
                    usuario_id INTEGER,
                    acao TEXT CHECK (acao IN ('CRIADO','EDITADO','EXCLUIDO')),
                    dados_anteriores JSONB,
                    dados_novos JSONB,
                    data_acao TIMESTAMP DEFAULT NOW()
                );
            """)

        conn.commit()

def _to_dict_from_row(row):
    if not row:
        return None
    cols = [
        "id","congregacao","tipo","subtipo","turma_ebd","data","horario",
        "dirigente1","dirigente2","dirigente3",
        "portaria1","portaria2","portaria3",
        "recepcao1","recepcao2","recepcao3",
        "secretaria","observacoes","criado_em","atualizado_em"
    ]
    return dict(zip(cols, row))

def _log(conn, evento_id, usuario_id, acao, antes=None, depois=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO eventos_log (evento_id, usuario_id, acao, dados_anteriores, dados_novos)
            VALUES (%s, %s, %s, %s, %s);
        """, (
            evento_id,
            usuario_id,
            acao,
            json.dumps(antes, default=str) if antes else None,
            json.dumps(depois, default=str) if depois else None
        ))

def create_event(payload: dict, usuario_id: int | None = None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eventos (
                    congregacao,tipo,subtipo,turma_ebd,data,horario,
                    dirigente1,dirigente2,dirigente3,
                    portaria1,portaria2,portaria3,
                    recepcao1,recepcao2,recepcao3,
                    secretaria,observacoes
                )
                VALUES (
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,%s,
                    %s,%s,%s,
                    %s,%s,%s,
                    %s,%s
                )
                RETURNING id;
            """, (
                payload.get("congregacao"),
                payload.get("tipo"),
                payload.get("subtipo"),
                payload.get("turma_ebd"),
                payload.get("data"),
                payload.get("horario"),
                payload.get("dirigente1"),
                payload.get("dirigente2"),
                payload.get("dirigente3"),
                payload.get("portaria1"),
                payload.get("portaria2"),
                payload.get("portaria3"),
                payload.get("recepcao1"),
                payload.get("recepcao2"),
                payload.get("recepcao3"),
                payload.get("secretaria"),
                payload.get("observacoes"),
            ))
            new_id = cur.fetchone()[0]

        depois = get_event(new_id, _existing_conn=conn)
        _log(conn, new_id, usuario_id, "CRIADO", antes=None, depois=depois)
        conn.commit()
    return new_id

def get_event(event_id: int, _existing_conn=None):
    conn = _existing_conn or get_db_connection().__enter__()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id,congregacao,tipo,subtipo,turma_ebd,data,horario,
                       dirigente1,dirigente2,dirigente3,
                       portaria1,portaria2,portaria3,
                       recepcao1,recepcao2,recepcao3,
                       secretaria,observacoes,criado_em,atualizado_em
                FROM eventos
                WHERE id=%s;
            """, (event_id,))
            row = cur.fetchone()
        return _to_dict_from_row(row)
    finally:
        if _existing_conn is None:
            conn.close()

def update_event(event_id: int, payload: dict, usuario_id: int | None = None):
    with get_db_connection() as conn:
        antes = get_event(event_id, _existing_conn=conn)

        with conn.cursor() as cur:
            cur.execute("""
                UPDATE eventos
                SET
                    congregacao=%s,
                    tipo=%s,
                    subtipo=%s,
                    turma_ebd=%s,
                    data=%s,
                    horario=%s,
                    dirigente1=%s, dirigente2=%s, dirigente3=%s,
                    portaria1=%s, portaria2=%s, portaria3=%s,
                    recepcao1=%s, recepcao2=%s, recepcao3=%s,
                    secretaria=%s,
                    observacoes=%s,
                    atualizado_em=NOW()
                WHERE id=%s;
            """, (
                payload.get("congregacao"),
                payload.get("tipo"),
                payload.get("subtipo"),
                payload.get("turma_ebd"),
                payload.get("data"),
                payload.get("horario"),
                payload.get("dirigente1"),
                payload.get("dirigente2"),
                payload.get("dirigente3"),
                payload.get("portaria1"),
                payload.get("portaria2"),
                payload.get("portaria3"),
                payload.get("recepcao1"),
                payload.get("recepcao2"),
                payload.get("recepcao3"),
                payload.get("secretaria"),
                payload.get("observacoes"),
                event_id
            ))

        depois = get_event(event_id, _existing_conn=conn)
        _log(conn, event_id, usuario_id, "EDITADO", antes=antes, depois=depois)
        conn.commit()

def delete_event(event_id: int, usuario_id: int | None = None):
    with get_db_connection() as conn:
        antes = get_event(event_id, _existing_conn=conn)

        with conn.cursor() as cur:
            cur.execute("DELETE FROM eventos WHERE id=%s;", (event_id,))

        _log(conn, event_id, usuario_id, "EXCLUIDO", antes=antes, depois=None)
        conn.commit()

def list_events_between(dt_ini: date, dt_fim: date, congregacao=None, tipo=None):
    sql = """
        SELECT id,congregacao,tipo,subtipo,turma_ebd,data,horario,
               dirigente1,dirigente2,dirigente3,
               portaria1,portaria2,portaria3,
               recepcao1,recepcao2,recepcao3,
               secretaria,observacoes,criado_em,atualizado_em
        FROM eventos
        WHERE data BETWEEN %s AND %s
    """
    params = [dt_ini, dt_fim]

    if congregacao:
        sql += " AND congregacao=%s"
        params.append(congregacao)

    if tipo:
        sql += " AND tipo=%s"
        params.append(tipo)

    sql += " ORDER BY data ASC, horario ASC, congregacao ASC;"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    return [_to_dict_from_row(r) for r in rows]

def list_event_logs(evento_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, evento_id, usuario_id, acao, dados_anteriores, dados_novos, data_acao
                FROM eventos_log
                WHERE evento_id=%s
                ORDER BY data_acao DESC;
            """, (evento_id,))
            rows = cur.fetchall()

    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "evento_id": r[1],
            "usuario_id": r[2],
            "acao": r[3],
            "antes": r[4],
            "depois": r[5],
            "data_acao": r[6],
        })
    return out
