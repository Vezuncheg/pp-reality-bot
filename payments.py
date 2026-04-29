"""
payments.py — обработчик платежей ЮКасса + webhook сервер
Запускается рядом с ботом на Railway через Procfile
"""
import os
import json
import hmac
import hashlib
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from aiohttp import web
import httpx

# ── Переменные окружения ──
YUKASSA_SHOP_ID  = os.getenv("YUKASSA_SHOP_ID")
YUKASSA_SECRET   = os.getenv("YUKASSA_SECRET_KEY")
BOT_TOKEN        = os.getenv("BOT_TOKEN")
CHANNEL_ID       = int(os.getenv("CHANNEL_ID", "0"))
CLUB_CHAT_ID     = int(os.getenv("CLUB_CHAT_ID", "0"))
ADMIN_TG_ID      = int(os.getenv("ADMIN_TG_ID", "0"))
DB_PATH          = "/app/payments.db"
PORT             = int(os.getenv("PAYMENT_PORT", "8080"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Тарифы ──
PLANS = {
    "base":     {"name": "Стартовый пинок",     "amount": 100,  "club": False},  # 1 руб для теста
    "extended": {"name": "Полное погружение",    "amount": 100,  "club": True},
    "personal": {"name": "Иван лично со мной",  "amount": 100,  "club": True},
}

# ── База данных ──
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id      TEXT UNIQUE,
            tg_id           INTEGER,
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
    conn.close()
    logger.info("БД инициализирована")


def save_payment(data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO payments
        (payment_id, tg_id, tg_username, name, email, plan, plan_name,
         amount, paid_at, club_until, channel_link, club_link, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["payment_id"], data["tg_id"], data.get("tg_username"),
        data.get("name"), data.get("email"),
        data["plan"], data["plan_name"], data["amount"],
        data["paid_at"], data.get("club_until"),
        data.get("channel_link"), data.get("club_link"), "active"
    ))
    conn.commit()
    conn.close()


# ── Telegram API ──
async def tg_api(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=payload)
        return r.json()


async def send_message(chat_id: int, text: str, **kwargs):
    await tg_api("sendMessage", {"chat_id": chat_id, "text": text, **kwargs})


async def create_invite_link(chat_id: int, name: str) -> str:
    """Создаёт одноразовую invite-ссылку (member_limit=1)"""
    result = await tg_api("createChatInviteLink", {
        "chat_id": chat_id,
        "name": name,
        "member_limit": 1,  # только одно вступление
        "creates_join_request": False,
    })
    if result.get("ok"):
        return result["result"]["invite_link"]
    raise Exception(f"Ошибка создания ссылки: {result}")


# ── Создание платежа ЮКасса ──
async def create_payment(plan_key: str, tg_id: int, name: str, email: str, tg_username: str = "") -> dict:
    plan = PLANS[plan_key]
    idempotence_key = f"{tg_id}-{plan_key}-{int(datetime.now().timestamp())}"

    payload = {
        "amount": {
            "value": f"{plan['amount']:.2f}",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://pp-reality.ru/pay.html?success=1&tg_id={tg_id}"
        },
        "description": f"{plan['name']} — Реалити #ПП",
        "metadata": {
            "tg_id": str(tg_id),
            "tg_username": tg_username,
            "name": name,
            "email": email,
            "plan": plan_key,
        },
        "receipt": {
            "customer": {"email": email},
            "items": [{
                "description": f"{plan['name']} — Реалити #ПП «Программа Преображения»",
                "quantity": "1",
                "amount": {
                    "value": f"{plan['amount']:.2f}",
                    "currency": "RUB"
                },
                "vat_code": 1,  # без НДС
                "payment_mode": "full_payment",
                "payment_subject": "service"
            }]
        }
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.yookassa.ru/v3/payments",
            json=payload,
            auth=(YUKASSA_SHOP_ID, YUKASSA_SECRET),
            headers={"Idempotence-Key": idempotence_key}
        )
        result = r.json()

    if r.status_code not in (200, 201):
        raise Exception(f"ЮКасса ошибка: {result}")

    return {
        "payment_id": result["id"],
        "payment_url": result["confirmation"]["confirmation_url"],
        "plan_key": plan_key,
        "plan_name": plan["name"],
        "amount": plan["amount"],
        "tg_id": tg_id,
        "tg_username": tg_username,
        "name": name,
        "email": email,
    }


# ── Обработка успешного платежа ──
async def handle_successful_payment(payment_data: dict):
    meta = payment_data.get("metadata", {})
    tg_id       = int(meta.get("tg_id", 0))
    tg_username = meta.get("tg_username", "")
    name        = meta.get("name", "")
    email       = meta.get("email", "")
    plan_key    = meta.get("plan", "base")
    plan        = PLANS.get(plan_key, PLANS["base"])
    payment_id  = payment_data["id"]
    amount      = int(float(payment_data["amount"]["value"]))
    paid_at     = datetime.now().isoformat()

    logger.info(f"Успешная оплата: tg_id={tg_id} plan={plan_key} amount={amount}")

    # Генерируем invite-ссылки
    ts = datetime.now().strftime("%d.%m %H:%M")
    channel_link = await create_invite_link(CHANNEL_ID, f"{name} {ts}")

    club_link  = None
    club_until = None

    if plan["club"]:
        club_link  = await create_invite_link(CLUB_CHAT_ID, f"Клуб {name} {ts}")
        club_until = (datetime.now() + timedelta(days=30)).isoformat()

    # Сохраняем в БД
    save_payment({
        "payment_id":   payment_id,
        "tg_id":        tg_id,
        "tg_username":  tg_username,
        "name":         name,
        "email":        email,
        "plan":         plan_key,
        "plan_name":    plan["name"],
        "amount":       amount,
        "paid_at":      paid_at,
        "club_until":   club_until,
        "channel_link": channel_link,
        "club_link":    club_link,
    })

    # Отправляем ссылки пользователю
    if plan["club"]:
        msg = (
            f"✅ Оплата прошла успешно!\n\n"
            f"Добро пожаловать в Реалити #ПП «Программа Преображения»!\n\n"
            f"Вы приобрели тариф *{plan['name']}*\n\n"
            f"📌 *Ваши ссылки для вступления:*\n\n"
            f"1️⃣ Закрытый канал реалити:\n{channel_link}\n\n"
            f"2️⃣ Клуб поддержки (доступен после завершения реалити):\n{club_link}\n\n"
            f"⚠️ Каждая ссылка одноразовая — только для Вас.\n"
            f"Не передавайте её другим людям.\n\n"
            f"Старт: 11 мая. Ждём Вас! 🔥"
        )
    else:
        msg = (
            f"✅ Оплата прошла успешно!\n\n"
            f"Добро пожаловать в Реалити #ПП «Программа Преображения»!\n\n"
            f"Вы приобрели тариф *{plan['name']}*\n\n"
            f"📌 *Ваша ссылка для вступления:*\n\n"
            f"🔗 Закрытый канал реалити:\n{channel_link}\n\n"
            f"⚠️ Ссылка одноразовая — только для Вас.\n"
            f"Не передавайте её другим людям.\n\n"
            f"Старт: 11 мая. Ждём Вас! 🔥"
        )

    await send_message(tg_id, msg, parse_mode="Markdown")

    # Уведомление администратору
    admin_msg = (
        f"💰 *Новая оплата!*\n\n"
        f"👤 {name} (@{tg_username}, ID: {tg_id})\n"
        f"📧 {email}\n"
        f"📦 Тариф: {plan['name']}\n"
        f"💵 Сумма: {amount} ₽\n"
        f"🕐 {paid_at[:16].replace('T', ' ')}"
    )
    await send_message(ADMIN_TG_ID, admin_msg, parse_mode="Markdown")


# ── HTTP сервер ──
async def handle_create_payment(request: web.Request) -> web.Response:
    """POST /create-payment — создаёт платёж и возвращает URL"""
    try:
        body = await request.json()
        plan_key    = body.get("plan", "base")
        tg_id       = int(body.get("tg_id", 0))
        name        = body.get("name", "")
        email       = body.get("email", "")
        tg_username = body.get("tg_username", "")

        if not tg_id or not email or not name:
            return web.json_response({"error": "Заполните все поля"}, status=400)

        if plan_key not in PLANS:
            return web.json_response({"error": "Неверный тариф"}, status=400)

        result = await create_payment(plan_key, tg_id, name, email, tg_username)
        return web.json_response({"payment_url": result["payment_url"]})

    except Exception as e:
        logger.error(f"create_payment error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_webhook(request: web.Request) -> web.Response:
    """POST /webhook — обрабатывает уведомления от ЮКассы"""
    try:
        body = await request.read()
        data = json.loads(body)

        event = data.get("event")
        payment = data.get("object", {})

        logger.info(f"Webhook: event={event} payment_id={payment.get('id')}")

        if event == "payment.succeeded":
            await handle_successful_payment(payment)

        return web.Response(status=200, text="ok")

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500, text=str(e))


async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


def create_app():
    app = web.Application()
    app.router.add_post("/create-payment", handle_create_payment)
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/health", handle_health)
    return app


if __name__ == "__main__":
    init_db()
    app = create_app()
    logger.info(f"Payment server starting on port {PORT}")
    web.run_app(app, port=PORT)
