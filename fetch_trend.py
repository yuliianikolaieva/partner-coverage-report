# -*- coding: utf-8 -*-
"""Pull 12+ month trend (by segment) and per-provider first-order month for onboarding/forecast."""
import os, json
from pathlib import Path
from databricks import sql as dbsql
HERE=Path(__file__).parent
ENV=Path("/Users/yuliia.nikolaieva/Downloads/Reports GIT HUB/VARUS/.env")
for line in ENV.read_text().splitlines():
    line=line.strip()
    if not line or line.startswith("#") or "=" not in line: continue
    k,_,v=line.partition("="); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
kw={}
if os.environ.get("DATABRICKS_TLS_NO_VERIFY","").lower() in ("1","true","yes"): kw["_tls_no_verify"]=True
conn=dbsql.connect(server_hostname=os.environ["DATABRICKS_HOST"],
    http_path=f"/sql/1.0/warehouses/{os.environ['DATABRICKS_WAREHOUSE_ID']}",
    access_token=os.environ["DATABRICKS_TOKEN"],**kw)
cur=conn.cursor()
def run(sql):
    cur.execute(sql); cols=[d[0] for d in cur.description]
    out=[]
    for r in cur.fetchall():
        d={}
        for c,x in zip(cols,r):
            if x is None: d[c]=None
            elif c in ("gmv",): d[c]=float(x)
            elif c in ("locations","partners","orders"): d[c]=int(x)
            else: d[c]=x
        out.append(d)
    return out

MONTHLY=f"""
SELECT DATE_FORMAT(f.order_created_date,'yyyy-MM') AS period,
  p.business_segment_v2 AS seg,
  COUNT(DISTINCT f.provider_id) AS locations,
  COUNT(DISTINCT p.group_name) AS partners,
  SUM(f.order_gmv_eur) AS gmv,
  COUNT(*) AS orders
FROM hive_metastore.ng_delivery_spark.fact_order_delivery f
JOIN hive_metastore.ng_delivery_spark.dim_provider_v2 p ON f.provider_id=p.provider_id
WHERE p.country_code='ua' AND f.order_state='delivered' AND p.delivery_vertical LIKE 'store%'
  AND f.order_created_date>=DATE'2024-06-01' AND f.order_created_date<=DATE'2026-05-31'
GROUP BY 1,2 ORDER BY 1,2
"""
FIRST=f"""
SELECT f.provider_id,
  MAX(p.group_name) AS grp,
  MAX(p.business_segment_v2) AS seg,
  DATE_FORMAT(MIN(f.order_created_date),'yyyy-MM') AS first_m
FROM hive_metastore.ng_delivery_spark.fact_order_delivery f
JOIN hive_metastore.ng_delivery_spark.dim_provider_v2 p ON f.provider_id=p.provider_id
WHERE p.country_code='ua' AND f.order_state='delivered' AND p.delivery_vertical LIKE 'store%'
  AND f.order_created_date>=DATE'2024-01-01' AND f.order_created_date<=DATE'2026-05-31'
GROUP BY f.provider_id
"""
print("monthly..."); m=run(MONTHLY); print("rows",len(m))
print("first..."); fst=run(FIRST); print("rows",len(fst))
C=json.load(open(HERE/"dbx_cache.json"))
C["trend_monthly"]=m; C["first_seen"]=fst
json.dump(C,open(HERE/"dbx_cache.json","w"),ensure_ascii=False)
cur.close(); conn.close(); print("saved")
