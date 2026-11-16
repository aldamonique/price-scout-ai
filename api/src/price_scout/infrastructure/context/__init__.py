from pathlib import Path

import yaml

from price_scout.domain.catalog.markets import MARKETS
from price_scout.domain.catalog.store_policy import StorePolicies, StorePolicy

CONTEXT_FILE = Path(__file__).parent / "business_context.yml"
STORE_POLICY_FILE = Path(__file__).parent / "store_policy.yml"


def load_business_context() -> str:
    text = CONTEXT_FILE.read_text(encoding="utf-8")
    yaml.safe_load(text)
    return text


def load_store_policies(path: Path = STORE_POLICY_FILE) -> StorePolicies:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    default = data["default"]
    blocked = list(default["blocked"])
    reason = _text(default["reason"])

    by_country: dict[str, StorePolicy] = {}
    for country, rules in (data.get("markets") or {}).items():
        if country not in MARKETS:
            raise ValueError(f"{path.name}: unknown market {country!r}")
        allowed = {name.lower() for name in rules.get("allowed", [])}
        names = [name for name in blocked if name.lower() not in allowed]
        names += rules.get("also_blocked", [])
        by_country[country] = StorePolicy(
            blocked=tuple(names), reason=_text(rules.get("reason", reason))
        )
    return StorePolicies(StorePolicy(blocked=tuple(blocked), reason=reason), by_country)


def _text(value: str) -> str:
    return " ".join(value.split())
