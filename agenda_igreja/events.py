# agenda_igreja/events.py
from __future__ import annotations

from datetime import date
from typing import Optional, Any
from agenda_igreja.db import get_db_connection


def init_events():
    """
    Cria a tabela e faz migrações (adiciona colunas que podem estar faltando).
    Isso resolve o erro do atualizado_em em banco antigo.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Tabela base
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
                    atualizado_em TIMESTAMP
                );
            """)

            # Migrações para bancos que já tinham a tabela antiga
            cur.execute("ALTER TABLE eventos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW();")
            cur.execute("ALTER TABLE eventos ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP;")

            # Índices pra lista por período ficar rápida
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos (data);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos (tipo);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_congregacao ON eventos (congregacao);")

        conn.commit()


def create_event(payload: dict):
    cols = [
        "congregacao", "tipo", "subtipo", "turma_ebd", "data", "horario",
        "dirigente1", "dirigente2", "dirigente3",
        "portaria1", "portaria2", "portaria3",
        "recepcao1", "recepcao2", "recepcao3",
        "secretaria", "observacoes"
    ]
    values = [payload.get(c) for c in cols]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO eventos ({",".join(cols)})
                VALUES ({",".join(["%s"] * len(cols))})
                RETURNING id;
                """,
                tuple(values),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
    return new_id


def update_event(event_id: int, payload: dict):
    cols = [
        "congregacao", "tipo", "subtipo", "turma_ebd", "data", "horario",
        "dirigente1", "dirigente2", "dirigente3",
        "portaria1", "portaria2", "portaria3",
        "recepcao1", "recepcao2", "recepcao3",
        "secretaria", "observacoes"
    ]

    sets = [f"{c}=%s" for c in cols]
    values = [payload.get(c) for c in cols]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE eventos
                SET {",".join(sets)},
                    atualizado_em = NOW()
                WHERE id=%s;
                """,
                tuple(values + [event_id]),
            )
        conn.commit()


def delete_event(event_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eventos WHERE id=%s;", (event_id,))
        conn.commit()


def get_event(event_id: int) -> Optional[dict[str, Any]]:
    if not event_id:
        return None

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, congregacao, tipo, subtipo, turma_ebd, data, horario,
                    dirigente1, dirigente2, dirigente3,
                    portaria1, portaria2, portaria3,
                    recepcao1, recepcao2, recepcao3,
                    secretaria, observacoes,
                    criado_em, atualizado_em
                FROM eventos
                WHERE id=%s
                LIMIT 1;
                """,
                (event_id,),
            )
            row = cur.fetchone()

    if not row:
        return None

    keys = [
        "id", "congregacao", "tipo", "subtipo", "turma_ebd", "data", "horario",
        "dirigente1", "dirigente2", "dirigente3",
        "portaria1", "portaria2", "portaria3",
        "recepcao1", "recepcao2", "recepcao3",
        "secretaria", "observacoes",
        "criado_em", "atualizado_em"
    ]
    return dict(zip(keys, row))


def list_events_between(dt_ini: date, dt_fim: date, congregacao: str | None = None, tipo: str | None = None):
    """
    Retorna lista de dicts.
    Não quebra se a UI pedir.
    """
    where = ["data >= %s", "data <= %s"]
    params = [dt_ini, dt_fim]

    if congregacao:
        where.append("congregacao = %s")
        params.append(congregacao)

    if tipo:
        where.append("tipo = %s")
        params.append(tipo)

    sql = f"""
        SELECT
            id, congregacao, tipo, subtipo, turma_ebd, data, horario,
            dirigente1, dirigente2, dirigente3,
            portaria1, portaria2, portaria3,
            recepcao1, recepcao2, recepcao3,
            secretaria, observacoes,
            criado_em, atualizado_em
        FROM eventos
        WHERE {" AND ".join(where)}
        ORDER BY data ASC, horario ASC, congregacao ASC;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    keys = [
        "id", "congregacao", "tipo", "subtipo", "turma_ebd", "data", "horario",
        "dirigente1", "dirigente2", "dirigente3",
        "portaria1", "portaria2", "portaria3",
        "recepcao1", "recepcao2", "recepcao3",
        "secretaria", "observacoes",
        "criado_em", "atualizado_em"
    ]

    out = []
    for r in rows:
        out.append(dict(zip(keys, r)))
    return out
