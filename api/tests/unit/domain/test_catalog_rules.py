from datetime import date

from builders import product

from price_scout.domain.catalog.models import Product
from price_scout.domain.catalog.rules import preference_matches, rank_by_preference, search_id_for

DAY = date(2026, 11, 16)


def test_search_id_ignores_case_and_extra_spaces() -> None:
    assert search_id_for("Sofá  3 Lugares ", "br", DAY) == search_id_for(
        "sofá 3 lugares", "br", DAY
    )


def test_search_id_differs_for_different_queries() -> None:
    assert search_id_for("sofá 3 lugares", "br", DAY) != search_id_for("sofá 2 lugares", "br", DAY)


def test_the_same_query_in_another_country_is_another_search() -> None:
    assert search_id_for("sofa", "br", DAY) != search_id_for("sofa", "pt", DAY)


def test_the_same_query_on_another_day_is_a_fresh_search() -> None:
    assert search_id_for("sofa", "br", DAY) != search_id_for("sofa", "br", date(2026, 11, 17))


def named(name: str, price: float) -> Product:
    return product(f"p-{name}", prices=(price,)).model_copy(update={"name": name})


def test_products_with_the_preferred_color_come_first_then_by_price() -> None:
    products = [
        named("Ipanema Classica Flip-Flops", 9.69),
        named("Ipanema Diversa Flat Sandals", 34.99),
        named("Ipanema Solar Sandals, Red", 35.0),
        named("Ipanema Women's Sandals, Tomato Red and Pink", 317.52),
    ]

    ranked = rank_by_preference(products, ["red"])

    assert [p.min_price for p in ranked] == [35.0, 317.52, 9.69, 34.99]


def test_a_preference_matches_whole_words_ignoring_case_and_accents() -> None:
    assert preference_matches("Sandália Vermelha", ["vermelha"]) == 1
    assert preference_matches("Ipanema Solar Sandals, RED", ["red"]) == 1
    assert preference_matches("Shredder Bag", ["red"]) == 0
    assert preference_matches("Whey 900 g, Vanilla", ["vanilla", "isolate"]) == 1
    assert preference_matches("Anything", ["", "  "]) == 0


def test_without_preferences_the_cheapest_come_first() -> None:
    products = [named("B", 20), named("A", 10)]

    assert [p.min_price for p in rank_by_preference(products, [])] == [10, 20]
