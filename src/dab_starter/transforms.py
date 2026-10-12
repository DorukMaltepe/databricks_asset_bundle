"""Pure DataFrame -> DataFrame functions. No I/O here, so they can be unit tested locally."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def clean_orders(orders: DataFrame) -> DataFrame:
    """Drop orders without a key and keep one row per key."""
    return orders.filter(F.col("o_orderkey").isNotNull()).dropDuplicates(["o_orderkey"])


def daily_revenue(orders: DataFrame) -> DataFrame:
    """Total order value and order count per day."""
    return orders.groupBy(F.col("o_orderdate").alias("order_date")).agg(
        F.sum("o_totalprice").alias("revenue"),
        F.count("*").alias("orders"),
    )
