from pytest import fixture

from kirby.api import Table, Transaction

PRICE_BREAD = 0.95
VOLUME_BREAD = 4
SUM_PRICE_BREAD = PRICE_BREAD * VOLUME_BREAD

PRICE_PAIN_CHOCOLAT = 1.5
VOLUME_PAIN_CHOCOLAT = 10
SUM_PRICE_PAIN_CHOCOLAT = PRICE_PAIN_CHOCOLAT * VOLUME_BREAD


@fixture
def table():
    return [
        [VOLUME_BREAD, SUM_PRICE_BREAD],
        [VOLUME_PAIN_CHOCOLAT, SUM_PRICE_PAIN_CHOCOLAT],
    ]


@fixture
def table_repr():
    return [
        ["item", "sum_volume", "sum_price"],
        ["bread", VOLUME_BREAD, SUM_PRICE_BREAD],
        ["pain chocolat", VOLUME_PAIN_CHOCOLAT, SUM_PRICE_PAIN_CHOCOLAT],
    ]


@fixture(scope="function")
def computed_table(table):
    with Table(
        table,
        headers=["sum_volume", "sum_price"],
        index=["bread", "pain chocolat"],
    ) as computed_table:
        yield computed_table


def test_it_creates_a_table(computed_table, table, table_repr):
    assert computed_table == table
    assert repr(computed_table) == table_repr


def test_it_add_listener(computed_table):
    with Transaction(computed_table):
        table.bread.sum_volume += 3
        table.bread.sum_price = table.bread.sum_volume * PRICE_BREAD

        table.pain_chocolat.sum_volume += 2
        table.pain_chocolat.sum_price = (
            table.pain_chocolat.sum_volume * PRICE_PAIN_CHOCOLAT
        )

        new_table = [
            [table.bread.sum_volume, table.bread.sum_price],
            [table.pain_chocolat.sum_volume, table.pain_chocolat.sum_price],
        ]
    assert computed_table == new_table
