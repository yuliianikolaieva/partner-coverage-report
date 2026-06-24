import pandas as pd, re, json, unicodedata

SRC = "/Users/yuliia.nikolaieva/Library/CloudStorage/GoogleDrive-yuliia.nikolaieva@bolt.eu/My Drive/Cursor/Key Account dashboard/data/Merchant-level Overview.csv"
df = pd.read_csv(SRC)
print("rows", len(df))
print("cols", list(df.columns)[:25])

def money(s):
    if pd.isna(s): return 0.0
    s = str(s).replace("€","").replace(",","").replace('"','').strip()
    if s in ("","-",): return 0.0
    try: return float(s)
    except: return 0.0

df["gmv"] = df["Total GMV Before Discounts, €"].apply(money)
df["comm"] = df["Total Invoiced Merchant Commission, €"].apply(money)
df["orders"] = df["Merchant Delivered Orders Count, #"].apply(money)

print("\n=== Business Segment V2 ===")
print(df["Business Segment V2"].value_counts(dropna=False))
print("\n=== Provider Status ===")
print(df["Provider Status"].value_counts(dropna=False))
print("\n=== Account Manager Name (top 30) ===")
print(df["Account Manager Name"].value_counts(dropna=False).head(30))
print("\nTotal GMV", df["gmv"].sum(), "Total comm", df["comm"].sum())

# user managed list
managed = ["LEPRUKON","DIMPYVA","CHILL TIME","RODYNNA KOVBASKA","NO TABOO","VAPE SHOP KYIV",
"VAPORS","HOP HEY","BEER MARKET","KOPIYKA","LOKO","PYVNA BORODA","SANTIM","KOPIYKA MINI","OKKO",
"BRSM","ATB","LIKI 24","CAFE RYNOK","BEERLAND","WINETIME","SPRAGA","MAXBEER","FLOWERS UA","TAISTRA",
"O'NDE","SPAR","FORA","ANRI","RUKAVYCHKA","REMESLO BREWERY","PYVNE REMESLO","ROZETKA","VARUS",
"THRASH","E-ZOO","РОСТ","TOCHKA","FLOWER SHOP"]

def norm(s):
    if pd.isna(s): return ""
    s = str(s).upper().strip()
    s = s.replace("'","'").replace("`","'")
    s = re.sub(r"\s+"," ",s)
    return s

brands = df["Brand Name"].dropna().unique()
groups = df["Group Name"].dropna().unique()
nb = {norm(b): b for b in brands}
ng = {norm(g): g for g in groups}

print("\n=== MATCHING managed list ===")
matched = {}
for m in managed:
    mn = norm(m)
    hit = None
    # exact in brand or group
    if mn in nb: hit=("brand",nb[mn])
    elif mn in ng: hit=("group",ng[mn])
    else:
        # contains
        cand = [v for k,v in nb.items() if mn in k or k in mn]
        if cand: hit=("brand~",cand[0])
        else:
            cand=[v for k,v in ng.items() if mn in k or k in mn]
            if cand: hit=("group~",cand[0])
    matched[m]=hit
    print(f"{m:20} -> {hit}")
