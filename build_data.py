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
 "LIKI 24":["LIKI24"],"VARUS":["VARUS"],"ROZETKA":["ROZETKA"],
 "ATB":["ATB CHERKASY","ATB KYIV"],
}
external_nodata=["O'NDE","FORA","ANRI","THRASH","E-ZOO","MASTER ZOO","ROST"]
am_map={}
for n in ["KOPIYKA","PYVNA BORODA","WINETIME","SANTIM","MAXBEER","SPRAGA","O'NDE","SPAR",
          "BRSM","FLOWERS UA","ATB","FORA","ANRI","HOP HEY","BEER MARKET","LOKO",
          "CAFE RYNOK","BEERLAND","TAISTRA","RUKAVYCHKA"]: am_map[n]=BRYN
for n in ["REMESLO BREWERY","TOCHKA","FLOWER SHOP","LIKI 24","VARUS","THRASH","E-ZOO","ROST","MASTER ZOO"]: am_map[n]=SKAL
for n in ["LEPRUKON","DIMPYVA","CHILL TIME","VAPE SHOP KYIV","NO TABOO","RODYNNA KOVBASKA","VAPORS","ROZETKA"]: am_map[n]=BER
MANAGED_GROUP_AM={}
for disp,keys in resolver.items():
    for k in keys: MANAGED_GROUP_AM[k]=am_map.get(disp)

def pctof(part,whole): return round(part/whole*100,1) if whole>0 else None
def partner_record(k,mt,dim,gmv_m,loc_m):
    d=mt.get(k,{c:0.0 for c in NUMCOLS})
    di=dim.get(k,{"stores":0,"active":0,"seg":"Missing Segment","am":None,"cities":0})
    gmv=d["gmv"]; comm=d["commission"]
    return {"name":k,"seg":di["seg"],"stores":di["stores"],"active":di["active"],
        "am":MANAGED_GROUP_AM.get(k) or di["am"],
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
# unassigned (no AM at all)
unassigned=[p for p in full if not p["am"]]
T["unassigned_partners"]=len(unassigned)
T["unassigned_stores"]=sumf(unassigned,"stores")
T["unassigned_gmv"]=sumf(unassigned,"gmv")
T["am_count"]=len({p["am"] for p in full if p["am"]})

# ---------------- segment overview ----------------
SEGS=["Enterprise","Mid-market","SMB","Missing Segment"]
seg_overview=[]
for s in SEGS:
    g=[p for p in full if p["seg"]==s]
    np_=len(g); gmv=sumf(g,"gmv"); comm=sumf(g,"comm")
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
        dd=MM.get(k)
        if dd:
            for c in NUMCOLS: d[c]+=dd[c]
            for m in MONTHS: gmv_m[m]+=MGMV[k][m]; loc_m[m]+=MLOC[k][m]
        di=MD.get(k)
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
        "am":am_map.get(dispname,"—"),
        "gmv_trend":[round(gmv_m[m]) for m in MONTHS] if gmv>0 else None,
        "loc_trend":[round(loc_m[m]) for m in MONTHS] if gmv>0 else None,
        "external":False}

partners=[merge_groups(n,ks) for n,ks in resolver.items()]
for e in external_nodata:
    partners.append({"name":("РОСТ" if e=="ROST" else e),"seg":"Enterprise","stores":None,"active":None,
        "gmv":None,"orders":None,"comm":None,"comm_pct":None,"eater_fees":None,
        "camp_bolt":None,"camp_merch":None,"cp_l1":None,"cp_pct":None,
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

out={"totals":T,"seg_overview":seg_overview,"partners":partners,"managed_totals":managed_totals,
     "team":team,"full":full,"months":MONTHS,"data_start":C["start"],"data_end":C["end"]}
json.dump(out,open(os.path.join(HERE,"data.json"),"w"),ensure_ascii=False,indent=1)

print("TOTALS",{k:T[k] for k in ['partners','active_partners','stores','gmv','comm','comm_pct','cp_l1','cp_pct','unassigned_partners','unassigned_stores']})
print("SEG:")
for s in seg_overview: print(f"  {s['seg']:16} {s['partners']:4} partn  GMV {s['gmv']:>9,}  GMV/p {s['gmv_per']:>7,}  comm% {s['comm_pct']}  CP {s['cp_l1']:>8,}")
print("MANAGED:",managed_totals)
for t in team: print(f"  {t['am']}: {t['partners']}p ({t['external']} ext) {t['stores']}loc GMV {t['gmv']:,} CP {t['cp_l1']:,}")
print("managed list:")
for p in partners: print(f"  {p['name']:18} {p['seg']:12} GMV {str(p['gmv']):>8} comm% {p['comm_pct']} CP {p['cp_l1']} AM {p['am']}")
print("full partners:",len(full)," gmv>0:",T['active_partners'])
