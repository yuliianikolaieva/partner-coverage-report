# -*- coding: utf-8 -*-
"""Build data.json for the Partner Coverage report from Databricks cache (Jan-May 2026)."""
import json, os
from collections import defaultdict
HERE=os.path.dirname(os.path.abspath(__file__))
C=json.load(open(os.path.join(HERE,"dbx_cache.json"),encoding="utf-8"))
MONTHS=["2026-01","2026-02","2026-03","2026-04","2026-05"]
NUMCOLS=["orders","locations","gmv","commission","eater_fees","camp_bolt","camp_merch",
         "delivery_rev","courier_cost","refunds","demand_incentives","supply_incentives"]

def f(x):
    try: return float(x) if x is not None else 0.0
    except: return 0.0
def norm_seg(s):
    if not s: return "Missing Segment"
    return str(s).replace(" (AM Segment)","").strip() or "Missing Segment"

def cp_l1(d):
    return (d["commission"]+d["eater_fees"]+d["delivery_rev"]-d["courier_cost"]
            -d["demand_incentives"]-d["camp_bolt"]-d["refunds"])

def agg_monthly(rows):
    """grp -> {totals..., gmv_m{month:v}, loc_m{month:v}}"""
    g=defaultdict(lambda:{c:0.0 for c in NUMCOLS_INIT()})
    gmv_m=defaultdict(lambda:{m:0.0 for m in MONTHS})
    loc_m=defaultdict(lambda:{m:0.0 for m in MONTHS})
    for r in rows:
        k=str(r["grp"])
        for c in NUMCOLS: g[k][c]+=f(r.get(c))
        p=r.get("period")
        if p in MONTHS:
            gmv_m[k][p]+=f(r.get("gmv")); loc_m[k][p]+=f(r.get("locations"))
    return g,gmv_m,loc_m
def NUMCOLS_INIT(): return NUMCOLS

def agg_dim(rows):
    """grp -> {stores,active,seg,am,cities,brand}"""
    by=defaultdict(list)
    for r in rows: by[str(r["grp"])].append(r)
    out={}
    for k,rs in by.items():
        stores=sum(int(f(r.get("stores"))) for r in rs)
        active=sum(int(f(r.get("stores"))) for r in rs if r.get("status")=="active")
        # seg / am by max stores
        seg_row=max(rs,key=lambda r:f(r.get("stores")))
        seg=norm_seg(seg_row.get("seg"))
        am_rows=[r for r in rs if r.get("am")]
        am=None
        if am_rows:
            am=max(am_rows,key=lambda r:f(r.get("stores"))).get("am")
        cities=len({r.get("city") for r in rs if r.get("city")})
        out[k]={"stores":stores,"active":active,"seg":seg,"am":am,"cities":cities,
                "brand":seg_row.get("brand")}
    return out

EXCLUDE={"OKKO CAFE GROUP"}  # removed from all calculations per request
C["monthly"]=[r for r in C["monthly"] if str(r["grp"]) not in EXCLUDE]
C["dim"]=[r for r in C["dim"] if str(r["grp"]) not in EXCLUDE]
C["man_monthly"]=[r for r in C["man_monthly"] if str(r["grp"]) not in EXCLUDE]
C["man_dim"]=[r for r in C["man_dim"] if str(r["grp"]) not in EXCLUDE]

UM,UGMV,ULOC=agg_monthly(C["monthly"])
UD=agg_dim(C["dim"])
MM,MGMV,MLOC=agg_monthly(C["man_monthly"])
MD=agg_dim(C["man_dim"])

def series(dmap,k): return [round(dmap[k][m]) for m in MONTHS] if k in dmap else None

# managed AM overrides keyed by DB group_name (so full list shows the same AM as the managed table)
BRYN="Mykhailo Brynchak"; SKAL="Viktor Skalivskiy"; BER="Khrystyna Berezna"
resolver={
 "LEPRUKON":["LEPRUKON"],"DIMPYVA":["DIMPYVA"],"CHILL TIME":["CHILL TIME"],
 "RODYNNA KOVBASKA":["RODYNNA KOVBASKA"],"NO TABOO":["NO TABOO"],
 "VAPE SHOP KYIV":["VAPE SHOP KYIV"],"VAPORS":["VAPORS"],"HOP HEY":["HOP HEY"],
 "BEER MARKET":["BEER MARKET"],"KOPIYKA":["KOPIYKA"],"LOKO":["LOKO"],
 "PYVNA BORODA":["PYVNA BORODA"],"SANTIM":["SANTIM"],"BRSM":["BRSM"],
 "CAFE RYNOK":["CAFE RYNOK"],"BEERLAND":["BEERLAND"],"WINETIME":["WINETIME"],
 "SPRAGA":["SPRAGA"],"MAXBEER":["MAXBEER"],"FLOWERS UA":["FLOWERS"],
 "TAISTRA":["TAISTRA"],"SPAR":["SPAR"],"RUKAVYCHKA":["RUKAVYCHKA"],
 "REMESLO BREWERY":["REMESLO BREWERY"],"TOCHKA":["TOCHKA"],"FLOWER SHOP":["FLOWER SHOP"],
 "LIKI 24":["LIKI24"],"VARUS":["VARUS"],"ROZETKA":["ROZETKA"],"ANRI-PHARM":["ANRI-PHARM"],
 "ATB":["ATB CHERKASY","ATB KYIV"],"BEERLAND K":["BEERLAND K"],
 "VAPERY | VAPE SHOP":["VAPERY | VAPE SHOP"],
}
external_nodata=["O'NDE","FORA","THRASH","E-ZOO","MASTER ZOO","ROST"]
am_map={}
for n in ["KOPIYKA","PYVNA BORODA","WINETIME","SANTIM","MAXBEER","SPRAGA","O'NDE","SPAR",
          "BRSM","FLOWERS UA","ATB","FORA","HOP HEY","BEER MARKET","LOKO",
          "CAFE RYNOK","BEERLAND","BEERLAND K","TAISTRA","RUKAVYCHKA"]: am_map[n]=BRYN
for n in ["REMESLO BREWERY","TOCHKA","FLOWER SHOP","LIKI 24","VARUS","THRASH","E-ZOO","ROST","MASTER ZOO","ANRI-PHARM"]: am_map[n]=SKAL
for n in ["LEPRUKON","DIMPYVA","CHILL TIME","VAPE SHOP KYIV","NO TABOO","RODYNNA KOVBASKA","VAPORS","ROZETKA","VAPERY | VAPE SHOP"]: am_map[n]=BER
MANAGED_GROUP_AM={}
for disp,keys in resolver.items():
    for k in keys: MANAGED_GROUP_AM[k]=am_map.get(disp)

def pctof(part,whole): return round(part/whole*100,1) if whole>0 else None
def partner_record(k,mt,dim,gmv_m,loc_m):
    d=mt.get(k,{c:0.0 for c in NUMCOLS})
    di=dim.get(k,{"stores":0,"active":0,"seg":"Missing Segment","am":None,"cities":0})
    gmv=d["gmv"]; comm=d["commission"]
    return {"name":k,"seg":di["seg"],"stores":di["stores"],"active":di["active"],
        "am_managed":MANAGED_GROUP_AM.get(k),"am_data":di["am"],
        "gmv":round(gmv),"orders":int(d["orders"]),"comm":round(comm),
        "comm_pct":pctof(comm,gmv),
        "eater_fees":round(d["eater_fees"]),"camp_bolt":round(d["camp_bolt"]),
        "camp_merch":round(d["camp_merch"]),
        "camp_bolt_pct":pctof(d["camp_bolt"],gmv),"camp_merch_pct":pctof(d["camp_merch"],gmv),
        "cp_l1":round(cp_l1(d)),"cp_pct":pctof(cp_l1(d),gmv),
        "gmv_trend":series(gmv_m,k),"loc_trend":series(loc_m,k)}

# ---------------- universe full list ----------------
universe_keys=set(UD)|set(UM)
full=[partner_record(k,UM,UD,UGMV,ULOC) for k in universe_keys]
full=sorted(full,key=lambda x:-x["gmv"])

# ---------------- totals ----------------
def sumf(lst,key): return round(sum(p[key] for p in lst))
T={"partners":len(full),
   "active_partners":sum(1 for p in full if p["gmv"]>0),
   "stores":sumf(full,"stores"),"active":sumf(full,"active"),
   "gmv":sumf(full,"gmv"),"orders":sumf(full,"orders"),"comm":sumf(full,"comm"),
   "eater_fees":sumf(full,"eater_fees"),"camp_bolt":sumf(full,"camp_bolt"),
   "camp_merch":sumf(full,"camp_merch"),"cp_l1":sumf(full,"cp_l1")}
T["comm_pct"]=round(T["comm"]/T["gmv"]*100,1)
T["cp_pct"]=round(T["cp_l1"]/T["gmv"]*100,1)
# unassigned = neither in our 3-AM managed book nor any system AM
unassigned=[p for p in full if not p["am_managed"] and not p["am_data"]]
T["unassigned_partners"]=len(unassigned)
T["unassigned_stores"]=sumf(unassigned,"stores")
T["unassigned_gmv"]=sumf(unassigned,"gmv")
T["am_count"]=len({p["am_data"] for p in full if p["am_data"]})

# ---------------- segment overview ----------------
SEGS=["Enterprise","Mid-market","SMB","Missing Segment"]
seg_overview=[]
for s in SEGS:
    g=[p for p in full if p["seg"]==s]
    ga=[p for p in g if p["gmv"]>0]            # active partners only
    np_=len(ga); gmv=sumf(g,"gmv"); comm=sumf(g,"comm")
    seg_overview.append({"seg":s,"partners":np_,"stores":sumf(g,"stores"),
        "active":sumf(g,"active"),"gmv":gmv,"orders":sumf(g,"orders"),"comm":comm,
        "cp_l1":sumf(g,"cp_l1"),
        "gmv_per":round(gmv/np_) if np_ else 0,"comm_per":round(comm/np_) if np_ else 0,
        "comm_pct":round(comm/gmv*100,1) if gmv>0 else 0})

# ---------------- managed partners (resolver/am_map defined above) ----------------
def merge_groups(dispname,keys):
    d={c:0.0 for c in NUMCOLS}; gmv_m={m:0.0 for m in MONTHS}; loc_m={m:0.0 for m in MONTHS}
    stores=active=cities=0; segs=[]
    for k in keys:
        dd=MM.get(k); gsrc,lsrc=(MGMV,MLOC)
        if not dd: dd=UM.get(k); gsrc,lsrc=(UGMV,ULOC)  # fall back to store universe
        if dd:
            for c in NUMCOLS: d[c]+=dd[c]
            if k in gsrc:
                for m in MONTHS: gmv_m[m]+=gsrc[k][m]; loc_m[m]+=lsrc[k][m]
        di=MD.get(k) or UD.get(k)
        if di:
            stores+=di["stores"]; active+=di["active"]; cities+=di["cities"]; segs.append((di["stores"],di["seg"]))
    seg=max(segs,key=lambda x:x[0])[1] if segs else "Missing Segment"
    gmv=d["gmv"]; comm=d["commission"]
    return {"name":dispname,"seg":seg,"stores":stores,"active":active,
        "gmv":round(gmv),"orders":int(d["orders"]),"comm":round(comm),
        "comm_pct":round(comm/gmv*100,1) if gmv>0 else None,
        "eater_fees":round(d["eater_fees"]),"camp_bolt":round(d["camp_bolt"]),
        "camp_merch":round(d["camp_merch"]),"cp_l1":round(cp_l1(d)),
        "cp_pct":round(cp_l1(d)/gmv*100,1) if gmv>0 else None,
        "camp_vs_comm":round(d["camp_bolt"]/comm*100,1) if comm>0 else None,
        "am":am_map.get(dispname,"—"),
        "gmv_trend":[round(gmv_m[m]) for m in MONTHS] if gmv>0 else None,
        "loc_trend":[round(loc_m[m]) for m in MONTHS] if gmv>0 else None,
        "external":False}

partners=[merge_groups(n,ks) for n,ks in resolver.items()]
for e in external_nodata:
    partners.append({"name":("РОСТ" if e=="ROST" else e),"seg":"Enterprise","stores":None,"active":None,
        "gmv":None,"orders":None,"comm":None,"comm_pct":None,"eater_fees":None,
        "camp_bolt":None,"camp_merch":None,"cp_l1":None,"cp_pct":None,"camp_vs_comm":None,
        "am":am_map.get(e,SKAL),"gmv_trend":None,"loc_trend":None,"external":True})
partners=sorted(partners,key=lambda x:(x["gmv"] is None,-(x["gmv"] or 0)))

mp=[p for p in partners if p["gmv"] is not None]
managed_totals={"partners":len(partners),"in_data":len(mp),
    "external":len(external_nodata),"managers":3,
    "stores":round(sum(p["stores"] for p in mp)),"gmv":round(sum(p["gmv"] for p in mp)),
    "orders":round(sum(p["orders"] for p in mp)),"comm":round(sum(p["comm"] for p in mp)),
    "cp_l1":round(sum(p["cp_l1"] for p in mp))}

team=[]
for am in [BRYN,SKAL,BER]:
    g=[p for p in partners if p["am"]==am]
    ind=[p for p in g if p["gmv"] is not None]
    team.append({"am":am,"partners":len(g),"external":len(g)-len(ind),
        "stores":round(sum(p["stores"] for p in ind)),"gmv":round(sum(p["gmv"] for p in ind)),
        "orders":round(sum(p["orders"] for p in ind)),"comm":round(sum(p["comm"] for p in ind)),
        "cp_l1":round(sum(p["cp_l1"] for p in ind))})

# ---------------- churn (location-level): active Jan-Feb -> lost by Apr-May ----------------
managed_live_groups=set()
for keys in resolver.values():
    for k in keys: managed_live_groups.add(k)
def active_early(r): return bool(r.get("m01") or r.get("m02"))
def active_late(r):  return bool(r.get("m04") or r.get("m05"))
def cstats(rows):  # location-level churn
    cohort=[r for r in rows if active_early(r)]
    churned=[r for r in cohort if not active_late(r)]
    n=len(cohort)
    return {"cohort":n,"churned":len(churned),"pct":round(len(churned)/n*100,1) if n else 0}
def pstats(rows):  # partner-level (group) churn
    g={}
    for r in rows:
        d=g.setdefault(str(r.get("grp")),{"m01":0,"m02":0,"m04":0,"m05":0})
        for k in ("m01","m02","m04","m05"): d[k]+=r.get(k) or 0
    cohort=[k for k,d in g.items() if d["m01"] or d["m02"]]
    churned=[k for k in cohort if not (g[k]["m04"] or g[k]["m05"])]
    n=len(cohort)
    return {"cohort":n,"churned":len(churned),"pct":round(len(churned)/n*100,1) if n else 0}
def gmv5(r): return sum(r.get(f"g0{i}") or 0 for i in range(1,6))
def glost(rows):  # GMV lost via churned locations
    churned=[r for r in rows if active_early(r) and not active_late(r)]
    total=sum(gmv5(r) for r in churned)
    runrate=sum(((r.get("g01") or 0)+(r.get("g02") or 0))/2 for r in churned)
    return {"count":len(churned),"total":round(total),"runrate":round(runrate)}

ch=C.get("churn",[])
for r in ch: r["_seg"]=norm_seg(r.get("seg")); r["_man"]=str(r.get("grp")) in managed_live_groups
seg_gmv={s["seg"]:s["gmv"] for s in seg_overview}
churn={"overall":cstats(ch),
       "managed":cstats([r for r in ch if r["_man"]]),
       "unmanaged":cstats([r for r in ch if not r["_man"]]),
       "by_segment":[],"by_seg_mgmt":[],
       # partner-level
       "p_overall":pstats(ch),"p_managed":pstats([r for r in ch if r["_man"]]),
       "p_unmanaged":pstats([r for r in ch if not r["_man"]]),"p_by_segment":[],"p_by_seg_mgmt":[],
       # gmv lost
       "gmv_lost":glost(ch),"gmv_lost_managed":glost([r for r in ch if r["_man"]]),
       "gmv_lost_unmanaged":glost([r for r in ch if not r["_man"]]),"gmv_lost_by_segment":[]}
for s in ["Enterprise","Mid-market","SMB"]:
    rows=[r for r in ch if r["_seg"]==s]
    st=cstats(rows); st["seg"]=s; churn["by_segment"].append(st)
    m=cstats([r for r in rows if r["_man"]]); u=cstats([r for r in rows if not r["_man"]])
    churn["by_seg_mgmt"].append({"seg":s,"man_pct":m["pct"],"man_n":m["cohort"],"man_ch":m["churned"],
                                 "unm_pct":u["pct"],"unm_n":u["cohort"],"unm_ch":u["churned"]})
    ps=pstats(rows); ps["seg"]=s; churn["p_by_segment"].append(ps)
    pm=pstats([r for r in rows if r["_man"]]); pu=pstats([r for r in rows if not r["_man"]])
    churn["p_by_seg_mgmt"].append({"seg":s,"man_pct":pm["pct"],"man_n":pm["cohort"],"man_ch":pm["churned"],
                                   "unm_pct":pu["pct"],"unm_n":pu["cohort"],"unm_ch":pu["churned"]})
    gl=glost(rows); gl["seg"]=s; gl["pct_of_gmv"]=round(gl["total"]/seg_gmv[s]*100,1) if seg_gmv.get(s) else 0
    churn["gmv_lost_by_segment"].append(gl)
churn["gmv_lost"]["pct_of_gmv"]=round(churn["gmv_lost"]["total"]/T["gmv"]*100,1) if T["gmv"] else 0

# ---------------- SMB onboarding / forecast / ROI ----------------
import statistics as _st
from collections import defaultdict as _dd
tm=C.get("trend_monthly",[]); fs=C.get("first_seen",[])
WIN=[f"2025-{m:02d}" for m in range(6,13)]+[f"2026-{m:02d}" for m in range(1,6)]  # trailing 12m
smb_tm=sorted([r for r in tm if norm_seg(r["seg"])=="SMB" and r["period"] in WIN],key=lambda r:r["period"])
smb_gmv_avg=_st.mean(r["gmv"] for r in smb_tm)
smb_gmv_annual=round(smb_gmv_avg*12)
smb_part_avg=_st.mean(r["partners"] for r in smb_tm)
smb_part_now=smb_tm[-1]["partners"]; smb_loc_now=smb_tm[-1]["locations"]
net_part_yr=smb_part_now-smb_tm[0]["partners"]; net_loc_yr=smb_loc_now-smb_tm[0]["locations"]
gmv_growth_yr=round(smb_tm[-1]["gmv"]/smb_tm[0]["gmv"]-1,3)
gmv_per_part_yr=round(smb_gmv_annual/smb_part_avg)
# gross onboarding (first order in window)
grp_first=_dd(lambda:"9999"); grp_seg={}
for r in fs:
    g=str(r["grp"]); grp_seg[g]=norm_seg(r["seg"])
    if r["first_m"] and r["first_m"]<grp_first[g]: grp_first[g]=r["first_m"]
onb_loc_yr=sum(1 for r in fs if norm_seg(r["seg"])=="SMB" and r["first_m"] in WIN)
onb_part_yr=sum(1 for g,fm in grp_first.items() if grp_seg.get(g)=="SMB" and fm in WIN)
leak_part=onb_part_yr-net_part_yr
leak_pct=round(leak_part/onb_part_yr*100) if onb_part_yr else 0

# assumptions (clearly exposed)
AGENT_COST_MO=1000
CH_UNM=next(x["unm_pct"] for x in churn["by_seg_mgmt"] if x["seg"]=="SMB")/100   # SMB no-AM churn
CH_TARGET=0.05                                                                   # target churn with outsourced coverage
AGENT_CAP=120                                                                    # SMB partners per outsource agent
RAMP=0.5                                                                         # first-year realization of steady-state GMV
smb_comm_rate=next(s["comm_pct"] for s in seg_overview if s["seg"]=="SMB")/100
# forecast — status quo (continue observed trajectory)
sq_part=smb_part_now+net_part_yr; sq_loc=smb_loc_now+net_loc_yr
sq_gmv_annual=round(smb_gmv_annual*(1+gmv_growth_yr))
# forecast — outsourced (retain onboarding, churn ~5%)
net_part_out=onb_part_yr-round(CH_TARGET*smb_part_now)
out_part=smb_part_now+net_part_out
out_loc=smb_loc_now+round(onb_loc_yr*(1-CH_TARGET))
extra_part=out_part-sq_part
incr_gmv_steady=round(extra_part*gmv_per_part_yr)
incr_gmv_y1=round(incr_gmv_steady*RAMP)
out_gmv_annual=sq_gmv_annual+incr_gmv_y1
# ROI
agents=max(1,round(out_part/AGENT_CAP))
cost_yr=agents*AGENT_COST_MO*12
churn_saved_gmv=round((CH_UNM-CH_TARGET)*smb_gmv_annual)
benefit_gmv=churn_saved_gmv+incr_gmv_y1
benefit_comm=round(benefit_gmv*smb_comm_rate)
roi_pct=round((benefit_comm-cost_yr)/cost_yr*100)
payback_mo=round(cost_yr/(benefit_comm/12),1) if benefit_comm else None

smb={
 "losses":{"loc":churn["overall"]["churned"],"part":churn["p_overall"]["churned"],
           "gmv":churn["gmv_lost"]["total"],"runrate":churn["gmv_lost"]["runrate"],
           "annualized":round(churn["gmv_lost"]["runrate"]*12)},
 "now":{"part":smb_part_now,"loc":smb_loc_now,"gmv_annual":smb_gmv_annual,
        "gmv_per_part_yr":gmv_per_part_yr,"comm_rate":round(smb_comm_rate*100,1)},
 "onboard":{"part_yr":onb_part_yr,"loc_yr":onb_loc_yr,"net_part_yr":net_part_yr,
            "net_loc_yr":net_loc_yr,"leak_part":leak_part,"leak_pct":leak_pct,
            "gmv_growth_yr":round(gmv_growth_yr*100)},
 "forecast":{"sq_part":sq_part,"sq_loc":sq_loc,"sq_gmv":sq_gmv_annual,
             "out_part":out_part,"out_loc":out_loc,"out_gmv":out_gmv_annual,
             "extra_part":extra_part,"incr_gmv_y1":incr_gmv_y1},
 "roi":{"agents":agents,"agent_cost_mo":AGENT_COST_MO,"cost_yr":cost_yr,
        "ch_unm":round(CH_UNM*100,1),"ch_target":round(CH_TARGET*100,1),"agent_cap":AGENT_CAP,
        "churn_saved_gmv":churn_saved_gmv,"incr_gmv_y1":incr_gmv_y1,"benefit_gmv":benefit_gmv,
        "benefit_comm":benefit_comm,"roi_pct":roi_pct,"payback_mo":payback_mo,"ramp":int(RAMP*100)},
}

out={"totals":T,"seg_overview":seg_overview,"partners":partners,"managed_totals":managed_totals,
     "team":team,"full":full,"months":MONTHS,"data_start":C["start"],"data_end":C["end"],
     "churn":churn,"smb":smb}
json.dump(out,open(os.path.join(HERE,"data.json"),"w"),ensure_ascii=False,indent=1)

print("TOTALS",{k:T[k] for k in ['partners','active_partners','stores','gmv','comm','comm_pct','cp_l1','cp_pct','unassigned_partners','unassigned_stores']})
print("SEG:")
for s in seg_overview: print(f"  {s['seg']:16} {s['partners']:4} partn  GMV {s['gmv']:>9,}  GMV/p {s['gmv_per']:>7,}  comm% {s['comm_pct']}  CP {s['cp_l1']:>8,}")
print("MANAGED:",managed_totals)
for t in team: print(f"  {t['am']}: {t['partners']}p ({t['external']} ext) {t['stores']}loc GMV {t['gmv']:,} CP {t['cp_l1']:,}")
print("managed list:")
for p in partners: print(f"  {p['name']:18} {p['seg']:12} GMV {str(p['gmv']):>8} comm% {p['comm_pct']} CP {p['cp_l1']} AM {p['am']}")
print("full partners:",len(full)," gmv>0:",T['active_partners'])
