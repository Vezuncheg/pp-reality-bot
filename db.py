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

    # Платежи
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
            status          TEXT DEFAULT 'active',
            utm_source      TEXT,
            utm_medium      TEXT,
            utm_campaign    TEXT
        )
    """)

    # Воронка пользователей
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

    # Все пользователи бота
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id           BIGINT PRIMARY KEY,
            username        TEXT,
            full_name       TEXT,
            first_seen      TIMESTAMP NOT NULL DEFAULT NOW(),
            last_seen       TIMESTAMP NOT NULL DEFAULT NOW(),
            start_count     INTEGER NOT NULL DEFAULT 1,
            archetype       TEXT,
            gender          TEXT,
            age             INTEGER,
            weight          NUMERIC,
            height          NUMERIC,
            goal            TEXT,
            utm_source      TEXT,
            utm_medium      TEXT,
            utm_campaign    TEXT,
            quiz_answers    TEXT
        )
    """)

    # События пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_events (
            id              SERIAL PRIMARY KEY,
            tg_id           BIGINT NOT NULL,
            event           TEXT NOT NULL,
            data            TEXT,
            created_at      TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_tg_id ON user_events(tg_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_event ON user_events(event)")

    # Миграция — добавляем новые колонки если их нет
    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS utm_source TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS utm_medium TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS utm_campaign TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_answers TEXT",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS utm_source TEXT",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS utm_medium TEXT",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS utm_campaign TEXT",
    ]
    for m in migrations:
        try:
            cur.execute(m)
        except Exception:
            pass

    conn.commit()
    cur.close()
    conn.close()
    logger.info("БД инициализирована (PostgreSQL) ✅")


# ── PAYMENTS ──────────────────────────────────────────────

def save_payment(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    # Берём UTM из таблицы users если не переданы явно
    utm_source = data.get("utm_source")
    utm_medium = data.get("utm_medium")
    utm_campaign = data.get("utm_campaign")
    if not utm_source and data.get("tg_id"):
        try:
            cur.execute("SELECT utm_source, utm_medium, utm_campaign FROM users WHERE tg_id=%s", (data["tg_id"],))
            row = cur.fetchone()
            if row:
                utm_source, utm_medium, utm_campaign = row
        except Exception:
            pass
    cur.execute("""
        INSERT INTO payments
        (payment_id, tg_id, tg_username, name, email, plan, plan_name,
         amount, paid_at, club_until, channel_link, club_link, status,
         utm_source, utm_medium, utm_campaign)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
        data.get("status", "active"),
        utm_source, utm_medium, utm_campaign
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
               amount, paid_at, club_until, status,
               utm_source, utm_medium, utm_campaign
        FROM payments ORDER BY paid_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ── USER FUNNELS ───────────────────────────────────────────

def funnel_start(tg_id: int, d1h_at, b1_at):
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
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_funnels
            SET blocks_sent = CASE
                WHEN blocks_sent = '' THEN %s
                ELSE blocks_sent || ',' || %s
            END,
            updated_at = NOW()
            WHERE tg_id = %s
        """, (block, block, tg_id))
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


# ── USERS ─────────────────────────────────────────────────

def user_upsert(tg_id: int, username: str = None, full_name: str = None):
    """Создаёт или обновляет пользователя. Считает запуски."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (tg_id, username, full_name, first_seen, last_seen, start_count)
            VALUES (%s, %s, %s, NOW(), NOW(), 1)
            ON CONFLICT (tg_id) DO UPDATE SET
                username    = COALESCE(EXCLUDED.username, users.username),
                full_name   = COALESCE(EXCLUDED.full_name, users.full_name),
                last_seen   = NOW(),
                start_count = users.start_count + 1
        """, (tg_id, username, full_name))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"user_upsert error: {e}")


def user_update_profile(tg_id: int, archetype: str = None, gender: str = None,
                        age: int = None, weight: float = None,
                        height: float = None, goal: str = None,
                        utm_source: str = None, utm_medium: str = None,
                        utm_campaign: str = None, quiz_answers: str = None):
    """Сохраняет данные анкеты пользователя."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        fields = []
        values = []
        for col, val in [("archetype", archetype), ("gender", gender), ("age", age),
                         ("weight", weight), ("height", height), ("goal", goal),
                         ("utm_source", utm_source), ("utm_medium", utm_medium),
                         ("utm_campaign", utm_campaign), ("quiz_answers", quiz_answers)]:
            if val is not None:
                fields.append(f"{col} = %s")
                values.append(val)
        if fields:
            values.append(tg_id)
            cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE tg_id = %s", values)
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"user_update_profile error: {e}")


def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.tg_id, u.username, u.full_name, u.first_seen, u.last_seen,
               u.start_count, u.archetype, u.gender, u.age, u.weight, u.height, u.goal,
               COALESCE(p.plan_name, '—') as plan,
               COALESCE(p.amount::text, '—') as amount,
               COALESCE(p.paid_at, '—') as paid_at,
               u.utm_source, u.utm_medium, u.utm_campaign, u.quiz_answers
        FROM users u
        LEFT JOIN payments p ON p.tg_id = u.tg_id AND p.status = 'active'
        ORDER BY u.first_seen DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_broadcast_users():
    """Возвращает всех пользователей для рассылки."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT tg_id FROM users ORDER BY first_seen ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        logger.error(f"get_broadcast_users error: {e}")
        return []


# ── USER EVENTS ────────────────────────────────────────────

def log_event(tg_id: int, event: str, data: str = None):
    """Записывает событие пользователя."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_events (tg_id, event, data) VALUES (%s, %s, %s)",
            (tg_id, event, data)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"log_event error: {e}")


def get_stats():
    """Возвращает сводную статистику."""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users WHERE first_seen > NOW() - INTERVAL '24 hours'")
        new_today = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users WHERE first_seen > NOW() - INTERVAL '7 days'")
        new_week = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT tg_id) FROM payments WHERE status='active'")
        paid_total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT tg_id) FROM user_funnels WHERE is_paid = FALSE")
        in_funnel = cur.fetchone()[0]

        cur.execute("""
            SELECT event, COUNT(*) FROM user_events
            GROUP BY event ORDER BY COUNT(*) DESC
        """)
        events = cur.fetchall()

        cur.execute("""
            SELECT archetype, COUNT(*) FROM users
            WHERE archetype IS NOT NULL
            GROUP BY archetype ORDER BY COUNT(*) DESC
        """)
        archetypes = cur.fetchall()

        cur.execute("SELECT SUM(amount) FROM payments WHERE status='active'")
        revenue = cur.fetchone()[0] or 0

        cur.close()
        conn.close()
        return {
            "total_users": total_users,
            "new_today": new_today,
            "new_week": new_week,
            "paid_total": paid_total,
            "in_funnel": in_funnel,
            "events": events,
            "archetypes": archetypes,
            "revenue": revenue,
        }
    except Exception as e:
        logger.error(f"get_stats error: {e}")
        return {}


def get_all_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.tg_id, u.full_name, u.username, e.event, e.data, e.created_at
        FROM user_events e
        LEFT JOIN users u ON u.tg_id = e.tg_id
        ORDER BY e.created_at DESC
        LIMIT 10000
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
