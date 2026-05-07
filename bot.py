import os
import logging
import asyncio
from datetime import datetime
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
QUIZ_URL  = "https://pp-reality.ru"
PAY_URL   = "https://pp-reality.ru/pay.html"
PAY_PROMO = "https://pp-reality.ru/pay.html?promo=1"
PAYMENT_URL = PAY_URL
PHOTOS_URL = "https://raw.githubusercontent.com/Vezuncheg/fitstate/main/images"
SUPPORT_GROUP_ID = int(os.getenv("SUPPORT_GROUP_ID", "-1003977221459"))

ASK_GENDER, ASK_AGE, ASK_WEIGHT, ASK_HEIGHT, ASK_GOAL = range(5)

ARCHETYPES = {
    "emotional_eater": {
        "emoji": "😰", "name": "Эмоциональный едок",
        "problem": "Вы не срываетесь потому что слабый.\nВы срываетесь, потому что мозг выучил паттерн:\nстресс → еда → легче.\n\nЭто не вопрос силы воли — это вопрос замены инструмента.\nБез работы с этим — любая диета временная.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Стресс активирует тягу к еде\n→ Ты ешь — становится легче\n→ Потом вина → ещё стресс → снова ешь\n→ Круг замкнулся",
        "solution": "✅ Что реально помогает:\n\n→ Замечать триггер до того, как рука потянулась\n→ Заменить еду другим инструментом снятия стресса\n→ Убрать провоцирующие ситуации заранее\n\nЭто навык. Ему можно научиться за 3–4 недели.",
        "tools": "🛠 Что добавим в Вашем случае:\n\n1️⃣ Техники прерывания эмоционального триггера — заметите импульс до того, как потянулись к еде\n2️⃣ Быстрые замены — 3–4 инструмента снятия стресса без еды\n3️⃣ Структуру питания — уберём ситуации, где срыв наиболее вероятен",
        "day3": "📌 Топ-3 ошибки эмоционального едока:\n\n1. Держать дома запасы любимой еды\n2. Пропускать приёмы пищи — голод усиливает триггер\n3. Бороться силой воли — нужно переключать, не бороться",
        "proof": "Анна, 34 года — минус 11 кг за 28 дней.\nПерестала есть от стресса уже на 2-й неделе.\n\nМихаил, 31 год — минус 9 кг. Впервые не сорвался ни разу.",
    },
    "social_hostage": {
        "emoji": "🍕", "name": "Социальный заложник",
        "problem": "Наедине с собой Вы держитесь отлично.\nНо любое застолье или компания — всё рушится.\n\nЭто не слабость характера — это отсутствие конкретной стратегии.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Всю неделю держишься — приходит праздник\n→ Неловко отказывать, не хочешь выделяться\n→ Ешь как все — прогресс обнуляется\n→ Снова с понедельника",
        "solution": "✅ Что реально помогает:\n\n→ Конкретные сценарии: кафе, корпоратив, застолье\n→ Фразы-ответы, которые не обидят\n→ Правило 80/20 — как позволять себе без ущерба\n\nЭто навык, а не сила воли.",
        "tools": "🛠 Что добавим в Вашем случае:\n\n1️⃣ Стратегию поведения в любой компании — кафе, корпоратив, застолье\n2️⃣ Гибкую систему питания — любой праздник больше не обнуляет прогресс\n3️⃣ Конкретные фразы — как отказывать без обид и не выделяться",
        "day3": "📌 Топ-3 ошибки социального заложника:\n\n1. Ждать подходящего момента — его не будет\n2. Избегать мероприятий — это не жизнь\n3. Есть про запас перед выходом — не работает",
        "proof": "Катя, 29 лет — минус 8 кг без отказа от вечеринок.\n\nДмитрий, 36 лет — минус 10 кг. Рестораны с клиентами каждую неделю — ни одного срыва.",
    },
    "metabolic_skeptic": {
        "emoji": "⚖️", "name": "Метаболический скептик",
        "problem": "Вы едите немного, стараетесь, делаете всё правильно.\nА результата нет.\n\nСтандартные советы просто не подходят для Вашей ситуации.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Ешь мало — вес стоит или растёт\n→ Добавляешь активность — результата нет\n→ Думаешь «мне не дано»\n→ Опускаешь руки",
        "solution": "✅ Что реально помогает:\n\n→ Точный расчёт твоего реального коридора калорий\n→ Перезапуск обмена через правильный дефицит\n→ Работа с режимом сна и стрессом\n\nМетаболизм не сломан. Ему дают неправильный сигнал.",
        "tools": "🛠 Что добавим в Вашем случае:\n\n1️⃣ Точный расчёт калорийности — реальный дефицит именно под Ваши параметры\n2️⃣ Правильный состав питания — соотношение БЖУ, которое запускает жиросжигание\n3️⃣ Работу с режимом — сон и стресс влияют на вес сильнее, чем многие думают",
        "day3": "📌 Почему «мало ешь, но не худеешь»:\n\n1. Хроническое недоедание замедляет метаболизм\n2. Скрытые калории в «здоровых» продуктах\n3. Кортизол от стресса блокирует жиросжигание",
        "proof": "Ирина, 38 лет — 2 года не могла сдвинуться с места.\nЗа 28 дней минус 7 кг. Оказалось — ела слишком мало.\n\nСергей, 33 года — тренировался 4 раза в неделю. Поменяли питание — минус 9 кг.",
    },
    "starter_stopper": {
        "emoji": "🔁", "name": "Стартер-стопер",
        "problem": "В начале мотивация огромная.\nНо через 10–14 дней она испаряется — и всё заново.\n\nПроблема не в Вас.\nПроблема в том, что Вы работаете на силе воли. А она конечна у всех.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Мощный старт — мотивация на максимуме\n→ Через 1–2 недели энтузиазм падает\n→ Один пропуск → ощущение провала → бросаешь\n→ Через время — снова с понедельника",
        "solution": "✅ Что реально помогает:\n\n→ Заменить мотивацию системой — она не исчезает\n→ Внешние точки контроля: куратор, группа\n→ Маленькие wins вместо большой далёкой цели\n\nКогда есть система и окружение — мотивация не нужна.",
        "tools": "🛠 Что добавим в Вашем случае:\n\n1️⃣ Систему вместо силы воли — ежедневную структуру, которой легко следовать\n2️⃣ Внешнюю поддержку — куратор и группа, которые не дают выпасть\n3️⃣ Протокол срыва — чёткий алгоритм что делать, если пропустили, чтобы не бросить совсем",
        "day3": "📌 Почему стартер-стопер останавливается на 2-й неделе:\n\n1. Мотивация эмоциональная — она быстро гаснет\n2. Нет системы на сложный день — один пропуск = провал\n3. Цель далеко — мозг не видит прогресса",
        "proof": "Олег, 27 лет — начинал 6 раз за 2 года.\nВ потоке FitState впервые прошёл все 28 дней. Минус 8 кг.\n\nНастя, 31 год — группа и куратор сделали то, что сила воли не смогла за 3 года.",
    },
}


def calc(weight, height, goal):
    bmi = round(weight / ((height / 100) ** 2), 1)
    if goal == "fat":
        # Реалистичные показатели за 28 дней
        lo, hi = (4, 6) if bmi > 30 else (3, 5) if bmi > 25 else (2, 4)
        wlo, whi = round(weight - hi), round(weight - lo)
        bmi2 = round((wlo + whi) / 2 / ((height / 100) ** 2), 1)
        return dict(cw=weight, cb=bmi, wr=f"{wlo}–{whi} кг",
                    ch=f"−{lo}–{hi} кг жира",
                    muscle="+0.5–1 кг мышц при правильном балансе БЖУ",
                    b2=bmi2,
                    waist=f"минус {lo}–{hi} см в талии",
                    en="заметно вырастет к 3-й неделе")
    elif goal == "muscle":
        return dict(cw=weight, cb=bmi,
                    wr=f"{round(weight+1)}–{round(weight+2)} кг",
                    ch="+1–2 кг мышечной массы",
                    muscle="жировая прослойка снизится на 0.5–1%",
                    b2=round(bmi+0.3, 1),
                    waist="больше мышц, рельеф",
                    en="вырастет к 2-й неделе")
    else:
        wlo, whi = round(weight - 3), round(weight - 2)
        bmi2 = round((wlo + whi) / 2 / ((height / 100) ** 2), 1)
        return dict(cw=weight, cb=bmi, wr=f"{wlo}–{whi} кг",
                    ch="−2–3 кг + рельеф и тонус",
                    muscle="+0.5–1.5 кг мышечного тонуса",
                    b2=bmi2,
                    waist="минус 2–4 см, заметный рельеф",
                    en="вырастет уже к концу 1-й недели")


def visual(f, name):
    return (
        f"🖼 *ТЫ СЕЙЧАС*\n"
        f"Вес: {f['cw']} кг\n"
        f"_{name}_\n\n"
        f"⬇️ Реалити #ПП «Программа Преображения» 28 дней ⬇️\n\n"
        f"🖼 *ТЫ ЧЕРЕЗ 28 ДНЕЙ*\n"
        f"Вес: {f['wr']}\n"
        f"*{f['ch']}*\n"
        f"*{f['muscle']}*\n\n"
        f"→ Объём: {f['waist']}\n"
        f"→ Энергия: {f['en']}\n\n"
        f"_На основе Ваших параметров и средних результатов участников с похожим профилем._"
    )


def pay_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Записаться →", url=PAYMENT_URL)]])


def more_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 История Ивана Самохина", callback_data="start_b1")],
        [InlineKeyboardButton("💪 Что вы получите в реалити?", callback_data="start_b2")],
        [InlineKeyboardButton("✅ Кому подходит, а кому нет?", callback_data="start_b3")],
        [InlineKeyboardButton("Записаться →", url=PAY_URL)],
    ])


async def send_photo_url(bot, chat_id, url, caption=None):
    """Скачивает фото и отправляет как файл. 3 попытки при ошибке."""
    import io
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(url, follow_redirects=True)
                r.raise_for_status()
            bio = io.BytesIO(r.content)
            bio.name = url.split("/")[-1]
            if caption:
                await bot.send_photo(chat_id=chat_id, photo=bio, caption=caption)
            else:
                await bot.send_photo(chat_id=chat_id, photo=bio)
            return  # успех — выходим
        except Exception as e:
            logger.warning(f"Попытка {attempt+1}/3 не удалась для {url}: {e}")
            if attempt < 2:
                await asyncio.sleep(3)  # пауза перед повтором
    # Все 3 попытки провалились
    logger.error(f"Не удалось отправить фото {url} после 3 попыток")
    await bot.send_message(chat_id=chat_id, text="📸 [фото временно недоступно]")


async def send_media_group_urls(bot, chat_id, urls):
    """Скачивает фото параллельно, конвертирует PNG→JPEG и отправляет медиагруппой."""
    import io
    import asyncio as _asyncio
    from PIL import Image

    async def fetch(url):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(url, follow_redirects=True)
                r.raise_for_status()
            data = r.content
            # Конвертируем PNG в JPEG чтобы Telegram не падал на image_process_failed
            if url.lower().endswith('.png'):
                img = Image.open(io.BytesIO(data)).convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=92)
                buf.seek(0)
                buf.name = url.split("/")[-1].replace('.png', '.jpg')
                return buf
            else:
                bio = io.BytesIO(data)
                bio.name = url.split("/")[-1]
                return bio
        except Exception as e:
            logger.error(f"Не удалось скачать фото {url}: {e}")
            return None

    bios = await _asyncio.gather(*[fetch(u) for u in urls])
    valid_bios = [bio for bio in bios if bio is not None]

    if not valid_bios:
        logger.error("Все фото в медиагруппе недоступны")
        return

    # Пробуем отправить медиагруппой
    try:
        media = [InputMediaPhoto(media=bio) for bio in valid_bios]
        await bot.send_media_group(
            chat_id=chat_id, media=media,
            write_timeout=120, read_timeout=120, connect_timeout=60
        )
    except Exception as e:
        logger.error(f"Медиагруппа не отправилась ({e}), отправляем по одному")
        # Fallback — отправляем каждое фото отдельно
        for bio in valid_bios:
            try:
                bio.seek(0)
                await bot.send_photo(chat_id=chat_id, photo=bio,
                    write_timeout=60, read_timeout=60)
                await asyncio.sleep(1)
            except Exception as e2:
                logger.error(f"Фото не отправилось: {e2}")


async def schedule_dojim(uid, context):
    jq = context.application.job_queue
    if not jq:
        return

    # ── Через 1 час: таймер истёк, предлагаем 3 раздела ──
    async def d1h(ctx):
        if is_paid(uid):
            logger.info(f"uid={uid} уже оплатил — d1h пропущен")
            return
        await ctx.bot.send_message(
            uid,
            "Прежде чем примите решение, хочу рассказать Вам больше о том, что стоит за Реалити #ПП.\n\n"
            "Выберите, с чего начать 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 История Ивана Самохина", callback_data="start_b1")],
                [InlineKeyboardButton("💪 Что вы получите в реалити?", callback_data="start_b2")],
                [InlineKeyboardButton("✅ Кому подходит реалити, а кому нет?", callback_data="start_b3")],
                [InlineKeyboardButton("Записаться →", url=f"{PAY_URL}?tg_id={uid}")],
            ])
        )
        # Помечаем как выполненный — при следующем деплое не будет восстанавливаться
        try:
            from db import funnel_mark_block as _mark_d1h
            _mark_d1h(uid, "d1h")
        except Exception as e:
            logger.error(f"funnel_mark_block d1h error: {e}")

    # ── Блок 1: Об Иване (день 1) ──
    async def block1(ctx):
        if is_paid(uid):
            logger.info(f"uid={uid} уже оплатил — блок 1 пропущен")
            return

        # Вступление от команды
        await ctx.bot.send_message(uid,
            "*Кто такой Иван Самохин?*\n"
            "Создатель Реалити #ПП «Программа Преображения» 👇\n\n"
            "Вы знаете его как создателя и ведущего подкаста «Состояние» "
            "со 155 000 подписчиков на YouTube и 65+ миллионами просмотров "
            "на интервью с врачами, психологами, тренерами и политологами.\n\n"
            "Но сейчас Вы узнаете про его путь в преображении тела и поддержании "
            "хорошей формы на протяжении 24 лет. Иван расскажет свою историю 👇",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)

        # Часть 1 — детство, генетика, привычки
        await ctx.bot.send_message(uid,
            "*НАЧАЛО*\n\n"
            "В детстве я был слабым ребёнком — постоянно болел, плохой иммунитет. "
            "Таких сейчас называют астеник. Можно уверенно сказать, что я был дрыщом в 14 лет.\n\n"
            "*«У тебя просто генетика» — самый вредный миф*\n\n"
            "Когда люди видят мой результат сегодня, говорят: «Ну у тебя гены». "
            "Они не видели меня в 14 лет — худого, слабого, с плохим иммунитетом. "
            "Я начал качаться под впечатлением от Сталлоне и Шварценеггера, как и многие из вас.\n\n"
            "Важна не генетика, а привычки. За последние три месяца я не пропустил ни одной "
            "из трёх тренировок в неделю. Не потому что я сверхчеловек. А потому что это стало "
            "такой же автоматикой, как чистить зубы.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)

        # Фото 1 — коллаж по годам
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/ivan_years.jpeg")
        await asyncio.sleep(20)

        # Часть 3 — почему не тренер (жирный заголовок)
        await ctx.bot.send_message(uid,
            "*Почему я не тренер (и почему это вам выгодно)*\n\n"
            "За 24 года я перепробовал сотни тренеров в разных странах. И знаете что?\n\n"
            "Большинство из них:\n"
            "→ Рано или поздно предлагают анаболики (им нужен быстрый кейс, а не ваше здоровье)\n"
            "→ Живут в зале по 12 часов, питаются из контейнеров, не выходят в рестораны\n"
            "→ Видят только вес и процент жира, забывая про кожу, волосы, ментальное состояние\n\n"
            "Я не тренер и не врач. Я практик с 24-летним стажем, который провёл 60+ интервью "
            "с учёными, генетиками и эндокринологами. Я не рассказываю теорию — я применяю всё на себе.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)

        # Фото — книги и канал медиагруппой
        await send_media_group_urls(ctx.bot, uid, [
            f"{PHOTOS_URL}/book_sostoyanie.jpeg",
            f"{PHOTOS_URL}/book_sostoyanie2.jpeg",
            f"{PHOTOS_URL}/youtube_channel.jpeg",
        ])
        await asyncio.sleep(20)

        # Часть 4 — почему тренировки не работают
        await ctx.bot.send_message(uid,
            "*Почему ваши тренировки не работают (и что делать вместо этого)*\n\n"
            "Вы знаете это чувство: купили абонемент, пошли три недели, потом работа, "
            "командировка, «всё потом нагоню». Или сели на марафон — отказались от всего, "
            "тренировались как сумасшедшие, а через месяц вернулись к жизни с лишними тремя "
            "килограммами и чувством вины.\n\n"
            "Я проходил это. Ломал ногу, пропадал на месяцы, работал допоздна. И каждый раз "
            "возвращался к форме не благодаря «железной воле», а благодаря системе, которая "
            "работает даже когда жизнь летит к чертям.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)

        # Часть 5 — система против марафонов
        await ctx.bot.send_message(uid,
            "*Система против марафонов*\n\n"
            "Марафон по природе вырывает вас из жизни: резкие запреты, режим, отказ от семьи "
            "и работы. Потом — обязательный откат.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)

        # Часть 6 — мой подход другой
        await ctx.bot.send_message(uid,
            "*Мой подход другой.*\n\n"
            "Я работаю каждый день в своём бизнесе, ем в ресторанах, бывает и фастфуд, "
            "перелёты, дедлайны. И при этом уже 24 года держу форму.\n\n"
            "Секрет не в отказах, а в пропорциях. Как в хорошем супе — важно соотношение "
            "ингредиентов, а не голодовка.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)

        # Фото — результаты 28 дней (новое фото с реальными цифрами)
        # Часть 7 — реальные цифры
        await ctx.bot.send_message(uid,
            "*Реальные цифры (снято на камеру)*\n\n"
            "Перед запуском я прошёл программу сам. С нуля, зафиксировав всё:\n\n"
            "За 28 дней:\n"
            "→ −4,3 кг общего веса\n"
            "→ −2,2 кг жировой массы\n"
            "→ −1,8% телесного жира\n\n"
            "При этом я не сидел на воде и огурцах. Ходил в рестораны, работал, жил нормальной жизнью.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/ivan_before_after.jpeg")
        await asyncio.sleep(20)

        # Часть 8 — что вы получите + закрывающий CTA
        await ctx.bot.send_message(uid,
            "*Что вы получите*\n\n"
            "Это не очередной «стань качком за месяц» с фейковыми фото. Это система привычек, которая:\n\n"
            "→ Работает в условиях перегрузов и командировок\n"
            "→ Не требует жить в зале и носить еду в контейнерах\n"
            "→ Учитывает ваше ментальное и физическое здоровье как единое целое\n"
            "→ Остаётся с вами навсегда, а не на 28 дней\n\n"
            "*Старт программы: 21 мая.*\n\n"
            "Места ограничены — я работаю с небольшими группами, чтобы отслеживать результат каждого.\n\n"
            "Если вы устали от тренеров-зомби и марафонов, которые ведут к откату — "
            "*пришло время для системы, которая работает в реальной жизни.\n"
            "Если Вы чувствуете, что это то, что Вам нужно — не откладывайте.*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )

        # Помечаем b1 как выполненный
        try:
            from db import funnel_mark_block as _mark_b1
            _mark_b1(uid, "b1")
        except Exception as e:
            logger.error(f"funnel_mark_block b1 error: {e}")
        # Запускаем следующий непросмотренный блок
        await schedule_next_unseen(uid, "b1", ctx)

    # ── Блок 2: Подробно о продукте (день 2) ──
    async def block2(ctx):
        if is_paid(uid):
            logger.info(f"uid={uid} уже оплатил — блок 2 пропущен")
            return

        # Вступление
        await ctx.bot.send_message(uid,
            "☄️ Почему Вы не худеете — и это точно не лень\n\n"
            "Иван записал урок, который отвечает на главный вопрос: "
            "почему Вы уже 100 раз начинали, срывались, а вес возвращался."
        )
        await asyncio.sleep(20)

        # Что внутри урока
        await ctx.bot.send_message(uid,
            "Что внутри:\n\n"
            "• Почему дело часто не в «силе воли»\n"
            "• Как худеть без голода и без «есть на 1200»\n"
            "• Примеры питания на 1500 / 2000 / 2500 / 3000 ккал\n"
            "• Как вписывать «запрещёнку» — бургер, пиво, шаурму, сладкое, десерты — без чувства вины\n\n"
            "После просмотра Вы:\n\n"
            "• Поймёте, почему раньше не получалось\n"
            "• Увидите, какие шаги реально дают результат\n"
            "• Перестанете ломать себя и начнёте действовать по системе"
        )
        await asyncio.sleep(20)

        # Ссылка на урок + призыв
        await ctx.bot.send_message(uid,
            "Смотрите урок по ссылке:\n"
            "👉 https://kinescope.io/hubcbT4t5vnaLVYPC6UjAK\n\n"
            "─────────────────\n\n"
            "А всё, о чём говорится в уроке — это основа Реалити #ПП. "
            "Только не в формате видео, а в формате живого процесса рядом с Иваном и куратором. "
            "28 дней, каждый день, с Вашим типом и Вашей целью.\n\n"
            "Старт *21 мая*. Если урок откликнулся — самое время сделать следующий шаг.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )

        # Запускаем block3 через 1 минуту после последнего сообщения
        jq = ctx.application.job_queue
        if jq:
            jq.run_once(block3, 60, name=f"b3_{uid}")

    # ── Блок 3: Кому подойдёт, а кому нет (день 3) ──
    async def block3(ctx):
        if is_paid(uid):
            logger.info(f"uid={uid} уже оплатил — блок 3 пропущен")
            return

        # Сообщение 1 — вступление + кому НЕ подойдёт + кому подойдёт (всё вместе)
        await ctx.bot.send_message(uid,
            "Хотим быть с Вами честными.\n\n"
            "Реалити #ПП подходит не всем — и это важно понять до того, как принимать решение. "
            "Прочитайте внимательно: это сэкономит Вам время и деньги, "
            "если программа действительно не для Вас. "
            "И укрепит уверенность — если Вы узнаёте себя в первом списке.\n\n"
            "🚫 Реалити не для Вас, если:\n\n"
            "❌ Вы ищете жёсткую диету с полным списком запретов — "
            "здесь нет запрещённых продуктов, только понимание пропорций\n\n"
            "❌ Вы хотите «минус 10 кг за неделю» — "
            "таких результатов не бывает без вреда для здоровья, "
            "и мы их не обещаем\n\n"
            "❌ Вы ждёте волшебную таблетку — "
            "здесь нужно участвовать, смотреть, применять. "
            "Пассивное наблюдение результата не даст\n\n"
            "✅ Реалити создано для Вас, если:\n\n"
            "✔ У Вас нет времени на сложные многочасовые программы — "
            "Вы живёте в режиме обычного человека: работа, семья, дела\n\n"
            "✔ Вы устали и в стрессе — и хотите наконец выстроить режим, "
            "не ломая себя и не отказываясь от жизни\n\n"
            "✔ Вы уже проходили через срывы и качели веса — "
            "начинали, бросали, снова начинали. И хотите выбраться из этого круга\n\n"
            "✔ Вы хотите форму без фанатизма — без лотков с едой, "
            "без двенадцати часов в зале, без ощущения, что жизнь проходит мимо\n\n"
            "✔ Вы хотите результат, который вписывается в обычную жизнь — "
            "с ресторанами, фастфудом, командировками и выходными"
        )
        await asyncio.sleep(20)

        # Сообщение 2 — что почувствуете + Иван прошёл + фото + CTA
        await ctx.bot.send_message(uid,
            "Что Вы почувствуете через 28 дней:\n\n"
            "✔ Снижение веса и объёмов — без голода и срывов\n"
            "✔ Больше энергии — уже к концу первой недели\n"
            "✔ Меньше тяги к вредной еде — потому что она перестаёт быть запретной\n"
            "✔ Уверенность в своём теле — Вы снова начинаете его понимать\n"
            "✔ Ощущение контроля — над едой, активностью, своим днём\n"
            "✔ Привычки, которые остаются с Вами — не временный марш-бросок, "
            "а новый способ жить\n\n"
            "Я уже прошёл этот путь.\n\n"
            "Эти 28 дней — не теория и не план. "
            "Это реальный процесс, который я прошёл сам и записал день за днём. "
            "Специально для того, чтобы Вам было легче пройти его сейчас.\n\n"
            "Никакого монтажа в стиле «до/после». "
            "Всё как есть, каждый день — питание, тренировки, усталость, обычная жизнь. "
            "Без фильтров и идеальных условий."
        )
        await asyncio.sleep(20)

        # Фото — до/после 28 дней
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/ivan_before_after.jpeg")
        await asyncio.sleep(20)

        # Закрывающий продающий текст + кнопка
        await ctx.bot.send_message(uid,
            "За 28 дней:\n"
            "→ −4,3 кг веса\n"
            "→ −2,2 кг жировой массы\n"
            "→ −1,8% телесного жира\n\n"
            "Без анаболиков. Без жёстких ограничений. В условиях обычной жизни.\n\n"
            "─────────────────\n\n"
            "Вы прочитали три блока. Вы знаете, кто Иван и почему ему можно доверять. "
            "Вы знаете, что внутри продукта. Вы знаете, для кого это.\n\n"
            "Если Вы узнали себя в списке тех, кому это подойдёт — "
            "не нужно больше думать и откладывать. "
            "Каждый день ожидания — это ещё один день в том же круге.\n\n"
            "*Старт 21 мая. Места ограничены.*\n\n"
            "Сделайте шаг прямо сейчас — пока есть возможность.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Записаться в Реалити →", url=PAY_URL)]
            ])
        )

        # Запускаем final через 1 минуту после последнего сообщения
        jq = ctx.application.job_queue
        if jq:
            jq.run_once(final, 60, name=f"fin_{uid}")

    # ── Финальный дожим (день 5) ──
    async def final(ctx):
        if is_paid(uid):
            logger.info(f"uid={uid} уже оплатил — финал пропущен")
            return
        await ctx.bot.send_message(
            uid,
            "*Реалити уже скоро!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Выбрать тариф →", url=PAY_URL)]
            ])
        )

    # ── ТАЙМИНГИ ──
    from datetime import timedelta
    now = datetime.now()
    d1h_at = now + timedelta(seconds=3600)
    b1_at  = now + timedelta(seconds=86400)

    # Сохраняем воронку в БД — восстановится после деплоя
    try:
        from db import funnel_start as _funnel_start
        _funnel_start(uid, d1h_at, b1_at)
    except Exception as e:
        logger.error(f"funnel_start DB error: {e}")

    jq.run_once(d1h,    3600,  name=f"d1h_{uid}")   # 1 час после оффера
    jq.run_once(block1, 86400, name=f"b1_{uid}")    # 1 сутки после оффера
    # block2, block3, final запускаются цепочкой внутри каждого блока


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arch_key = (context.args or [None])[0]
    arch = ARCHETYPES.get(arch_key)
    context.user_data["arch_key"] = arch_key

    # Логируем пользователя и событие
    uid = update.effective_user.id
    try:
        from db import user_upsert as _upsert, log_event as _log
        _upsert(uid,
                username=update.effective_user.username,
                full_name=update.effective_user.full_name)
        _log(uid, "start", arch_key or "direct")
        if arch_key:
            from db import user_update_profile as _profile
            _profile(uid, archetype=arch_key)
    except Exception as e:
        logger.error(f"analytics start error: {e}")

    if not arch:
        await update.message.reply_text(
            "Привет! 👋\nПройдите тест и получи разбор:\n\n"
            "👉 " + QUIZ_URL)
        return ConversationHandler.END

    context.user_data["in_quiz"] = True  # начало анкеты — блокируем пересылку в поддержку
    await update.message.reply_text("Привет! 👋\n\nПолучил Ваши ответы. Даю разбор — 1 минута.")
    await asyncio.sleep(1.2)
    await update.message.reply_text(f"*{arch['emoji']} Ваш тип: {arch['name']}*\n\n{arch['problem']}", parse_mode="Markdown")
    await asyncio.sleep(1.2)
    await update.message.reply_text(arch["cycle"])
    await asyncio.sleep(1.2)
    await update.message.reply_text(arch["solution"])
    await update.message.reply_text(
        "Хотите узнать — *каким Вы можете стать за 28 дней?*\n\nЕсли внедрить одну простую систему.\nЯ задам всего пару вопросов.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Да, хочу узнать →", callback_data="go")],
            [InlineKeyboardButton("Может позже", callback_data="later")],
        ]))
    return ASK_GENDER


async def cb_later(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["in_quiz"] = False  # пользователь отказался — снимаем блок
    await update.callback_query.message.reply_text("Хорошо! Когда будете готовы — /start\nМеню: /menu")
    return ConversationHandler.END


async def cb_go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Отлично! Отвечайте как есть.\n\n*Ты мужчина или женщина?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Мужчина", callback_data="gm"),
            InlineKeyboardButton("Женщина", callback_data="gf"),
        ]]))
    return ASK_GENDER


async def cb_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["gender"] = "male" if update.callback_query.data == "gm" else "female"
    await update.callback_query.message.reply_text("*Сколько Вам лет?*\n\nНапишите число:", parse_mode="Markdown")
    return ASK_AGE


async def got_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text.strip())
        assert 10 <= age <= 100
        context.user_data["age"] = age
        await update.message.reply_text("*Текущий вес в кг?*\n\nНапример: 84", parse_mode="Markdown")
        return ASK_WEIGHT
    except:
        await update.message.reply_text("Напишите число, например: 28")
        return ASK_AGE


async def got_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        w = float(update.message.text.strip().replace(",", "."))
        assert 30 <= w <= 300
        context.user_data["weight"] = w
        await update.message.reply_text("*Рост в см?*\n\nНапример: 178", parse_mode="Markdown")
        return ASK_HEIGHT
    except:
        await update.message.reply_text("Напишите вес, например: 84")
        return ASK_WEIGHT


async def got_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        h = float(update.message.text.strip().replace(",", "."))
        assert 100 <= h <= 250
        context.user_data["height"] = h
        await update.message.reply_text(
            "*Какой результат важнее всего?*", parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Убрать лишний жир", callback_data="gl_fat")],
                [InlineKeyboardButton("Набрать мышечную массу", callback_data="gl_muscle")],
                [InlineKeyboardButton("Улучшить форму и рельеф", callback_data="gl_tone")],
                [InlineKeyboardButton("Стать здоровее и энергичнее", callback_data="gl_health")],
            ]))
        return ASK_GOAL
    except:
        await update.message.reply_text("Напишите рост в см, например: 178")
        return ASK_HEIGHT


async def got_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    gmap = {"gl_fat": "fat", "gl_muscle": "muscle", "gl_tone": "tone", "gl_health": "tone"}
    goal = gmap.get(update.callback_query.data, "fat")
    context.user_data["goal"] = goal

    w = context.user_data["weight"]
    h = context.user_data["height"]
    arch_key = context.user_data.get("arch_key", "emotional_eater")
    arch = ARCHETYPES.get(arch_key, ARCHETYPES["emotional_eater"])

    await update.callback_query.message.reply_text("Считаю Ваш результат... ⏳")

    f = calc(w, h, goal)
    context.user_data["forecast"] = f

    await update.callback_query.message.reply_text(visual(f, arch["name"]), parse_mode="Markdown")
    await asyncio.sleep(30)  # пауза 30 секунд перед следующим сообщением
    await update.callback_query.message.reply_text(arch["tools"])
    await asyncio.sleep(1.5)

    uid = update.callback_query.from_user.id
    await update.callback_query.message.reply_text(
        "🎯 *Хотите достичь этого результата вместе с нами в группе?*\n\n"
        "Я запустил онлайн программу, в которой вы:\n"
        "— Похудеете и приведёте тело в форму 🔥\n"
        "— Получите ощутимый результат за 28 дней\n"
        "— Получите лёгкую систему на всю жизнь, а не на короткий период\n"
        "— Сделаете это даже без обязательного посещения спортзала\n"
        "— Будете при этом наслаждаться жизнью, не испытывать стресс и голод\n"
        "— Сможете вписать в программу даже «запрещёнку» — бургер, пиво, шаурму, сладкое, десерты — без чувства вины 🔥\n\n"
        "Набор в Реалити #ПП «Программа Преображения» открыт прямо сейчас.\n\n"
        "Старт: *21 мая*\n"
        "Длительность: *28 дней*\n\n"
        "*ФОРМАТ:*\n"
        "❌ ЭТО НЕ КУРС\n"
        "❌ Не краткосрочная программа\n"
        "❌ Не марафон\n"
        "❌ Не челлендж\n"
        "👉 Это участие в процессе — реалити практикум. Записанные видео + живое сопровождение Ивана и куратора\n\n"
        "*Вот что вы получите, чтобы добиться своей цели по преображению тела:*\n\n"
        "✅ Доступ к реалити «Программа Преображения» на 28 дней\n"
        "✅ Закрытый Telegram-канал реалити\n"
        "✅ Ежедневные короткие видео от Ивана Самохина: конкретика по системе питания и тренировок\n"
        "✅ Персональный план тренировок под Ваш тип тела и образ жизни\n"
        "✅ Систему питания и персональный план — без голодания и жёстких ограничений\n"
        "✅ Обратная связь от куратора ежедневно\n"
        "✅ Разбор прогресса участников еженедельно от Ивана Самохина\n"
        "✅ Поддержка от Ивана и других участников реалити\n\n"
        "*ПОЧЕМУ РЕАЛИТИ?*\n"
        "Тут будет реальная жизнь, а не идеальная картинка.\n\n"
        "В закрытом канале Иван каждый день показывает, как за 4 недели вернул форму — без диет, насилия и марафонов.\n\n"
        "Всё из реальной жизни: какие продукты покупает, как готовит, как считает КБЖУ, как тренируется, как справляется с усталостью.\n\n"
        "За 28 дней вы почувствуете контроль над телом, едой и энергией — без диет, запретов и жизни в спортзале.\n\n"
        "⏱ *Прямо сейчас для Вас действует специальная цена — только 1 час.*\n\n"
        "Хотите воспользоваться специальной ценой прямо сейчас?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Получить специальную цену →",
                url=f"{PAY_PROMO}&tg_id={uid}")],
        ]))

    # Логируем завершение анкеты
    try:
        from db import log_event as _log, user_update_profile as _profile
        _log(uid, "quiz_completed", f"goal={goal}")
        _profile(uid, goal=goal,
                 weight=context.user_data.get("weight"),
                 height=context.user_data.get("height"),
                 age=context.user_data.get("age"),
                 gender=context.user_data.get("gender"))
    except Exception as e:
        logger.error(f"analytics quiz error: {e}")

    # Логируем клик на кнопку оплаты
    try:
        from db import log_event as _log
        _log(uid, "pay_clicked", "promo_offer")
    except Exception as e:
        logger.error(f"analytics pay click error: {e}")

    context.user_data["in_quiz"] = False  # анкета завершена
    await schedule_dojim(uid, context)
    return ConversationHandler.END


async def cb_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Что Вам важнее всего узнать?", reply_markup=more_kb())


async def _launch_block(update, context, block_key, auto_job_name, greeting):
    """Запускает блок по кнопке с защитой от повтора (правка 4)."""
    await update.callback_query.answer()
    uid = update.callback_query.from_user.id
    jq = context.application.job_queue
    if jq:
        for job in jq.get_jobs_by_name(f"{auto_job_name}_{uid}"):
            job.schedule_removal()
            logger.info(f"Отменён автозапуск {auto_job_name}_{uid}")
    sent = context.user_data.setdefault("blocks_sent", set())
    if block_key in sent:
        await update.callback_query.message.reply_text(
            "Вы уже читали этот раздел. Записаться можно здесь:",
            reply_markup=pay_kb()
        )
        return
    sent.add(block_key)
    await update.callback_query.message.reply_text(greeting)
    if jq:
        if block_key == "b1":
            jq.run_once(lambda ctx: _dispatch_next_block(uid, "b1", ctx),
                        when=2, name=f"man_b1_{uid}")
        elif block_key == "b2":
            jq.run_once(lambda ctx: _dispatch_next_block(uid, "b2", ctx),
                        when=2, name=f"man_b2_{uid}")
        elif block_key == "b3":
            jq.run_once(lambda ctx: _dispatch_next_block(uid, "b3", ctx),
                        when=2, name=f"man_b3_{uid}")


async def cb_start_b1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _launch_block(update, context, "b1", "b1", "Сейчас пришлю историю Ивана 👇")

async def cb_start_b2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _launch_block(update, context, "b2", "b2", "Сейчас расскажу, что вас ждёт внутри 👇")

async def cb_start_b3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _launch_block(update, context, "b3", "b3", "Сейчас расскажу честно — кому подойдёт 👇")

async def cb_i_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cb_start_b1(update, context)

async def cb_i_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cb_start_b2(update, context)

async def cb_i_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cb_start_b3(update, context)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arch_key = context.user_data.get("arch_key")
    f = context.user_data.get("forecast")
    arch = ARCHETYPES.get(arch_key)
    txt = "📋 *Реалити #ПП «Программа Преображения»*\n\n"
    if arch and f:
        txt += f"Ваш тип: *{arch['emoji']} {arch['name']}*\nПрогноз: {f['wr']} за 28 дней\n\n"
    await update.message.reply_text(txt, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Мой результат", callback_data="my_res")],
            [InlineKeyboardButton("📖 История Ивана Самохина", callback_data="start_b1")],
            [InlineKeyboardButton("💪 Что вы получите в реалити?", callback_data="start_b2")],
            [InlineKeyboardButton("✅ Кому подходит, а кому нет?", callback_data="start_b3")],
            [InlineKeyboardButton("💳 Записаться", url=PAYMENT_URL)],
        ]))


async def cb_my_res(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    arch_key = context.user_data.get("arch_key")
    f = context.user_data.get("forecast")
    arch = ARCHETYPES.get(arch_key)
    if arch and f:
        await update.callback_query.message.reply_text(visual(f, arch["name"]), parse_mode="Markdown")
        await update.callback_query.message.reply_text(
            f"*Ваш тип:* {arch['emoji']} {arch['name']}\n*Прогноз:* {f['wr']} ({f['ch']}) за 28 дней",
            parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text("Пройдите тест:\n👉 https://pp-reality.ru")


async def _exec_block1(uid, bot, jq):
    P = PHOTOS_URL
    async def s(text, **kw): await bot.send_message(chat_id=uid, text=text, **kw)
    async def ph(url): await send_photo_url(bot, uid, url)
    async def mg(urls): await send_media_group_urls(bot, uid, urls)

    await s("*Кто такой Иван Самохин?*\n"
            "Создатель Реалити #ПП «Программа Преображения» 👇\n\n"
            "Вы знаете его как создателя и ведущего подкаста «Состояние» "
            "со 155 000 подписчиков на YouTube и 65+ миллионами просмотров.\n\n"
            "Но сейчас Вы узнаете про его путь в преображении тела на протяжении 24 лет. "
            "Иван расскажет свою историю 👇", parse_mode="Markdown")
    await asyncio.sleep(20)
    await s("*НАЧАЛО*\n\n"
            "В детстве я был слабым ребёнком — постоянно болел, плохой иммунитет. "
            "Таких сейчас называют астеник. Можно уверенно сказать, что я был дрыщом в 14 лет.\n\n"
            "*«У тебя просто генетика» — самый вредный миф*\n\n"
            "Когда люди видят мой результат сегодня, говорят: «Ну у тебя гены». "
            "Я начал качаться под впечатлением от Сталлоне и Шварценеггера, как и многие из вас.\n\n"
            "Важна не генетика, а привычки. За последние три месяца я не пропустил ни одной "
            "из трёх тренировок в неделю. Не потому что сверхчеловек — а потому что это "
            "стало автоматикой, как чистить зубы.", parse_mode="Markdown")
    await asyncio.sleep(20)
    await ph(f"{P}/ivan_years.jpeg")
    await asyncio.sleep(20)
    await s("*Почему я не тренер (и почему это вам выгодно)*\n\n"
            "За 24 года я перепробовал сотни тренеров в разных странах.\n\n"
            "Большинство из них:\n"
            "→ Рано или поздно предлагают анаболики (им нужен быстрый кейс, а не ваше здоровье)\n"
            "→ Живут в зале по 12 часов, питаются из контейнеров\n"
            "→ Видят только вес и процент жира, забывая про ментальное состояние\n\n"
            "Я не тренер и не врач. Я практик с 24-летним стажем, который провёл 60+ интервью "
            "с учёными, генетиками и эндокринологами.", parse_mode="Markdown")
    await asyncio.sleep(20)
    await mg([f"{P}/book_sostoyanie.jpeg", f"{P}/book_sostoyanie2.jpeg", f"{P}/youtube_channel.jpeg"])
    await asyncio.sleep(20)
    await s("*Почему ваши тренировки не работают (и что делать вместо этого)*\n\n"
            "Вы знаете это чувство: купили абонемент, пошли три недели, потом работа, "
            "командировка, «всё потом нагоню». Или сели на марафон — отказались от всего, "
            "а через месяц вернулись с лишними килограммами и чувством вины.\n\n"
            "Я проходил это. Ломал ногу, пропадал на месяцы. И каждый раз возвращался "
            "к форме не благодаря «железной воле», а благодаря системе.", parse_mode="Markdown")
    await asyncio.sleep(20)
    await s("*Система против марафонов*\n\n"
            "Марафон вырывает вас из жизни: резкие запреты, режим, отказ от семьи и работы. "
            "Потом — обязательный откат.", parse_mode="Markdown")
    await asyncio.sleep(20)
    await s("*Мой подход другой.*\n\n"
            "Я работаю каждый день, ем в ресторанах, бывает и фастфуд, перелёты, дедлайны. "
            "И при этом уже 24 года держу форму.\n\n"
            "Секрет не в отказах, а в пропорциях. Как в хорошем супе — важно соотношение "
            "ингредиентов, а не голодовка.", parse_mode="Markdown")
    await asyncio.sleep(20)
    await s("*Реальные цифры (снято на камеру)*\n\n"
            "Перед запуском я прошёл программу сам. С нуля, зафиксировав всё:\n\n"
            "За 28 дней:\n"
            "→ −4,3 кг общего веса\n"
            "→ −2,2 кг жировой массы\n"
            "→ −1,8% телесного жира\n\n"
            "При этом я не сидел на воде и огурцах. Ходил в рестораны, работал, жил нормально.",
            parse_mode="Markdown")
    await asyncio.sleep(20)
    await ph(f"{P}/ivan_before_after.jpeg")
    await asyncio.sleep(20)
    await bot.send_message(chat_id=uid,
        text="*Что вы получите*\n\n"
             "Это не очередной «стань качком за месяц». Это система привычек, которая:\n\n"
             "→ Работает в условиях перегрузов и командировок\n"
             "→ Не требует жить в зале и носить еду в контейнерах\n"
             "→ Учитывает ваше ментальное и физическое здоровье как единое целое\n"
             "→ Остаётся с вами навсегда, а не на 28 дней\n\n"
             "*Старт программы: 21 мая.*\n\n"
             "Места ограничены. Если вы устали от тренеров-зомби и марафонов — "
             "*пришло время для системы, которая работает в реальной жизни.\n"
             "Если Вы чувствуете, что это то, что Вам нужно — не откладывайте.*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться в Реалити →", url=f"{PAY_URL}?tg_id={uid}")]]))
    # Планируем следующий непросмотренный блок
    await schedule_next_unseen(uid, "b2", jq)
    # Планируем следующий непросмотренный блок
    await schedule_next_unseen(uid, "b1", jq)


async def _exec_block2(uid, bot, jq):
    await bot.send_message(chat_id=uid,
        text="☄️ Почему Вы не худеете — и это точно не лень\n\n"
             "Иван записал урок, который отвечает на главный вопрос: "
             "почему Вы уже 100 раз начинали, срывались, а вес возвращался.")
    await asyncio.sleep(20)
    await bot.send_message(chat_id=uid,
        text="Что внутри:\n\n"
             "• Почему дело часто не в «силе воли»\n"
             "• Как худеть без голода и без «есть на 1200»\n"
             "• Примеры питания на 1500 / 2000 / 2500 / 3000 ккал\n"
             "• Как вписывать «запрещёнку» — бургер, пиво, шаурму — без чувства вины\n\n"
             "После просмотра Вы:\n\n"
             "• Поймёте, почему раньше не получалось\n"
             "• Увидите, какие шаги реально дают результат\n"
             "• Перестанете ломать себя и начнёте действовать по системе")
    await asyncio.sleep(20)
    await bot.send_message(chat_id=uid,
        text="Смотрите урок по ссылке:\n"
             "👉 https://kinescope.io/hubcbT4t5vnaLVYPC6UjAK\n\n"
             "─────────────────\n\n"
             "А всё, о чём говорится в уроке — это основа Реалити #ПП. "
             "28 дней, каждый день, с Вашим типом и Вашей целью.\n\n"
             "Старт *21 мая*. Если урок откликнулся — самое время сделать следующий шаг.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]]))


async def _exec_block3(uid, bot, jq):
    # Сообщение 1 — вступление + кому НЕ + кому ДА
    await bot.send_message(chat_id=uid,
        text="Хотим быть с Вами честными.\n\n"
             "Реалити #ПП подходит не всем — и это важно понять до принятия решения. "
             "Прочитайте внимательно: это сэкономит Вам время и деньги, "
             "если программа действительно не для Вас.\n\n"
             "🚫 Реалити не для Вас, если:\n\n"
             "❌ Вы ищете жёсткую диету с полным списком запретов — "
             "здесь нет запрещённых продуктов, только понимание пропорций\n\n"
             "❌ Вы хотите «минус 10 кг за неделю» — "
             "таких результатов не бывает без вреда для здоровья\n\n"
             "❌ Вы ждёте волшебную таблетку — "
             "здесь нужно участвовать, смотреть, применять\n\n"
             "✅ Реалити создано для Вас, если:\n\n"
             "✔ Нет времени на сложные многочасовые программы\n"
             "✔ Устали и в стрессе — хотите выстроить режим, не ломая себя\n"
             "✔ Проходили через срывы и качели веса и хотите выбраться из круга\n"
             "✔ Хотите форму без фанатизма — без лотков с едой\n"
             "✔ Хотите результат, который вписывается в обычную жизнь")
    await asyncio.sleep(20)

    # Сообщение 2 — что почувствуете + путь Ивана + фото + CTA
    await bot.send_message(chat_id=uid,
        text="Что Вы почувствуете через 28 дней:\n\n"
             "✔ Снижение веса и объёмов — без голода и срывов\n"
             "✔ Больше энергии — уже к концу первой недели\n"
             "✔ Меньше тяги к вредной еде\n"
             "✔ Уверенность в своём теле\n"
             "✔ Ощущение контроля — над едой, активностью, своим днём\n"
             "✔ Привычки, которые остаются с Вами навсегда\n\n"
             "Я уже прошёл этот путь.\n\n"
             "Эти 28 дней — не теория и не план. "
             "Это реальный процесс, который я прошёл сам и записал день за днём. "
             "Специально для того, чтобы Вам было легче пройти его сейчас.")
    await asyncio.sleep(20)
    await send_photo_url(bot, uid, f"{PHOTOS_URL}/ivan_before_after.jpeg")
    await asyncio.sleep(20)
    await bot.send_message(chat_id=uid,
        text="За 28 дней:\n"
             "→ −4,3 кг веса\n"
             "→ −2,2 кг жировой массы\n"
             "→ −1,8% телесного жира\n\n"
             "Без анаболиков. Без жёстких ограничений. В условиях обычной жизни.\n\n"
             "─────────────────\n\n"
             "Если Вы узнали себя в списке тех, кому это подойдёт — "
             "не нужно больше думать и откладывать. "
             "Каждый день ожидания — это ещё один день в том же круге.\n\n"
             "*Старт 21 мая. Места ограничены.*\n\n"
             "Сделайте шаг прямо сейчас — пока есть возможность.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Записаться в Реалити →", url=f"{PAY_URL}?tg_id={uid}")]]))
    # Планируем следующий непросмотренный блок
    await schedule_next_unseen(uid, "b3", jq)


async def cmd_ivan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ivan — история Ивана Самохина."""
    uid = update.effective_user.id
    sent = context.user_data.setdefault("blocks_sent", set())
    if "b1" in sent:
        await update.message.reply_text(
            "Вы уже читали этот раздел. Записаться можно здесь:",
            reply_markup=pay_kb()
        )
        return
    sent.add("b1")
    await update.message.reply_text("Сейчас пришлю историю Ивана 👇")
    jq = context.application.job_queue
    if jq:
        jq.run_once(lambda ctx: _exec_block1(uid, ctx.bot, ctx.application.job_queue),
                    when=2, name=f"cmd_b1_{uid}")


async def cmd_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /product — что вы получите в реалити."""
    uid = update.effective_user.id
    sent = context.user_data.setdefault("blocks_sent", set())
    if "b2" in sent:
        await update.message.reply_text(
            "Вы уже читали этот раздел. Записаться можно здесь:",
            reply_markup=pay_kb()
        )
        return
    sent.add("b2")
    await update.message.reply_text("Сейчас расскажу, что вас ждёт внутри 👇")
    jq = context.application.job_queue
    if jq:
        jq.run_once(lambda ctx: _exec_block2(uid, ctx.bot, ctx.application.job_queue),
                    when=2, name=f"cmd_b2_{uid}")


async def cmd_fitsfor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /fitsfor — кому подходит реалити."""
    uid = update.effective_user.id
    sent = context.user_data.setdefault("blocks_sent", set())
    if "b3" in sent:
        await update.message.reply_text(
            "Вы уже читали этот раздел. Записаться можно здесь:",
            reply_markup=pay_kb()
        )
        return
    sent.add("b3")
    await update.message.reply_text("Сейчас расскажу честно — кому подойдёт 👇")
    jq = context.application.job_queue
    if jq:
        jq.run_once(lambda ctx: _exec_block3(uid, ctx.bot, ctx.application.job_queue),
                    when=2, name=f"cmd_b3_{uid}")


async def cmd_myresult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /myresult — показывает результат теста."""
    arch_key = context.user_data.get("arch_key")
    f = context.user_data.get("forecast")
    arch = ARCHETYPES.get(arch_key)
    if arch and f:
        await update.message.reply_text(visual(f, arch["name"]), parse_mode="Markdown")
        await asyncio.sleep(1)
        await update.message.reply_text(
            f"*Ваш тип:* {arch['emoji']} {arch['name']}\n"
            f"*Прогноз:* {f['wr']} ({f['ch']}) за 28 дней",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )
    else:
        await update.message.reply_text(
            "Результат пока не найден. Пройдите тест, чтобы получить персональный разбор:\n\n"
            "👉 " + QUIZ_URL
        )



async def schedule_next_unseen(uid, current_block, context_or_jq):
    """После завершения блока запускает следующий непросмотренный через заданное время."""
    # Получаем job_queue
    if hasattr(context_or_jq, 'application'):
        jq = context_or_jq.application.job_queue
        user_data = context_or_jq.user_data if hasattr(context_or_jq, 'user_data') else {}
    else:
        jq = context_or_jq
        user_data = {}

    if not jq:
        return

    # Порядок блоков
    order = ["b1", "b2", "b3", "final"]
    delay = 86400  # 1 сутки между блоками

    # Определяем какие блоки уже отправлены
    # Берём из хранилища приложения по uid
    app = jq.application if hasattr(jq, 'application') else None
    if app and hasattr(app, 'user_data'):
        sent = app.user_data.get(uid, {}).get("blocks_sent", set())
    else:
        sent = set()

    # Помечаем текущий как отправленный
    sent.add(current_block)
    if app and hasattr(app, 'user_data'):
        if uid not in app.user_data:
            app.user_data[uid] = {}
        app.user_data[uid]["blocks_sent"] = sent

    # Ищем следующий непросмотренный
    current_idx = order.index(current_block) if current_block in order else -1
    for i in range(current_idx + 1, len(order)):
        next_block = order[i]
        if next_block not in sent:
            logger.info(f"Планируем следующий блок {next_block} для uid={uid} через {delay}с")

            async def _run_next(ctx, _block=next_block):
                await _dispatch_next_block(uid, _block, ctx)

            jq.run_once(_run_next, when=delay, name=f"auto_{next_block}_{uid}")
            break


async def _dispatch_next_block(uid, block_key, ctx):
    """Запускает нужный блок и помечает как просмотренный."""
    if is_paid(uid):
        logger.info(f"uid={uid} уже оплатил — {block_key} пропущен")
        return
    bot = ctx.bot
    jq = ctx.application.job_queue

    # Помечаем как отправленный
    if hasattr(ctx.application, 'user_data'):
        if uid not in ctx.application.user_data:
            ctx.application.user_data[uid] = {}
        ctx.application.user_data[uid].setdefault("blocks_sent", set()).add(block_key)

    if block_key == "b1":
        await _exec_block1(uid, bot, jq)
        await schedule_next_unseen(uid, "b1", ctx)
    elif block_key == "b2":
        await _exec_block2(uid, bot, jq)
        await schedule_next_unseen(uid, "b2", ctx)
    elif block_key == "b3":
        await _exec_block3(uid, bot, jq)
        await schedule_next_unseen(uid, "b3", ctx)
    elif block_key == "final":
        await _exec_final(uid, bot, jq)


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /export — выгрузка БД в Excel (только для админа)"""
    uid = update.effective_user.id
    admin_id = int(os.getenv("ADMIN_TG_ID", "0"))

    if uid != admin_id:
        await update.message.reply_text("⛔ Нет доступа.")
        return

    try:
        from export import export_to_excel
        import io
        data = export_to_excel()
        fname = f"payments_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        await update.message.reply_document(
            document=io.BytesIO(data),
            filename=fname,
            caption=f"📊 Выгрузка платежей — {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")



def is_paid(tg_id: int) -> bool:
    """Проверяет оплатил ли пользователь через PostgreSQL."""
    try:
        from db import is_paid as _is_paid
        return _is_paid(tg_id)
    except Exception:
        return False



async def forward_to_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение пользователя в группу поддержки."""
    if not SUPPORT_GROUP_ID:
        return
    msg = update.message
    if not msg:
        return
    uid = msg.from_user.id
    # Не пересылаем сообщения из самой группы поддержки
    if msg.chat.id == SUPPORT_GROUP_ID:
        return
    # Не пересылаем команды
    if msg.text and msg.text.startswith('/'):
        return

    # Не пересылаем если пользователь проходит анкету
    if context.user_data.get("in_quiz"):
        return

    name = msg.from_user.full_name or ""
    username = f"@{msg.from_user.username}" if msg.from_user.username else "без username"

    # Простой текст без parse_mode — спецсимволы в именах не вызывают ошибок
    header = f"👤 {name} | {username} | ID: {uid}"

    try:
        # Отправляем заголовок
        header_msg = await context.bot.send_message(
            chat_id=SUPPORT_GROUP_ID,
            text=header,
        )
        # Пересылаем само сообщение
        fwd_msg = await msg.forward(chat_id=SUPPORT_GROUP_ID)
        # Сохраняем связь: оба message_id → tg_id пользователя
        support_map = context.bot_data.setdefault("support_map", {})
        support_map[header_msg.message_id] = uid
        support_map[fwd_msg.message_id] = uid
        logger.info(f"Переслано в поддержку от uid={uid}, msg_ids={header_msg.message_id},{fwd_msg.message_id}")
    except Exception as e:
        logger.error(f"Ошибка пересылки в поддержку: {e}")


async def reply_from_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет ответ из группы поддержки пользователю."""
    msg = update.message
    if not msg or not msg.reply_to_message:
        return
    if msg.chat.id != SUPPORT_GROUP_ID:
        return

    # Ищем tg_id пользователя по reply
    support_map = context.bot_data.get("support_map", {})
    replied_id = msg.reply_to_message.message_id
    tg_id = support_map.get(replied_id)

    if not tg_id:
        # Пробуем соседние message_id (пересланное сообщение идёт после заголовка)
        for offset in [-1, 0, 1, -2, 2]:
            tg_id = support_map.get(replied_id + offset)
            if tg_id:
                break

    if not tg_id:
        await msg.reply_text("⚠️ Не удалось найти пользователя. Убедитесь что отвечаете реплаем на пересланное сообщение.")
        return

    try:
        if msg.text:
            await context.bot.send_message(
                chat_id=tg_id,
                text="Ответ от команды:\n\n" + msg.text,
                parse_mode="Markdown"
            )
        elif msg.photo:
            await context.bot.send_photo(
                chat_id=tg_id,
                photo=msg.photo[-1].file_id,
                caption=msg.caption or ""
            )
        elif msg.voice:
            await context.bot.send_voice(chat_id=tg_id, voice=msg.voice.file_id)
        elif msg.document:
            await context.bot.send_document(chat_id=tg_id, document=msg.document.file_id)

        await msg.reply_text(f"✅ Ответ отправлен пользователю ID: {tg_id}")
        logger.info(f"Ответ отправлен пользователю {tg_id}")
    except Exception as e:
        await msg.reply_text(f"⚠️ Ошибка отправки: {e}")
        logger.error(f"Ошибка ответа пользователю {tg_id}: {e}")








async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats — сводная статистика (только для админа)."""
    uid = update.effective_user.id
    admin_id = int(os.getenv("ADMIN_TG_ID", "0"))
    if uid != admin_id:
        await update.message.reply_text("⛔ Нет доступа.")
        return

    try:
        from db import get_stats as _get_stats
        s = _get_stats()
        if not s:
            await update.message.reply_text("Ошибка получения статистики.")
            return

        # Конверсия
        conv = round(s["paid_total"] / s["total_users"] * 100, 1) if s["total_users"] else 0

        # Топ архетипы
        arch_names = {
            "emotional_eater": "Эмоц. едок",
            "social_hostage": "Соц. заложник",
            "metabolic_skeptic": "Метаб. скептик",
            "starter_stopper": "Стартер-стопер",
        }
        arch_lines = ""
        for arch, cnt in s.get("archetypes", []):
            arch_lines += f"  {arch_names.get(arch, arch)}: {cnt}\n"

        # Топ события
        event_lines = ""
        for event, cnt in s.get("events", [])[:8]:
            event_lines += f"  {event}: {cnt}\n"

        text = (
            f"📈 *Статистика бота*\n\n"
            f"👥 Всего пользователей: *{s['total_users']}*\n"
            f"🆕 Новых сегодня: *{s['new_today']}*\n"
            f"📅 Новых за неделю: *{s['new_week']}*\n\n"
            f"💰 Оплатили: *{s['paid_total']}*\n"
            f"💵 Выручка: *{s['revenue']:,} ₽*\n"
            f"📊 Конверсия: *{conv}%*\n\n"
            f"⏳ В воронке сейчас: *{s['in_funnel']}*\n\n"
            f"🎭 *Архетипы:*\n{arch_lines}\n"
            f"🔢 *События:*\n{event_lines}"
        )
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /broadcast <текст> — рассылка всем пользователям (только для админа)."""
    uid = update.effective_user.id
    admin_id = int(os.getenv("ADMIN_TG_ID", "0"))
    if uid != admin_id:
        await update.message.reply_text("⛔ Нет доступа.")
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Использование: /broadcast Текст сообщения\n\n"
            "Поддерживается Markdown разметка."
        )
        return

    try:
        from db import get_broadcast_users as _get_users, log_event as _log
        users = _get_users()
        if not users:
            await update.message.reply_text("Нет пользователей для рассылки.")
            return

        await update.message.reply_text(
            f"📢 Начинаю рассылку для *{len(users)}* пользователей...",
            parse_mode="Markdown"
        )

        sent = 0
        failed = 0
        for tg_id in users:
            try:
                await context.bot.send_message(
                    chat_id=tg_id,
                    text=text,
                    parse_mode="Markdown"
                )
                sent += 1
                await asyncio.sleep(0.05)  # защита от flood limit
            except Exception:
                failed += 1

        # Логируем рассылку
        _log(uid, "broadcast_sent", f"sent={sent} failed={failed}")

        await update.message.reply_text(
            f"✅ Рассылка завершена!\n\n"
            f"Отправлено: *{sent}*\n"
            f"Ошибок: *{failed}*",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


async def restore_funnels(application):
    """Восстанавливает запланированные задачи после деплоя из БД."""
    from datetime import timedelta
    try:
        from db import funnel_get_active as _get_active
        rows = _get_active()
        if not rows:
            logger.info("Нет активных воронок для восстановления")
            return

        now = datetime.now()
        jq = application.job_queue
        restored = 0

        for row in rows:
            tg_id, blocks_sent_str, d1h_at, b1_at, b2_at, b3_at, final_at = row
            sent = set(blocks_sent_str.split(',')) if blocks_sent_str else set()

            # Для каждого незапланированного блока — проверяем время
            schedule_map = {
                "d1h":   d1h_at,
                "b1":    b1_at,
                "b2":    b2_at,
                "b3":    b3_at,
                "final": final_at,
            }

            for block_key, send_at in schedule_map.items():
                if send_at is None:
                    continue
                if block_key in sent:
                    continue  # уже отправлен

                # Считаем задержку — только будущие задачи
                delay = (send_at - now).total_seconds()
                if delay < 0:
                    # Время уже прошло — задача либо выполнена, либо потеряна при деплое
                    # В обоих случаях пропускаем — blocks_sent должен был быть обновлён
                    logger.info(f"Блок {block_key} для uid={tg_id} в прошлом, пропускаем")
                    continue

                # Планируем задачу
                _uid = tg_id
                _key = block_key

                async def _run(ctx, uid=_uid, key=_key):
                    await _dispatch_block_by_key(uid, key, ctx)

                job_name = f"restore_{block_key}_{tg_id}"
                # Не дублируем если уже запланировано
                existing = jq.get_jobs_by_name(job_name)
                if not existing:
                    jq.run_once(_run, when=delay, name=job_name)
                    restored += 1
                    logger.info(f"Восстановлен блок {block_key} для uid={tg_id} через {int(delay)}с")

        logger.info(f"Восстановлено задач: {restored} для {len(rows)} пользователей ✅")

    except Exception as e:
        logger.error(f"restore_funnels error: {e}")


async def _dispatch_block_by_key(uid: int, block_key: str, ctx):
    """Универсальный запуск блока по ключу (для восстановления)."""
    if is_paid(uid):
        logger.info(f"uid={uid} уже оплатил — {block_key} пропущен при восстановлении")
        return

    bot = ctx.bot
    jq = ctx.application.job_queue

    try:
        from db import funnel_mark_block as _mark
        # Логируем просмотр блока
        try:
            from db import log_event as _log
            _log(uid, f"block_viewed", block_key)
        except Exception as e:
            logger.error(f"analytics block log error: {e}")

        if block_key == "d1h":
            await ctx.bot.send_message(
                uid,
                "Прежде чем примите решение, хочу рассказать Вам больше о том, что стоит за Реалити #ПП.\n\n"
                "Выберите, с чего начать 👇",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 История Ивана Самохина", callback_data="start_b1")],
                    [InlineKeyboardButton("💪 Что вы получите в реалити?", callback_data="start_b2")],
                    [InlineKeyboardButton("✅ Кому подходит реалити, а кому нет?", callback_data="start_b3")],
                    [InlineKeyboardButton("Записаться →", url=f"{PAY_URL}?tg_id={uid}")],
                ])
            )
            _mark(uid, "d1h")
            logger.info(f"d1h выполнен и помечен для uid={uid}")
        elif block_key == "b1":
            await _exec_block1(uid, bot, jq)
            _mark(uid, "b1", "b2", datetime.now() + __import__('datetime').timedelta(seconds=86400))
        elif block_key == "b2":
            await _exec_block2(uid, bot, jq)
            _mark(uid, "b2", "b3", datetime.now() + __import__('datetime').timedelta(seconds=86400))
        elif block_key == "b3":
            await _exec_block3(uid, bot, jq)
            _mark(uid, "b3", "final", datetime.now() + __import__('datetime').timedelta(seconds=86400))
        elif block_key == "final":
            if not is_paid(uid):
                await ctx.bot.send_message(
                    uid,
                    "*Реалити уже скоро!*",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Выбрать тариф →", url=PAY_URL)]])
                )
            _mark(uid, "final")
    except Exception as e:
        logger.error(f"_dispatch_block_by_key error uid={uid} block={block_key}: {e}")


def main():
    if not TOKEN:
        logger.error("BOT_TOKEN не установлен!")
        return

    from telegram import BotCommand

    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("myresult",  "📊 Мой результат теста"),
            BotCommand("ivan",      "📖 История Ивана Самохина"),
            BotCommand("product",   "💪 Что вы получите в реалити"),
            BotCommand("fitsfor",   "✅ Кому подходит реалити"),
            BotCommand("menu",      "📋 Главное меню"),
            BotCommand("export",    "📥 Выгрузить базу данных"),
            BotCommand("stats",     "📈 Статистика (админ)"),
            BotCommand("broadcast", "📢 Рассылка (админ)"),
        ])
        logger.info("Команды меню установлены ✅")

        # Запускаем payment server в том же event loop
        try:
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from aiohttp import web as _web
            from payments import create_app as _create_app
            from db import init_db as _init_db
            _init_db()
            _payment_app = _create_app()
            _port = int(os.getenv("PORT", "8080"))
            runner = _web.AppRunner(_payment_app)
            await runner.setup()
            site = _web.TCPSite(runner, "0.0.0.0", _port)
            await site.start()
            logger.info(f"Payment server запущен на порту {_port} ✅")
        except Exception as e:
            logger.error(f"Payment server ошибка: {e}")

        # Восстанавливаем воронки после деплоя
        await restore_funnels(application)

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            ASK_GENDER: [
                CallbackQueryHandler(cb_go, pattern="^go$"),
                CallbackQueryHandler(cb_later, pattern="^later$"),
                CallbackQueryHandler(cb_gender, pattern="^g[mf]$"),
            ],
            ASK_AGE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_age)],
            ASK_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_weight)],
            ASK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_height)],
            ASK_GOAL:   [CallbackQueryHandler(got_goal, pattern="^gl_")],
        },
        fallbacks=[CommandHandler("menu", cmd_menu)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("menu",      cmd_menu))
    app.add_handler(CommandHandler("ivan",      cmd_ivan))
    app.add_handler(CommandHandler("product",   cmd_product))
    app.add_handler(CommandHandler("fitsfor",   cmd_fitsfor))
    app.add_handler(CommandHandler("myresult",  cmd_myresult))
    app.add_handler(CommandHandler("export",    cmd_export))
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CallbackQueryHandler(cb_more,      pattern="^more_info$"))
    app.add_handler(CallbackQueryHandler(cb_start_b1,  pattern="^start_b1$"))
    app.add_handler(CallbackQueryHandler(cb_start_b2,  pattern="^start_b2$"))
    app.add_handler(CallbackQueryHandler(cb_start_b3,  pattern="^start_b3$"))
    app.add_handler(CallbackQueryHandler(cb_i_about,   pattern="^i_about$"))
    app.add_handler(CallbackQueryHandler(cb_i_program, pattern="^i_program$"))
    app.add_handler(CallbackQueryHandler(cb_i_results, pattern="^i_results$"))
    app.add_handler(CallbackQueryHandler(cb_my_res,    pattern="^my_res$"))
    # Поддержка — пересылка сообщений
    # group=1 означает что ConversationHandler (group=0) обрабатывается первым
    # и если он взял сообщение — forward_to_support не вызывается
    app.add_handler(MessageHandler(filters.Chat(SUPPORT_GROUP_ID) & filters.REPLY, reply_from_support))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Chat(SUPPORT_GROUP_ID), forward_to_support), group=1)

    logger.info("Программа Преображения bot started ✅")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
