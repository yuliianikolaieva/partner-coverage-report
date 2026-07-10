# Partner Portfolio — Coverage & Segmentation

Internal report for management (director + sales director): how many partners we have,
how they split by segment (Enterprise / Mid-market / SMB), turnover (GMV) and profitability,
how much the team currently covers, and why there is no capacity to take on new partners —
especially in SMB / MM.

## Structure

- `index.html` — the report (published to GitHub Pages). English.
- `fetch_dbx.py` — pulls per-partner (group_name) per-month metrics from Databricks (Jan–Jun 2026) → `dbx_cache.json`.
- `build_data.py` — aggregates the cache into `data.json` (segments, managed partners, team load, full list, trends).
- `build_html.py` — renders `index.html` from `data.json`.

## How to refresh

```bash
python3 fetch_dbx.py     # pull fresh data from Databricks (needs VARUS/.env credentials)
python3 build_data.py    # aggregate
python3 build_html.py    # render index.html
```

## Data & definitions

Source: Databricks `hive_metastore.ng_delivery_spark.fact_order_delivery` joined to
`dim_provider_v2`, Bolt UA, `delivery_vertical = store`, delivered orders, Jan–Jun 2026.
GMV is before discounts, in EUR. Partner = `group_name`, location = provider.

- **CP L1** = commission + eater fees + delivery revenue − courier cost − demand incentives − Bolt campaign spend − refunds. (Validated against the Key Account dashboard: ≈ −0.1% of GMV.)
- **Eater fees** = service fee + small order fee.
- **Camp Bolt / Camp Merch** = campaign spend funded by Bolt / by the merchant.

Account managers are set manually for the 38 managed partners (`am_map` in `build_data.py`):
Mykhailo Brynchak, Viktor Skalivskiy, Khrystyna Berezna. For all other partners the AM comes
from `dim_provider_v2.account_manager_name` (or "Not assigned").

7 chains from the managed list (FORA, ANRI, E-ZOO, master zoo, THRASH, РОСТ, O'NDE) are not on
Bolt UA stores in the period and are shown as "centralised".
