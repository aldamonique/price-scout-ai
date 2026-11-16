from price_scout.domain.catalog.models import Market

MARKETS: dict[str, Market] = {
    market.country: market
    for market in (
        Market(country="br", language="pt-br", currency="BRL"),
        Market(country="us", language="en", currency="USD"),
        Market(country="ca", language="en", currency="CAD"),
        Market(country="mx", language="es", currency="MXN"),
        Market(country="ar", language="es", currency="ARS"),
        Market(country="gb", language="en", currency="GBP"),
        Market(country="pt", language="pt-pt", currency="EUR"),
        Market(country="es", language="es", currency="EUR"),
        Market(country="fr", language="fr", currency="EUR"),
        Market(country="de", language="de", currency="EUR"),
        Market(country="it", language="it", currency="EUR"),
        Market(country="au", language="en", currency="AUD"),
    )
}


def market_for(country: str) -> Market:
    return MARKETS[country.lower()]
