# -*- coding: utf-8 -*-
"""Тягне з Databricks per-partner (group_name) per-month метрики Jan-May 2026."""
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
def q(sql):
    cur.execute(sql); cols=[d[0] for d in cur.description]
    return [dict(zip(cols,[float(x) if hasattr(x,'__float__') and not isinstance(x,bool) else x for x in r])) for r in cur.fetchall()]

START="2026-01-01"; END="2026-05-31"
BOLT="(COALESCE(f.bolt_spend_am_spend_campaign,0)+COALESCE(f.bolt_spend_liquidity_campaign,0)+COALESCE(f.bolt_spend_marketing_campaign,0)+COALESCE(f.bolt_spend_user_lifecycle_campaign,0)+COALESCE(f.bolt_spend_merchant_lifecycle_campaign,0)+COALESCE(f.bolt_spend_other_campaign,0))"
MERCH="(COALESCE(f.provider_spend_am_spend_campaign,0)+COALESCE(f.provider_spend_liquidity_campaign,0)+COALESCE(f.provider_spend_marketing_campaign,0)+COALESCE(f.provider_spend_user_lifecycle_campaign,0)+COALESCE(f.provider_spend_merchant_lifecycle_campaign,0)+COALESCE(f.provider_spend_other_campaign,0))"

MONTHLY=f"""
SELECT DATE_FORMAT(f.order_created_date,'yyyy-MM') AS period,
  p.group_name AS grp,
  COUNT(*) AS orders,
  COUNT(DISTINCT f.provider_id) AS locations,
  SUM(f.order_gmv_eur) AS gmv,
  SUM(COALESCE(f.commission_eur,0)) AS commission,
  SUM(COALESCE(f.order_service_fee_eur,0)+COALESCE(f.small_order_fee_eur,0)) AS eater_fees,
  SUM({BOLT}) AS camp_bolt,
  SUM({MERCH}) AS camp_merch,
  SUM(COALESCE(f.delivery_price_after_discount_eur,0)) AS delivery_rev,
  SUM(COALESCE(f.courier_earning_eur,0)+COALESCE(f.courier_bonus_eur,0)) AS courier_cost,
  SUM(COALESCE(f.total_refunds_eur,0)) AS refunds,
  SUM(COALESCE(f.demand_incentives_eur,0)) AS demand_incentives,
  SUM(COALESCE(f.supply_incentives_eur,0)) AS supply_incentives
FROM hive_metastore.ng_delivery_spark.fact_order_delivery f
JOIN hive_metastore.ng_delivery_spark.dim_provider_v2 p ON f.provider_id=p.provider_id
WHERE p.country_code='ua' AND f.order_state='delivered'
  AND p.delivery_vertical LIKE 'store%'
  AND f.order_created_date>=DATE'{START}' AND f.order_created_date<=DATE'{END}'
GROUP BY 1,2
"""

DIM=f"""
SELECT p.group_name AS grp, p.brand_name AS brand,
  p.business_segment_v2 AS seg, p.provider_status AS status,
  p.account_manager_name AS am, p.city_name AS city,
  COUNT(DISTINCT p.provider_id) AS stores
FROM hive_metastore.ng_delivery_spark.dim_provider_v2 p
WHERE p.country_code='ua' AND p.delivery_vertical LIKE 'store%'
GROUP BY 1,2,3,4,5,6
"""

# managed partners across ALL verticals (capture food parts of SANTIM/OKKO/LIKI etc.)
MG=("'LEPRUKON','DIMPYVA','CHILL TIME','RODYNNA KOVBASKA','NO TABOO','VAPE SHOP KYIV','VAPORS',"
    "'HOP HEY','BEER MARKET','KOPIYKA','LOKO','PYVNA BORODA','SANTIM','BRSM','CAFE RYNOK',"
    "'BEERLAND','WINETIME','SPRAGA','MAXBEER','FLOWERS','TAISTRA','SPAR','RUKAVYCHKA',"
    "'REMESLO BREWERY','TOCHKA','FLOWER SHOP','OKKO CAFE GROUP','LIKI24','VARUS','ROZETKA',"
    "'ATB CHERKASY','ATB KYIV'")
MAN_MONTHLY=MONTHLY.replace("AND p.delivery_vertical LIKE 'store%'", f"AND p.group_name IN ({MG})")
MAN_DIM=DIM.replace("WHERE p.country_code='ua' AND p.delivery_vertical LIKE 'store%'",
                    f"WHERE p.country_code='ua' AND p.group_name IN ({MG})")

print("fetching monthly..."); m=q(MONTHLY); print("monthly rows",len(m))
print("fetching dim..."); d=q(DIM); print("dim rows",len(d))
print("fetching managed monthly..."); mm=q(MAN_MONTHLY); print("managed monthly rows",len(mm))
print("fetching managed dim..."); md=q(MAN_DIM); print("managed dim rows",len(md))
json.dump({"monthly":m,"dim":d,"man_monthly":mm,"man_dim":md,"start":START,"end":END},
          open(HERE/"dbx_cache.json","w"),ensure_ascii=False)
cur.close(); conn.close()
# quick sanity
import collections
g=collections.defaultdict(float)
for r in m: g[r["grp"]]+=r["gmv"] or 0
print("total GMV Jan-May:",round(sum(g.values())))
for name in ["LOKO","KOPIYKA","HOP HEY","BEER MARKET"]:
    print(name,"->",round(g.get(name,0)))
