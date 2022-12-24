from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

CURRENCIES = {
    cur: [cur] + sorted(values, key=lambda val: len(val), reverse=True)
    for cur, values in {
        "шекель": ["шк", "ш", "шек"],
        "рубль": ["руб", "ру", "р", "r", "ru", "rub"],
        "драм": ["др", "д", "d", "dr"],
        "доллар": ["бакс", "бак", "долл", "дол", "do", "dol", "doll"],
        "евро": ["евр", "ев"],
        "лари": ["лр", "л"],
        "бат": ["бт"],
    }.items()
}


@dataclass
class RashodikInfo:
    amount: int
    currency: str
    description: str | None


class ParseErrorType(Enum):
    NO_AMOUNT = auto()
    NO_CURRENCY = auto()
    NO_DESCRIPTION = auto()


class ParseError(RuntimeError):
    def __init__(self, error: ParseErrorType):
        self.error = error


def parse_rashodik(msg: str) -> RashodikInfo:
    amount_str, _, remaining_str = msg.partition(" ")
    amount = _parse_amount(amount_str)
    currency, description = _parse_remaining(remaining_str)
    return RashodikInfo(amount=amount, currency=currency, description=description)


def _parse_amount(amount_str):
    try:
        multiplier = 1 if amount_str.startswith("+") else -1
        return multiplier * abs(int(amount_str))
    except ValueError:
        raise ParseError(error=ParseErrorType.NO_AMOUNT)


def _parse_remaining(remaining: str) -> Tuple[str, str]:
    for currency, currency_strings in CURRENCIES.items():
        for currency_str in currency_strings:
            if remaining.lower().startswith(currency_str):
                remove_prefix = len(currency_str)
                description = remaining[remove_prefix:].strip()
                if not description:
                    raise ParseError(error=ParseErrorType.NO_DESCRIPTION)
                return currency, description
    raise ParseError(error=ParseErrorType.NO_CURRENCY)
