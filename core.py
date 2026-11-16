"""Чисте ядро: функціональний конвеєр рейтингу книг (варіант 6).

Кожна трансформація — фабрика, що повертає функцію
Iterable[Book] -> Iterable[Book]. Вхідні записи ніколи не змінюються:
кожен крок створює нові словники через {**book, ...}.
"""

from collections.abc import Callable, Iterable, Iterator
from functools import reduce
from itertools import islice
from typing import Any, TypedDict


class Book(TypedDict, total=False):
    id: int
    title: str
    genre: str
    ratings: list[int]  # оцінки читачів 1..5
    avg_rating: float  # з'являється в конвеєрі
    score: float  # підсилений рейтинг для сортування


class Stats(TypedDict):
    count: int
    rating_sum: float
    avg_rating: float


Stage = Callable[[Iterable[Book]], Iterable[Book]]


# ---------- Композиція ----------


def compose(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """compose(f, g, h)(x) == f(g(h(x))) — справа наліво."""
    return lambda x: reduce(lambda acc, f: f(acc), reversed(funcs), x)


def pipe(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """pipe(h, g, f)(x) == f(g(h(x))) — зліва направо, у порядку читання."""
    return compose(*reversed(funcs))


# ---------- Чисті трансформації ----------


def normalize_fields() -> Stage:
    """Назва: без зайвих пробілів і з великої літери; жанр: у нижньому регістрі."""

    def _clean(title: str) -> str:
        text = " ".join(title.split())
        return text[:1].upper() + text[1:]

    return lambda books: map(
        lambda b: {
            **b,
            "title": _clean(b.get("title", "")),
            "genre": b.get("genre", "").strip().lower(),
        },
        books,
    )


def only_rated(min_votes: int) -> Stage:
    """Відкидає книги, у яких замало оцінок для чесного середнього."""
    return lambda books: filter(lambda b: len(b.get("ratings", [])) >= min_votes, books)


def with_avg_rating() -> Stage:
    def _avg(ratings: list[int]) -> float:
        return round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    def _stage(books: Iterable[Book]) -> Iterator[Book]:
        for b in books:
            avg = _avg(b.get("ratings", []))
            yield {**b, "avg_rating": avg, "score": avg}

    return _stage


def boost_genre(genre: str, factor: float) -> Stage:
    """Підсилює score книг вибраного жанру (регістр не враховується)."""
    target = genre.strip().lower()

    def _boost(b: Book) -> Book:
        score = b.get("score", 0.0)
        if b.get("genre", "").lower() == target:
            score = round(score * factor, 2)
        return {**b, "score": score}

    return lambda books: map(_boost, books)


def drop_low(min_score: float) -> Stage:
    return lambda books: (b for b in books if b.get("score", 0.0) >= min_score)


def sort_by_score_desc() -> Callable[[Iterable[Book]], list[Book]]:
    """Два ключі: score спадно, при рівності — більше оцінок, далі id зростанням."""
    return lambda books: sorted(
        books,
        key=lambda b: (
            -b.get("score", 0.0),
            -len(b.get("ratings", [])),
            b.get("id", 0),
        ),
    )


def take(n: int) -> Callable[[Iterable[Book]], list[Book]]:
    return lambda books: list(islice(books, n))


# ---------- reduce-агрегація ----------


def reduce_stats(books: Iterable[Book]) -> Stats:
    count, total = reduce(
        lambda acc, b: (acc[0] + 1, acc[1] + b.get("avg_rating", 0.0)),
        books,
        (0, 0.0),
    )
    return {
        "count": count,
        "rating_sum": round(total, 2),
        "avg_rating": round(total / count, 2) if count else 0.0,
    }


def genre_counts(books: Iterable[Book]) -> dict[str, int]:
    """Скільки книг кожного жанру (reduce з новим словником на кожному кроці)."""
    return reduce(
        lambda acc, b: {
            **acc,
            b.get("genre", "?"): acc.get(b.get("genre", "?"), 0) + 1,
        },
        books,
        {},
    )


# ---------- Складання конвеєра ----------


def build_ranking(
    *, genre: str, factor: float, min_score: float, min_votes: int
) -> Callable[[Iterable[Book]], list[Book]]:
    """Повний відсортований рейтинг (без обрізання до Top-N)."""
    return pipe(
        normalize_fields(),
        only_rated(min_votes),
        with_avg_rating(),
        boost_genre(genre, factor),
        drop_low(min_score),
        sort_by_score_desc(),
    )


def build_pipeline(
    *,
    top_n: int,
    genre: str,
    factor: float,
    min_score: float,
    min_votes: int,
) -> Callable[[Iterable[Book]], list[Book]]:
    """Рейтинг + Top-N, зібрані через compose (читається справа наліво)."""
    ranking = build_ranking(
        genre=genre, factor=factor, min_score=min_score, min_votes=min_votes
    )
    return compose(take(top_n), ranking)
