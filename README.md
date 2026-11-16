# Лабораторна робота №2. Функції вищого порядку, lambda, композиція

**Студентка:** Зьомків А. І., група ФЕП-21
**Варіант:** 6 — «Рейтинг книг»

## Мета
Побудувати конвеєр перетворень над списком записів без мутацій, використовуючи
`map` / `filter` / `reduce`, `lambda`, функції вищого порядку та композицію.

## Варіант
**Запис:** книга `{id, title, genre, ratings}`, де `ratings` — оцінки читачів 1–5.

**Конвеєр** (збирається через `pipe` / `compose`):
1. `normalize_fields` — прибрати зайві пробіли в назві, жанр у нижній регістр (`map`);
2. `only_rated(min_votes)` — лише книги з достатньою кількістю оцінок (`filter`);
3. `with_avg_rating` — середній рейтинг (генератор);
4. `boost_genre(genre, factor)` — підсилити score вибраного жанру (`map`);
5. `drop_low(min_score)` — відкинути низький рейтинг (генераторний вираз);
6. `sort_by_score_desc` — сортування за двома ключами: score ↓, кількість оцінок ↓, id ↑;
7. `take(n)` — Top-N через `itertools.islice`.

**reduce-агрегація:** `reduce_stats` → `count`, `rating_sum`, `avg_rating`;
додатково `genre_counts` — кількість книг за жанрами.

## Структура
```
lab02/
├── core.py            # чисте ядро: трансформації, compose/pipe, reduce
├── app.py             # I/O: CLI-аргументи, читання JSON, друк
├── data/books.json    # вхідні дані
├── tests/test_core.py # pytest
├── pyproject.toml     # налаштування black, ruff, mypy (strict), pytest
└── requirements.txt
```

## Запуск
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

pytest -q
python main.py --top 5 --boost-genre фентезі --factor 1.1
python main.py --top 3 --boost-genre детектив --factor 1.2 --min-rating 4

black --check .
ruff check .
mypy core.py app.py tests/
```
