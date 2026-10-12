"""Job entry point: the only place that reads or writes tables."""

import argparse

from pyspark.sql import SparkSession

from dab_starter.transforms import clean_orders, daily_revenue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args()
    target = f"`{args.catalog}`.`{args.schema}`"

    spark = SparkSession.builder.getOrCreate()
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {target}")
    orders = spark.read.table("samples.tpch.orders")
    daily_revenue(clean_orders(orders)).write.mode("overwrite").saveAsTable(f"{target}.daily_revenue")


if __name__ == "__main__":
    main()
