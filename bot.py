<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Реалити #ПП «Программа Преображения» — Выберите тариф</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0d12;--card:#15151f;--card2:#1a1a28;
  --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
  --purple:#7c3aed;--purpleL:#9d5ff7;--purpleXL:#c4b5fd;
  --green:#4ade80;--greenD:#22c55e;
  --amber:#f59e0b;--amberL:#fcd34d;
  --text:#f0effe;--muted:#7c7a96;--mutedL:#a09dbf;
  --r:16px;--rsm:10px;
}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;overflow-x:hidden;min-height:100vh}
.wrap{max-width:1100px;margin:0 auto;padding:0 20px}
.grad{background:linear-gradient(130deg,var(--purpleL),var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}

/* NAV */
nav{display:flex;align-items:center;justify-content:space-between;padding:16px 32px;background:rgba(13,13,18,.92);backdrop-filter:blur(18px);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
.logo{font-size:20px;font-weight:900;background:linear-gradient(135deg,#fff,var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.nav-back{font-size:13px;color:var(--muted);text-decoration:none;display:flex;align-items:center;gap:6px}
.nav-back:hover{color:var(--text)}

/* HERO */
.hero{padding:52px 0 40px;text-align:center;background:radial-gradient(ellipse 80% 50% at 50% 0%,rgba(124,58,237,.13) 0%,transparent 70%),var(--bg)}
.hero-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(74,222,128,.1);border:1px solid rgba(74,222,128,.25);color:var(--green);padding:7px 18px;border-radius:100px;font-size:12px;font-weight:700;margin-bottom:20px}
.hero h1{font-size:clamp(26px,5vw,44px);font-weight:900;line-height:1.1;margin-bottom:14px}
.hero-sub{font-size:16px;color:var(--muted);max-width:520px;margin:0 auto 28px;line-height:1.7}

/* PROMO BANNER */
.promo-banner{display:none;max-width:560px;margin:0 auto 32px;background:linear-gradient(135deg,rgba(124,58,237,.18),rgba(74,222,128,.1));border:1px solid rgba(124,58,237,.35);border-radius:var(--r);padding:16px 24px;text-align:center}
.promo-banner.show{display:block}
.promo-banner p{font-size:14px;color:var(--purpleXL);margin-bottom:8px}
.promo-banner strong{color:#fff}
.timer-row{display:flex;align-items:center;justify-content:center;gap:8px;font-size:22px;font-weight:800;color:#fff}
.timer-sep{color:var(--muted);font-size:18px}
.timer-block{display:flex;flex-direction:column;align-items:center;gap:2px}
.timer-label{font-size:10px;font-weight:600;color:var(--muted);letter-spacing:.06em}

/* GRID */
.plans{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:0 0 60px}
.plan{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:28px 24px;display:flex;flex-direction:column;position:relative;transition:border-color .25s,transform .25s}
.plan:hover{border-color:var(--border2);transform:translateY(-3px)}

/* FEATURED plan */
.plan.featured{background:var(--card2);border:1.5px solid var(--purpleL);transform:none}
.plan.featured:hover{transform:translateY(-3px)}
.featured-badge{position:absolute;top:-13px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,var(--purple),var(--purpleL));color:#fff;font-size:11px;font-weight:800;padding:4px 18px;border-radius:100px;white-space:nowrap;letter-spacing:.04em}

/* Plan header */
.plan-icon{font-size:24px;margin-bottom:10px}
.plan-name{font-size:13px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
.price-row{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}
.price{font-size:32px;font-weight:900;color:var(--text)}
.price-old{font-size:16px;color:var(--muted);text-decoration:line-through}
.price-save{font-size:12px;font-weight:700;color:var(--green);background:rgba(74,222,128,.1);border:1px solid rgba(74,222,128,.2);padding:2px 8px;border-radius:100px}
.plan-tagline{font-size:15px;font-weight:700;color:var(--text);margin-bottom:14px;line-height:1.3}
.price-period{font-size:12px;color:var(--muted);margin-bottom:20px}

/* Features */
.features{list-style:none;display:flex;flex-direction:column;gap:10px;margin-bottom:24px;flex:1}
.feat{display:flex;align-items:flex-start;gap:10px;font-size:14px;line-height:1.45}
.feat.off{color:var(--muted);text-decoration:line-through;opacity:.45}
.feat-icon{width:18px;height:18px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;margin-top:1px}
.feat-icon.on{background:rgba(74,222,128,.15)}
.feat-icon.off-ic{background:rgba(255,255,255,.05)}
.feat-check{width:9px;height:7px}
.feat-x{width:8px;height:8px}

/* CTA button */
.plan-btn{display:block;width:100%;padding:14px;border-radius:100px;font-family:inherit;font-size:15px;font-weight:700;cursor:pointer;border:none;text-align:center;text-decoration:none;transition:transform .18s,box-shadow .18s,opacity .18s}
.plan-btn:hover{transform:translateY(-2px)}
.plan-btn.default{background:rgba(255,255,255,.07);color:var(--text);border:1px solid var(--border2)}
.plan-btn.default:hover{background:rgba(255,255,255,.12)}
.plan-btn.accent{background:linear-gradient(135deg,var(--purple),var(--purpleL));color:#fff;box-shadow:0 4px 20px rgba(124,58,237,.35)}
.plan-btn.accent:hover{box-shadow:0 8px 28px rgba(124,58,237,.55)}

/* COMPARE TABLE */
.compare{padding:0 0 60px}
.compare h2{font-size:clamp(20px,3vw,32px);font-weight:800;text-align:center;margin-bottom:32px}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px}
thead th{padding:14px 16px;font-weight:700;font-size:13px;border-bottom:1px solid var(--border2)}
thead th:first-child{text-align:left;color:var(--muted)}
thead th:not(:first-child){text-align:center;min-width:120px}
thead th.th-feat{color:var(--purpleXL);position:relative}
thead th.th-feat::after{content:'';position:absolute;inset:0;background:rgba(124,58,237,.07);border-radius:8px 8px 0 0;pointer-events:none}
tbody tr{border-bottom:1px solid var(--border)}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(255,255,255,.02)}
td{padding:12px 16px}
td:first-child{color:var(--mutedL);font-size:13px}
td:not(:first-child){text-align:center}
td.td-feat{background:rgba(124,58,237,.04)}
.check-y{color:var(--green);font-size:16px}
.check-n{color:rgba(255,255,255,.2);font-size:16px}
.check-partial{font-size:12px;color:var(--amber);font-weight:600}

/* GUARANTEE */
.guarantee{max-width:640px;margin:0 auto 60px;background:rgba(74,222,128,.06);border:1px solid rgba(74,222,128,.18);border-radius:var(--r);padding:24px 28px;text-align:center}
.guarantee h3{font-size:18px;font-weight:700;margin-bottom:8px}
.guarantee p{font-size:14px;color:var(--muted);line-height:1.7}

/* FAQ */
.faq{max-width:640px;margin:0 auto 60px}
.faq h2{font-size:clamp(20px,3vw,28px);font-weight:800;margin-bottom:24px;text-align:center}
.faq-item{border:1px solid var(--border);border-radius:var(--rsm);margin-bottom:8px;overflow:hidden}
.faq-q{padding:16px 20px;font-size:14px;font-weight:600;cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none}
.faq-q:hover{background:rgba(255,255,255,.03)}
.faq-q span{color:var(--muted);font-size:18px;transition:transform .2s}
.faq-item.open .faq-q span{transform:rotate(45deg)}
.faq-a{display:none;padding:0 20px 16px;font-size:13px;color:var(--muted);line-height:1.7}
.faq-item.open .faq-a{display:block}

/* FOOTER */
footer{padding:28px 0;border-top:1px solid var(--border);text-align:center}
.fl{font-size:16px;font-weight:900;background:linear-gradient(135deg,#fff,var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px}
footer p{font-size:12px;color:var(--muted)}
footer a{color:var(--muted);text-decoration:none}
footer a:hover{color:var(--text)}

@media(max-width:900px){
  .plans{grid-template-columns:1fr}
  .plan.featured{transform:none}
  nav{padding:14px 16px}
}
</style>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://pp-reality.ru/pay.html">
  <meta property="og:title" content="Выберите тариф — Реалити #ПП «Программа Преображения»">
  <meta property="og:description" content="Базовый от 5 300 ₽, Расширенный от 7 900 ₽, Личный от 21 200 ₽. Старт 23 июня.">
  <meta property="og:image" content="https://raw.githubusercontent.com/Vezuncheg/fitstate/main/images/ivan_photo.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="description" content="Базовый от 5 300 ₽, Расширенный от 7 900 ₽, Личный от 21 200 ₽. Старт 23 июня.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Выберите тариф — Реалити #ПП «Программа Преображения»">
  <meta name="twitter:description" content="Базовый от 5 300 ₽, Расширенный от 7 900 ₽, Личный от 21 200 ₽. Старт 23 июня.">
  <meta name="twitter:image" content="https://raw.githubusercontent.com/Vezuncheg/fitstate/main/images/ivan_photo.jpg">
</head>
<body>

<nav>
  <div class="logo">Реалити #ПП</div>
  <a href="index-main.html" class="nav-back">← На главную страницу</a>
</nav>

<section class="hero">
  <div class="wrap">
    <div class="hero-badge" id="heroBadge">🎯 Выберите тариф и начните уже сегодня</div>
    <h1>Выберите <span class="grad">свой тариф</span></h1>
    <p class="hero-sub" id="heroSub">8 недель программы Реалити #ПП «Программа Преображения» — персональный план под Ваш тип, закрытый канал и реальный результат</p>
    <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.3);color:#c4b5fd;padding:10px 24px;border-radius:100px;font-size:14px;font-weight:700;margin-bottom:12px;">
      🗓 Старт следующего потока: <strong style="color:#fff;">23 июня 2026</strong>
    </div>

    <!-- Promo banner (показывается только со скидкой) -->
    <div class="promo-banner" id="promoBanner">
      <p>&#9889; <strong>Специальное предложение истекает через 1 час!</strong><br>Специальная цена активна — выберите тариф прямо сейчас:</p>
      <div class="timer-row">
        <div class="timer-block"><span id="tMin">59</span><span class="timer-label">МИН</span></div>
        <span class="timer-sep">:</span>
        <div class="timer-block"><span id="tSec">59</span><span class="timer-label">СЕК</span></div>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="plans" id="plansGrid">

      <!-- БАЗОВЫЙ -->
      <div class="plan" id="plan0">
        <div class="plan-icon">⚡</div>
        <div class="plan-name">Базовый</div>
        <div class="plan-tagline">Стартовый пинок</div>
        <div class="price-row">
          <span class="price" id="p0">5 300 ₽</span>
          <span class="price-old" id="p0old" style="display:none">5 300 ₽</span>
        </div>
        <div class="price-save" id="p0save" style="display:none">Специальная цена</div>
        <div class="price-period">разовый платёж · 8 недель</div>
        <ul class="features">
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Доступ в реалити на 8 недель</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Закрытый канал в Telegram</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Персональный план под Ваш тип</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Чат участников</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Обратная связь от куратора</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Еженедельные видеоконференции</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Приложение «Ассистент Состояния»</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Планер «Состояние»</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Книга «Состояние»</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Индивидуальный созвон с Иваном</li>
        </ul>
        <a href="#" class="plan-btn default" id="btn0" onclick="openModal('Стартовый пинок', 'btn0'); return false">Выбрать базовый</a>
      </div>

      <!-- РАСШИРЕННЫЙ (featured) -->
      <div class="plan featured" id="plan1">
        <div class="featured-badge">⭐ Рекомендуем</div>
        <div class="plan-icon">💎</div>
        <div class="plan-name">Расширенный</div>
        <div class="plan-tagline">Полное погружение</div>
        <div class="price-row">
          <span class="price" id="p1">7 900 ₽</span>
          <span class="price-old" id="p1old" style="display:none">7 900 ₽</span>
        </div>
        <div class="price-save" id="p1save" style="display:none">Специальная цена</div>
        <div class="price-period">разовый платёж · 8 недель</div>
        <ul class="features">
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Доступ в реалити на 8 недель</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Закрытый канал в Telegram</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Персональный план под Ваш тип</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Чат участников</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Ежедневная обратная связь от куратора</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Еженедельные видеоконференции с Иваном</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Приложение «Ассистент Состояния»</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Планер «Состояние»</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Книга «Состояние»</li>
          <li class="feat off"><div class="feat-icon off-ic"><svg class="feat-x" viewBox="0 0 8 8" fill="none"><path d="M1 1l6 6M7 1L1 7" stroke="#555" stroke-width="1.5" stroke-linecap="round"/></svg></div>Индивидуальный созвон с Иваном</li>
        </ul>
        <a href="#" class="plan-btn accent" id="btn1" onclick="openModal('Полное погружение', 'btn1'); return false">Выбрать расширенный →</a>
      </div>

      <!-- ЛИЧНЫЙ -->
      <div class="plan" id="plan2">
        <div class="plan-icon">👑</div>
        <div class="plan-name">Личный</div>
        <div class="plan-tagline">Иван лично со мной</div>
        <div class="price-row">
          <span class="price" id="p2">21 200 ₽</span>
          <span class="price-old" id="p2old" style="display:none">21 200 ₽</span>
        </div>
        <div class="price-save" id="p2save" style="display:none">Специальная цена</div>
        <div class="price-period">разовый платёж · 8 недель</div>
        <ul class="features">
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Доступ в реалити на 8 недель</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Закрытый канал в Telegram</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Персональный план под Ваш тип</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Чат участников</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Ежедневная обратная связь от куратора</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Еженедельные видеоконференции с Иваном</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Приложение «Ассистент Состояния»</li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Планер «Состояние» <span style="font-size:11px;color:var(--amber)">с автографом Ивана</span></li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>Книга «Состояние» <span style="font-size:11px;color:var(--amber)">с автографом Ивана</span></li>
          <li class="feat"><div class="feat-icon on"><svg class="feat-check" viewBox="0 0 9 7" fill="none"><path d="M1 3.5l2.5 2.5 4.5-5" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div><span>Индивидуальный созвон с Иваном <span style="font-size:11px;color:var(--amber);">★ первые 20 чел.</span></span></li>
        </ul>
        <a href="#" class="plan-btn default" id="btn2" onclick="openModal('Иван лично со мной', 'btn2'); return false">Выбрать личный</a>
      </div>

    </div>
  </div>
</section>

<!-- GUARANTEE -->
<section>
  <div class="wrap">
    <div class="guarantee">
      <h3>✅ Гарантия результата</h3>
      <p>Если после 8 недель Вы не увидите результата — мы вернём деньги. Без вопросов. Мы уверены в программе, потому что она работает уже 24 года.</p>
    </div>
  </div>
</section>

<!-- FAQ -->
<section>
  <div class="wrap">
    <div class="faq">
      <h2>Частые вопросы</h2>
      <div class="faq-item">
        <div class="faq-q" onclick="toggleFaq(this)">Когда начинается поток? <span>+</span></div>
        <div class="faq-a">Ближайший поток стартует <strong>23 июня 2026</strong>. Реалити длится <strong>28 дней</strong>. После этого участники 2-го и 3-го тарифов переходят в закрытый клуб поддержки на 1 месяц. После оплаты Вы получите ссылку на закрытый канал и подготовительные материалы для подготовки к старту.</div>
      </div>
      <div class="faq-item">
        <div class="faq-q" onclick="toggleFaq(this)">Чем отличается Расширенный от Базового? <span>+</span></div>
        <div class="faq-a">В Расширенном тарифе Вы получаете живую обратную связь от куратора каждый день, чат с другими участниками, еженедельные видеоконференции с Иваном и приложение-ассистент. Это не просто контент — это полное сопровождение.</div>
      </div>
      <div class="faq-item">
        <div class="faq-q" onclick="toggleFaq(this)">Что такое приложение «Ассистент Состояния»? <span>+</span></div>
        <div class="faq-a">Это наша собственная разработка — цифровой помощник, созданный специально под методику FitState. Ассистент помогает лучше понять, что с Вами происходит прямо сейчас: снизить внутреннее напряжение, вернуть фокус и найти опору в моменты, когда сложно. Доступен 24/7 и знает Ваш тип и цели.</div>
      </div>
      <div class="faq-item">
        <div class="faq-q" onclick="toggleFaq(this)">Как происходит оплата? <span>+</span></div>
        <div class="faq-a">Оплата производится в полном объёме до начала реалити. После подтверждения оплаты Вы получаете ссылку на закрытый Telegram-канал потока и доступ ко всем материалам выбранного тарифа.</div>
      </div>
      <div class="faq-item">
        <div class="faq-q" onclick="toggleFaq(this)">Специальная цена — для всех? <span>+</span></div>
        <div class="faq-a">Специальная цена действует только для тех, кто пришёл из Telegram-бота в течение 1 часа после получения персонального результата теста. После истечения таймера действуют стандартные цены.</div>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="fl">Реалити #ПП</div>
    <p>© 2026 Реалити #ПП «Программа Преображения» · <a href="privacy.html" style="color:var(--muted);text-decoration:none">Политика конфиденциальности</a> · <a href="offer.html" style="color:var(--muted);text-decoration:none">Договор оферты</a><a href="https://vezuncheg.github.io/fitstate">Пройти тест</a></p>
  </div>
</footer>

<script>
// ── ЦЕНЫ ──
var PRICES = {
  base:     { normal: 5300,  sale: 4600  },
  extended: { normal: 7900,  sale: 6900  },
  personal: { normal: 21200, sale: 18500 },
};

// ── Форматирование ──
function fmt(n) {
  return n.toLocaleString('ru-RU') + ' ₽';
}

// ── Определяем режим (скидка или нет) по URL-параметру ──
var params = new URLSearchParams(window.location.search);
var isPromo = params.get('promo') === '1';

function applyPrices() {
  if (isPromo) {
    // Скидочные цены
    document.getElementById('p0').textContent = fmt(PRICES.base.sale);
    document.getElementById('p0old').textContent = fmt(PRICES.base.normal);
    document.getElementById('p0old').style.display = 'inline';
    document.getElementById('p0save').style.display = 'inline-block';

    document.getElementById('p1').textContent = fmt(PRICES.extended.sale);
    document.getElementById('p1old').textContent = fmt(PRICES.extended.normal);
    document.getElementById('p1old').style.display = 'inline';
    document.getElementById('p1save').style.display = 'inline-block';

    document.getElementById('p2').textContent = fmt(PRICES.personal.sale);
    document.getElementById('p2old').textContent = fmt(PRICES.personal.normal);
    document.getElementById('p2old').style.display = 'inline';
    document.getElementById('p2save').style.display = 'inline-block';

    document.getElementById('promoBanner').classList.add('show');
    document.getElementById('heroBadge').textContent = '⚡ Ваша специальная цена активна — выберите тариф';
    document.getElementById('heroSub').innerHTML = 'Специальная цена действует ещё 1 час.<br>8 недель программы Реалити #ПП «Программа Преображения» — персональный план, закрытый канал, реальный результат.';

    // Ссылки на оплату со скидкой


    startTimer();
  } else {
    // Стандартные цены

  }
}

// ── ТАЙМЕР ──
function startTimer() {
  // Сохраняем дедлайн в sessionStorage чтобы не сбрасывался при перезагрузке
  var key = 'fitstate_promo_end';
  var end = sessionStorage.getItem(key);
  if (!end) {
    end = Date.now() + 3600 * 1000;
    sessionStorage.setItem(key, end);
  }
  end = parseInt(end);

  function tick() {
    var left = Math.max(0, end - Date.now());
    var min = Math.floor(left / 60000);
    var sec = Math.floor((left % 60000) / 1000);
    document.getElementById('tMin').textContent = String(min).padStart(2, '0');
    document.getElementById('tSec').textContent = String(sec).padStart(2, '0');
    if (left > 0) {
      setTimeout(tick, 1000);
    } else {
      // Таймер истёк — убираем скидку
      document.getElementById('promoBanner').innerHTML =
        '<p>⏰ <strong>Время специальной цены истекло.</strong> Действуют стандартные цены.</p>';
      isPromo = false;
      applyNormalPrices();
    }
  }
  tick();
}

function applyNormalPrices() {
  document.getElementById('p0').textContent = fmt(PRICES.base.normal);
  document.getElementById('p0old').style.display = 'none';
  document.getElementById('p0save').style.display = 'none';
  document.getElementById('p1').textContent = fmt(PRICES.extended.normal);
  document.getElementById('p1old').style.display = 'none';
  document.getElementById('p1save').style.display = 'none';
  document.getElementById('p2').textContent = fmt(PRICES.personal.normal);
  document.getElementById('p2old').style.display = 'none';
  document.getElementById('p2save').style.display = 'none';
}

// ── FAQ ──
function toggleFaq(el) {
  var item = el.parentElement;
  item.classList.toggle('open');
}

applyPrices();
</script>
</body>
</html>
