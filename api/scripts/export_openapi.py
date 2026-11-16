import json
import sys
from pathlib import Path
from typing import Any, cast

from price_scout.presentation.app import UseCases, create_app


def main(target: Path) -> None:
    unused = cast(Any, None)
    app = create_app(UseCases(*[unused] * 7))
    document = json.dumps(app.openapi(), indent=2) + "\n"
    target.write_bytes(document.encode("utf-8"))
    print(f"OpenAPI schema written to {target}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json"))
