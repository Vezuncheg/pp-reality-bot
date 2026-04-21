import os
import logging
import asyncio
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        "tools": "🛠 Что уберём в Вашем случае:\n\n1️⃣ Техники прерывания триггера\n2️⃣ Быстрые замены — 3–4 инструмента без еды\n3️⃣ Структура питания — убираем ситуации срыва",
        "day3": "📌 Топ-3 ошибки эмоционального едока:\n\n1. Держать дома запасы любимой еды\n2. Пропускать приёмы пищи — голод усиливает триггер\n3. Бороться силой воли — нужно переключать, не бороться",
        "proof": "Анна, 34 года — минус 11 кг за 8 недель.\nПерестала есть от стресса уже на 2-й неделе.\n\nМихаил, 31 год — минус 9 кг. Впервые не сорвался ни разу.",
    },
    "social_hostage": {
        "emoji": "🍕", "name": "Социальный заложник",
        "problem": "Наедине с собой Вы держитесь отлично.\nНо любое застолье или компания — всё рушится.\n\nЭто не слабость характера — это отсутствие конкретной стратегии.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Всю неделю держишься — приходит праздник\n→ Неловко отказывать, не хочешь выделяться\n→ Ешь как все — прогресс обнуляется\n→ Снова с понедельника",
        "solution": "✅ Что реально помогает:\n\n→ Конкретные сценарии: кафе, корпоратив, застолье\n→ Фразы-ответы, которые не обидят\n→ Правило 80/20 — как позволять себе без ущерба\n\nЭто навык, а не сила воли.",
        "tools": "🛠 Что уберём в Вашем случае:\n\n1️⃣ Стратегия поведения в компании без срывов\n2️⃣ Гибкая система — любой праздник не ломает прогресс\n3️⃣ Коммуникация — как отказывать без обид",
        "day3": "📌 Топ-3 ошибки социального заложника:\n\n1. Ждать подходящего момента — его не будет\n2. Избегать мероприятий — это не жизнь\n3. Есть про запас перед выходом — не работает",
        "proof": "Катя, 29 лет — минус 8 кг без отказа от вечеринок.\n\nДмитрий, 36 лет — минус 10 кг. Рестораны с клиентами каждую неделю — ни одного срыва.",
    },
    "metabolic_skeptic": {
        "emoji": "⚖️", "name": "Метаболический скептик",
        "problem": "Вы едите немного, стараетесь, делаете всё правильно.\nА результата нет.\n\nСтандартные советы просто не подходят для Вашей ситуации.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Ешь мало — вес стоит или растёт\n→ Добавляешь активность — результата нет\n→ Думаешь «мне не дано»\n→ Опускаешь руки",
        "solution": "✅ Что реально помогает:\n\n→ Точный расчёт твоего реального коридора калорий\n→ Перезапуск обмена через правильный дефицит\n→ Работа с режимом сна и стрессом\n\nМетаболизм не сломан. Ему дают неправильный сигнал.",
        "tools": "🛠 Что уберём в Вашем случае:\n\n1️⃣ Точная калорийность — реальный дефицит именно для Вас\n2️⃣ Состав питания — БЖУ, запускающий жиросжигание\n3️⃣ Режим — сон и стресс влияют сильнее, чем многие думают",
        "day3": "📌 Почему «мало ешь, но не худеешь»:\n\n1. Хроническое недоедание замедляет метаболизм\n2. Скрытые калории в «здоровых» продуктах\n3. Кортизол от стресса блокирует жиросжигание",
        "proof": "Ирина, 38 лет — 2 года не могла сдвинуться с места.\nЗа 8 недель минус 7 кг. Оказалось — ела слишком мало.\n\nСергей, 33 года — тренировался 4 раза в неделю. Поменяли питание — минус 9 кг.",
    },
    "starter_stopper": {
        "emoji": "🔁", "name": "Стартер-стопер",
        "problem": "В начале мотивация огромная.\nНо через 10–14 дней она испаряется — и всё заново.\n\nПроблема не в Вас.\nПроблема в том, что Вы работаете на силе воли. А она конечна у всех.",
        "cycle": "🔴 Что происходит у Вас:\n\n→ Мощный старт — мотивация на максимуме\n→ Через 1–2 недели энтузиазм падает\n→ Один пропуск → ощущение провала → бросаешь\n→ Через время — снова с понедельника",
        "solution": "✅ Что реально помогает:\n\n→ Заменить мотивацию системой — она не исчезает\n→ Внешние точки контроля: куратор, группа\n→ Маленькие wins вместо большой далёкой цели\n\nКогда есть система и окружение — мотивация не нужна.",
        "tools": "🛠 Что уберём в Вашем случае:\n\n1️⃣ Система вместо силы воли — структура, которой легко следовать\n2️⃣ Куратор и группа — поддержка, которая не даёт выпасть\n3️⃣ Протокол срыва — что делать если пропустил",
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
                    ch=f"−{lo}–{hi} кг жира", b2=bmi2, waist=f"−{lo+1}–{hi-1} см",
                    en="заметно вырастет к 3-й неделе")
    elif goal == "muscle":
        return dict(cw=weight, cb=bmi, wr=f"{round(weight+3)}–{round(weight+6)} кг",
                    ch="+3–6 кг мышц", b2=round(bmi+0.8, 1), waist="без изменений",
                    en="вырастет к 2-й неделе")
    else:
        wlo, whi = round(weight - 5), round(weight - 3)
        bmi2 = round((wlo + whi) / 2 / ((height / 100) ** 2), 1)
        return dict(cw=weight, cb=bmi, wr=f"{wlo}–{whi} кг",
                    ch="−3–5 кг + рельеф", b2=bmi2, waist="−3–5 см",
                    en="вырастет уже к концу 1-й недели")


def visual(f, name):
    return (f"🖼 *ТЫ СЕЙЧАС*\nВес: {f['cw']} кг  |  ИМТ: {f['cb']}\n_{name}_\n\n"
            f"⬇️  8 недель FitState  ⬇️\n\n"
            f"🖼 *ТЫ ЧЕРЕЗ 2 МЕСЯЦА*\nВес: {f['wr']}  |  ИМТ: {f['b2']}\n_{f['ch']}_")


def pay_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Записаться →", url=PAYMENT_URL)]])


def more_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("О нас и команде", callback_data="i_about")],
        [InlineKeyboardButton("Программа подробно", callback_data="i_program")],
        [InlineKeyboardButton("Результаты участников", callback_data="i_results")],
    ])


async def send_photo_url(bot, chat_id, url, caption=None):
    """Скачивает фото и отправляет как файл — обходит ограничение Telegram на GitHub URLs"""
    import io
    async with httpx.AsyncClient() as client:
        r = await client.get(url, follow_redirects=True, timeout=15)
        r.raise_for_status()
    bio = io.BytesIO(r.content)
    bio.name = url.split("/")[-1]
    if caption:
        await bot.send_photo(chat_id=chat_id, photo=bio, caption=caption)
    else:
        await bot.send_photo(chat_id=chat_id, photo=bio)


async def schedule_dojim(uid, context):
    jq = context.application.job_queue
    if not jq:
        return

    # ── Через 1 час: таймер истёк, скидки нет, но запись открыта ──
    async def d1h(ctx):
        await ctx.bot.send_message(
            uid,
            "Скидка 20% истекла, но запись в Реалити ещё открыта.\n\n"
            "👇 Успейте занять место по стандартной цене:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Выбрать тариф →", url=PAY_URL)]
            ])
        )

    # ── Блок 1: Об Иване (день 1) ──
    async def block1(ctx):

        # Вступление — подводка
        await ctx.bot.send_message(uid,
            "Любой хороший продукт начинается с человека, который его создал.\n\n"
            "Прежде чем рассказать Вам о том, что Вас ждёт внутри Реалити — "
            "хочу познакомить Вас с Иваном Самохиным. Не с его регалиями и цифрами. "
            "А с его историей. Потому что именно она объясняет, почему этот продукт "
            "работает так, как работает.\n\n"
            "Читайте от первого лица."
        )
        await asyncio.sleep(20)

        # Часть 1 — детство, история, 24 года
        await ctx.bot.send_message(uid,
            "В детстве я был слабым ребёнком — постоянно болел, плохой иммунитет. "
            "Таких сейчас называют астеник. При этом я рос в эпоху Сталлоне и Шварценеггера, "
            "и для многих пацанов типа меня они стали мотивацией и прообразом того, каким хочется быть. "
            "Это и стала первой причиной, почему в 14 лет я решил заняться собой.\n\n"
            "С тех пор прошло 24 года. И нет, я не тот человек, который никогда не срывался "
            "и всегда был в форме. Бывало по-разному. Когда ломал ногу и вылетал на несколько месяцев. "
            "Когда много работал, поздно уходил из офиса, постоянно ездил в командировки. "
            "Всё это влияет на восстановление, на режим, на состояние. Форма уходила.\n\n"
            "Именно в этом контексте обычной жизни я и научился находить время для себя и своего тела. "
            "Выработал личные привычки и принципы, которые стали для меня опорой. "
            "Когда наступает не лучший период — смотрю на себя в зеркало, понимаю, что мне так не нравится, "
            "и возвращаюсь к своим привычкам.\n\n"
            "И кстати, когда люди сейчас смотрят на меня, часто говорят: ну у тебя генетика. "
            "Но они не видели меня в 14 лет — худого, слабого, который не мог долгое время набрать массу. "
            "Дрыщ, если честно. Генетика здесь ни при чём.\n\n"
            "Вопрос в количестве попыток и в том, каким человеком ты становишься в процессе. "
            "За последние три месяца у меня было три тренировки в неделю — и я не пропустил ни одной. "
            "Не потому что у меня железная воля. А потому что это стало такой же привычкой, как почистить зубы. "
            "Моя генетика — в принципах и привычках, а не в генах."
        )
        await asyncio.sleep(20)

        # Фото 1 — коллаж по годам
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/ivan_years.jpeg")
        await asyncio.sleep(20)

        # Часть 2 — подкаст и книги
        await ctx.bot.send_message(uid,
            "В 2024 году я начал вести подкаст и за это время провёл больше 60 выпусков — "
            "в том числе с учёными, докторами, генетиками, эндокринологами, биофизиками. "
            "Подкаст — это не диплом, я понимаю. Но чтобы подготовиться к каждому интервью, "
            "мне нужно глубоко погрузиться в тему. И бывало, что в ходе разговора я понимал: "
            "сам доктор заблуждается — потому что я нашёл новые данные, которые опровергают то, "
            "во что он верил годами.\n\n"
            "Доктора тоже получают знания извне — из исследований, из практики. "
            "Я делаю то же самое, просто другим путём. Эти встречи помогли мне стать глубже "
            "в вопросах здоровья и того, как разные аспекты жизни влияют на то, как мы выглядим "
            "и как себя чувствуем. Это не просто «ешь, спи, качайся». Наша жизнь гораздо больше, "
            "чем спортзал, два грамма белка на килограмм веса и банка протеина. "
            "На наше состояние влияет огромное количество факторов.\n\n"
            "Это я понял спустя 24 года личной практики и благодаря своим гостям. "
            "Всё это вылилось в две книги о здоровье, состоянии и о том, что на него влияет."
        )
        await asyncio.sleep(20)

        # Фото 2 — книга Состояние
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/book_sostoyanie.jpeg")
        await asyncio.sleep(20)

        # Фото 3 — книга Состояние 2.0
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/book_sostoyanie2.png")
        await asyncio.sleep(20)

        # Фото 4 — YouTube канал
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/youtube_channel.jpeg")
        await asyncio.sleep(20)

        # Часть 3 — не тренер и не врач, рациональный путь, марафоны
        await ctx.bot.send_message(uid,
            "Я не тренер и не врач, и считаю, что это скорее плюс. "
            "Я часто вижу докторов, которые сами выглядят не очень. С лишним весом, с плохими привычками. "
            "И у меня один простой вопрос: почему я должен слушать человека, который на своём теле "
            "не применяет то, о чём говорит?\n\n"
            "С тренерами другая история. За 24 года я занимался с большим количеством тренеров "
            "в разных залах и странах. И вот что я заметил. Почти все рано или поздно предлагают "
            "перейти на анаболики — потому что им важно сделать из тебя кейс. "
            "При этом мало кто думает о твоём реальном здоровье и долголетии. Мне этот путь не близок.\n\n"
            "Второй момент — у большинства тренеров нет комплексного подхода. "
            "Они видят вес, подкожный жир, мышцы. Но мне важно как выглядит моя кожа, мои волосы, "
            "насколько я здоров ментально и психологически — а это всё взаимосвязано, "
            "наш организм работает как единое целое. "
            "Многих тренеров, которых я вижу даже в своём зале, я бы не назвал здоровыми людьми. "
            "У многих расстройства пищевого поведения, маниакальное отношение к калоражу, "
            "они торчат по двенадцать часов в день в зале, питание из контейнеров, никаких ресторанов. "
            "Они живут в своём мире и с осуждением смотрят на всех остальных.\n\n"
            "Я для себя выбрал другой путь — рациональный. "
            "Жить полноценно, без перегибов, без лотков с едой и без этого зомби-режима. "
            "И при этом выглядеть хорошо. Мне кажется, большинству людей нужно именно это.\n\n"
            "Я живу как обычный человек. С работой, командировками, едой не всегда правильной. "
            "Да, бывает фастфуд, да, часто ем в ресторанах. "
            "И кстати, когда понимаешь сколько тебе реально нужно есть — тратишь меньше, а не больше. "
            "Питаясь хаотично, люди тратят гораздо больше денег, чем думают. "
            "И несмотря на всё это — вот уже 24 года держу себя в форме.\n\n"
            "Ещё один момент. Если Вы уже проходили марафоны и всё откатывалось — я понимаю. "
            "Марафон по природе своей вырывает Вас из жизненного контекста: от чего-то резко отказываетесь, "
            "держитесь, потом всё возвращается. Я из контекста не вырываю: с работой, с любимой едой, "
            "с ресторанами, с семьёй. Задача не в том, чтобы за 28 дней стать качком. "
            "Задача в том, чтобы научить Вас правильно распределить ингредиенты — "
            "как в хорошем супе, где важны пропорции. "
            "Когда Вы это понимаете, результат остаётся. "
            "Потому что это становится Вашим образом жизни, а не временным марш-броском."
        )
        await asyncio.sleep(20)

        # Фото 5 — до/после 28 дней
        await send_photo_url(ctx.bot, uid, f"{PHOTOS_URL}/ivan_before_after.jpeg")
        await asyncio.sleep(20)

        # Часть 4 — результат и честность + запуск block2 через 1 мин
        await ctx.bot.send_message(uid,
            "Прямо перед запуском программы я прошёл её в очередной раз сам. "
            "С нуля, всё зафиксировал. И в этот раз просто снял всё на камеру.\n\n"
            "За 28 дней:\n"
            "→ −4,3 кг веса\n"
            "→ −2,2 кг жировой массы\n"
            "→ −1,8% телесного жира\n\n"
            "Я не продаю мечту про «стань качком за месяц» и не обещаю минус тридцать килограмм "
            "с кубиками на прессе. Это фейк, который продают большинство блогеров через собственный пример. "
            "У всех разный контекст, разный старт, разная психология.\n\n"
            "Я говорю о другом. О принципах и привычках, которые 24 года позволяют мне выглядеть хорошо "
            "в условиях обычной жизни. С фастфудом, ресторанами, периодами, когда всё летит к чертям — "
            "но находить причины и силы возвращаться обратно.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )

        # ── Запускаем block2 через 1 минуту после последнего сообщения ──
        jq = ctx.application.job_queue
        if jq:
            jq.run_once(block2, 60, name=f"b2_{uid}")   # 1 мин (боевой: 86400)

    # ── Блок 2: Подробно о продукте (день 2) ──
    async def block2(ctx):
        await ctx.bot.send_message(
            uid,
            "[ БЛОК 2 — О ПРОДУКТЕ ]\n\n"
            "⏳ Здесь будет подробный рассказ о Реалити #ПП от Ивана — "
            "что внутри, как устроен процесс, почему это работает.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )
        # ── Запускаем block3 через 1 минуту после последнего сообщения ──
        jq = ctx.application.job_queue
        if jq:
            jq.run_once(block3, 60, name=f"b3_{uid}")   # 1 мин (боевой: 259200)

    # ── Блок 3: Кому подойдёт, а кому нет (день 3) ──
    async def block3(ctx):
        await ctx.bot.send_message(
            uid,
            "[ БЛОК 3 — КОМУ ПОДОЙДЁТ ]\n\n"
            "⏳ Здесь будет честный разбор — кому Реалити даст результат, "
            "а кому пока рано. Это важно, чтобы Вы приняли осознанное решение.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Записаться в Реалити →", url=PAY_URL)]
            ])
        )
        # ── Запускаем final через 1 минуту после последнего сообщения ──
        jq = ctx.application.job_queue
        if jq:
            jq.run_once(final, 60, name=f"fin_{uid}")   # 1 мин (боевой: 432000)

    # ── Финальный дожим (день 5) ──
    async def final(ctx):
        await ctx.bot.send_message(
            uid,
            "*Реалити уже идёт. Места заканчиваются.*\n\n"
            "Вы уже знаете свой тип и свою причину.\n"
            "Осталось сделать один шаг — выбрать тариф и начать.\n\n"
            "Старт: *11 мая*",
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
        "Хотите узнать — *каким Вы можете стать за 2 месяца?*\n\nНужно задать пару вопросов.",
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
    await asyncio.sleep(1.2)
    await update.callback_query.message.reply_text(
        f"*📊 Прогноз на 8 недель:*\n\n"
        f"Сейчас: *{f['cw']} кг*, ИМТ *{f['cb']}*\n\n"
        f"Через 8 недель:\n"
        f"→ Вес: *{f['wr']}* ({f['ch']})\n"
        f"→ ИМТ: *{f['b2']}*\n"
        f"→ Объём: *{f['waist']}*\n"
        f"→ Энергия: {f['en']}\n\n"
        f"_На основе Ваших параметров и средних результатов участников с похожим профилем._",
        parse_mode="Markdown")
    await asyncio.sleep(1.2)
    await update.callback_query.message.reply_text(arch["tools"])
    await asyncio.sleep(1.5)

    uid = update.callback_query.from_user.id
    await update.callback_query.message.reply_text(
        "🎯 *Хотите достичь этого результата вместе с нами в группе?*\n\n"
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
        "⏱ *Прямо сейчас — скидка 20%, она действует 1 час с этого момента.*\n\n"
        "Хотите воспользоваться скидкой 20% прямо сейчас?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Воспользоваться скидкой 20% →", url=PAY_PROMO)],
        ]))

    await schedule_dojim(uid, context)
    return ConversationHandler.END


async def cb_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Что Вам важнее всего узнать?", reply_markup=more_kb())


async def cb_i_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "*О нас и команде*\n\n9 лет. 55 000+ участников.\nНаучный подход — алгоритмы на основе ВОЗ.\n\nМы меняем причину, по которой у Вас не получалось.",
        parse_mode="Markdown", reply_markup=pay_kb())


async def cb_i_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "*Программа по неделям:*\n\n📍 1–2: диагностика и настройка\n📍 3–4: первые результаты\n📍 5–6: закрепление\n📍 7–8: финальный рывок + план на после",
        parse_mode="Markdown", reply_markup=pay_kb())


async def cb_i_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    arch_key = context.user_data.get("arch_key", "emotional_eater")
    arch = ARCHETYPES.get(arch_key, ARCHETYPES["emotional_eater"])
    await update.callback_query.message.reply_text(
        f"*Результаты участников:*\n\n{arch['proof']}",
        parse_mode="Markdown", reply_markup=pay_kb())


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arch_key = context.user_data.get("arch_key")
    f = context.user_data.get("forecast")
    arch = ARCHETYPES.get(arch_key)
    txt = "📋 *Главное меню FitState*\n\n"
    if arch and f:
        txt += f"Ваш тип: *{arch['emoji']} {arch['name']}*\nПрогноз: {f['wr']} за 8 недель\n\n"
    await update.message.reply_text(txt, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Мой результат", callback_data="my_res")],
            [InlineKeyboardButton("📖 О программе", callback_data="i_program")],
            [InlineKeyboardButton("🏆 Результаты участников", callback_data="i_results")],
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


def main():
    if not TOKEN:
        logger.error("BOT_TOKEN не установлен!")
        return

    app = Application.builder().token(TOKEN).build()

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
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CallbackQueryHandler(cb_more,     pattern="^more_info$"))
    app.add_handler(CallbackQueryHandler(cb_i_about,  pattern="^i_about$"))
    app.add_handler(CallbackQueryHandler(cb_i_program,pattern="^i_program$"))
    app.add_handler(CallbackQueryHandler(cb_i_results,pattern="^i_results$"))
    app.add_handler(CallbackQueryHandler(cb_my_res,   pattern="^my_res$"))

    logger.info("FitState bot started ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
