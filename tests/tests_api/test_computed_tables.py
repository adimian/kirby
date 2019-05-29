from pytest import fixture, raises

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


def test_it_do_a_transaction(computed_table):
    with Transaction(computed_table):
        computed_table.bread.sum_volume += 3
        computed_table.bread.sum_price = (
            computed_table.bread.sum_volume * PRICE_BREAD
        )

        computed_table.pain_chocolat.sum_volume += 2
        computed_table.pain_chocolat.sum_price = (
            computed_table.pain_chocolat.sum_volume * PRICE_PAIN_CHOCOLAT
        )

        new_table = [
            [computed_table.bread.sum_volume, computed_table.bread.sum_price],
            [
                computed_table.pain_chocolat.sum_volume,
                computed_table.pain_chocolat.sum_price,
            ],
        ]
    assert computed_table == new_table

    with raises(ZeroDivisionError):
        with Transaction(computed_table):
            table.bread.sum_volume /= 0
    assert computed_table == new_table
