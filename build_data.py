# -*- coding: utf-8 -*-
import pandas as pd, re, json
BASE="/Users/yuliia.nikolaieva/Library/CloudStorage/GoogleDrive-yuliia.nikolaieva@bolt.eu/My Drive/Cursor/"
SRC=BASE+"Key Account dashboard/data/Merchant-level Overview.csv"
df=pd.read_csv(SRC)

def money(s):
    if pd.isna(s):return 0.0
    s=str(s).replace("€","").replace(",","").replace('"','').strip()
    if s in ("","-"):return 0.0
    try:return float(s)
    except:return 0.0
def norm(s):
    if pd.isna(s):return ""
    s=str(s).upper().strip().replace("`","'"); s=re.sub(r"\s+"," ",s);return s

df["gmv"]=df["Total GMV Before Discounts, €"].apply(money)
df["comm"]=df["Total Invoiced Merchant Commission, €"].apply(money)
df["orders"]=df["Merchant Delivered Orders Count, #"].apply(money)
df["seg"]=df["Business Segment V2"].fillna("Missing Segment").str.replace(" (AM Segment)","",regex=False)
df["grp"]=df["Group Name"].fillna(df["Brand Name"]).fillna(df["Provider Name"])

pn2grp=dict(zip(df["Provider Name"].astype(str),df["grp"].astype(str)))
# brand upper -> group (mode)
brand2grp={}
for b,sub in df.dropna(subset=["Brand Name"]).groupby(df["Brand Name"].str.upper()):
    brand2grp[b]=sub["grp"].mode().iloc[0]

# ---------------- monthly GMV per group (Jan-Apr) ----------------
dyn=pd.read_csv(BASE+"Key Account dashboard/data/Entity performance dynamics (PoP) (2).csv",header=[0,1])
ent=dyn.iloc[:,1].astype(str)
gmv_months=['2026-01','2026-02','2026-03','2026-04']
gmv_trend={}
for m in gmv_months:
    col=dyn[(m,'Total GMV Before Discounts, €')].apply(money)
    for e,v in zip(ent,col):
        g=pn2grp.get(e)
        if g is None:continue
        gmv_trend.setdefault(g,{}).setdefault(m,0.0)
        gmv_trend[g][m]+=v
def gmv_series(g):
    d=gmv_trend.get(g)
    if not d:return None
    return [round(d.get(m,0.0)) for m in gmv_months]

# ---------------- monthly locations per group (Jan-May) ----------------
act=pd.read_csv(BASE+"Active store/active_stores_from_dbx.csv")
act["m"]=act["Report Time (dynamic)"].str[:7]
def act2grp(row):
    pn=str(row["Provider Name"])
    if pn in pn2grp:return pn2grp[pn]
    b=str(row["Brand Name"]).upper()
    return brand2grp.get(b)
act["g"]=act.apply(act2grp,axis=1)
loc_months=['2026-01','2026-02','2026-03','2026-04','2026-05']
# per month, use the LAST weekly snapshot in that month
loc_trend={}
for m in loc_months:
    sub=act[act["m"]==m]
    if len(sub)==0:continue
    last_week=sub["Report Time (dynamic)"].max()
    snap_w=sub[sub["Report Time (dynamic)"]==last_week]
    agg=snap_w.dropna(subset=["g"]).groupby("g")["Active Merchant Count, #"].sum()
    for g,v in agg.items():
        loc_trend.setdefault(g,{})[m]=int(v)
def loc_series(g):
    d=loc_trend.get(g)
    if not d:return None
    return [int(d.get(m,0)) for m in loc_months]

# ---------------- managed partners (with AM overrides) ----------------
BRYN="Mykhailo Brynchak"; SKAL="Viktor Skalivskiy"; BER="Khrystyna Berezna"
am_override={}
for n in ["KOPIYKA","PYVNA BORODA","WINETIME","SANTIM","MAXBEER","SPRAGA","O'NDE","SPAR","OKKO",
          "BRSM","FLOWERS UA","ATB","FORA","ANRI","HOP HEY","BEER MARKET","LOKO","KOPIYKA MINI",
          "CAFE RYNOK","BEERLAND","TAISTRA","RUKAVYCHKA"]: am_override[n]=BRYN
for n in ["REMESLO BREWERY","TOCHKA","FLOWER SHOP","LIKI 24","VARUS","THRASH","E-ZOO","РОСТ","MASTER ZOO"]: am_override[n]=SKAL
for n in ["LEPRUKON","DIMPYVA","CHILL TIME","VAPE SHOP KYIV","NO TABOO","RODYNNA KOVBASKA","VAPORS","ROZETKA"]: am_override[n]=BER

# managed list -> match key in snapshot
managed_match=[
 ("LEPRUKON","LEPRUKON"),("DIMPYVA","DIMPYVA"),("CHILL TIME","CHILL TIME"),
 ("RODYNNA KOVBASKA","RODYNNA KOVBASKA"),("NO TABOO","NO TABOO"),("VAPE SHOP KYIV","VAPE SHOP KYIV"),
 ("VAPORS","VAPORS"),("HOP HEY","HOP HEY"),("BEER MARKET","BEER MARKET"),("KOPIYKA","KOPIYKA"),
 ("LOKO","LOKO"),("PYVNA BORODA","PYVNA BORODA"),("SANTIM","SANTIM"),("KOPIYKA MINI","KOPIYKA MINI"),
 ("OKKO","OKKO CAFE"),("BRSM","BRSM-NAFTA"),("LIKI 24","LIKI24"),("CAFE RYNOK","CAFE RYNOK"),
 ("BEERLAND","BEERLAND"),("WINETIME","WINETIME"),("SPRAGA","SPRAGA"),("MAXBEER","MAXBEER"),
 ("FLOWERS UA","FLOWERS"),("TAISTRA","TAISTRA"),("O'NDE","O'NDE"),("SPAR","SPAR"),
 ("RUKAVYCHKA","RUKAVYCHKA"),("REMESLO BREWERY","REMESLO BREWERY"),("TOCHKA","TOCHKA"),
 ("FLOWER SHOP","FLOWER SHOP"),
]
enterprise_external=["ATB","FORA","ANRI","ROZETKA","VARUS","THRASH","E-ZOO","РОСТ","MASTER ZOO"]

nb={norm(b) for b in df["Brand Name"].dropna()}; ng={norm(g) for g in df["Group Name"].dropna()}
partners=[]
for disp,key in managed_match:
    nn=norm(key)
    if nn in nb: sub=df[df["Brand Name"].apply(norm)==nn]
    elif nn in ng: sub=df[df["Group Name"].apply(norm)==nn]
    else: sub=df[(df["Brand Name"].apply(norm)==nn)|(df["Group Name"].apply(norm)==nn)]
    if len(sub)==0: print("MISS",disp); continue
    seg=sub["seg"].mode().iloc[0] if len(sub["seg"].mode()) else "Missing Segment"
    gkey=sub["grp"].mode().iloc[0]
    partners.append({"name":disp,"seg":seg,"stores":int(len(sub)),
        "active":int((sub["Provider Status"]=="active").sum()),
        "gmv":round(float(sub["gmv"].sum())),"orders":int(sub["orders"].sum()),
        "comm":round(float(sub["comm"].sum())),"am":am_override.get(disp,"—"),
        "gmv_trend":gmv_series(gkey),"loc_trend":loc_series(gkey)})
for e in enterprise_external:
    partners.append({"name":e,"seg":"Enterprise","stores":None,"active":None,
        "gmv":None,"orders":None,"comm":None,"am":am_override.get(e,SKAL),
        "gmv_trend":None,"loc_trend":None})
partners_sorted=sorted(partners,key=lambda x:(x["gmv"] is None,-(x["gmv"] or 0)))

# ---------------- segment overview (+comm per partner) ----------------
seg_overview=[]
for seg in ["Enterprise","Mid-market","SMB","Missing Segment"]:
    s=df[df["seg"]==seg]
    np_=int(s["grp"].nunique())
    seg_overview.append({"seg":seg,"partners":np_,"stores":int(len(s)),
        "active":int((s["Provider Status"]=="active").sum()),
        "gmv":round(float(s["gmv"].sum())),"orders":int(s["orders"].sum()),
        "comm":round(float(s["comm"].sum())),
        "comm_per":round(float(s["comm"].sum())/np_) if np_ else 0})

# ---------------- full partner list (all groups) with trend ----------------
full=[]
for g,s in df.groupby("grp"):
    seg=s["seg"].mode().iloc[0] if len(s["seg"].mode()) else "Missing Segment"
    full.append({"name":g,"seg":seg,"stores":int(len(s)),
        "active":int((s["Provider Status"]=="active").sum()),
        "gmv":round(float(s["gmv"].sum())),"orders":int(s["orders"].sum()),
        "comm":round(float(s["comm"].sum())),
        "gmv_trend":gmv_series(g),"loc_trend":loc_series(g)})
full=sorted(full,key=lambda x:-x["gmv"])

# ---------------- team (3 managers) workload over managed ----------------
team=[]
for am in [BRYN,SKAL,BER]:
    mp=[p for p in partners if p["am"]==am]
    indata=[p for p in mp if p["gmv"] is not None]
    team.append({"am":am,"partners":len(mp),"in_data":len(indata),
        "external":len(mp)-len(indata),
        "stores":sum(p["stores"] for p in indata),
        "gmv":sum(p["gmv"] for p in indata),
        "orders":sum(p["orders"] for p in indata),
        "comm":sum(p["comm"] for p in indata),
        "names":[p["name"] for p in mp]})

mp_all=[p for p in partners if p["gmv"] is not None]
managed_totals={"partners":len(partners),"in_data":len(mp_all),
    "external":len(enterprise_external),"managers":3,
    "stores":sum(p["stores"] for p in mp_all),"gmv":sum(p["gmv"] for p in mp_all),
    "orders":sum(p["orders"] for p in mp_all),"comm":sum(p["comm"] for p in mp_all)}

unassigned=df[df["Account Manager Name"].isna()]
totals={"providers":int(len(df)),"partners":int(df["grp"].nunique()),
    "active":int((df["Provider Status"]=="active").sum()),
    "onboarding":int((df["Provider Status"]=="onboarding").sum()),
    "gmv":round(float(df["gmv"].sum())),"orders":int(df["orders"].sum()),
    "comm":round(float(df["comm"].sum())),
    "unassigned_stores":int(df["Account Manager Name"].isna().sum()),
    "unassigned_gmv":round(float(unassigned["gmv"].sum())),
    "unassigned_partners":int(unassigned["grp"].nunique())}

out={"totals":totals,"seg_overview":seg_overview,"partners":partners_sorted,
     "managed_totals":managed_totals,"enterprise_external":enterprise_external,
     "team":team,"full":full,"gmv_months":gmv_months,"loc_months":loc_months}
with open(BASE+"Reports GIT HUB/Partner-Coverage/data.json","w") as f:
    json.dump(out,f,ensure_ascii=False,indent=1)

print("TOTALS",totals)
print("\nTEAM:")
for t in team: print(f"  {t['am']}: {t['partners']} партн ({t['external']} зовн), {t['stores']} лок, €{t['gmv']:,}, ком €{t['comm']:,}")
print("\nSEG:")
for s in seg_overview: print(" ",s["seg"],s["partners"],"партн, €",s["gmv"],"comm/partner €",s["comm_per"])
print("\nfull partners:",len(full),"| with gmv_trend:",sum(1 for f in full if f["gmv_trend"]),"| with loc_trend:",sum(1 for f in full if f["loc_trend"]))
print("managed:",len(partners_sorted))
