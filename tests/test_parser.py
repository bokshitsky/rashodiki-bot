import pytest

from rashodiki_bot.parser import _parse_amount

testdata = [
    (" 1500р ", -1500, "рубль"),
    ("1500 ", -1500, None),
    ("1500рУбль ", -1500, "рубль"),
    (" 1500рУбль ", -1500, "рубль"),
    (" -1500рУбль ", -1500, "рубль"),
    (" +1500рУбль ", 1500, "рубль"),
    (" +1597dr ", 1597, "драм"),
]


@pytest.mark.parametrize("line, expected_amount, expected_currency", testdata)
def test_parse_amount(line, expected_amount, expected_currency):
    amount, currency = _parse_amount(line)
    assert amount == expected_amount
    assert currency == expected_currency
