from price_scout.domain.formatting import format_dimensions, money, plural


def test_money_uses_the_currency_symbol() -> None:
    assert money(1299.5, "BRL") == "R$ 1,299.50"
    assert money(1299.5, "EUR") == "€ 1,299.50"


def test_money_falls_back_to_the_currency_code() -> None:
    assert money(1299.5, "CHF") == "CHF 1,299.50"


def test_format_dimensions_uses_meters() -> None:
    assert format_dimensions(200, 90, 95) == "2.00 x 0.90 x 0.95 m"


def test_format_dimensions_shows_only_the_width_when_the_rest_is_missing() -> None:
    assert format_dimensions(210, None, None) == "2.10 m wide"


def test_format_dimensions_is_none_without_the_width() -> None:
    assert format_dimensions(None, 90, 95) is None


def test_plural_adds_an_s_by_default() -> None:
    assert (plural(1, "product"), plural(3, "product")) == ("1 product", "3 products")


def test_plural_accepts_an_irregular_form() -> None:
    assert plural(2, "discarded", "discarded") == "2 discarded"
