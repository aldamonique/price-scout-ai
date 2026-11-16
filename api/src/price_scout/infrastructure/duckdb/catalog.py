from collections.abc import Callable

import duckdb

from price_scout.domain.catalog.models import (
    Category,
    CategoryStats,
    Offer,
    Product,
    SearchIntent,
    StoreOffer,
)
from price_scout.domain.formatting import format_dimensions
from price_scout.infrastructure.duckdb.connection import fetch_dicts, fetch_one
from price_scout.infrastructure.duckdb.medallion import MedallionSql


class DuckDbCatalog:
    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        medallion: MedallionSql,
        bronze_file: Callable[[str], str],
    ) -> None:
        self._connection = connection
        self._medallion = medallion
        self._bronze_file = bronze_file

    def offers(self, search_id: str) -> list[Offer]:
        cursor = self._connection.cursor()
        cursor.execute(
            self._search_sql(search_id)
            + """
            select offer_id, title, store, price, url, image_url
            from silver_offers
            order by price
            """,
            {"search_id": search_id},
        )
        return [Offer.model_validate(row) for row in fetch_dicts(cursor)]

    def products(self, search_id: str, intent: SearchIntent) -> list[Product]:
        cursor = self._connection.cursor()
        cursor.execute(
            self._search_sql(search_id)
            + """
            select products.product_id, products.name, products.category,
                   products.width_cm, products.depth_cm, products.height_cm,
                   products.image_url, products.min_price, products.store_count,
                   offers.store, offers.price, offers.url, offers.store_icon,
                   offers.installment_months, offers.installment_amount
            from gold_products as products
            inner join gold_product_offers as offers
                on products.product_id = offers.product_id
            where ($max_price::double is null or products.min_price <= $max_price::double)
              and ($max_width::double is null or products.width_cm is null
                   or products.width_cm <= $max_width::double)
            order by products.min_price, products.product_id, offers.price
            """,
            {
                "search_id": search_id,
                "max_price": intent.max_price,
                "max_width": intent.max_width_cm,
            },
        )

        products: dict[str, Product] = {}
        for row in fetch_dicts(cursor):
            product = products.get(row["product_id"])
            if product is None:
                product = products[row["product_id"]] = Product(
                    id=row["product_id"],
                    name=row["name"],
                    category=row["category"],
                    width_cm=row["width_cm"],
                    dimensions=format_dimensions(
                        row["width_cm"], row["depth_cm"], row["height_cm"]
                    ),
                    image_url=row["image_url"],
                    min_price=row["min_price"],
                    store_count=row["store_count"],
                    offers=[],
                )
            product.offers.append(
                StoreOffer(
                    store=row["store"],
                    price=row["price"],
                    url=row["url"],
                    store_icon=row["store_icon"],
                    installment_months=row["installment_months"],
                    installment_amount=row["installment_amount"],
                )
            )
        return list(products.values())

    def category_stats(self, category: Category, country: str) -> CategoryStats:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            select count(*) as product_count,
                   avg(min_price) as avg_price,
                   min(min_price) as min_price,
                   max(min_price) as max_price
            from gold_products
            where category = ? and country = ?
            """,
            [category, country],
        )
        return CategoryStats.model_validate(
            {"category": category, "country": country, **fetch_one(cursor)}
        )

    def _search_sql(self, search_id: str) -> str:
        return self._medallion.for_search(self._bronze_file(search_id))
