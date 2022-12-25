from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple, Optional

from rashodiki_bot.model import Chat

CURRENCIES = {
    cur: sorted([cur] + values, key=lambda val: len(val), reverse=True)
    for cur, values in {
        "шекель": ["шк", "ш", "шек"],
        "рубль": ["руб", "ру", "р", "r", "ru", "rub", "₽"],
        "драм": ["др", "д", "d", "dr"],
        "доллар": ["бакс", "бак", "долл", "дол", "do", "dol", "doll", "$", "баксов", "грина"],
        "евро": ["евр", "ев", "€"],
        "лари": ["лр", "л"],
        "бат": ["бт"],
        "тенге": ["тг"],
    }.items()
}


@dataclass
class SpendInfo:
    amount: int
    currency: str | None
    description: str


class ParseErrorType(Enum):
    NO_AMOUNT = auto()
    NO_DESCRIPTION = auto()


class ParseError(RuntimeError):
    def __init__(self, error: ParseErrorType):
        self.error = error


def parse_rashodik(msg: str, chat: Chat) -> SpendInfo:
    amount_str, _, remaining_str = msg.partition(" ")
    amount, currency = _parse_amount(amount_str)
    if not currency:
        currency = chat.default_currency
    description = remaining_str.strip()
    if not description:
        raise ParseError(error=ParseErrorType.NO_DESCRIPTION)
    return SpendInfo(amount=amount, currency=currency, description=description)


def _parse_amount(amount_str) -> Tuple[int, Optional[str]]:
    amount_str = amount_str.strip()
    multiplier = 1 if amount_str.startswith("+") else -1

    currency, currency_str = _find_currency(amount_str)
    amount_str = "".join(filter(str.isdigit, amount_str))

    try:
        return multiplier * abs(int(amount_str)), currency
    except ValueError:
        raise ParseError(error=ParseErrorType.NO_AMOUNT)


def _find_currency(line) -> Tuple[Optional[str], Optional[str]]:
    line = "".join(filter(lambda c: not (str.isdigit(c) or c in ("+", "-")), line))
    for currency, currency_strings in CURRENCIES.items():
        for currency_str in currency_strings:
            if line.lower() == currency_str:
                return currency, currency_str
    return None, None
