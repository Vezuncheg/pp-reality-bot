"""
db.py — единый модуль работы с БД (PostgreSQL через Supabase)
Используй Transaction Pooler URL (порт 6543) в DATABASE_URL для Railway.
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Таблица платежей
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

    # Таблица воронки пользователей — для восстановления после деплоя
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_funnels (
            tg_id           BIGINT PRIMARY KEY,
            started_at      TIMESTAMP NOT NULL DEFAULT NOW(),
            blocks_sent     TEXT NOT NULL DEFAULT '',
            d1h_at          TIMESTAMP,
            b1_at           TIMESTAMP,
            b2_at           TIMESTAMP,
            b3_at           TIMESTAMP,
            final_at        TIMESTAMP,
            is_paid         BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    logger.info("БД инициализирована (PostgreSQL) ✅")


# ── PAYMENTS ──────────────────────────────────────────────

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


# ── USER FUNNELS ───────────────────────────────────────────

def funnel_start(tg_id: int, d1h_at, b1_at):
    """Создаёт запись воронки при старте пользователя."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_funnels (tg_id, started_at, d1h_at, b1_at, updated_at)
            VALUES (%s, NOW(), %s, %s, NOW())
            ON CONFLICT (tg_id) DO UPDATE SET
                started_at = NOW(),
                blocks_sent = '',
                d1h_at = EXCLUDED.d1h_at,
                b1_at  = EXCLUDED.b1_at,
                b2_at  = NULL,
                b3_at  = NULL,
                final_at = NULL,
                is_paid = FALSE,
                updated_at = NOW()
        """, (tg_id, d1h_at, b1_at))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"funnel_start error: {e}")


def funnel_mark_block(tg_id: int, block: str, next_block: str = None, next_at=None):
    """Помечает блок как отправленный и планирует следующий."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        # Добавляем блок в список отправленных
        cur.execute("""
            UPDATE user_funnels
            SET blocks_sent = CASE
                WHEN blocks_sent = '' THEN %s
                ELSE blocks_sent || ',' || %s
            END,
            updated_at = NOW()
            WHERE tg_id = %s
        """, (block, block, tg_id))

        # Обновляем время следующего блока
        if next_block and next_at:
            col_map = {"d1h": "d1h_at", "b1": "b1_at", "b2": "b2_at", "b3": "b3_at", "final": "final_at"}
            col = col_map.get(next_block)
            if col:
                cur.execute(f"UPDATE user_funnels SET {col} = %s WHERE tg_id = %s", (next_at, tg_id))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"funnel_mark_block error: {e}")


def funnel_mark_paid(tg_id: int):
    """Отмечает пользователя как оплатившего — останавливает воронку."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE user_funnels SET is_paid = TRUE, updated_at = NOW() WHERE tg_id = %s",
            (tg_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"funnel_mark_paid error: {e}")


def funnel_get_active():
    """Возвращает все активные воронки для восстановления после деплоя."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT tg_id, blocks_sent, d1h_at, b1_at, b2_at, b3_at, final_at
            FROM user_funnels
            WHERE is_paid = FALSE
              AND started_at > NOW() - INTERVAL '7 days'
            ORDER BY started_at ASC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"funnel_get_active error: {e}")
        return []
