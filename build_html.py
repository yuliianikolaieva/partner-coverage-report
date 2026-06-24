# -*- coding: utf-8 -*-
"""Генерує index.html для звіту 'Покриття та сегментація партнерського портфеля'."""
import json, os, datetime

HERE=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"data.json"),encoding="utf-8") as f: D=json.load(f)
T=D["totals"]; SEG=D["seg_overview"]; P=D["partners"]; MT=D["managed_totals"]
TEAM=D["team"]; FULL=D["full"]; GMVM=D["gmv_months"]; LOCM=D["loc_months"]

def eur(v):
    if v is None:return "—"
    return f"€{v:,.0f}".replace(","," ")
def num(v):
    if v is None:return "—"
    return f"{v:,.0f}".replace(","," ")
def pct(p,w,d=1):
    if not w:return "0%"
    return f"{p/w*100:.{d}f}%"

seg_order={"Enterprise":0,"Mid-market":1,"SMB":2,"Missing Segment":3}
SEG=sorted(SEG,key=lambda s:seg_order.get(s["seg"],9))
seg_label={"Enterprise":"Enterprise","Mid-market":"Mid-market (MM)","SMB":"SMB","Missing Segment":"Без сегмента"}
seg_short={"Enterprise":"ENT","Mid-market":"MM","SMB":"SMB","Missing Segment":"—"}
seg_class={"Enterprise":"ent","Mid-market":"mm","SMB":"smb","Missing Segment":"none"}
def sg(n): return next(s for s in SEG if s["seg"]==n)
ent,mm,smb=sg("Enterprise"),sg("Mid-market"),sg("SMB")
gmv_per=lambda s:s["gmv"]/s["partners"] if s["partners"] else 0
today=datetime.date.today().strftime("%d.%m.%Y")
bryn=next(t for t in TEAM if "Brynchak" in t["am"])
ml={"2026-01":"січ","2026-02":"лют","2026-03":"бер","2026-04":"кві","2026-05":"тра"}

def spark(series,months,color):
    if not series or sum(series)==0: return '<span class="muted" style="font-size:11px">—</span>'
    w,h,pad=78,22,2
    lo,hi=min(series),max(series)
    rng=(hi-lo) or 1
    n=len(series)
    pts=[]
    for i,v in enumerate(series):
        x=pad+(w-2*pad)*(i/(n-1) if n>1 else 0)
        y=pad+(h-2*pad)*(1-(v-lo)/rng)
        pts.append(f"{x:.1f},{y:.1f}")
    poly=" ".join(pts)
    lx,ly=pts[-1].split(",")
    tip=" · ".join(f"{ml.get(m,m)}: {v:,.0f}".replace(","," ") for m,v in zip(months,series))
    # trend % first nonzero -> last
    fnz=next((v for v in series if v>0),0)
    last=series[-1]
    if fnz>0:
        d=(last-fnz)/fnz*100
        arr="▲" if d>2 else ("▼" if d<-2 else "▬")
        cl="up" if d>2 else ("down" if d<-2 else "flat")
        badge=f'<span class="tr {cl}">{arr}{abs(d):.0f}%</span>'
    else:
        badge=""
    return (f'<span class="spark" title="{tip}">'
            f'<svg width="{w}" height="{h}">'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="1.6"/>'
            f'<circle cx="{lx}" cy="{ly}" r="2" fill="{color}"/></svg>{badge}</span>')

# ---------- segment overview rows ----------
seg_rows=""
for s in SEG:
    seg_rows+=f"""<tr><td style="text-align:left"><span class="dot {seg_class[s['seg']]}"></span>{seg_label[s['seg']]}</td>
      <td>{num(s['partners'])}</td><td class="muted">{pct(s['partners'],T['partners'])}</td>
      <td>{num(s['stores'])}</td><td><b>{eur(s['gmv'])}</b></td><td class="muted">{pct(s['gmv'],T['gmv'])}</td>
      <td>{eur(round(gmv_per(s)))}</td><td>{eur(s['comm'])}</td><td><b>{eur(s['comm_per'])}</b></td></tr>"""

# ---------- concentration ----------
def barb(v,tot,c): 
    w=v/tot*100 if tot else 0
    return f'<div class="barfill {c}" style="width:{w:.1f}%"></div>'
conc_rows=""
for s in SEG:
    if s["seg"]=="Missing Segment":continue
    conc_rows+=f"""<div class="conc-row"><div class="conc-name"><span class="dot {seg_class[s['seg']]}"></span>{seg_label[s['seg']]}</div>
      <div class="conc-bars"><div class="conc-line"><span class="conc-lab">Партнери {pct(s['partners'],T['partners'])}</span><div class="bartrack">{barb(s['partners'],T['partners'],'c-part')}</div><span class="conc-val">{num(s['partners'])}</span></div>
      <div class="conc-line"><span class="conc-lab">GMV {pct(s['gmv'],T['gmv'])}</span><div class="bartrack">{barb(s['gmv'],T['gmv'],'c-gmv')}</div><span class="conc-val">{eur(s['gmv'])}</span></div></div></div>"""

# ---------- managed partners table ----------
maxg=max((p["gmv"] or 0) for p in P) or 1
part_rows=""
for p in P:
    inv=p["gmv"] is None
    gbar="" if inv else f'<div class="minibar"><div style="width:{(p["gmv"]/maxg*100):.0f}%"></div></div>'
    am=f'<span class="ext">{p["am"]} · централізовано</span>' if inv else p["am"]
    part_rows+=f"""<tr><td style="text-align:left"><b>{p['name']}</b></td>
      <td><span class="seg-pill {seg_class.get(p['seg'],'none')}">{seg_short.get(p['seg'],p['seg'])}</span></td>
      <td>{num(p['stores'])}</td><td style="text-align:left">{eur(p['gmv'])}{gbar}</td>
      <td>{num(p['orders'])}</td><td>{eur(p['comm'])}</td>
      <td style="text-align:left;font-size:12px">{am}</td></tr>"""

# ---------- team table ----------
team_rows=""
max_tg=max(t["gmv"] for t in TEAM) or 1
for t in TEAM:
    ext=f' <span class="muted">(+{t["external"]} зовн. мереж)</span>' if t["external"] else ""
    team_rows+=f"""<tr><td style="text-align:left"><b>{t['am']}</b>{ext}</td>
      <td>{t['partners']}</td><td style="text-align:left">{num(t['stores'])}</td>
      <td style="text-align:left"><b>{eur(t['gmv'])}</b><div class="minibar"><div style="width:{t['gmv']/max_tg*100:.0f}%"></div></div></td>
      <td class="muted">{pct(t['gmv'],T['gmv'])}</td><td>{num(t['orders'])}</td><td>{eur(t['comm'])}</td></tr>"""

# ---------- full list collapsible ----------
def full_table(seg):
    rows=[p for p in FULL if p["seg"]==seg]
    rows=sorted(rows,key=lambda x:-x["gmv"])
    sgmv=sum(r["gmv"] for r in rows); sst=sum(r["stores"] for r in rows)
    body=""
    for r in rows:
        body+=f"""<tr><td style="text-align:left">{r['name']}</td>
          <td>{num(r['stores'])}</td><td>{num(r['active'])}</td>
          <td style="text-align:left">{eur(r['gmv'])}</td><td>{num(r['orders'])}</td><td>{eur(r['comm'])}</td>
          <td style="text-align:left">{spark(r['gmv_trend'],GMVM,'#2563eb')}</td>
          <td style="text-align:left">{spark(r['loc_trend'],LOCM,'#0e7faa')}</td></tr>"""
    opn=" open" if seg=="Enterprise" else ""
    return f"""<details class="seg-acc"{opn}><summary><span class="dot {seg_class[seg]}"></span><b>{seg_label[seg]}</b> · {len(rows)} партнерів · {eur(sgmv)} GMV · {num(sst)} локацій <span class="chev">▾</span></summary>
    <div class="tablewrap"><table class="full"><thead><tr><th style="text-align:left">Партнер</th><th>Локацій</th><th>Активних</th><th style="text-align:left">GMV</th><th>Замовл.</th><th>Комісія</th><th style="text-align:left">GMV тренд (січ–кві)</th><th style="text-align:left">Локації (січ–тра)</th></tr></thead><tbody>{body}</tbody></table></div></details>"""

full_sections="".join(full_table(s) for s in ["Enterprise","Mid-market","SMB","Missing Segment"])

HTML=f"""<!DOCTYPE html>
<html lang="uk"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Покриття та сегментація партнерського портфеля</title>
<style>
:root{{--bg:#eef1f7;--panel:#fff;--panel2:#f6f8fc;--line:#dfe5ee;--text:#13203a;--muted:#5d6b85;--soft:#33425d;
--accent:#2563eb;--accent2:#0e7faa;--ent:#7c3aed;--mm:#0e7faa;--smb:#ea580c;--none:#94a3b8;--crit:#dc2626;--high:#ea580c;--good:#15a34a;}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:radial-gradient(1200px 600px at 80% -10%,#16223e 0%,var(--bg) 55%);color:var(--text);line-height:1.55}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 20px 90px}} section[id]{{scroll-margin-top:64px}}
nav.topnav{{position:sticky;top:0;z-index:50;background:rgba(10,16,30,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}}
nav.topnav .inner{{max-width:1180px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
nav.topnav .brand{{font-weight:800;font-size:13px;color:var(--accent2);margin-right:8px}}
nav.topnav a{{color:#aab6cd;text-decoration:none;font-size:13px;padding:6px 11px;border-radius:8px;border:1px solid transparent;white-space:nowrap}}
nav.topnav a:hover{{background:#13203a;border-color:#243150;color:#fff}}
header.hero{{padding:34px 30px;border:1px solid var(--line);border-radius:18px;background:linear-gradient(135deg,#16233f,#0e1830);overflow:hidden;color:#fff}}
.hero .tag{{display:inline-block;margin-bottom:12px;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#5bb4d6;font-weight:700}}
.hero h1{{margin:0 0 8px;font-size:27px}} .hero .sub{{color:#c3cee0;font-size:15px;max-width:820px}}
.meta{{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}}
.meta .pill{{background:#0d1730;border:1px solid #243150;border-radius:999px;padding:6px 13px;font-size:12.5px;color:#c3cee0}}
h2.section{{font-size:20px;margin:46px 0 6px;display:flex;align-items:center;gap:10px}}
h2.section .bar{{width:6px;height:22px;border-radius:3px;background:var(--accent)}}
.section-desc{{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:900px}}
.grid{{display:grid;gap:14px}} .kpis{{grid-template-columns:repeat(4,1fr);margin-top:22px}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 17px}}
.kpi .n{{font-size:25px;font-weight:800;letter-spacing:-.3px}} .kpi .l{{color:var(--muted);font-size:12.5px;margin-top:3px}}
.kpi.crit .n{{color:var(--crit)}} .kpi.high .n{{color:var(--high)}} .kpi.good .n{{color:var(--good)}} .kpi.ent .n{{color:var(--ent)}}
.callout{{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;padding:18px 20px;margin-top:20px}}
.callout.warn{{border-left-color:var(--crit)}} .callout h3{{margin:0 0 10px;font-size:16px}}
.callout ul{{margin:6px 0 0;padding-left:18px;color:var(--soft);font-size:14.5px}} .callout li{{margin:7px 0}} .callout b{{color:var(--text)}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin-top:18px;overflow:hidden}}
.card .top{{padding:14px 20px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#13203a,#101a30);color:#fff;font-weight:700;font-size:15px}}
.card .body{{padding:6px 8px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:10px 11px;text-align:center;border-bottom:1px solid var(--line)}}
th{{background:var(--panel2);color:var(--soft);font-weight:700;font-size:11.5px;text-transform:uppercase;letter-spacing:.3px}}
tbody tr:hover{{background:#f3f7ff}} td.muted,.muted{{color:var(--muted)}} .tablewrap{{overflow-x:auto}}
table.full td,table.full th{{padding:7px 10px;font-size:12.5px}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;vertical-align:middle}}
.dot.ent{{background:var(--ent)}} .dot.mm{{background:var(--mm)}} .dot.smb{{background:var(--smb)}} .dot.none{{background:var(--none)}}
.seg-pill{{font-size:10.5px;font-weight:800;padding:3px 8px;border-radius:999px;color:#fff}}
.seg-pill.ent{{background:var(--ent)}} .seg-pill.mm{{background:var(--mm)}} .seg-pill.smb{{background:var(--smb)}} .seg-pill.none{{background:var(--none)}}
.ext{{color:var(--ent);font-weight:700}}
.minibar{{height:5px;background:#eef1f7;border-radius:3px;margin-top:5px;overflow:hidden}} .minibar div{{height:100%;background:var(--accent);border-radius:3px}}
.conc-row{{display:grid;grid-template-columns:150px 1fr;gap:14px;padding:14px 4px;border-bottom:1px solid var(--line)}}
.conc-name{{font-weight:700;font-size:14px;align-self:center}} .conc-line{{display:flex;align-items:center;gap:10px;margin:5px 0}}
.conc-lab{{width:130px;font-size:12px;color:var(--muted);text-align:right}} .bartrack{{flex:1;height:14px;background:#eef1f7;border-radius:7px;overflow:hidden}}
.barfill{{height:100%;border-radius:7px}} .barfill.c-part{{background:var(--none)}} .barfill.c-gmv{{background:var(--accent)}} .conc-val{{width:90px;font-size:12.5px;font-weight:700;text-align:right}}
.spark{{display:inline-flex;align-items:center;gap:6px}} .spark svg{{vertical-align:middle}}
.tr{{font-size:11px;font-weight:800}} .tr.up{{color:var(--good)}} .tr.down{{color:var(--crit)}} .tr.flat{{color:var(--muted)}}
details.seg-acc{{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin-top:14px;overflow:hidden}}
details.seg-acc summary{{cursor:pointer;list-style:none;padding:14px 18px;font-size:14px;background:var(--panel2);display:flex;align-items:center;gap:8px}}
details.seg-acc summary::-webkit-details-marker{{display:none}}
details.seg-acc .chev{{margin-left:auto;color:var(--muted);transition:transform .2s}} details.seg-acc[open] .chev{{transform:rotate(180deg)}}
.note{{font-size:12px;color:var(--muted);margin-top:8px}}
.foot{{margin-top:50px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);padding-top:16px}}
@media(max-width:820px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.conc-row{{grid-template-columns:1fr}}}}
</style></head><body>
<nav class="topnav"><div class="inner"><span class="brand">ПАРТНЕРСЬКИЙ ПОРТФЕЛЬ</span>
<a href="#overview">Огляд</a><a href="#segments">Сегменти</a><a href="#economics">Економіка</a>
<a href="#coverage">Що ведемо</a><a href="#team">Команда</a><a href="#fulllist">Усі партнери</a><a href="#verdict">Висновки</a></div></nav>
<div class="wrap">
<header class="hero"><span class="tag">Внутрішній аналіз · для керівництва</span>
<h1>Покриття та сегментація партнерського портфеля</h1>
<p class="sub">Скільки в нас партнерів, як вони діляться за сегментами, обігом і прибутковістю, який обсяг команда веде сьогодні — і чому немає капасіті брати нових партнерів, особливо SMB та Mid-market.</p>
<div class="meta"><span class="pill">Для: команда · директор · директор з продажів</span>
<span class="pill">Партнерів: {num(T['partners'])}</span><span class="pill">Локацій: {num(T['providers'])}</span>
<span class="pill">GMV: {eur(T['gmv'])}</span><span class="pill">Станом на {today}</span></div></header>

<div class="callout warn"><h3>Головне за 30 секунд</h3><ul>
<li><b>Портфель:</b> {num(T['partners'])} партнерів / {num(T['providers'])} локацій / {eur(T['gmv'])} GMV. Структура — гостра піраміда: <b>Enterprise + MM = {pct(ent['partners']+mm['partners'],T['partners'])} партнерів, але {pct(ent['gmv']+mm['gmv'],T['gmv'])} GMV</b>.</li>
<li><b>SMB — довгий хвіст:</b> {num(smb['partners'])} партнерів ({pct(smb['partners'],T['partners'])}) дають лише {pct(smb['gmv'],T['gmv'])} GMV. Середній SMB = {eur(round(gmv_per(smb)))} GMV і всього {eur(smb['comm_per'])} комісії на партнера проти {eur(ent['comm_per'])} в Enterprise.</li>
<li><b>Ведемо {MT['partners']} ключових партнерів силами лише {MT['managers']} менеджерів</b> — це {pct(MT['gmv'],T['gmv'])} усього GMV портфеля.</li>
<li><b>Навантаження критично нерівномірне:</b> 1 менеджер (M. Brynchak) тримає {num(bryn['stores'])} локацій і {pct(bryn['gmv'],T['gmv'])} GMV портфеля. Плюс {num(T['unassigned_stores'])} локацій ({pct(T['unassigned_stores'],T['providers'])}) у портфелі взагалі без AM.</li>
<li><b>Висновок:</b> капасіті брати нових партнерів немає. Кожен новий SMB/MM забирає той самий ресурс, що й Enterprise, але приносить у рази менше.</li></ul></div>

<section id="overview"><h2 class="section"><span class="bar"></span>1. Загальна картина</h2>
<p class="section-desc">«Партнер» = бренд/мережа, «локація» = окрема торгова точка.</p>
<div class="grid kpis">
<div class="kpi"><div class="n">{num(T['partners'])}</div><div class="l">Партнерів</div></div>
<div class="kpi"><div class="n">{num(T['providers'])}</div><div class="l">Локацій усього</div></div>
<div class="kpi good"><div class="n">{num(T['active'])}</div><div class="l">Активних локацій</div></div>
<div class="kpi"><div class="n">{num(T['onboarding'])}</div><div class="l">На онбордингу</div></div>
<div class="kpi"><div class="n">{eur(T['gmv'])}</div><div class="l">GMV (товарообіг)</div></div>
<div class="kpi"><div class="n">{eur(T['comm'])}</div><div class="l">Комісія Bolt</div></div>
<div class="kpi"><div class="n">{num(T['orders'])}</div><div class="l">Замовлень доставлено</div></div>
<div class="kpi"><div class="n">{MT['managers']}</div><div class="l">Менеджери команди</div></div></div></section>

<section id="segments"><h2 class="section"><span class="bar"></span>2. Розбивка за сегментами</h2>
<p class="section-desc">Скільки партнерів і локацій у кожному сегменті, обіг (GMV), частка, середній обіг та комісія на партнера.</p>
<div class="card"><div class="top">Портфель за сегментами</div><div class="body tablewrap"><table>
<thead><tr><th style="text-align:left">Сегмент</th><th>Партнерів</th><th>% партн.</th><th>Локацій</th><th>GMV</th><th>% GMV</th><th>GMV / партнер</th><th>Комісія</th><th>Комісія / партнер</th></tr></thead>
<tbody>{seg_rows}<tr style="background:#f3f7ff;font-weight:800"><td style="text-align:left">Разом</td><td>{num(T['partners'])}</td><td>100%</td><td>{num(T['providers'])}</td><td>{eur(T['gmv'])}</td><td>100%</td><td>{eur(round(T['gmv']/T['partners']))}</td><td>{eur(T['comm'])}</td><td>{eur(round(T['comm']/T['partners']))}</td></tr></tbody></table></div></div>
<div class="card"><div class="top">Концентрація: де партнери, а де гроші</div><div class="body" style="padding:6px 18px 14px"><div class="conc">{conc_rows}</div>
<p class="note">Сіра смуга — частка партнерів, синя — частка GMV. «Перевернута піраміда»: у SMB багато партнерів, мало обігу.</p></div></div></section>

<section id="economics"><h2 class="section"><span class="bar"></span>3. Економіка сегментів: цінність vs зусилля</h2>
<p class="section-desc">Ведення одного партнера коштує приблизно однаково зусиль незалежно від сегмента, а віддача — різна на порядок.</p>
<div class="grid kpis">
<div class="kpi ent"><div class="n">{eur(round(gmv_per(ent)))}</div><div class="l">Сер. GMV на Enterprise-партнера</div></div>
<div class="kpi"><div class="n">{eur(round(gmv_per(mm)))}</div><div class="l">Сер. GMV на MM-партнера</div></div>
<div class="kpi high"><div class="n">{eur(round(gmv_per(smb)))}</div><div class="l">Сер. GMV на SMB-партнера</div></div>
<div class="kpi crit"><div class="n">~{round(gmv_per(ent)/gmv_per(smb))}×</div><div class="l">Enterprise цінніший за SMB</div></div></div>
<div class="callout"><h3>Як це читати</h3><ul>
<li>За ті ж зусилля Enterprise-партнер дає {eur(round(gmv_per(ent)))} обігу та {eur(ent['comm_per'])} комісії, а SMB — лише {eur(round(gmv_per(smb)))} обігу та {eur(smb['comm_per'])} комісії.</li>
<li>SMB — {pct(smb['partners'],T['partners'])} партнерів, але {pct(smb['gmv'],T['gmv'])} GMV і {pct(smb['comm'],T['comm'])} комісії. Найдорожчий і найменш віддачний сегмент.</li>
<li>Нарощування саме в SMB/MM розмиває ресурс, який зараз тримає {pct(ent['gmv']+mm['gmv'],T['gmv'])} GMV.</li></ul></div></section>

<section id="coverage"><h2 class="section"><span class="bar"></span>4. Що ми покриваємо сьогодні</h2>
<p class="section-desc">Команда веде {MT['partners']} ключових партнерів. {MT['in_data']} присутні в датасеті, {MT['external']} великих мереж (ATB, ROZETKA, VARUS, FORA, master zoo та ін.) ведуться централізовано. Разом — {pct(MT['gmv'],T['gmv'])} GMV портфеля.</p>
<div class="grid kpis">
<div class="kpi"><div class="n">{MT['partners']}</div><div class="l">Партнерів під веденням</div></div>
<div class="kpi good"><div class="n">{pct(MT['gmv'],T['gmv'])}</div><div class="l">Частка GMV портфеля</div></div>
<div class="kpi"><div class="n">{eur(MT['gmv'])}</div><div class="l">GMV під веденням</div></div>
<div class="kpi crit"><div class="n">{MT['managers']}</div><div class="l">Менеджери на весь обсяг</div></div></div>
<div class="card"><div class="top">Наші партнери ({len(P)}) — за обігом</div><div class="body tablewrap"><table>
<thead><tr><th style="text-align:left">Партнер</th><th>Сегмент</th><th>Локацій</th><th style="text-align:left">GMV</th><th>Замовлень</th><th>Комісія</th><th style="text-align:left">Менеджер</th></tr></thead>
<tbody>{part_rows}</tbody></table></div></div>
<p class="note">8 великих мереж позначено «централізовано» — вони ведуться як key accounts і відсутні в цьому датасеті (GMV рахується окремо).</p></section>

<section id="team"><h2 class="section"><span class="bar"></span>5. Команда та навантаження</h2>
<p class="section-desc">Увесь ключовий портфель тримають {MT['managers']} менеджери. Навантаження вкрай нерівномірне і вже на межі.</p>
<div class="grid kpis">
<div class="kpi"><div class="n">{MT['managers']}</div><div class="l">Менеджерів у команді</div></div>
<div class="kpi"><div class="n">{num(MT['stores'])}</div><div class="l">Локацій під веденням</div></div>
<div class="kpi high"><div class="n">{pct(bryn['gmv'],T['gmv'])}</div><div class="l">GMV на 1 менеджері (Brynchak)</div></div>
<div class="kpi crit"><div class="n">{num(T['unassigned_stores'])}</div><div class="l">Локацій у портфелі без AM</div></div></div>
<div class="card"><div class="top">Навантаження по менеджерах</div><div class="body tablewrap"><table>
<thead><tr><th style="text-align:left">Менеджер</th><th>Партнерів</th><th style="text-align:left">Локацій</th><th style="text-align:left">GMV</th><th>% GMV</th><th>Замовлень</th><th>Комісія</th></tr></thead>
<tbody>{team_rows}</tbody></table></div></div>
<p class="note">GMV/комісія рахуються за партнерами, що є в датасеті; зовнішні мережі (ATB, VARUS, ROZETKA, master zoo тощо) додають навантаження понад показане. Один менеджер тримає {pct(bryn['gmv'],T['gmv'])} GMV — це точка ризику концентрації.</p></section>

<section id="fulllist"><h2 class="section"><span class="bar"></span>6. Повний список партнерів</h2>
<p class="section-desc">Усі {num(T['partners'])} партнерів з ключовими даними, згруповані за сегментами (натисніть, щоб розгорнути). Колонки тренду: <b>GMV</b> — помісячно січень–квітень, <b>Локації</b> — кількість активних точок січень–травень. Наведіть на графік, щоб побачити значення; стрілка — зміна від першого до останнього місяця.</p>
{full_sections}
<p class="note">Тренд GMV доступний для відстежуваних у дашборді партнерів (січ–кві 2026); тренд локацій — із вивантаження активних магазинів (січ–тра 2026). «—» означає, що партнер не має історичних даних у відповідному джерелі.</p></section>

<section id="verdict"><h2 class="section"><span class="bar"></span>7. Висновок: чому немає капасіті брати нових партнерів</h2>
<div class="callout warn"><h3>Аргументація</h3><ul>
<li><b>1. Лише {MT['managers']} менеджери на весь ключовий портфель.</b> Вони ведуть {num(MT['stores'])} локацій ({MT['in_data']} партнерів + {MT['external']} великих мереж). Команда фізично на межі.</li>
<li><b>2. Концентрація ризику.</b> Один менеджер (M. Brynchak) тримає {pct(bryn['gmv'],T['gmv'])} GMV і {num(bryn['stores'])} локацій. Будь-які нові партнери без нових людей лише поглиблять перекіс.</li>
<li><b>3. Економіка проти SMB/MM.</b> Новий SMB-партнер приносить у середньому {eur(round(gmv_per(smb)))} GMV і {eur(smb['comm_per'])} комісії, але вимагає такого ж онбордингу й супроводу, як Enterprise з {eur(round(gmv_per(ent)))}. Зусилля однакові — віддача в ~{round(gmv_per(ent)/gmv_per(smb))}× менша.</li>
<li><b>4. Фокус на цінності.</b> {MT['partners']} веденими партнерами вже покрито {pct(MT['gmv'],T['gmv'])} GMV. Розпорошення на дрібний SMB/MM послабить роботу з топ-партнерами.</li>
<li><b>5. Хвіст не масштабується руками.</b> {num(smb['partners'])} SMB-партнерів неможливо вести персонально наявною командою — це задача для self-serve/автоматизації.</li></ul></div>
<div class="callout"><h3>Що пропонуємо замість «брати ще»</h3><ul>
<li>Заморозити набір нових SMB/MM під персональне ведення до появи додаткового ресурсу.</li>
<li>Спершу закрити {num(T['unassigned_stores'])} локацій без AM або перевести їх у self-serve.</li>
<li>Розвантажити ключового менеджера — зняти ризик концентрації {pct(bryn['gmv'],T['gmv'])} GMV на одній людині.</li>
<li>Нові партнери — лише точково в Enterprise/високий MM з обігом вище середнього по сегменту.</li>
<li>SMB-хвіст вести через автоматизовані/групові процеси, а не індивідуально.</li></ul></div></section>

<div class="foot">Джерела: Merchant-level Overview та Entity performance dynamics (Key Account dashboard), вивантаження активних магазинів (Active stores), Bolt UA. Партнер = Group/Brand, локація = окремий provider. GMV — до знижок. Згенеровано {today}.</div>
</div></body></html>"""

with open(os.path.join(HERE,"index.html"),"w",encoding="utf-8") as f: f.write(HTML)
print("index.html written:",len(HTML),"chars")
