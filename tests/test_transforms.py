from datetime import date

from dab_starter.transforms import clean_orders, daily_revenue

COLUMNS = "o_orderkey long, o_orderdate date, o_totalprice double"


def test_clean_orders_drops_null_and_duplicate_keys(spark):
    df = spark.createDataFrame(
        [
            (1, date(2024, 1, 1), 10.0),
            (1, date(2024, 1, 1), 10.0),
            (None, date(2024, 1, 1), 5.0),
        ],
        COLUMNS,
    )
    assert [r.o_orderkey for r in clean_orders(df).collect()] == [1]


def test_daily_revenue_sums_per_day(spark):
    df = spark.createDataFrame(
        [
            (1, date(2024, 1, 1), 10.0),
            (2, date(2024, 1, 1), 5.5),
            (3, date(2024, 1, 2), 1.0),
        ],
        COLUMNS,
    )
    rows = {r.order_date: (r.revenue, r.orders) for r in daily_revenue(df).collect()}
    assert rows == {date(2024, 1, 1): (15.5, 2), date(2024, 1, 2): (1.0, 1)}
