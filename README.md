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

Джерело: `Key Account dashboard/data/Merchant-level Overview.csv` (Bolt UA).
Партнер = Group/Brand, локація = окремий provider. GMV — до знижок.

8 великих мереж зі списку ведення (ATB, FORA, ANRI, ROZETKA, VARUS, THRASH, E-ZOO, РОСТ)
ведуться централізовано як key accounts і відсутні в цьому датасеті — у звіті позначені окремо.
