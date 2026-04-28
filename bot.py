import os
import logging
import asyncio
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
QUIZ_URL  = "https://vezuncheg.github.io/fitstate"
PAY_URL   = "https://vezuncheg.github.io/fitstate/pay.html"
PAY_PROMO = "https://vezuncheg.github.io/fitstate/pay.html?promo=1"
PAYMENT_URL = PAY_URL
PHOTOS_URL = "https://raw.githubusercontent.com/Vezuncheg/fitstate/main/images"

ASK_GENDER, ASK_AGE, ASK_WEIGHT, ASK_HEIGHT, ASK_GOAL = range(5)

ARCHETYPES = {
    "emotional_eater": {
        "emoji": "😰", "name": "Эмоциональный едок",
        "problem": "Вы не срываетесь потому что слабый.\nВы срываетесь, потому что мозг выучил паттерн:\nстресс → еда → легче.\n\nЭто не вопрос силы воли — это вопрос замены инструмента.\nБез работы с этим — любая диета временная.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Стресс активирует тягу к еде\n→ Ты ешь — становится легче\n→ Потом вина → ещё стресс → снова ешь\n→ Круг замкнулся",
        "solution": "✅ Что реально помогает:\n\n→ Замечать триггер до того, как рука потянулась\n→ Заменить еду другим инструментом снятия стресса\n→ Убрать провоцирующие ситуации заранее\n\nЭто навык. Ему можно научиться за 3–4 недели.",
        "tools": "🛠 Что добавим в Вашем случае:\n\n1️⃣ Техники прерывания эмоционального триггера — заметите импульс до того, как потянулись к еде\n2️⃣ Быстрые замены — 3–4 инструмента снятия стресса без еды\n3️⃣ Структуру питания — уберём ситуации, где срыв наиболее вероятен",
        "day3": "📌 Топ-3 ошибки эмоционального едока:\n\n1. Держать дома запасы любимой еды\n2. Пропускать приёмы пищи — голод усиливает триггер\n3. Бороться силой воли — нужно переключать, не бороться",
        "proof": "Анна, 34 года — минус 11 кг за 8 недель.\nПерестала есть от стресса уже на 2-й неделе.\n\nМихаил, 31 год — минус 9 кг. Впервые не сорвался ни разу.",
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
        "proof": "Ирина, 38 лет — 2 года не могла сдвинуться с места.\nЗа 8 недель минус 7 кг. Оказалось — ела слишком мало.\n\nСергей, 33 года — тренировался 4 раза в неделю. Поменяли питание — минус 9 кг.",
    },
    "starter_stopper": {
        "emoji": "🔁", "name": "Стартер-стопер",
        "problem": "В начале мотивация огромная.\nНо через 10–14 дней она испаряется — и всё заново.\n\nПроблема не в Вас.\nПроблема в том, что Вы работаете на силе воли. А она конечна у всех.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Мощный старт — мотивация на максимуме\n→ Через 1–2 недели энтузиазм падает\n→ Один пропуск → ощущение провала → бросаешь\n→ Через время — снова с понедельника",
        "solution": "✅ Что реально помогает:\n\n→ Заменить мотивацию системой — она не исчезает\n→ Внешние точки контроля: куратор, группа\n→ Маленькие wins вместо большой далёкой цели\n\nКогда есть система и окружение — мотивация не нужна.",
        "tools": "🛠 Что добавим в Вашем случае:\n\n1️⃣ Систему вместо силы воли — ежедневную структуру, которой легко следовать\n2️⃣ Внешнюю поддержку — куратор и группа, которые не дают выпасть\n3️⃣ Протокол срыва — чёткий алгоритм что делать, если пропустили, чтобы не бросить совсем",
        "day3": "📌 Почему стартер-стопер останавливается на 2-й неделе:\n\n1. Мотивация эмоциональная — она быстро гаснет\n2. Нет системы на сложный день — один пропуск = провал\n3. Цель далеко — мозг не видит прогресса",
        "proof": "Олег, 27 лет — начинал 6 раз за 2 года.\nВ потоке FitState впервые прошёл все 8 недель. Минус 8 кг.\n\nНастя, 31 год — группа и куратор сделали то, что сила воли не смогла за 3 года.",
    },
}


def calc(weight, height, goal):
    bmi = round(weight / ((height / 100) ** 2), 1)
    if goal == "fat":
        lo, hi = (8, 12) if bmi > 30 else (6, 9) if bmi > 25 else (4, 7)
        wlo, whi = round(weight - hi), round(weight - lo)
        bmi2 = round((wlo + whi) / 2 / ((height / 100) ** 2), 1)
        return dict(cw=weight, cb=bmi, wr=f"{wlo}–{whi} кг",
                    ch=f"−{lo}–{hi} кг жира",
                    muscle="+1–2 кг мышц при правильном балансе БЖУ",
                    b2=bmi2,
                    waist=f"минус {lo+1}–{hi-1} см в талии",
                    en="заметно вырастет к 3-й неделе")
    elif goal == "muscle":
        return dict(cw=weight, cb=bmi,
                    wr=f"{round(weight+3)}–{round(weight+6)} кг",
                    ch="+3–6 кг мышечной массы",
                    muscle="жировая прослойка снизится на 1–2%",
                    b2=round(bmi+0.8, 1),
                    waist="больше мышц, рельеф",
                    en="вырастет к 2-й неделе")
    else:
        wlo, whi = round(weight - 5), round(weight - 3)
        bmi2 = round((wlo + whi) / 2 / ((height / 100) ** 2), 1)
        return dict(cw=weight, cb=bmi, wr=f"{wlo}–{whi} кг",
                    ch="−3–5 кг + рельеф и тонус",
                    muscle="+1–3 кг мышечного тонуса",
                    b2=bmi2,
                    waist="минус 3–5 см, заметный рельеф",
                    en="вырастет уже к концу 1-й недели")


def visual(f, name):
    return (
        f"🖼 *ТЫ СЕЙЧАС*\n"
        f"Вес: {f['cw']} кг  |  ИМТ: {f['cb']}\n"
        f"_{name}_\n\n"
        f"⬇️ 8 недель Реалити #ПП «Программа Преображения» ⬇️\n\n"
        f"🖼 *ТЫ ЧЕРЕЗ 2 МЕСЯЦА*\n"
        f"Вес: {f['wr']}  |  ИМТ: {f['b2']}\n"
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
        await ctx.bot.send_message(
            uid,
            "Прежде чем примите решение, хочу рассказать Вам больше о том, что стоит за Реалити #ПП.\n\n"
            "Выберите, с чего начать 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 История Ивана Самохина", callback_data="start_b1")],
                [InlineKeyboardButton("💪 Что вы получите в реалити?", callback_data="start_b2")],
                [InlineKeyboardButton("✅ Кому подходит реалити, а кому нет?", callback_data="start_b3")],
                [InlineKeyboardButton("Записаться →", url=PAY_URL)],
            ])
        )

    # ── Блок 1: Об Иване (день 1) ──
    async def block1(ctx):

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
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/ivan_results.png")
        await asyncio.sleep(20)

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
            "*Старт программы: 11 мая.*\n\n"
            "Места ограничены — я работаю с небольшими группами, чтобы отслеживать результат каждого.\n\n"
            "Если вы устали от тренеров-зомби и марафонов, которые ведут к откату — "
            "*пришло время для системы, которая работает в реальной жизни.\n"
            "Если Вы чувствуете, что это то, что Вам нужно — не откладывайте.*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )

        # Запускаем block2 через 1 минуту после последнего сообщения
        jq = ctx.application.job_queue
        if jq:
            jq.run_once(block2, 60, name=f"b2_{uid}")

    # ── Блок 2: Подробно о продукте (день 2) ──
    async def block2(ctx):

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
            "• Как вписывать «запрещёнку» — бургер, пиво, шаурму, тирамису — без чувства вины\n\n"
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
            "8 недель, каждый день, с Вашим типом и Вашей целью.\n\n"
            "Старт *11 мая*. Если урок откликнулся — самое время сделать следующий шаг.",
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
            "*Старт 11 мая. Места ограничены.*\n\n"
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
        await ctx.bot.send_message(
            uid,
            "*Реалити уже скоро!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Выбрать тариф →", url=PAY_URL)]
            ])
        )

    # ── ТЕСТОВЫЕ ТАЙМИНГИ (заменить на боевые после проверки) ──
    # Блоки запускают друг друга цепочкой от последнего сообщения
    jq.run_once(d1h,    60,  name=f"d1h_{uid}")   # 1 мин после оффера (боевой: 3600)
    jq.run_once(block1, 120, name=f"b1_{uid}")    # 2 мин после оффера (боевой: 86400)
    # block2, block3, final запускаются цепочкой внутри каждого блока


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arch_key = (context.args or [None])[0]
    arch = ARCHETYPES.get(arch_key)
    context.user_data["arch_key"] = arch_key

    if not arch:
        await update.message.reply_text(
            "Привет! 👋\nПройдите тест и получи разбор:\n\n"
            "👉 " + QUIZ_URL)
        return ConversationHandler.END

    await update.message.reply_text("Привет! 👋\n\nПолучил Ваши ответы. Даю разбор — 1 минута.")
    await asyncio.sleep(1.2)
    await update.message.reply_text(f"*{arch['emoji']} Ваш тип: {arch['name']}*\n\n{arch['problem']}", parse_mode="Markdown")
    await asyncio.sleep(1.2)
    await update.message.reply_text(arch["cycle"])
    await asyncio.sleep(1.2)
    await update.message.reply_text(arch["solution"])
    await update.message.reply_text(
        "Хотите узнать — *каким Вы можете стать за 2 месяца?*\n\nЕсли внедрить одну простую систему.\nЯ задам всего пару вопросов.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Да, хочу узнать →", callback_data="go")],
            [InlineKeyboardButton("Может позже", callback_data="later")],
        ]))
    return ASK_GENDER


async def cb_later(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
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
    await asyncio.sleep(60)  # пауза 1 минута перед следующим сообщением
    await update.callback_query.message.reply_text(arch["tools"])
    await asyncio.sleep(1.5)

    uid = update.callback_query.from_user.id
    await update.callback_query.message.reply_text(
        "🎯 *Хотите достичь этого результата вместе с нами в группе?*\n\n"
        "Я запустил онлайн программу, в которой вы:\n"
        "— Похудеете и приведёте тело в форму 🔥\n"
        "— Получите ощутимый результат за 2 месяца\n"
        "— Получите лёгкую систему на всю жизнь, а не на короткий период\n"
        "— Сделаете это даже без обязательного посещения спортзала\n"
        "— Будете при этом наслаждаться жизнью, не испытывать стресс и голод\n"
        "— Сможете вписать в программу даже «запрещёнку» — бургер, пиво, шаурму, тирамису — без чувства вины 🔥\n\n"
        "Набор в Реалити #ПП «Программа Преображения» открыт прямо сейчас.\n\n"
        "Старт: *11 мая*\n"
        "Длительность: *8 недель*\n\n"
        "*ФОРМАТ:*\n"
        "❌ ЭТО НЕ КУРС\n"
        "❌ Не краткосрочная программа\n"
        "❌ Не марафон\n"
        "❌ Не челлендж\n"
        "👉 Это участие в процессе — реалити практикум. Записанные видео + живое сопровождение Ивана и куратора\n\n"
        "*Вот что вы получите, чтобы добиться своей цели по преображению тела:*\n\n"
        "✅ Доступ в закрытый Telegram-канал\n"
        "✅ Доступ в закрытый чат с участниками группы\n"
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
        "За 8 недель вы почувствуете контроль над телом, едой и энергией — без диет, запретов и жизни в спортзале.\n\n"
        "⏱ *Прямо сейчас для Вас действует специальная цена — только 1 час.*\n\n"
        "Хотите воспользоваться специальной ценой прямо сейчас?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Получить специальную цену →", url=PAY_PROMO)],
        ]))

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
        bot = context.bot
        if block_key == "b1":
            jq.run_once(lambda ctx: _exec_block1(uid, ctx.bot, ctx.application.job_queue),
                        when=2, name=f"man_b1_{uid}")
        elif block_key == "b2":
            jq.run_once(lambda ctx: _exec_block2(uid, ctx.bot, ctx.application.job_queue),
                        when=2, name=f"man_b2_{uid}")
        elif block_key == "b3":
            jq.run_once(lambda ctx: _exec_block3(uid, ctx.bot, ctx.application.job_queue),
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
        txt += f"Ваш тип: *{arch['emoji']} {arch['name']}*\nПрогноз: {f['wr']} за 8 недель\n\n"
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
            f"*Ваш тип:* {arch['emoji']} {arch['name']}\n*Прогноз:* {f['wr']} ({f['ch']}) за 8 недель",
            parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text("Пройдите тест:\n👉 https://vezuncheg.github.io/fitstate")


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
    await ph(f"{P}/ivan_results.png")
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
             "*Старт программы: 11 мая.*\n\n"
             "Места ограничены. Если вы устали от тренеров-зомби и марафонов — "
             "*пришло время для системы, которая работает в реальной жизни.\n"
             "Если Вы чувствуете, что это то, что Вам нужно — не откладывайте.*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]]))


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
             "8 недель, каждый день, с Вашим типом и Вашей целью.\n\n"
             "Старт *11 мая*. Если урок откликнулся — самое время сделать следующий шаг.",
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
             "*Старт 11 мая. Места ограничены.*\n\n"
             "Сделайте шаг прямо сейчас — пока есть возможность.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Записаться в Реалити →", url=PAY_URL)]]))


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
            f"*Прогноз:* {f['wr']} ({f['ch']}) за 8 недель",
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
        ])
        logger.info("Команды меню установлены ✅")

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
    app.add_handler(CallbackQueryHandler(cb_more,      pattern="^more_info$"))
    app.add_handler(CallbackQueryHandler(cb_start_b1,  pattern="^start_b1$"))
    app.add_handler(CallbackQueryHandler(cb_start_b2,  pattern="^start_b2$"))
    app.add_handler(CallbackQueryHandler(cb_start_b3,  pattern="^start_b3$"))
    app.add_handler(CallbackQueryHandler(cb_i_about,   pattern="^i_about$"))
    app.add_handler(CallbackQueryHandler(cb_i_program, pattern="^i_program$"))
    app.add_handler(CallbackQueryHandler(cb_i_results, pattern="^i_results$"))
    app.add_handler(CallbackQueryHandler(cb_my_res,    pattern="^my_res$"))

    logger.info("Программа Преображения bot started ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
