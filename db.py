"""
db.py — единый модуль работы с БД (PostgreSQL через Supabase)
Используй Transaction Pooler URL (порт 6543) в DATABASE_URL для Railway.
"""
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    import psycopg2
    # connect_timeout — защита от зависания при недоступной БД
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id              SERIAL PRIMARY KEY,
            payment_id      TEXT UNIQUE,
            tg_id           BIGINT,
            tg_username     TEXT,
            name            TEXT,
            email           TEXT,
            plan            TEXT,
            plan_name       TEXT,
            amount          INTEGER,
            paid_at         TEXT,
            club_until      TEXT,
            channel_link    TEXT,
            club_link       TEXT,
            status          TEXT DEFAULT 'active'
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("БД инициализирована (PostgreSQL) ✅")


def save_payment(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO payments
        (payment_id, tg_id, tg_username, name, email, plan, plan_name,
         amount, paid_at, club_until, channel_link, club_link, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (payment_id) DO UPDATE SET
            channel_link = EXCLUDED.channel_link,
            club_link    = EXCLUDED.club_link,
            club_until   = EXCLUDED.club_until
    """, (
        data["payment_id"], data["tg_id"], data.get("tg_username"),
        data.get("name"), data.get("email"),
        data["plan"], data["plan_name"], data["amount"],
        data["paid_at"], data.get("club_until"),
        data.get("channel_link"), data.get("club_link"),
        data.get("status", "active")
    ))
    conn.commit()
    cur.close()
    conn.close()


def update_payment_links(payment_id: str, channel_link: str, club_link: str, club_until: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE payments SET channel_link=%s, club_link=%s, club_until=%s WHERE payment_id=%s",
        (channel_link, club_link, club_until, payment_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def is_paid(tg_id: int) -> bool:
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM payments WHERE tg_id=%s AND status='active' LIMIT 1",
            (tg_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row is not None
    except Exception as e:
        logger.error(f"is_paid error: {e}")
        return False


def get_all_payments():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, email, tg_id, tg_username, plan_name,
               amount, paid_at, club_until, status
        FROM payments ORDER BY paid_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
