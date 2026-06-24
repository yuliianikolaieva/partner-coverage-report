# -*- coding: utf-8 -*-
"""Генерує index.html для звіту 'Покриття та сегментація партнерського портфеля'."""
import json, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
    D = json.load(f)

T = D["totals"]; SEG = D["seg_overview"]; AM = D["am_work"]
P = D["partners"]; MT = D["managed_totals"]; EXT = D["enterprise_external"]

def eur(v):
    if v is None: return "—"
    return f"€{v:,.0f}".replace(",", " ")
def num(v):
    if v is None: return "—"
    return f"{v:,.0f}".replace(",", " ")
def pct(part, whole, d=1):
    if not whole: return "0%"
    return f"{part/whole*100:.{d}f}%"

# ---- derived ----
seg_order = {"Enterprise":0,"Mid-market":1,"SMB":2,"Missing Segment":3}
SEG = sorted(SEG, key=lambda s: seg_order.get(s["seg"],9))
seg_label = {"Enterprise":"Enterprise","Mid-market":"Mid-market (MM)","SMB":"SMB","Missing Segment":"Без сегмента"}
seg_class = {"Enterprise":"ent","Mid-market":"mm","SMB":"smb","Missing Segment":"none"}

managed_in_data = [p for p in P if p["gmv"] is not None]
managed_no_am = [p for p in managed_in_data if p["am"] == "—"]
core_ams = [a for a in AM if a["gmv"] > 100]
brynchak = next((a for a in AM if "Brynchak" in a["am"]), None)

# segment economics
def seg_get(name): return next(s for s in SEG if s["seg"]==name)
ent, mm, smb = seg_get("Enterprise"), seg_get("Mid-market"), seg_get("SMB")
gmv_per = lambda s: s["gmv"]/s["partners"] if s["partners"] else 0

today = datetime.date.today().strftime("%d.%m.%Y")

# ---------- segment overview rows ----------
seg_rows = ""
for s in SEG:
    seg_rows += f"""<tr>
      <td style="text-align:left"><span class="dot {seg_class[s['seg']]}"></span>{seg_label[s['seg']]}</td>
      <td>{num(s['partners'])}</td><td class="muted">{pct(s['partners'],T['partners'])}</td>
      <td>{num(s['stores'])}</td>
      <td><b>{eur(s['gmv'])}</b></td><td class="muted">{pct(s['gmv'],T['gmv'])}</td>
      <td>{eur(round(gmv_per(s)))}</td>
      <td>{eur(s['comm'])}</td>
    </tr>"""

# ---------- GMV vs partners concentration bars ----------
def bar_block(s, total, color):
    w = s/total*100 if total else 0
    return f'<div class="barfill {color}" style="width:{w:.1f}%"></div>'

conc_rows = ""
for s in SEG:
    if s["seg"]=="Missing Segment": continue
    conc_rows += f"""<div class="conc-row">
      <div class="conc-name"><span class="dot {seg_class[s['seg']]}"></span>{seg_label[s['seg']]}</div>
      <div class="conc-bars">
        <div class="conc-line"><span class="conc-lab">Партнери {pct(s['partners'],T['partners'])}</span><div class="bartrack">{bar_block(s['partners'],T['partners'],'c-part')}</div><span class="conc-val">{num(s['partners'])}</span></div>
        <div class="conc-line"><span class="conc-lab">GMV {pct(s['gmv'],T['gmv'])}</span><div class="bartrack">{bar_block(s['gmv'],T['gmv'],'c-gmv')}</div><span class="conc-val">{eur(s['gmv'])}</span></div>
      </div>
    </div>"""

# ---------- managed partners table ----------
part_rows = ""
maxg = max((p["gmv"] or 0) for p in P) or 1
for p in P:
    inv = p["gmv"] is None
    am = p["am"]
    am_html = f'<span class="no-am">не закріплено</span>' if am=="—" else am
    if inv:
        am_html = '<span class="ext">централізовано (KAM)</span>'
    gmv_bar = "" if inv else f'<div class="minibar"><div style="width:{(p["gmv"]/maxg*100):.0f}%"></div></div>'
    part_rows += f"""<tr>
      <td style="text-align:left"><b>{p['name']}</b></td>
      <td><span class="seg-pill {seg_class.get(p['seg'],'none')}">{seg_label.get(p['seg'],p['seg'])}</span></td>
      <td>{num(p['stores'])}</td>
      <td>{num(p['active']) if p['active'] is not None else '—'}</td>
      <td style="text-align:left">{eur(p['gmv'])}{gmv_bar}</td>
      <td>{num(p['orders'])}</td>
      <td>{eur(p['comm'])}</td>
      <td style="text-align:left;font-size:12px">{am_html}</td>
    </tr>"""

# ---------- AM workload ----------
am_rows = ""
max_am_gmv = max(a["gmv"] for a in AM) or 1
max_am_st = max(a["stores"] for a in AM) or 1
for a in AM:
    if a["gmv"]<=100 and a["stores"]<=3: continue
    am_rows += f"""<tr>
      <td style="text-align:left"><b>{a['am']}</b></td>
      <td>{num(a['partners'])}</td>
      <td style="text-align:left">{num(a['stores'])}<div class="minibar st"><div style="width:{a['stores']/max_am_st*100:.0f}%"></div></div></td>
      <td>{num(a['active'])}</td>
      <td style="text-align:left"><b>{eur(a['gmv'])}</b><div class="minibar"><div style="width:{a['gmv']/max_am_gmv*100:.0f}%"></div></div></td>
      <td class="muted">{pct(a['gmv'],T['gmv'])}</td>
      <td>{num(a['orders'])}</td>
      <td>{eur(a['comm'])}</td>
    </tr>"""

bryn_gmv_share = pct(brynchak["gmv"], T["gmv"]) if brynchak else "—"
bryn_st_share = pct(brynchak["stores"], T["assigned_stores"]) if brynchak else "—"

HTML = f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Покриття та сегментація партнерського портфеля</title>
<style>
:root{{
  --bg:#eef1f7; --panel:#ffffff; --panel2:#f6f8fc; --line:#dfe5ee;
  --text:#13203a; --muted:#5d6b85; --soft:#33425d;
  --accent:#2563eb; --accent2:#0e7faa;
  --ent:#7c3aed; --mm:#0e7faa; --smb:#ea580c; --none:#94a3b8;
  --crit:#dc2626; --high:#ea580c; --good:#15a34a;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:radial-gradient(1200px 600px at 80% -10%,#16223e 0%,var(--bg) 55%);color:var(--text);line-height:1.55}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 20px 90px}}
section[id]{{scroll-margin-top:64px}}

nav.topnav{{position:sticky;top:0;z-index:50;background:rgba(10,16,30,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}}
nav.topnav .inner{{max-width:1180px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
nav.topnav .brand{{font-weight:800;font-size:13px;color:var(--accent2);margin-right:8px;white-space:nowrap}}
nav.topnav a{{color:#aab6cd;text-decoration:none;font-size:13px;padding:6px 11px;border-radius:8px;border:1px solid transparent;white-space:nowrap}}
nav.topnav a:hover{{background:#13203a;border-color:#243150;color:#fff}}

header.hero{{padding:34px 30px;border:1px solid var(--line);border-radius:18px;
  background:linear-gradient(135deg,#16233f 0%,#0e1830 100%);position:relative;overflow:hidden;color:#fff}}
.hero .tag{{display:inline-block;margin-bottom:12px;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#5bb4d6;font-weight:700}}
.hero h1{{margin:0 0 8px;font-size:27px;letter-spacing:.2px}}
.hero .sub{{color:#c3cee0;font-size:15px;max-width:820px}}
.meta{{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}}
.meta .pill{{background:#0d1730;border:1px solid #243150;border-radius:999px;padding:6px 13px;font-size:12.5px;color:#c3cee0}}

h2.section{{font-size:20px;margin:46px 0 6px;display:flex;align-items:center;gap:10px}}
h2.section .bar{{width:6px;height:22px;border-radius:3px;background:var(--accent)}}
.section-desc{{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:880px}}

.grid{{display:grid;gap:14px}}
.kpis{{grid-template-columns:repeat(4,1fr);margin-top:22px}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 17px}}
.kpi .n{{font-size:25px;font-weight:800;letter-spacing:-.3px}}
.kpi .l{{color:var(--muted);font-size:12.5px;margin-top:3px}}
.kpi.crit .n{{color:var(--crit)}} .kpi.high .n{{color:var(--high)}} .kpi.good .n{{color:var(--good)}} .kpi.ent .n{{color:var(--ent)}}

.callout{{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;padding:18px 20px;margin-top:20px}}
.callout.warn{{border-left-color:var(--crit)}}
.callout h3{{margin:0 0 10px;font-size:16px}}
.callout ul{{margin:6px 0 0;padding-left:18px;color:var(--soft);font-size:14.5px}}
.callout li{{margin:7px 0}}
.callout b{{color:var(--text)}}

.card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin-top:18px;overflow:hidden}}
.card .top{{padding:14px 20px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#13203a,#101a30);color:#fff;font-weight:700;font-size:15px}}
.card .body{{padding:6px 8px}}

table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:10px 11px;text-align:center;border-bottom:1px solid var(--line)}}
th{{background:var(--panel2);color:var(--soft);font-weight:700;font-size:11.5px;text-transform:uppercase;letter-spacing:.3px;position:sticky;top:0}}
tbody tr:hover{{background:#f3f7ff}}
td.muted,.muted{{color:var(--muted)}}
.tablewrap{{overflow-x:auto}}

.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;vertical-align:middle}}
.dot.ent{{background:var(--ent)}} .dot.mm{{background:var(--mm)}} .dot.smb{{background:var(--smb)}} .dot.none{{background:var(--none)}}
.seg-pill{{font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;color:#fff;white-space:nowrap}}
.seg-pill.ent{{background:var(--ent)}} .seg-pill.mm{{background:var(--mm)}} .seg-pill.smb{{background:var(--smb)}} .seg-pill.none{{background:var(--none)}}
.no-am{{color:var(--crit);font-weight:700}}
.ext{{color:var(--ent);font-weight:700}}

.minibar{{height:5px;background:#eef1f7;border-radius:3px;margin-top:5px;overflow:hidden}}
.minibar div{{height:100%;background:var(--accent);border-radius:3px}}
.minibar.st div{{background:var(--mm)}}

.conc{{margin-top:8px}}
.conc-row{{display:grid;grid-template-columns:150px 1fr;gap:14px;padding:14px 4px;border-bottom:1px solid var(--line)}}
.conc-name{{font-weight:700;font-size:14px;align-self:center}}
.conc-line{{display:flex;align-items:center;gap:10px;margin:5px 0}}
.conc-lab{{width:130px;font-size:12px;color:var(--muted);text-align:right}}
.bartrack{{flex:1;height:14px;background:#eef1f7;border-radius:7px;overflow:hidden}}
.barfill{{height:100%;border-radius:7px}}
.barfill.c-part{{background:var(--none)}} .barfill.c-gmv{{background:var(--accent)}}
.conc-val{{width:90px;font-size:12.5px;font-weight:700;text-align:right}}

.split{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:18px}}
@media(max-width:820px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.split{{grid-template-columns:1fr}}.conc-row{{grid-template-columns:1fr}}}}

.foot{{margin-top:50px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);padding-top:16px}}
.note{{font-size:12px;color:var(--muted);margin-top:8px}}
</style>
</head>
<body>
<nav class="topnav"><div class="inner">
  <span class="brand">ПАРТНЕРСЬКИЙ ПОРТФЕЛЬ</span>
  <a href="#overview">Огляд</a>
  <a href="#segments">Сегменти</a>
  <a href="#economics">Економіка</a>
  <a href="#coverage">Що ведемо</a>
  <a href="#capacity">Навантаження</a>
  <a href="#verdict">Висновки</a>
</div></nav>

<div class="wrap">
<header class="hero">
  <span class="tag">Внутрішній аналіз · для керівництва</span>
  <h1>Покриття та сегментація партнерського портфеля</h1>
  <p class="sub">Скільки в нас партнерів, як вони діляться за сегментами, обігом і прибутковістю, який обсяг команда веде сьогодні — і чому немає капасіті брати нових партнерів, особливо в сегментах SMB та Mid-market.</p>
  <div class="meta">
    <span class="pill">Для: команда · директор · директор з продажів</span>
    <span class="pill">Партнерів у портфелі: {num(T['partners'])}</span>
    <span class="pill">Локацій: {num(T['providers'])}</span>
    <span class="pill">GMV: {eur(T['gmv'])}</span>
    <span class="pill">Станом на {today}</span>
  </div>
</header>

<div class="callout warn">
  <h3>Головне за 30 секунд</h3>
  <ul>
    <li><b>Портфель:</b> {num(T['partners'])} партнерів / {num(T['providers'])} локацій / {eur(T['gmv'])} GMV. Структура — гостра піраміда: <b>Enterprise + MM = {pct(ent['partners']+mm['partners'],T['partners'])} партнерів, але {pct(ent['gmv']+mm['gmv'],T['gmv'])} GMV</b>.</li>
    <li><b>SMB — це довгий хвіст:</b> {num(smb['partners'])} партнерів ({pct(smb['partners'],T['partners'])} усіх) дають лише {pct(smb['gmv'],T['gmv'])} GMV. Середній SMB-партнер = {eur(round(gmv_per(smb)))} проти {eur(round(gmv_per(ent)))} у Enterprise — різниця у ~{round(gmv_per(ent)/gmv_per(smb))}×.</li>
    <li><b>Ми активно ведемо {MT['partners']} ключових партнерів</b> — це {pct(MT['gmv'],T['gmv'])} усього GMV портфеля. Тобто фокус команди вже стоїть на тому, що приносить гроші.</li>
    <li><b>Навантаження критично нерівномірне:</b> 1 менеджер веде {num(brynchak['stores'])} локацій = {bryn_gmv_share} GMV портфеля. Водночас <b>{num(T['unassigned_stores'])} локацій ({pct(T['unassigned_stores'],T['providers'])}) взагалі не мають закріпленого AM</b>.</li>
    <li><b>Висновок:</b> капасіті брати нових партнерів немає. Кожен новий SMB/MM забирає той самий ресурс, що й Enterprise, але приносить у рази менше. Пріоритет — утримання та розвиток наявних топ-партнерів, а не нарощування кількості.</li>
  </ul>
</div>

<!-- ================= OVERVIEW ================= -->
<section id="overview">
<h2 class="section"><span class="bar"></span>1. Загальна картина</h2>
<p class="section-desc">Верхньорівневі цифри портфеля. «Партнер» = бренд/мережа, «локація» = окрема торгова точка (магазин/заклад).</p>
<div class="grid kpis">
  <div class="kpi"><div class="n">{num(T['partners'])}</div><div class="l">Партнерів (брендів/мереж)</div></div>
  <div class="kpi"><div class="n">{num(T['providers'])}</div><div class="l">Локацій усього</div></div>
  <div class="kpi good"><div class="n">{num(T['active'])}</div><div class="l">Активних локацій</div></div>
  <div class="kpi"><div class="n">{num(T['onboarding'])}</div><div class="l">На онбордингу</div></div>
  <div class="kpi"><div class="n">{eur(T['gmv'])}</div><div class="l">GMV (товарообіг)</div></div>
  <div class="kpi"><div class="n">{eur(T['comm'])}</div><div class="l">Комісія Bolt</div></div>
  <div class="kpi"><div class="n">{num(T['orders'])}</div><div class="l">Замовлень доставлено</div></div>
  <div class="kpi"><div class="n">{num(T['am_count'])}</div><div class="l">Менеджерів (AM) у даних</div></div>
</div>
</section>

<!-- ================= SEGMENTS ================= -->
<section id="segments">
<h2 class="section"><span class="bar"></span>2. Розбивка за сегментами</h2>
<p class="section-desc">Партнери діляться на Enterprise, Mid-market (MM) та SMB. Нижче — скільки партнерів і локацій у кожному, який обіг (GMV), яка частка та середній обіг на партнера.</p>
<div class="card">
  <div class="top">Портфель за сегментами</div>
  <div class="body tablewrap">
  <table>
    <thead><tr><th style="text-align:left">Сегмент</th><th>Партнерів</th><th>% партн.</th><th>Локацій</th><th>GMV</th><th>% GMV</th><th>GMV / партнер</th><th>Комісія</th></tr></thead>
    <tbody>{seg_rows}
      <tr style="background:#f3f7ff;font-weight:800"><td style="text-align:left">Разом</td><td>{num(T['partners'])}</td><td>100%</td><td>{num(T['providers'])}</td><td>{eur(T['gmv'])}</td><td>100%</td><td>{eur(round(T['gmv']/T['partners']))}</td><td>{eur(T['comm'])}</td></tr>
    </tbody>
  </table>
  </div>
</div>

<div class="card">
  <div class="top">Концентрація: де партнери, а де гроші</div>
  <div class="body" style="padding:6px 18px 14px">
    <div class="conc">{conc_rows}</div>
    <p class="note">Сіра смуга — частка партнерів, синя — частка GMV. Видно «перевернуту піраміду»: у SMB багато партнерів, але мало обігу; у Enterprise навпаки.</p>
  </div>
</div>
</section>

<!-- ================= ECONOMICS ================= -->
<section id="economics">
<h2 class="section"><span class="bar"></span>3. Економіка сегментів: цінність vs зусилля</h2>
<p class="section-desc">Ключове для рішення про капасіті: ведення одного партнера коштує приблизно однаково зусиль незалежно від сегмента, а от віддача — різна на порядок.</p>
<div class="grid kpis">
  <div class="kpi ent"><div class="n">{eur(round(gmv_per(ent)))}</div><div class="l">Сер. GMV на Enterprise-партнера</div></div>
  <div class="kpi"><div class="n">{eur(round(gmv_per(mm)))}</div><div class="l">Сер. GMV на MM-партнера</div></div>
  <div class="kpi high"><div class="n">{eur(round(gmv_per(smb)))}</div><div class="l">Сер. GMV на SMB-партнера</div></div>
  <div class="kpi crit"><div class="n">~{round(gmv_per(ent)/gmv_per(smb))}×</div><div class="l">Enterprise цінніший за SMB</div></div>
</div>
<div class="callout">
  <h3>Як це читати</h3>
  <ul>
    <li>Щоб «закрити» один Enterprise-партнер, менеджер працює з {eur(round(gmv_per(ent)))} обігу. За ті ж зусилля у SMB він отримує {eur(round(gmv_per(smb)))}.</li>
    <li>SMB — це {pct(smb['partners'],T['partners'])} усіх партнерів, але лише {pct(smb['gmv'],T['gmv'])} GMV і {pct(smb['comm'],T['comm'])} комісії. Це найдорожчий у обслуговуванні і найменш віддачний сегмент.</li>
    <li>Тому будь-яке нарощування кількості саме в SMB/MM розмиває фокус і ресурс, які зараз тримають {pct(ent['gmv']+mm['gmv'],T['gmv'])} GMV.</li>
  </ul>
</div>
</section>

<!-- ================= COVERAGE ================= -->
<section id="coverage">
<h2 class="section"><span class="bar"></span>4. Що ми покриваємо сьогодні</h2>
<p class="section-desc">Команда активно веде {MT['partners']} ключових партнерів. З них {MT['in_data']} присутні в цьому датасеті, а {MT['external']} великих мереж (ATB, ROZETKA, VARUS, FORA та ін.) ведуться централізовано як key accounts. Разом наш портфель ведення = {pct(MT['gmv'],T['gmv'])} GMV.</p>
<div class="grid kpis">
  <div class="kpi"><div class="n">{MT['partners']}</div><div class="l">Партнерів під веденням</div></div>
  <div class="kpi good"><div class="n">{pct(MT['gmv'],T['gmv'])}</div><div class="l">Частка GMV портфеля</div></div>
  <div class="kpi"><div class="n">{eur(MT['gmv'])}</div><div class="l">GMV під веденням</div></div>
  <div class="kpi crit"><div class="n">{len(managed_no_am)}</div><div class="l">З них без закріпленого AM</div></div>
</div>
<div class="card">
  <div class="top">Наші партнери ({len(P)}) — за обігом</div>
  <div class="body tablewrap">
  <table>
    <thead><tr><th style="text-align:left">Партнер</th><th>Сегмент</th><th>Локацій</th><th>Активних</th><th style="text-align:left">GMV</th><th>Замовлень</th><th>Комісія</th><th style="text-align:left">Менеджер</th></tr></thead>
    <tbody>{part_rows}</tbody>
  </table>
  </div>
</div>
<p class="note">Червоне «не закріплено» — партнер у нашому списку ведення, але без призначеного AM у системі (де-факто ведеться без формального ресурсу). Це вже ознака перевантаження.</p>
</section>

<!-- ================= CAPACITY ================= -->
<section id="capacity">
<h2 class="section"><span class="bar"></span>5. Навантаження на менеджерів</h2>
<p class="section-desc">Розподіл портфеля між AM. Видно, що навантаження вкрай нерівномірне і вже на межі.</p>
<div class="grid kpis">
  <div class="kpi"><div class="n">{len(core_ams)}</div><div class="l">Продуктивних AM</div></div>
  <div class="kpi"><div class="n">{num(T['assigned_stores'])}</div><div class="l">Закріплених локацій</div></div>
  <div class="kpi crit"><div class="n">{num(T['unassigned_stores'])}</div><div class="l">Локацій БЕЗ менеджера ({pct(T['unassigned_stores'],T['providers'])})</div></div>
  <div class="kpi high"><div class="n">{bryn_gmv_share}</div><div class="l">GMV на 1 менеджері (Brynchak)</div></div>
</div>
<div class="card">
  <div class="top">Портфель по менеджерах</div>
  <div class="body tablewrap">
  <table>
    <thead><tr><th style="text-align:left">Менеджер</th><th>Партнерів</th><th style="text-align:left">Локацій</th><th>Активних</th><th style="text-align:left">GMV</th><th>% GMV</th><th>Замовлень</th><th>Комісія</th></tr></thead>
    <tbody>{am_rows}
      <tr style="background:#fff4f4;font-weight:800"><td style="text-align:left">Без менеджера</td><td>{num(T['unassigned_partners'])}</td><td style="text-align:left">{num(T['unassigned_stores'])}</td><td>—</td><td style="text-align:left">{eur(T['unassigned_gmv'])}</td><td>{pct(T['unassigned_gmv'],T['gmv'])}</td><td>—</td><td>—</td></tr>
    </tbody>
  </table>
  </div>
</div>
<p class="note">Один менеджер (M. Brynchak) тримає {num(brynchak['stores'])} локацій ({bryn_st_share} усіх закріплених) і {bryn_gmv_share} GMV портфеля. Це точка ризику: вихід/перевантаження однієї людини = ризик для половини обігу.</p>
</section>

<!-- ================= VERDICT ================= -->
<section id="verdict">
<h2 class="section"><span class="bar"></span>6. Висновок: чому немає капасіті брати нових партнерів</h2>
<div class="callout warn">
  <h3>Аргументація</h3>
  <ul>
    <li><b>1. Команда вже перевантажена.</b> {len(core_ams)} продуктивних AM ведуть {num(T['assigned_stores'])} локацій, при цьому {num(T['unassigned_stores'])} локацій ({pct(T['unassigned_stores'],T['providers'])}) залишаються без жодного менеджера. Ми не закриваємо навіть наявний портфель.</li>
    <li><b>2. Концентрація ризику.</b> Один менеджер тримає {bryn_gmv_share} GMV. Додавання нових партнерів без нових людей лише поглибить цей перекіс.</li>
    <li><b>3. Економіка проти SMB/MM.</b> Новий SMB-партнер приносить у середньому {eur(round(gmv_per(smb)))} GMV, але вимагає такого ж онбордингу, навчання та супроводу, як Enterprise з {eur(round(gmv_per(ent)))}. Зусилля однакові — віддача в ~{round(gmv_per(ent)/gmv_per(smb))} разів менша.</li>
    <li><b>4. Фокус на цінності.</b> Наші {MT['partners']} веденими партнерами вже покривають {pct(MT['gmv'],T['gmv'])} GMV. Ресурс правильно стоїть на грошах; розпорошення на дрібний SMB/MM послабить роботу з топ-партнерами.</li>
    <li><b>5. Хвіст не масштабується руками.</b> {num(smb['partners'])} SMB-партнерів фізично неможливо вести персонально наявною командою — це задача для самообслуговування/автоматизації, а не для AM.</li>
  </ul>
</div>
<div class="callout">
  <h3>Що пропонуємо замість «брати ще»</h3>
  <ul>
    <li>Заморозити набір нових SMB/MM під персональне ведення до появи додаткового ресурсу.</li>
    <li>Спершу закрити {num(T['unassigned_stores'])} локацій без AM або перевести їх у self-serve.</li>
    <li>Розвантажити ключового менеджера — перерозподілити частину портфеля, щоб зняти ризик концентрації {bryn_gmv_share} GMV на одній людині.</li>
    <li>Нові партнери — лише точково в Enterprise/високий MM з обігом вище середнього по сегменту.</li>
    <li>SMB-хвіст вести через автоматизовані/групові процеси, а не індивідуально.</li>
  </ul>
</div>
</section>

<div class="foot">
  Джерело: Merchant-level Overview (Key Account dashboard, Bolt UA). Партнер = Group/Brand, локація = окремий provider. GMV — до знижок. Згенеровано {today}.
</div>
</div>
</body>
</html>"""

with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("index.html written:", len(HTML), "chars")
