from pytest import fixture

from kirby.api import Table


def process_generator(key):
    def process_orders(orders):
        return orders[key]

    return process_orders


@fixture
def table():
    return [[4, 6], [10, 15]]


@fixture
def table_repr():
    return [
        ["item", "sum_volume", "sum_price"],
        ["bread", 4, 6],
        ["pain chocolat", 10, 15],
    ]


@fixture(scope="function")
def computed_table(table):
    return Table(
        table,
        headers=["sum_volume", "sum_price"],
        index=["bread", "pain chocolat"],
    )


def test_it_creates_a_table(computed_table, table, table_repr):
    assert computed_table == table
    assert repr(computed_table) == table_repr


@fixture
def computed_table_with_listeners(
    kirby_app, kirby_topic_factory, computed_table
):
    orders = kirby_topic_factory("orders")
    cashregister = kirby_topic_factory("cashregister")

    computed_table.add_listener(
        orders,
        params={
            (0, 0): process_generator("bread_volume"),
            (0, 1): process_generator("bread_price"),
            (1, 0): process_generator("pain_chocolat_volume"),
            (1, 1): process_generator("pain_chocolat_price"),
        },
    )
    computed_table.add_listener(
        cashregister,
        params={
            (0, 0): process_generator("bread_volume"),
            (0, 1): process_generator("bread_price"),
            (1, 0): process_generator("pain_chocolat_volume"),
            (1, 1): process_generator("pain_chocolat_price"),
        },
    )
    return computed_table, [orders, cashregister]


def test_it_add_listener(computed_table_with_listeners):
    computed_table, topics = computed_table_with_listeners
    orders, cashregister = topics

    orders.send(
        {
            "bread_volume": 1,
            "bread_price": 1.5,
            "pain_chocolat_volume": 2,
            "pain_chocolat_price": 3,
        }
    )

    cashregister.send({"bread_volume": 5, "bread_price": 7.5})

    assert computed_table == [[10, 15], [12, 18]]
