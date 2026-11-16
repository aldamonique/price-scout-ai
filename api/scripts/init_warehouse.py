from price_scout.config import Settings
from price_scout.infrastructure.duckdb.connection import open_warehouse


def main() -> None:
    settings = Settings()
    open_warehouse(settings.data_dir).close()
    print(f"warehouse ready at {settings.data_dir / 'warehouse.duckdb'}")


if __name__ == "__main__":
    main()
