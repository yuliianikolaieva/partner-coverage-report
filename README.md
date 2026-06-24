# Покриття та сегментація партнерського портфеля

Внутрішній звіт для керівництва (директор + директор з продажів): скільки в нас партнерів,
як вони діляться за сегментами (Enterprise / Mid-market / SMB), товарообіг (GMV) та прибутковість,
який обсяг команда веде сьогодні і чому немає капасіті брати нових партнерів — особливо SMB/MM.

## Структура

- `index.html` — готовий звіт (публікується на GitHub Pages).
- `build_data.py` — читає `Merchant-level Overview.csv` з Key Account dashboard, рахує агрегати → `data.json`.
- `build_html.py` — генерує `index.html` з `data.json`.
- `data.json` — проміжні агреговані дані.

## Як оновити

```bash
python3 build_data.py   # перерахувати агрегати з CSV
python3 build_html.py   # згенерувати index.html
```

## Дані

Джерела:
- `Key Account dashboard/data/Merchant-level Overview.csv` — знімок портфеля (сегменти, GMV, комісія, локації).
- `Key Account dashboard/data/Entity performance dynamics (PoP) (2).csv` — помісячний GMV (січ–кві 2026) для відстежуваних партнерів.
- `Active store/active_stores_from_dbx.csv` — щотижневі активні магазини → тренд локацій (січ–тра 2026).

Партнер = Group/Brand, локація = окремий provider. GMV — до знижок.

Менеджери ведення задані вручну в `build_data.py` (`am_override`): Mykhailo Brynchak,
Viktor Skalivskiy, Khrystyna Berezna. 9 великих мереж (ATB, FORA, ANRI, ROZETKA, VARUS,
THRASH, E-ZOO, РОСТ, master zoo) ведуться централізовано і позначені у звіті окремо.
