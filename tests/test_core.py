from copy import deepcopy

import pytest

from core import (
    Book,
    boost_genre,
    build_pipeline,
    build_ranking,
    compose,
    genre_counts,
    normalize_fields,
    pipe,
    reduce_stats,
    sort_by_score_desc,
    take,
    with_avg_rating,
)


@pytest.fixture
def books() -> list[Book]:
    return [
        {"id": 1, "title": "a", "genre": "Fantasy", "ratings": [5, 5, 4]},
        {"id": 2, "title": "b", "genre": "drama", "ratings": [4, 4, 4, 4]},
        {"id": 3, "title": "c", "genre": "fantasy", "ratings": [3, 3, 3]},
        {"id": 4, "title": "d", "genre": "drama", "ratings": [5, 5]},
        {"id": 5, "title": "e", "genre": "drama", "ratings": [4, 4, 4]},
    ]


def test_top_n_order_and_size(books: list[Book]) -> None:
    top = build_pipeline(
        top_n=3, genre="fantasy", factor=1.2, min_score=3.5, min_votes=3
    )(books)
    # 1: 4.67*1.2=5.6; 2 і 5: 4.0 (у №2 більше оцінок); №3: 3.0*1.2=3.6; №4 мало оцінок
    assert [b["id"] for b in top] == [1, 2, 5]
    assert [b["score"] for b in top] == [5.6, 4.0, 4.0]


def test_full_ranking_contains_boosted_book(books: list[Book]) -> None:
    ranking = build_ranking(genre="fantasy", factor=1.2, min_score=3.5, min_votes=3)(
        books
    )
    assert [b["id"] for b in ranking] == [1, 2, 5, 3]


def test_without_boost_low_rating_is_dropped(books: list[Book]) -> None:
    ranking = build_ranking(genre="fantasy", factor=1.0, min_score=3.5, min_votes=3)(
        books
    )
    assert 3 not in [b["id"] for b in ranking]


def test_no_mutation(books: list[Book]) -> None:
    original = deepcopy(books)
    build_pipeline(top_n=2, genre="fantasy", factor=1.2, min_score=3.5, min_votes=3)(
        books
    )
    assert books == original


def test_pipeline_is_repeatable(books: list[Book]) -> None:
    run = build_pipeline(top_n=3, genre="fantasy", factor=1.2, min_score=0, min_votes=1)
    assert run(books) == run(books)


def test_reduce_stats() -> None:
    sample: list[Book] = [{"avg_rating": 4.0}, {"avg_rating": 5.0}, {"avg_rating": 3.0}]
    assert reduce_stats(sample) == {"count": 3, "rating_sum": 12.0, "avg_rating": 4.0}


def test_reduce_stats_empty() -> None:
    assert reduce_stats([]) == {"count": 0, "rating_sum": 0.0, "avg_rating": 0.0}


def test_compose_and_pipe_order() -> None:
    inc = lambda x: x + 1  # noqa: E731
    double = lambda x: x * 2  # noqa: E731
    assert compose(inc, double)(3) == 7  # inc(double(3))
    assert pipe(inc, double)(3) == 8  # double(inc(3))


def test_stages_compose_like_manual_calls(books: list[Book]) -> None:
    manual = take(2)(sort_by_score_desc()(with_avg_rating()(books)))
    composed = compose(take(2), sort_by_score_desc(), with_avg_rating())(books)
    assert composed == manual


def test_normalize_fields() -> None:
    raw: list[Book] = [{"title": "  гобіт   або туди  ", "genre": " Фентезі "}]
    (clean,) = normalize_fields()(raw)
    assert clean["title"] == "Гобіт або туди"
    assert clean["genre"] == "фентезі"


def test_boost_only_selected_genre() -> None:
    raw: list[Book] = [
        {"id": 1, "genre": "fantasy", "score": 4.0},
        {"id": 2, "genre": "drama", "score": 4.0},
    ]
    boosted = list(boost_genre("Fantasy", 1.5)(raw))
    assert [b["score"] for b in boosted] == [6.0, 4.0]


def test_genre_counts(books: list[Book]) -> None:
    normalized = list(normalize_fields()(books))
    assert genre_counts(normalized) == {"fantasy": 2, "drama": 3}
