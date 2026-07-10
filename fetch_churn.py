# -*- coding: utf-8 -*-
"""Pull per-location monthly activity (Jan-May 2026) to compute churn by segment / managed status."""
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
def col(m): return f"SUM(CASE WHEN DATE_FORMAT(f.order_created_date,'yyyy-MM')='2026-{m}' THEN 1 ELSE 0 END) AS m{m}"
def gcol(m): return f"SUM(CASE WHEN DATE_FORMAT(f.order_created_date,'yyyy-MM')='2026-{m}' THEN f.order_gmv_eur ELSE 0 END) AS g{m}"
CHURN=f"""
SELECT f.provider_id,
  MAX(p.group_name) AS grp,
  MAX(p.business_segment_v2) AS seg,
  {col('01')},{col('02')},{col('03')},{col('04')},{col('05')},{col('06')},
  {gcol('01')},{gcol('02')},{gcol('03')},{gcol('04')},{gcol('05')},{gcol('06')}
FROM hive_metastore.ng_delivery_spark.fact_order_delivery f
JOIN hive_metastore.ng_delivery_spark.dim_provider_v2 p ON f.provider_id=p.provider_id
WHERE p.country_code='ua' AND f.order_state='delivered'
  AND p.delivery_vertical LIKE 'store%'
  AND f.order_created_date>=DATE'2026-01-01' AND f.order_created_date<=DATE'2026-06-30'
GROUP BY f.provider_id
"""
cur.execute(CHURN); cols=[d[0] for d in cur.description]
GCOLS={f"g0{i}" for i in range(1,7)}; MCOLS={f"m0{i}" for i in range(1,7)}
def conv(c,x):
    if x is None: return None
    if c in GCOLS: return float(x)
    if c=="provider_id" or c in MCOLS: return int(x)
    return x
rows=[{c:conv(c,x) for c,x in zip(cols,r)} for r in cur.fetchall()]
print("churn rows",len(rows))
C=json.load(open(HERE/"dbx_cache.json"))
C["churn"]=rows
json.dump(C,open(HERE/"dbx_cache.json","w"),ensure_ascii=False)
cur.close(); conn.close()
print("saved")
