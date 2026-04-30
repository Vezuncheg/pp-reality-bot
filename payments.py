"""
payments.py — webhook сервер ЮКасса + обработка платежей
"""
import os
import json
import logging
from datetime import datetime, timedelta
from aiohttp import web
import httpx
from db import init_db, save_payment, update_payment_links

BOT_TOKEN    = os.getenv("BOT_TOKEN")
CHANNEL_ID   = int(os.getenv("CHANNEL_ID", "0"))
CLUB_CHAT_ID = int(os.getenv("CLUB_CHAT_ID", "0"))
ADMIN_TG_ID  = int(os.getenv("ADMIN_TG_ID", "0"))
YUKASSA_SHOP_ID = os.getenv("YUKASSA_SHOP_ID")
YUKASSA_SECRET  = os.getenv("YUKASSA_SECRET_KEY")
PORT = int(os.getenv("PORT", "8080"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PLANS = {
    "base":     {"name": "Стартовый пинок",    "amount": 5300,  "amount_sale": 4600,  "club": False},
    "extended": {"name": "Полное погружение",   "amount": 7900,  "amount_sale": 6900,  "club": True},
    "personal": {"name": "Иван лично со мной", "amount": 21200, "amount_sale": 18500, "club": True},
}

async def tg_api(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=payload)
        return r.json()

async def send_message(chat_id: int, text: str, **kwargs):
    await tg_api("sendMessage", {"chat_id": chat_id, "text": text, **kwargs})

async def create_invite_link(chat_id: int, name: str) -> str:
    result = await tg_api("createChatInviteLink", {
        "chat_id": chat_id,
        "name": name,
        "member_limit": 1,
        "creates_join_request": False,
    })
    if result.get("ok"):
        return result["result"]["invite_link"]
    raise Exception(f"Ошибка создания ссылки: {result}")

async def create_payment(plan_key: str, tg_id: int, name: str, email: str, tg_username: str = "", promo: bool = False) -> dict:
    plan = PLANS[plan_key]
    amount = plan["amount_sale"] if promo and "amount_sale" in plan else plan["amount"]
    idempotence_key = f"{tg_id}-{plan_key}-{int(datetime.now().timestamp())}"
    payload = {
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://pp-reality.ru/pay.html?success=1&tg_id={tg_id}"
        },
        "description": f"{plan['name']} — Реалити #ПП",
        "metadata": {
            "tg_id": str(tg_id), "tg_username": tg_username,
            "name": name, "email": email, "plan": plan_key,
        },
        "receipt": {
            "customer": {"email": email},
            "items": [{
                "description": f"{plan['name']} — Реалити #ПП «Программа Преображения»",
                "quantity": "1",
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "vat_code": 1,
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
        "plan_key": plan_key, "plan_name": plan["name"],
        "amount": amount, "tg_id": tg_id,
        "tg_username": tg_username, "name": name, "email": email,
    }

async def handle_successful_payment(payment_data: dict):
    meta      = payment_data.get("metadata", {})
    tg_id     = int(meta.get("tg_id", 0))
    tg_username = meta.get("tg_username", "")
    name      = meta.get("name", "")
    email     = meta.get("email", "")
    plan_key  = meta.get("plan", "base")
    plan      = PLANS.get(plan_key, PLANS["base"])
    payment_id = payment_data["id"]
    amount    = int(float(payment_data["amount"]["value"]))
    paid_at   = datetime.now().isoformat()

    logger.info(f"Успешная оплата: tg_id={tg_id} plan={plan_key} amount={amount}")

    # Отмечаем воронку как оплаченную — останавливает дальнейшие рассылки
    try:
        from db import funnel_mark_paid as _mark_paid
        _mark_paid(tg_id)
    except Exception as e:
        logger.error(f"funnel_mark_paid error: {e}")

    # Сохраняем сразу — данные не потеряются
    save_payment({
        "payment_id": payment_id, "tg_id": tg_id,
        "tg_username": tg_username, "name": name, "email": email,
        "plan": plan_key, "plan_name": plan["name"],
        "amount": amount, "paid_at": paid_at,
        "club_until": None, "channel_link": None, "club_link": None,
        "status": "active"
    })

    # Генерируем ссылки
    ts = datetime.now().strftime("%d.%m %H:%M")
    channel_link = None
    try:
        channel_link = await create_invite_link(CHANNEL_ID, f"{name} {ts}")
    except Exception as e:
        logger.error(f"Ошибка ссылки канала: {e}")
        await send_message(ADMIN_TG_ID,
            f"⚠️ Ошибка ссылки канала для {name} (tg_id={tg_id})\nПроверьте права бота!")

    club_link  = None
    club_until = None
    if plan["club"]:
        try:
            club_link  = await create_invite_link(CLUB_CHAT_ID, f"Клуб {name} {ts}")
            club_until = (datetime.now() + timedelta(days=30)).isoformat()
        except Exception as e:
            logger.error(f"Ошибка ссылки клуба: {e}")
            await send_message(ADMIN_TG_ID,
                f"⚠️ Ошибка ссылки клуба для {name} (tg_id={tg_id})\nПроверьте права бота!")

    # Обновляем ссылки в БД
    update_payment_links(payment_id, channel_link, club_link, club_until)

    # Отправляем ссылки пользователю
    if plan["club"]:
        msg = (
            f"✅ Оплата прошла успешно!\n\n"
            f"Добро пожаловать в Реалити #ПП «Программа Преображения»!\n\n"
            f"Вы приобрели тариф *{plan['name']}*\n\n"
            f"📌 *Ваши ссылки для вступления:*\n\n"
            f"1️⃣ Закрытый канал реалити:\n{channel_link or '⚠️ Ошибка — обратитесь в поддержку'}\n\n"
            f"2️⃣ Клуб поддержки (после завершения реалити):\n{club_link or '⚠️ Ошибка — обратитесь в поддержку'}\n\n"
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
            f"🔗 {channel_link or '⚠️ Ошибка — обратитесь в поддержку'}\n\n"
            f"⚠️ Ссылка одноразовая — только для Вас.\n"
            f"Старт: 11 мая. Ждём Вас! 🔥"
        )

    if tg_id:
        await send_message(tg_id, msg, parse_mode="Markdown")

    # Уведомление администратору
    await send_message(ADMIN_TG_ID,
        f"💰 *Новая оплата!*\n\n"
        f"👤 {name} (@{tg_username}, ID: {tg_id})\n"
        f"📧 {email}\n"
        f"📦 Тариф: {plan['name']}\n"
        f"💵 Сумма: {amount} ₽\n"
        f"🕐 {paid_at[:16].replace('T', ' ')}",
        parse_mode="Markdown"
    )

# HTTP handlers
async def cors_middleware(app, handler):
    async def middleware(request):
        if request.method == "OPTIONS":
            return web.Response(headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "86400",
            })
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    return middleware

async def handle_create_payment(request: web.Request) -> web.Response:
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
        promo = body.get("promo", False)
        result = await create_payment(plan_key, tg_id, name, email, tg_username, promo=promo)
        return web.json_response({"payment_url": result["payment_url"]})
    except Exception as e:
        logger.error(f"create_payment error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_webhook(request: web.Request) -> web.Response:
    try:
        body = await request.read()
        data = json.loads(body)
        event   = data.get("event")
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
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_post("/create-payment", handle_create_payment)
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/health", handle_health)
    app.router.add_route("OPTIONS", "/create-payment", lambda r: web.Response(
        headers={"Access-Control-Allow-Origin": "*",
                 "Access-Control-Allow-Methods": "POST, OPTIONS",
                 "Access-Control-Allow-Headers": "Content-Type"}))
    return app
