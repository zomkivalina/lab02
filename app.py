"""Оболонка I/O: аргументи командного рядка, читання JSON, друк рейтингу."""

import argparse
import json
from pathlib import Path

from core import Book, Stats, build_pipeline, build_ranking, genre_counts, reduce_stats

DEFAULT_DATA = Path(__file__).parent / "data" / "books.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Рейтинг книг (лабораторна №2, варіант 6)")
    p.add_argument("--data", type=Path, default=DEFAULT_DATA, help="JSON з книгами")
    p.add_argument("--top", type=int, default=5, help="скільки книг у Top-N")
    p.add_argument("--boost-genre", default="фентезі", help="жанр для підсилення")
    p.add_argument("--factor", type=float, default=1.1, help="коефіцієнт підсилення")
    p.add_argument("--min-rating", type=float, default=3.5, help="поріг рейтингу")
    p.add_argument("--min-votes", type=int, default=3, help="мінімум оцінок")
    return p.parse_args()


def load_books(path: Path) -> list[Book]:
    with path.open(encoding="utf-8") as f:
        books: list[Book] = json.load(f)
    return books


def print_table(books: list[Book]) -> None:
    print(
        f"{'#':>2}  {'ID':>3}  {'Назва':<36} {'Жанр':<14} {'Оцінок':>6}"
        f"  {'Сер.':>5}  {'Score':>5}"
    )
    print("-" * 82)
    for place, b in enumerate(books, start=1):
        print(
            f"{place:>2}  {b['id']:>3}  {b['title']:<36} {b['genre']:<14} "
            f"{len(b['ratings']):>6}  {b['avg_rating']:>5.2f}  {b['score']:>5.2f}"
        )


def print_stats(title: str, stats: Stats) -> None:
    print(
        f"{title}: count = {stats['count']}, rating_sum = {stats['rating_sum']:.2f}, "
        f"avg_rating = {stats['avg_rating']:.2f}"
    )


def run() -> None:
    args = parse_args()
    books = load_books(args.data)
    genre: str = args.boost_genre
    factor: float = args.factor
    min_score: float = args.min_rating
    min_votes: int = args.min_votes

    top = build_pipeline(
        top_n=args.top,
        genre=genre,
        factor=factor,
        min_score=min_score,
        min_votes=min_votes,
    )(books)
    ranking = build_ranking(
        genre=genre, factor=factor, min_score=min_score, min_votes=min_votes
    )(books)

    print(
        f"TOP-{args.top} КНИГ  (підсилення: «{args.boost_genre}» x{args.factor}, "
        f"поріг {args.min_rating}, мін. оцінок {args.min_votes})"
    )
    print("=" * 82)
    print_table(top)
    print("=" * 82)
    print_stats("Top-N         ", reduce_stats(top))
    print_stats("Усі в рейтингу", reduce_stats(ranking))
    print(f"Жанри в рейтингу: {genre_counts(ranking)}")
    print(f"Усього книг у файлі: {len(books)}, пройшли фільтри: {len(ranking)}")


if __name__ == "__main__":
    run()
