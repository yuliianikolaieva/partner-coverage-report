import pandas as pd, re, json

SRC = "/Users/yuliia.nikolaieva/Library/CloudStorage/GoogleDrive-yuliia.nikolaieva@bolt.eu/My Drive/Cursor/Key Account dashboard/data/Merchant-level Overview.csv"
df = pd.read_csv(SRC)

def money(s):
    if pd.isna(s): return 0.0
    s=str(s).replace("€","").replace(",","").replace('"','').strip()
    if s in ("","-"): return 0.0
    try: return float(s)
    except: return 0.0

df["gmv"]=df["Total GMV Before Discounts, €"].apply(money)
df["comm"]=df["Total Invoiced Merchant Commission, €"].apply(money)
df["orders"]=df["Merchant Delivered Orders Count, #"].apply(money)
df["seg"]=df["Business Segment V2"].fillna("Missing Segment").str.replace(" (AM Segment)","",regex=False)

def norm(s):
    if pd.isna(s): return ""
    s=str(s).upper().strip().replace("`","'")
    s=re.sub(r"\s+"," ",s); return s

# managed list with intended segment classification
managed = [
 ("LEPRUKON","brand"),("DIMPYVA","brand"),("CHILL TIME","brand"),("RODYNNA KOVBASKA","brand"),
 ("NO TABOO","brand"),("VAPE SHOP KYIV","brand"),("VAPORS","brand"),("HOP HEY","brand"),
 ("BEER MARKET","brand"),("KOPIYKA","brand"),("LOKO","brand"),("PYVNA BORODA","brand"),
 ("SANTIM","brand"),("KOPIYKA MINI","brand"),("OKKO CAFE","brand"),("BRSM-NAFTA","brand"),
 ("LIKI24","brand"),("CAFE RYNOK","brand"),("BEERLAND","brand"),("WINETIME","brand"),
 ("SPRAGA","brand"),("MAXBEER","brand"),("FLOWERS","brand"),("TAISTRA","brand"),("O'NDE","brand"),
 ("SPAR","brand"),("RUKAVYCHKA","brand"),("REMESLO BREWERY","brand"),("PYVNE REMESLO","brand"),
 ("TOCHKA","brand"),("FLOWER SHOP","brand"),
]
display_names = {
 "OKKO CAFE":"OKKO","BRSM-NAFTA":"BRSM","LIKI24":"LIKI 24","FLOWERS":"FLOWERS UA",
}
# enterprise chains not present in this dataset (managed centrally / other dataset)
enterprise_external = ["ATB","FORA","ANRI","ROZETKA","VARUS","THRASH","E-ZOO","РОСТ"]

nb={norm(b) for b in df["Brand Name"].dropna()}
ng={norm(g) for g in df["Group Name"].dropna()}

partners=[]
for name,_ in managed:
    nn=norm(name)
    if nn in nb:
        sub=df[df["Brand Name"].apply(norm)==nn]
    elif nn in ng:
        sub=df[df["Group Name"].apply(norm)==nn]
    else:
        sub=df[(df["Brand Name"].apply(norm)==nn)|(df["Group Name"].apply(norm)==nn)]
    if len(sub)==0:
        print("MISS",name); continue
    seg=sub["seg"].mode().iloc[0] if len(sub["seg"].mode()) else "Missing Segment"
    ams=sorted({a for a in sub["Account Manager Name"].dropna().unique()})
    status_counts=sub["Provider Status"].value_counts().to_dict()
    partners.append({
        "name":display_names.get(name,name),
        "seg":seg,
        "stores":int(len(sub)),
        "active":int((sub["Provider Status"]=="active").sum()),
        "onboarding":int((sub["Provider Status"]=="onboarding").sum()),
        "cities":int(sub["City Name"].nunique()),
        "gmv":round(float(sub["gmv"].sum())),
        "orders":int(sub["orders"].sum()),
        "comm":round(float(sub["comm"].sum())),
        "am":", ".join(ams) if ams else "—",
    })

# add enterprise external
for e in enterprise_external:
    partners.append({"name":e,"seg":"Enterprise","stores":None,"active":None,"onboarding":None,
        "cities":None,"gmv":None,"orders":None,"comm":None,"am":"central KAM"})

partners_sorted=sorted(partners,key=lambda x:(x["gmv"] is None, -(x["gmv"] or 0)))

# universe overview by segment (groups=partners, rows=stores)
df["grp"]=df["Group Name"].fillna(df["Brand Name"]).fillna(df["Provider Name"])
seg_overview=[]
for seg in ["Enterprise","Mid-market","SMB","Missing Segment"]:
    s=df[df["seg"]==seg]
    seg_overview.append({
        "seg":seg,
        "partners":int(s["grp"].nunique()),
        "stores":int(len(s)),
        "active":int((s["Provider Status"]=="active").sum()),
        "onboarding":int((s["Provider Status"]=="onboarding").sum()),
        "gmv":round(float(s["gmv"].sum())),
        "orders":int(s["orders"].sum()),
        "comm":round(float(s["comm"].sum())),
    })

# AM workload
am_work=[]
for am,s in df[df["Account Manager Name"].notna()].groupby("Account Manager Name"):
    am_work.append({
        "am":am,"partners":int(s["grp"].nunique()),"stores":int(len(s)),
        "active":int((s["Provider Status"]=="active").sum()),
        "gmv":round(float(s["gmv"].sum())),"orders":int(s["orders"].sum()),
        "comm":round(float(s["comm"].sum())),
    })
am_work=sorted(am_work,key=lambda x:-x["gmv"])
unassigned=df[df["Account Manager Name"].isna()]

totals={
 "providers":int(len(df)),
 "partners":int(df["grp"].nunique()),
 "active":int((df["Provider Status"]=="active").sum()),
 "onboarding":int((df["Provider Status"]=="onboarding").sum()),
 "gmv":round(float(df["gmv"].sum())),
 "orders":int(df["orders"].sum()),
 "comm":round(float(df["comm"].sum())),
 "assigned_stores":int(df["Account Manager Name"].notna().sum()),
 "unassigned_stores":int(df["Account Manager Name"].isna().sum()),
 "unassigned_gmv":round(float(unassigned["gmv"].sum())),
 "unassigned_partners":int(unassigned["grp"].nunique()),
 "am_count":int(df["Account Manager Name"].nunique()),
}

# managed totals (CSV-present only)
mp=[p for p in partners if p["gmv"] is not None]
managed_totals={
 "partners":len(partners),
 "in_data":len(mp),
 "external":len(enterprise_external),
 "stores":sum(p["stores"] for p in mp),
 "gmv":sum(p["gmv"] for p in mp),
 "orders":sum(p["orders"] for p in mp),
 "comm":sum(p["comm"] for p in mp),
}

out={"totals":totals,"seg_overview":seg_overview,"am_work":am_work,
     "partners":partners_sorted,"managed_totals":managed_totals,
     "enterprise_external":enterprise_external}
with open("/Users/yuliia.nikolaieva/Library/CloudStorage/GoogleDrive-yuliia.nikolaieva@bolt.eu/My Drive/Cursor/Reports GIT HUB/Partner-Coverage/data.json","w") as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
print(json.dumps(totals,ensure_ascii=False,indent=1))
print("SEG"); [print(s) for s in seg_overview]
print("AM"); [print(a) for a in am_work]
print("MANAGED TOTALS",managed_totals)
print("PARTNERS",len(partners_sorted))
for p in partners_sorted: print(p["name"],p["seg"],p["gmv"],p["stores"],p["am"])
