# -*- coding: utf-8 -*-
"""Generate index.html (English) for 'Partner Portfolio Coverage & Segmentation'."""
import json, os, datetime
HERE=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(HERE,"data.json"),encoding="utf-8"))
T=D["totals"]; SEG=D["seg_overview"]; P=D["partners"]; MT=D["managed_totals"]
TEAM=D["team"]; FULL=D["full"]; MONTHS=D["months"]
ML=["Jan","Feb","Mar","Apr","May"]

def eur(v):
    if v is None: return "—"
    s=f"€{abs(v):,.0f}".replace(","," ")
    return f"-{s}" if v<0 else s
def num(v):
    if v is None: return "—"
    return f"{v:,.0f}".replace(","," ")
def pctv(v): return "—" if v is None else f"{v:.1f}%"
def pct(p,w,d=1):
    if not w: return "0%"
    return f"{p/w*100:.{d}f}%"

seg_order={"Enterprise":0,"Mid-market":1,"SMB":2,"Missing Segment":3}
SEG=sorted(SEG,key=lambda s:seg_order.get(s["seg"],9))
seg_label={"Enterprise":"Enterprise","Mid-market":"Mid-market","SMB":"SMB","Missing Segment":"Unsegmented"}
seg_short={"Enterprise":"ENT","Mid-market":"MM","SMB":"SMB","Missing Segment":"—"}
seg_class={"Enterprise":"ent","Mid-market":"mm","SMB":"smb","Missing Segment":"none"}
def sg(n): return next(s for s in SEG if s["seg"]==n)
ent,mm,smb=sg("Enterprise"),sg("Mid-market"),sg("SMB")
today=datetime.date.today().strftime("%d %b %Y")
bryn=next(t for t in TEAM if "Brynchak" in t["am"])
ratio=round(ent["gmv_per"]/smb["gmv_per"]) if smb["gmv_per"] else 0

def cpcls(v): return "neg" if (v is not None and v<0) else "pos"

def spark(series,color):
    if not series or sum(series)==0: return '<span class="muted" style="font-size:11px">—</span>'
    w,h,pad=72,22,2; lo,hi=min(series),max(series); rng=(hi-lo) or 1; n=len(series)
    pts=[f"{pad+(w-2*pad)*(i/(n-1) if n>1 else 0):.1f},{pad+(h-2*pad)*(1-(v-lo)/rng):.1f}" for i,v in enumerate(series)]
    poly=" ".join(pts); lx,ly=pts[-1].split(",")
    tip=" · ".join(f"{ML[i]}: {v:,.0f}".replace(","," ") for i,v in enumerate(series))
    fnz=next((v for v in series if v>0),0); last=series[-1]
    badge=""
    if fnz>0:
        dd=(last-fnz)/fnz*100; arr="▲" if dd>2 else ("▼" if dd<-2 else "▬")
        cl="up" if dd>2 else ("down" if dd<-2 else "flat")
        badge=f'<span class="tr {cl}">{arr}{abs(dd):.0f}%</span>'
    return (f'<span class="spark" title="{tip}"><svg width="{w}" height="{h}">'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="1.6"/>'
            f'<circle cx="{lx}" cy="{ly}" r="2" fill="{color}"/></svg>{badge}</span>')

# ---- segment rows ----
seg_rows=""
for s in SEG:
    seg_rows+=f"""<tr><td style="text-align:left"><span class="dot {seg_class[s['seg']]}"></span>{seg_label[s['seg']]}</td>
    <td>{num(s['partners'])}</td><td class="muted">{pct(s['partners'],T['partners'])}</td>
    <td>{num(s['stores'])}</td><td><b>{eur(s['gmv'])}</b></td><td class="muted">{pct(s['gmv'],T['gmv'])}</td>
    <td>{eur(s['gmv_per'])}</td><td>{eur(s['comm'])}</td><td>{s['comm_pct']}%</td>
    <td><b>{eur(s['comm_per'])}</b></td><td class="{cpcls(s['cp_l1'])}">{eur(s['cp_l1'])}</td></tr>"""

# ---- concentration ----
def barb(v,tot,c):
    return f'<div class="barfill {c}" style="width:{(v/tot*100 if tot else 0):.1f}%"></div>'
conc_rows=""
for s in SEG:
    if s["seg"]=="Missing Segment": continue
    conc_rows+=f"""<div class="conc-row"><div class="conc-name"><span class="dot {seg_class[s['seg']]}"></span>{seg_label[s['seg']]}</div>
    <div class="conc-bars"><div class="conc-line"><span class="conc-lab">Partners {pct(s['partners'],T['partners'])}</span><div class="bartrack">{barb(s['partners'],T['partners'],'c-part')}</div><span class="conc-val">{num(s['partners'])}</span></div>
    <div class="conc-line"><span class="conc-lab">GMV {pct(s['gmv'],T['gmv'])}</span><div class="bartrack">{barb(s['gmv'],T['gmv'],'c-gmv')}</div><span class="conc-val">{eur(s['gmv'])}</span></div></div></div>"""

# ---- managed table ----
maxg=max((p["gmv"] or 0) for p in P) or 1
part_rows=""
for p in P:
    inv=p["gmv"] is None
    gbar="" if inv else f'<div class="minibar"><div style="width:{(p["gmv"]/maxg*100):.0f}%"></div></div>'
    am=f'<span class="ext">{p["am"]} · centralised</span>' if inv else p["am"]
    part_rows+=f"""<tr><td style="text-align:left"><b>{p['name']}</b></td>
    <td><span class="seg-pill {seg_class.get(p['seg'],'none')}">{seg_short.get(p['seg'],p['seg'])}</span></td>
    <td>{num(p['stores'])}</td><td style="text-align:left">{eur(p['gmv'])}{gbar}</td>
    <td>{eur(p['comm'])}</td><td>{pctv(p['comm_pct'])}</td>
    <td class="{cpcls(p['cp_l1'])}">{eur(p['cp_l1'])}</td>
    <td>{eur(p['eater_fees'])}</td><td>{eur(p['camp_bolt'])}</td><td>{eur(p['camp_merch'])}</td>
    <td style="text-align:left;font-size:12px">{am}</td></tr>"""

# ---- team table ----
team_rows=""
max_tg=max(t["gmv"] for t in TEAM) or 1
for t in TEAM:
    ext=f' <span class="muted">(+{t["external"]} centralised)</span>' if t["external"] else ""
    team_rows+=f"""<tr><td style="text-align:left"><b>{t['am']}</b>{ext}</td>
    <td>{t['partners']}</td><td style="text-align:left">{num(t['stores'])}</td>
    <td style="text-align:left"><b>{eur(t['gmv'])}</b><div class="minibar"><div style="width:{t['gmv']/max_tg*100:.0f}%"></div></div></td>
    <td class="muted">{pct(t['gmv'],T['gmv'])}</td><td>{num(t['orders'])}</td><td>{eur(t['comm'])}</td>
    <td class="{cpcls(t['cp_l1'])}">{eur(t['cp_l1'])}</td></tr>"""

# ---- full list collapsible ----
def am_cell(p):
    return p["am_data"] if p["am_data"] else '<span class="noam">Not assigned</span>'
def full_table(seg):
    rows=sorted([p for p in FULL if p["seg"]==seg],key=lambda x:-x["gmv"])
    sgmv=sum(r["gmv"] for r in rows); sst=sum(r["stores"] for r in rows)
    body=""
    for r in rows:
        body+=f"""<tr><td style="text-align:left">{r['name']}</td>
        <td>{num(r['stores'])}</td><td>{num(r['active'])}</td>
        <td style="text-align:left">{eur(r['gmv'])}</td><td>{eur(r['comm'])}</td><td>{pctv(r['comm_pct'])}</td>
        <td class="{cpcls(r['cp_l1'])}">{eur(r['cp_l1'])}</td>
        <td>{eur(r['eater_fees'])}</td><td>{eur(r['camp_bolt'])}</td><td>{eur(r['camp_merch'])}</td>
        <td style="text-align:left;font-size:11.5px">{am_cell(r)}</td>
        <td style="text-align:left">{spark(r['gmv_trend'],'#2563eb')}</td>
        <td style="text-align:left">{spark(r['loc_trend'],'#0e7faa')}</td></tr>"""
    opn=" open" if seg=="Enterprise" else ""
    return f"""<details class="seg-acc"{opn}><summary><span class="dot {seg_class[seg]}"></span><b>{seg_label[seg]}</b> · {len(rows)} partners · {eur(sgmv)} GMV · {num(sst)} locations <span class="chev">▾</span></summary>
    <div class="tablewrap"><table class="full"><thead><tr><th style="text-align:left">Partner</th><th>Loc.</th><th>Active</th><th style="text-align:left">GMV</th><th>Comm €</th><th>Comm %</th><th>CP L1</th><th>Eater fees</th><th>Camp Bolt</th><th>Camp Merch</th><th style="text-align:left">Account manager</th><th style="text-align:left">GMV trend</th><th style="text-align:left">Locations trend</th></tr></thead><tbody>{body}</tbody></table></div></details>"""
full_sections="".join(full_table(s) for s in ["Enterprise","Mid-market","SMB","Missing Segment"])

HTML=f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Partner Portfolio — Coverage & Segmentation</title>
<style>
:root{{--bg:#eef1f7;--panel:#fff;--panel2:#f6f8fc;--line:#dfe5ee;--text:#13203a;--muted:#5d6b85;--soft:#33425d;
--accent:#2563eb;--accent2:#0e7faa;--ent:#7c3aed;--mm:#0e7faa;--smb:#ea580c;--none:#94a3b8;--crit:#dc2626;--high:#ea580c;--good:#15a34a;}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:radial-gradient(1200px 600px at 80% -10%,#16223e 0%,var(--bg) 55%);color:var(--text);line-height:1.55}}
.wrap{{max-width:1240px;margin:0 auto;padding:28px 20px 90px}} section[id]{{scroll-margin-top:64px}}
nav.topnav{{position:sticky;top:0;z-index:50;background:rgba(10,16,30,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}}
nav.topnav .inner{{max-width:1240px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
nav.topnav .brand{{font-weight:800;font-size:13px;color:var(--accent2);margin-right:8px}}
nav.topnav a{{color:#aab6cd;text-decoration:none;font-size:13px;padding:6px 11px;border-radius:8px;border:1px solid transparent;white-space:nowrap}}
nav.topnav a:hover{{background:#13203a;border-color:#243150;color:#fff}}
header.hero{{padding:34px 30px;border:1px solid var(--line);border-radius:18px;background:linear-gradient(135deg,#16233f,#0e1830);overflow:hidden;color:#fff}}
.hero .tag{{display:inline-block;margin-bottom:12px;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#5bb4d6;font-weight:700}}
.hero h1{{margin:0 0 8px;font-size:27px}} .hero .sub{{color:#c3cee0;font-size:15px;max-width:860px}}
.meta{{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}}
.meta .pill{{background:#0d1730;border:1px solid #243150;border-radius:999px;padding:6px 13px;font-size:12.5px;color:#c3cee0}}
h2.section{{font-size:20px;margin:46px 0 6px;display:flex;align-items:center;gap:10px}}
h2.section .bar{{width:6px;height:22px;border-radius:3px;background:var(--accent)}}
.section-desc{{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:920px}}
.grid{{display:grid;gap:14px}} .kpis{{grid-template-columns:repeat(4,1fr);margin-top:22px}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 17px}}
.kpi .n{{font-size:24px;font-weight:800;letter-spacing:-.3px}} .kpi .l{{color:var(--muted);font-size:12.5px;margin-top:3px}}
.kpi.crit .n{{color:var(--crit)}} .kpi.high .n{{color:var(--high)}} .kpi.good .n{{color:var(--good)}} .kpi.ent .n{{color:var(--ent)}}
.callout{{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;padding:18px 20px;margin-top:20px}}
.callout.warn{{border-left-color:var(--crit)}} .callout h3{{margin:0 0 10px;font-size:16px}}
.callout ul{{margin:6px 0 0;padding-left:18px;color:var(--soft);font-size:14.5px}} .callout li{{margin:7px 0}} .callout b{{color:var(--text)}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin-top:18px;overflow:hidden}}
.card .top{{padding:14px 20px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#13203a,#101a30);color:#fff;font-weight:700;font-size:15px}}
.card .body{{padding:6px 8px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:9px 10px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap}}
th{{background:var(--panel2);color:var(--soft);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.3px}}
tbody tr:hover{{background:#f3f7ff}} td.muted,.muted{{color:var(--muted)}} .tablewrap{{overflow-x:auto}}
table.full td,table.full th{{padding:7px 9px;font-size:12px}}
.neg{{color:var(--crit);font-weight:600}} .pos{{color:var(--good);font-weight:600}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;vertical-align:middle}}
.dot.ent{{background:var(--ent)}} .dot.mm{{background:var(--mm)}} .dot.smb{{background:var(--smb)}} .dot.none{{background:var(--none)}}
.seg-pill{{font-size:10.5px;font-weight:800;padding:3px 8px;border-radius:999px;color:#fff}}
.seg-pill.ent{{background:var(--ent)}} .seg-pill.mm{{background:var(--mm)}} .seg-pill.smb{{background:var(--smb)}} .seg-pill.none{{background:var(--none)}}
.ext{{color:var(--ent);font-weight:700}} .noam{{color:var(--crit);font-weight:700}}
.minibar{{height:5px;background:#eef1f7;border-radius:3px;margin-top:5px;overflow:hidden}} .minibar div{{height:100%;background:var(--accent);border-radius:3px}}
.conc-row{{display:grid;grid-template-columns:140px 1fr;gap:14px;padding:14px 4px;border-bottom:1px solid var(--line)}}
.conc-name{{font-weight:700;font-size:14px;align-self:center}} .conc-line{{display:flex;align-items:center;gap:10px;margin:5px 0}}
.conc-lab{{width:120px;font-size:12px;color:var(--muted);text-align:right}} .bartrack{{flex:1;height:14px;background:#eef1f7;border-radius:7px;overflow:hidden}}
.barfill{{height:100%;border-radius:7px}} .barfill.c-part{{background:var(--none)}} .barfill.c-gmv{{background:var(--accent)}} .conc-val{{width:90px;font-size:12.5px;font-weight:700;text-align:right}}
.spark{{display:inline-flex;align-items:center;gap:5px}} .spark svg{{vertical-align:middle}}
.tr{{font-size:11px;font-weight:800}} .tr.up{{color:var(--good)}} .tr.down{{color:var(--crit)}} .tr.flat{{color:var(--muted)}}
details.seg-acc{{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin-top:14px;overflow:hidden}}
details.seg-acc summary{{cursor:pointer;list-style:none;padding:14px 18px;font-size:14px;background:var(--panel2);display:flex;align-items:center;gap:8px}}
details.seg-acc summary::-webkit-details-marker{{display:none}}
details.seg-acc .chev{{margin-left:auto;color:var(--muted);transition:transform .2s}} details.seg-acc[open] .chev{{transform:rotate(180deg)}}
.note{{font-size:12px;color:var(--muted);margin-top:8px}}
.foot{{margin-top:50px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);padding-top:16px}}
@media(max-width:820px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.conc-row{{grid-template-columns:1fr}}}}
</style></head><body>
<nav class="topnav"><div class="inner"><span class="brand">PARTNER PORTFOLIO</span>
<a href="#overview">Overview</a><a href="#segments">Segments</a><a href="#economics">Economics</a>
<a href="#coverage">Coverage</a><a href="#team">Team load</a><a href="#fulllist">All partners</a><a href="#verdict">Conclusion</a></div></nav>
<div class="wrap">
<header class="hero"><span class="tag">Internal analysis · for management</span>
<h1>Partner Portfolio — Coverage &amp; Segmentation</h1>
<p class="sub">How many partners we have, how they split by segment, turnover (GMV) and profitability, how much the team currently covers — and why there is no capacity to take on new partners, especially in SMB and Mid-market (MM).</p>
<div class="meta"><span class="pill">For: team · director · sales director</span>
<span class="pill">Partners: {num(T['partners'])}</span><span class="pill">Locations: {num(T['stores'])}</span>
<span class="pill">GMV (Jan–May 2026): {eur(T['gmv'])}</span><span class="pill">Generated {today}</span></div></header>

<div class="callout warn"><h3>Executive summary (30 sec)</h3><ul>
<li><b>Portfolio:</b> {num(T['partners'])} partners / {num(T['stores'])} locations / {eur(T['gmv'])} GMV over Jan–May 2026. Steep pyramid: <b>Enterprise + MM = {pct(ent['partners']+mm['partners'],T['partners'])} of partners but {pct(ent['gmv']+mm['gmv'],T['gmv'])} of GMV</b>.</li>
<li><b>SMB is a long tail:</b> {num(smb['partners'])} partners ({pct(smb['partners'],T['partners'])}) generate just {pct(smb['gmv'],T['gmv'])} of GMV. Average SMB partner = <b>{eur(smb['gmv_per'])}</b> GMV vs {eur(ent['gmv_per'])} for Enterprise — a ~{ratio}× gap.</li>
<li><b>The team actively manages {MT['partners']} key partners with only {MT['managers']} account managers (AM)</b> — covering the large majority of portfolio GMV.</li>
<li><b>Load is critically skewed:</b> one AM (M. Brynchak) carries {num(bryn['stores'])} locations and ~{pct(bryn['gmv'],T['gmv'])} of portfolio GMV. Meanwhile {num(T['unassigned_stores'])} locations across {num(T['unassigned_partners'])} partners have <b>no AM assigned</b>.</li>
<li><b>Conclusion:</b> there is no capacity to onboard more managed partners. Every new SMB/MM partner consumes the same effort as Enterprise but returns a fraction of the value.</li></ul></div>

<section id="overview"><h2 class="section"><span class="bar"></span>1. Big picture</h2>
<p class="section-desc">"Partner" = brand/chain (group), "location" = individual store (provider). All figures are Jan–May 2026, delivered orders, GMV before discounts, in EUR.</p>
<div class="grid kpis">
<div class="kpi"><div class="n">{num(T['partners'])}</div><div class="l">Partners in portfolio</div></div>
<div class="kpi"><div class="n">{num(T['active_partners'])}</div><div class="l">Partners with GMV (Jan–May)</div></div>
<div class="kpi"><div class="n">{num(T['stores'])}</div><div class="l">Locations</div></div>
<div class="kpi"><div class="n">{num(T['orders'])}</div><div class="l">Delivered orders</div></div>
<div class="kpi"><div class="n">{eur(T['gmv'])}</div><div class="l">GMV</div></div>
<div class="kpi"><div class="n">{eur(T['comm'])}</div><div class="l">Commission ({T['comm_pct']}% of GMV)</div></div>
<div class="kpi {cpcls(T['cp_l1'])}"><div class="n">{eur(T['cp_l1'])}</div><div class="l">Contribution Profit L1 ({T['cp_pct']}%)</div></div>
<div class="kpi"><div class="n">{MT['managers']}</div><div class="l">Account managers</div></div></div></section>

<section id="segments"><h2 class="section"><span class="bar"></span>2. Segmentation</h2>
<p class="section-desc">Partners split into Enterprise, Mid-market (MM) and SMB. Turnover, commission (in € and % of GMV), commission per partner and Contribution Profit L1 (CP L1) per segment.</p>
<div class="card"><div class="top">Portfolio by segment</div><div class="body tablewrap"><table>
<thead><tr><th style="text-align:left">Segment</th><th>Partners</th><th>% part.</th><th>Loc.</th><th>GMV</th><th>% GMV</th><th>GMV / partner</th><th>Commission</th><th>Comm %</th><th>Comm / partner</th><th>CP L1</th></tr></thead>
<tbody>{seg_rows}<tr style="background:#f3f7ff;font-weight:800"><td style="text-align:left">Total</td><td>{num(T['partners'])}</td><td>100%</td><td>{num(T['stores'])}</td><td>{eur(T['gmv'])}</td><td>100%</td><td>{eur(round(T['gmv']/T['partners']))}</td><td>{eur(T['comm'])}</td><td>{T['comm_pct']}%</td><td>{eur(round(T['comm']/T['partners']))}</td><td class="{cpcls(T['cp_l1'])}">{eur(T['cp_l1'])}</td></tr></tbody></table></div></div>
<div class="card"><div class="top">Concentration: where partners are vs where the money is</div><div class="body" style="padding:6px 18px 14px"><div class="conc">{conc_rows}</div>
<p class="note">Grey bar = share of partners, blue = share of GMV. Inverted pyramid: SMB has most partners but little turnover.</p></div></div></section>

<section id="economics"><h2 class="section"><span class="bar"></span>3. Segment economics: value vs effort</h2>
<p class="section-desc">Managing one partner costs roughly the same effort regardless of segment — but the return differs by an order of magnitude.</p>
<div class="grid kpis">
<div class="kpi ent"><div class="n">{eur(ent['gmv_per'])}</div><div class="l">Avg GMV / Enterprise partner</div></div>
<div class="kpi"><div class="n">{eur(mm['gmv_per'])}</div><div class="l">Avg GMV / MM partner</div></div>
<div class="kpi high"><div class="n">{eur(smb['gmv_per'])}</div><div class="l">Avg GMV / SMB partner</div></div>
<div class="kpi crit"><div class="n">~{ratio}×</div><div class="l">Enterprise vs SMB GMV/partner</div></div></div>
<div class="callout"><h3>How to read it</h3><ul>
<li>For the same managing effort, an Enterprise partner delivers {eur(ent['gmv_per'])} of GMV; an SMB partner delivers only {eur(smb['gmv_per'])}.</li>
<li>SMB is {pct(smb['partners'],T['partners'])} of partners but just {pct(smb['gmv'],T['gmv'])} of GMV. As a tail it can only be served at scale (self-serve / automation), not one-by-one by an AM.</li>
<li>Note on profitability: SMB runs a positive CP L1 ({eur(smb['cp_l1'])}) on high commission rates, while Enterprise/MM are intentionally subsidised (campaigns &amp; incentives) and run negative CP L1 to drive volume. So the constraint is not SMB profitability per euro — it is that each SMB partner is simply too small to justify hands-on management.</li></ul></div></section>

<section id="coverage"><h2 class="section"><span class="bar"></span>4. What we cover today</h2>
<p class="section-desc">The team manages {MT['partners']} key partners. {MT['in_data']} are live in Bolt UA store data; {MT['external']} large chains (FORA, ANRI, E-ZOO, master zoo, etc.) are managed centrally / not yet on Bolt UA stores and are shown separately. Table includes commission (€ and %), CP L1, eater fees and campaign spend by Bolt and by merchant.</p>
<div class="grid kpis">
<div class="kpi"><div class="n">{MT['partners']}</div><div class="l">Managed partners</div></div>
<div class="kpi good"><div class="n">{eur(MT['gmv'])}</div><div class="l">GMV under management</div></div>
<div class="kpi"><div class="n">{eur(MT['comm'])}</div><div class="l">Commission under management</div></div>
<div class="kpi crit"><div class="n">{MT['managers']}</div><div class="l">AMs covering all of it</div></div></div>
<div class="card"><div class="top">Managed partners ({len(P)}) — by GMV</div><div class="body tablewrap"><table>
<thead><tr><th style="text-align:left">Partner</th><th>Seg</th><th>Loc.</th><th style="text-align:left">GMV</th><th>Comm €</th><th>Comm %</th><th>CP L1</th><th>Eater fees</th><th>Camp Bolt</th><th>Camp Merch</th><th style="text-align:left">Account manager</th></tr></thead>
<tbody>{part_rows}</tbody></table></div></div>
<p class="note">"Centralised" = key-account chains handled outside this store dataset (no Bolt UA store GMV in the period). GMV/CP are Jan–May 2026, delivered orders.</p></section>

<section id="team"><h2 class="section"><span class="bar"></span>5. Team load</h2>
<p class="section-desc">The entire key portfolio is held by {MT['managers']} account managers. The load is extremely uneven and already at the limit.</p>
<div class="grid kpis">
<div class="kpi"><div class="n">{MT['managers']}</div><div class="l">Account managers</div></div>
<div class="kpi"><div class="n">{num(MT['stores'])}</div><div class="l">Managed locations</div></div>
<div class="kpi high"><div class="n">~{pct(bryn['gmv'],T['gmv'])}</div><div class="l">GMV on one AM (Brynchak)</div></div>
<div class="kpi crit"><div class="n">{num(T['unassigned_stores'])}</div><div class="l">Locations with no AM</div></div></div>
<div class="card"><div class="top">Load by account manager</div><div class="body tablewrap"><table>
<thead><tr><th style="text-align:left">Account manager</th><th>Partners</th><th style="text-align:left">Locations</th><th style="text-align:left">GMV</th><th>% GMV</th><th>Orders</th><th>Commission</th><th>CP L1</th></tr></thead>
<tbody>{team_rows}</tbody></table></div></div>
<p class="note">GMV/commission/CP are computed over managed partners present in the data; centralised chains add load beyond what is shown. One AM holds ~{pct(bryn['gmv'],T['gmv'])} of portfolio GMV — a single point of concentration risk.</p></section>

<section id="fulllist"><h2 class="section"><span class="bar"></span>6. Full partner list</h2>
<p class="section-desc">All {num(T['partners'])} partners with full metrics, grouped by segment (click to expand). The last column before the trends shows the assigned account manager — or "Not assigned" where none. Trend columns are monthly Jan–May 2026: <b>GMV</b> and number of <b>active locations</b>. Hover a sparkline for values; the arrow shows the change from the first to the last month.</p>
{full_sections}
<p class="note">Source: fact_order_delivery × dim_provider_v2 (Bolt UA, delivery_vertical = store). CP L1 = commission + eater fees + delivery revenue − courier cost − demand incentives − Bolt campaign spend − refunds. "—" = no delivered orders in the period.</p></section>

<section id="verdict"><h2 class="section"><span class="bar"></span>7. Conclusion: why there is no capacity for new partners</h2>
<div class="callout warn"><h3>Argument</h3><ul>
<li><b>1. Only {MT['managers']} AMs for the whole key portfolio.</b> They already cover {num(MT['stores'])} locations ({MT['in_data']} partners + {MT['external']} central chains). The team is physically at its limit.</li>
<li><b>2. Concentration risk.</b> One AM (M. Brynchak) holds ~{pct(bryn['gmv'],T['gmv'])} of GMV and {num(bryn['stores'])} locations. Adding partners without adding people deepens the imbalance.</li>
<li><b>3. Economics against SMB/MM.</b> A new SMB partner brings on average just {eur(smb['gmv_per'])} of GMV yet needs the same onboarding and ongoing support as an Enterprise partner at {eur(ent['gmv_per'])} — a ~{ratio}× worse effort-to-value ratio.</li>
<li><b>4. Focus on value.</b> {num(T['unassigned_stores'])} locations across {num(T['unassigned_partners'])} partners already have no AM. We are not even fully covering the existing book; spreading thinner onto small SMB/MM would weaken work with top partners.</li>
<li><b>5. The tail does not scale by hand.</b> {num(smb['partners'])} SMB partners cannot be managed individually with the current team — that is a self-serve / automation job, not an AM job.</li></ul></div>
<div class="callout"><h3>Recommended instead of "take more"</h3><ul>
<li>Freeze intake of new SMB/MM into hands-on management until additional headcount is added.</li>
<li>First cover (or move to self-serve) the {num(T['unassigned_stores'])} locations that currently have no AM.</li>
<li>Rebalance the book to remove the ~{pct(bryn['gmv'],T['gmv'])} GMV single-AM concentration risk.</li>
<li>Onboard new partners only selectively in Enterprise / high-MM above segment-average GMV.</li>
<li>Serve the SMB tail through automated / group processes, not individual management.</li></ul></div></section>

<div class="foot">Source: Databricks — hive_metastore.ng_delivery_spark.fact_order_delivery joined to dim_provider_v2 (Bolt UA, store vertical), delivered orders, {D['data_start']} → {D['data_end']}. Partner = group_name, location = provider. GMV before discounts, EUR. Managed-partner figures include cross-vertical group activity where applicable. Generated {today}.</div>
</div></body></html>"""

open(os.path.join(HERE,"index.html"),"w",encoding="utf-8").write(HTML)
print("index.html written:",len(HTML),"chars")
