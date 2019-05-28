from kirby.api.ext import Topic
from kirby.api import Table


def process_generator(key):
    def process_orders(orders):
        return orders[key]

    return process_orders


def test_it_compute_table(kirby_app):
    orders = Topic(kirby_app, "ORDERS_TOPIC_NAME")
    cashregister = Topic(kirby_app, "CASHREGISTER_TOPIC_NAME")

    t = Table(
        [
            ["product", "sum_volume", "sum_price"],
            ["bread", "4", "6"],
            ["pain chocolat", "10", "15"],
        ]
    )
    t.add_listener(
        orders,
        (slice(1, 3), slice(1, 3)),
        params={
            (0, 0): process_generator("bread_volume"),
            (0, 1): process_generator("bread_price"),
            (1, 0): process_generator("pain_chocolat_volume"),
            (1, 1): process_generator("pain_chocolat_price"),
        },
    )
    t.add_listener(
        cashregister,
        (slice(1, 3), slice(1, 3)),
        params={
            (0, 0): process_generator("bread_volume"),
            (0, 1): process_generator("bread_price"),
            (1, 0): process_generator("pain_chocolat_volume"),
            (1, 1): process_generator("pain_chocolat_price"),
        },
    )

    orders.send(
        {
            "bread_volume": 1,
            "bread_price": 1.5,
            "pain_chocolat_volume": 2,
            "pain_chocolat_price": 3,
        }
    )

    cashregister.send({"bread_volume": 5, "bread_price": 7.5})

    assert t[1:3][1:3] == [[10, 15], [12, 18]]
