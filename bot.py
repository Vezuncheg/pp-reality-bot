import asyncio
import json
import base64
import logging
import math
import os
import secrets
import httpx
from datetime import datetime
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, MenuButtonCommands
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

import aiosqlite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN     = os.getenv("BOT_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
DB_PATH       = "users.db"

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


# ───────── БД ─────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id       INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                created_at  TEXT,
                last_seen   TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id       INTEGER,
                data        TEXT,
                created_at  TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id       INTEGER,
                type        TEXT,
                content     TEXT,
                created_at  TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT PRIMARY KEY,
                data        TEXT,
                created_at  TEXT
            )
        """)
        await db.commit()


async def save_user(tg_id, username, first_name):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (tg_id, username, first_name, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET last_seen=?, first_name=?, username=?
        """, (tg_id, username, first_name, now, now, now, first_name, username))
        await db.commit()


async def save_assessment(tg_id, data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO assessments (tg_id, data, created_at) VALUES (?, ?, ?)",
            (tg_id, json.dumps(data, ensure_ascii=False), datetime.now().isoformat())
        )
        await db.commit()


async def get_last_assessment(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT data, created_at FROM assessments WHERE tg_id=? ORDER BY id DESC LIMIT 1",
            (tg_id,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return json.loads(row[0]), row[1]
    return None, None


async def save_plan(tg_id, plan_type, content):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO plans (tg_id, type, content, created_at) VALUES (?, ?, ?, ?)",
            (tg_id, plan_type, content, datetime.now().isoformat())
        )
        await db.commit()


async def save_session(session_id: str, data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO sessions (session_id, data, created_at) VALUES (?, ?, ?)",
            (session_id, json.dumps(data, ensure_ascii=False), datetime.now().isoformat())
        )
        await db.commit()


async def get_session(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT data FROM sessions WHERE session_id=?", (session_id,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return json.loads(row[0])
    return None


# ───────── HTTP API ─────────

async def handle_save_session(request):
    if request.method == 'OPTIONS':
        return web.Response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
    try:
        data = await request.json()
        session_id = secrets.token_urlsafe(8)
        await save_session(session_id, data)
        return web.json_response(
            {"session_id": session_id},
            headers={'Access-Control-Allow-Origin': '*'}
        )
    except Exception as e:
        logger.error(f"Save session error: {e}")
        return web.json_response(
            {"error": str(e)}, status=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )


async def handle_health(request):
    return web.Response(text="OK", headers={'Access-Control-Allow-Origin': '*'})


# ───────── HELPERS ─────────

def decode_data(raw: str) -> dict:
    try:
        padded = raw + "=" * (-len(raw) % 4)
        decoded = base64.urlsafe_b64decode(padded).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        logger.error(f"Decode error: {e}")
        return {}


def format_results(data: dict) -> str:
    g   = data.get("gender", "m")
    w   = float(data.get("weight", 0) or 0)
    h   = float(data.get("height", 0) or 0)
    age = float(data.get("age", 0) or 0)
    act = float(data.get("activity", 1.375) or 1.375)
    goal = data.get("goal", "maintain")

    goal_map = {"loss": "Похудение", "maintain": "Поддержание", "gain": "Набор массы", "health": "Здоровье"}
    fit_map  = {"beginner": "Новичок", "basic": "Базовый", "intermediate": "Средний", "advanced": "Продвинутый"}
    eat_map  = {"chaos": "Хаотичное", "schedule": "По расписанию", "skip": "Пропускает приёмы", "track": "Следит за питанием"}
    mot_map  = {"look": "внешний вид", "energy": "энергия", "sport": "спорт", "feel": "самочувствие", "strength": "сила", "balance": "баланс"}

    lines = ["📊 *Твои результаты*\n"]

    if w and h and age:
        bmr  = round(10*w + 6.25*h - 5*age + (5 if g == "m" else -161))
        goal_k = {"loss": 0.8, "maintain": 1.0, "gain": 1.15, "health": 1.0}.get(goal, 1.0)
        kcal = round(bmr * act * goal_k)
        prot = round(kcal * 0.25 / 4)
        fat  = round(kcal * 0.30 / 9)
        carb = round(kcal * 0.45 / 4)
        bmi  = round(w / (h / 100) ** 2, 1)
        bmi_cat = "Недовес" if bmi < 18.5 else "Норма" if bmi < 25 else "Избыток" if bmi < 30 else "Ожирение"
        water = round(w * 35)

        lines.append(f"*Параметры:* {w} кг · {h} см · {int(age)} лет")
        lines.append(f"*ИМТ:* {bmi} — {bmi_cat}")
        lines.append(f"*Базовый метаболизм:* {bmr} ккал")
        lines.append(f"*Норма калорий/день:* {kcal} ккал")
        lines.append(f"\n*БЖУ:*")
        lines.append(f"  🥩 Белки — {prot} г ({round(prot*4)} ккал)")
        lines.append(f"  🧈 Жиры — {fat} г ({round(fat*9)} ккал)")
        lines.append(f"  🍞 Углеводы — {carb} г ({round(carb*4)} ккал)")
        lines.append(f"\n💧 *Вода:* {water/1000:.1f} л/день")

    neck  = float(data.get("neck", 0) or 0)
    waist = float(data.get("waist", 0) or 0)
    hips  = float(data.get("hips", 0) or 0)
    if neck and waist and h:
        try:
            if g == "m":
                fp = 495 / (1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(h)) - 450
            elif hips:
                fp = 495 / (1.29579 - 0.35004 * math.log10(waist + hips - neck) + 0.22100 * math.log10(h)) - 450
            else:
                fp = None
            if fp and 3 <= fp <= 60:
                fp = round(fp, 1)
                fat_mass = round(w * fp / 100, 1)
                lean = round(w - fat_mass, 1)
                lines.append(f"\n🔥 *Процент жира:* {fp}%")
                lines.append(f"  Жировая масса: {fat_mass} кг")
                lines.append(f"  Мышечная масса: {lean} кг")
        except Exception as e:
            logger.error(f"Fat calc error: {e}")

    lines.append(f"\n*Цель:* {goal_map.get(goal, '—')}")

    if data.get("fitness_lvl"):
        lines.append(f"*Уровень подготовки:* {fit_map.get(data['fitness_lvl'], '—')}")
    if data.get("eating"):
        lines.append(f"*Питание сейчас:* {eat_map.get(data['eating'], '—')}")

    drive = data.get("drive", [])
    if drive:
        mots = ", ".join(mot_map.get(x, x) for x in (drive if isinstance(drive, list) else [drive]))
        lines.append(f"*Мотивация:* {mots}")

    return "\n".join(lines)


def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥗 План питания",      callback_data="plan_nutrition")],
        [InlineKeyboardButton(text="🏋️ План тренировок",  callback_data="plan_workout")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад в меню", callback_data="back_menu")]
    ])


# ───────── HANDLERS ─────────

@dp.message(CommandStart())
async def cmd_start(message: Message):
    args  = message.text.split(maxsplit=1)
    param = args[1] if len(args) > 1 else ""

    await save_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    data = {}
    if param:
        session_data = await get_session(param)
        if session_data:
            data = session_data
        else:
            data = decode_data(param)

    if data:
        await save_assessment(message.from_user.id, data)
        await message.answer(
            f"👋 Привет, *{message.from_user.first_name}*!\n\n"
            "Я *FitState Bot* — твой персональный ассистент по питанию и тренировкам.\n\n"
            "Я получил результаты твоего теста. Смотри данные ниже 👇",
            parse_mode="Markdown"
        )
        results_text = format_results(data)
        await message.answer(
            results_text + "\n\n*Что хочешь получить?*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            f"👋 Привет, *{message.from_user.first_name}*!\n\n"
            "Я *FitState Bot* — твой персональный ассистент по питанию и тренировкам.\n\n"
            "🧮 Пройди бесплатный тест на сайте и получи персональный план питания и тренировок.\n\n"
            "👉 Нажми кнопку ниже чтобы начать:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🌐 Пройти тест на сайте",
                    url="https://vezuncheg.github.io/kbzhu-calculator/assessment.html"
                )
            ]])
        )


@dp.message(Command("results"))
async def cmd_results(message: Message):
    data, created_at = await get_last_assessment(message.from_user.id)
    if not data:
        await message.answer(
            "У меня нет твоих результатов теста.\n\nПройди тест на сайте и возвращайся!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🌐 Пройти тест",
                    url="https://vezuncheg.github.io/kbzhu-calculator/assessment.html"
                )
            ]])
        )
        return
    date_str = created_at[:10] if created_at else "—"
    results_text = format_results(data)
    await message.answer(
        f"{results_text}\n\n📅 _Дата теста: {date_str}_",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


@dp.message(Command("nutrition"))
async def cmd_nutrition(message: Message):
    await handle_plan(message.from_user.id, "nutrition", message)


@dp.message(Command("workout"))
async def cmd_workout(message: Message):
    await handle_plan(message.from_user.id, "workout", message)


@dp.callback_query(F.data == "plan_nutrition")
async def cb_nutrition(callback: CallbackQuery):
    await callback.answer()
    await handle_plan(callback.from_user.id, "nutrition", callback.message)


@dp.callback_query(F.data == "plan_workout")
async def cb_workout(callback: CallbackQuery):
    await callback.answer()
    await handle_plan(callback.from_user.id, "workout", callback.message)


@dp.callback_query(F.data == "back_menu")
async def cb_back(callback: CallbackQuery):
    await callback.answer()
    data, _ = await get_last_assessment(callback.from_user.id)
    if data:
        results_text = format_results(data)
        await callback.message.answer(
            results_text + "\n\n*Что хочешь получить?*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        await callback.message.answer("Выбери действие:", reply_markup=main_keyboard())


async def handle_plan(tg_id: int, plan_type: str, message: Message):
    data, _ = await get_last_assessment(tg_id)
    if not data:
        await message.answer(
            "Сначала пройди тест на сайте — там я получу твои данные и смогу составить план.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🌐 Пройти тест",
                    url="https://vezuncheg.github.io/kbzhu-calculator/assessment.html"
                )
            ]])
        )
        return

    type_label = "питания" if plan_type == "nutrition" else "тренировок"
    wait_msg = await message.answer(
        f"⏳ Составляю персональный план {type_label}...\nОбычно это занимает 15–20 секунд."
    )

    plan = await generate_plan_claude(data, plan_type)
    await bot.delete_message(message.chat.id, wait_msg.message_id)

    chunks = [plan[i:i+4000] for i in range(0, len(plan), 4000)]
    for i, chunk in enumerate(chunks):
        kb = back_keyboard() if i == len(chunks) - 1 else None
        await message.answer(chunk, parse_mode="Markdown", reply_markup=kb)

    await save_plan(tg_id, plan_type, plan)


# ───────── CLAUDE API ─────────

async def generate_plan_claude(data: dict, plan_type: str) -> str:
    g = data.get("gender", "m")

    goal_map  = {"loss": "похудение", "maintain": "поддержание", "gain": "набор массы", "health": "здоровье"}
    fit_map   = {"beginner": "новичок", "basic": "базовый", "intermediate": "средний", "advanced": "продвинутый"}
    act_map   = {"1.2": "минимальная", "1.375": "лёгкая", "1.55": "умеренная", "1.725": "высокая"}
    place_map = {"gym": "зал", "home": "дома", "outdoor": "улица", "mix": "по-разному"}
    inj_map   = {"none": "нет", "legs": "колени/ноги", "back": "спина/плечи", "other": "другое"}
    eat_map   = {"chaos": "хаотичное", "schedule": "по расписанию", "skip": "пропускает приёмы", "track": "следит"}
    cook_map  = {"never": "почти никогда", "sometimes": "1–3 раза/нед", "often": "4–6 раз/нед", "always": "каждый день"}
    mot_map   = {"look": "внешний вид", "energy": "энергия", "sport": "спорт", "feel": "самочувствие", "strength": "сила", "balance": "баланс"}
    style_map = {"strict": "чёткий план", "flexible": "гибкий", "support": "с поддержкой", "science": "научный"}
    fail_map  = {"diet": "срывы в питании", "time": "нехватка времени", "noresult": "не было результата", "first": "первый раз"}
    sleep_map = {"bad": "меньше 6 часов", "ok": "6–7 часов", "good": "7–8 часов", "great": "больше 8 часов"}

    drive = data.get("drive", [])
    mots  = ", ".join(mot_map.get(x, x) for x in (drive if isinstance(drive, list) else [drive]))

    goal     = goal_map.get(data.get("goal", ""), "—")
    activity = act_map.get(str(data.get("activity", "")), "—")
    fitness  = fit_map.get(data.get("fitness_lvl", ""), "—")
    place    = place_map.get(data.get("place", ""), "—")
    injuries = inj_map.get(data.get("injuries", "none"), "нет")
    eating   = eat_map.get(data.get("eating", ""), "—")
    cook     = cook_map.get(data.get("cook", ""), "—")
    style    = style_map.get(data.get("style", ""), "—")
    fail     = fail_map.get(data.get("fail_reason", ""), "—")
    sleep    = sleep_map.get(data.get("sleep", ""), "—")
    stress   = data.get("stress", "—")
    gender_str = "мужской" if g == "m" else "женский"

    profile = (
        f"Пол: {gender_str}, возраст: {data.get('age','?')}, "
        f"рост: {data.get('height','?')} см, вес: {data.get('weight','?')} кг\n"
        f"Цель: {goal}\n"
        f"Активность: {activity}\n"
        f"Уровень подготовки: {fitness}\n"
        f"Место тренировок: {place}\n"
        f"Травмы: {injuries}\n"
        f"Сон: {sleep}\n"
        f"Стресс: {stress}/5\n"
        f"Питание сейчас: {eating}\n"
        f"Готовит дома: {cook}\n"
        f"Мотивация: {mots}\n"
        f"Подход: {style}\n"
        f"Причина прошлых неудач: {fail}"
    )

    if plan_type == "nutrition":
        prompt = (
            "Ты эксперт по спортивному питанию. Составь персональный план питания на неделю на русском языке.\n\n"
            f"ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n{profile}\n\n"
            "ФОРМАТ (Markdown для Telegram):\n"
            "*🥗 Персональный план питания*\n\n"
            "*Твои нормы:*\nКалории и БЖУ — конкретные цифры.\n\n"
            "*Принципы питания*\n3–4 правила под цель и образ жизни.\n\n"
            f"*Меню на неделю*\nКаждый день: завтрак, обед, ужин, перекус. Конкретные продукты с граммовками. Учти готовку дома: {cook}.\n\n"
            "*Список продуктов на неделю*\nКраткий список что купить.\n\n"
            "*Первые шаги*\n3 действия которые сделать сегодня.\n\n"
            f"Пиши конкретно, без воды. Подход: {style}."
        )
    else:
        prompt = (
            "Ты эксперт по фитнесу. Составь персональную программу тренировок на 4 недели на русском языке.\n\n"
            f"ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n{profile}\n\n"
            "ФОРМАТ (Markdown для Telegram):\n"
            "*🏋️ Персональный план тренировок*\n\n"
            "*Твой уровень и подход*\n2–3 предложения почему план составлен именно так.\n\n"
            f"*Расписание на неделю*\n7 дней: тренировки и отдых. Место: {place}.\n\n"
            f"*Программа тренировок*\nДля каждого тренировочного дня: упражнения, подходы × повторения, отдых. Учти травмы: {injuries}.\n\n"
            "*Прогрессия нагрузки*\nКак менять нагрузку по неделям (1–4 неделя).\n\n"
            f"*Восстановление*\n3 совета под стресс {stress}/5 и сон {sleep}.\n\n"
            "*Первые шаги*\n3 действия чтобы начать уже сегодня.\n\n"
            f"Пиши конкретно. Уровень: {fitness}."
        )

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            result = resp.json()
            return result["content"][0]["text"]
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return "Произошла ошибка при генерации плана. Попробуй ещё раз через минуту."


# ───────── ЗАПУСК ─────────

async def setup_commands():
    commands = [
        BotCommand(command="start",     description="Главное меню"),
        BotCommand(command="results",   description="Мои последние результаты"),
        BotCommand(command="nutrition", description="Мой план питания"),
        BotCommand(command="workout",   description="Мой план тренировок"),
    ]
    await bot.set_my_commands(commands)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def main():
    await init_db()
    await setup_commands()

    app = web.Application()
    app.router.add_post('/save_session', handle_save_session)
    app.router.add_options('/save_session', handle_save_session)
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server started on port {port}")

    logger.info("FitState Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
