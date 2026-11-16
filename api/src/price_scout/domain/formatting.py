CURRENCY_SYMBOLS = {
    "BRL": "R$",
    "USD": "US$",
    "EUR": "€",
    "GBP": "£",
    "CAD": "CA$",
    "AUD": "A$",
    "MXN": "MX$",
    "ARS": "AR$",
    "CLP": "CLP$",
    "COP": "COL$",
    "JPY": "¥",
}


def money(value: float, currency: str) -> str:
    return f"{CURRENCY_SYMBOLS.get(currency, currency)} {value:,.2f}"


def format_dimensions(
    width_cm: float | None, depth_cm: float | None, height_cm: float | None
) -> str | None:
    if width_cm is None:
        return None
    if depth_cm is None or height_cm is None:
        return f"{_meters(width_cm)} m wide"
    return " x ".join(_meters(cm) for cm in (width_cm, depth_cm, height_cm)) + " m"


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    if count == 1:
        return f"1 {singular}"
    return f"{count} {plural_form or singular + 's'}"


def _meters(cm: float) -> str:
    return f"{cm / 100:.2f}"
