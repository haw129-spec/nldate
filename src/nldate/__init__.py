import re
from calendar import monthrange
from datetime import date, timedelta

__all__ = ["parse"]

_MONTHS = {
    name: number
    for number, aliases in enumerate(
        (
            ("january", "jan"),
            ("february", "feb"),
            ("march", "mar"),
            ("april", "apr"),
            ("may",),
            ("june", "jun"),
            ("july", "jul"),
            ("august", "aug"),
            ("september", "sept", "sep"),
            ("october", "oct"),
            ("november", "nov"),
            ("december", "dec"),
        ),
        start=1,
    )
    for name in aliases
}
_WEEKDAYS = {
    name: number
    for number, aliases in enumerate(
        (
            ("monday", "mon"),
            ("tuesday", "tues", "tue"),
            ("wednesday", "weds", "wed"),
            ("thursday", "thurs", "thur", "thu"),
            ("friday", "fri"),
            ("saturday", "sat"),
            ("sunday", "sun"),
        ),
    )
    for name in aliases
}
_SMALL_NUMBERS = {
    word: value
    for value, word in enumerate(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        ]
    )
}
_TENS = {
    word: value * 10
    for value, word in enumerate(
        ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"],
        start=2,
    )
}
_RELATIVE_DAYS = {
    "today": 0,
    "now": 0,
    "tomorrow": 1,
    "yesterday": -1,
    "day after tomorrow": 2,
    "the day after tomorrow": 2,
    "day before yesterday": -2,
    "the day before yesterday": -2,
}

_NUMERIC_MONTH = r"(?P<month>[0-9]{1,2})"
_NUMERIC_DAY = r"(?P<day>[0-9]{1,2})"
_YEAR = r"(?P<year>[0-9]{4}|[0-9]{2})"
_YEAR_FIRST = re.compile(
    rf"(?P<year>[0-9]{{4}})(?P<sep>[-/.]){_NUMERIC_MONTH}(?P=sep){_NUMERIC_DAY}"
)
_MONTH_FIRST = re.compile(
    rf"{_NUMERIC_MONTH}(?P<sep>[-/.]){_NUMERIC_DAY}(?:(?P=sep){_YEAR})?"
)
_NAMED_MONTH = rf"(?P<month>{'|'.join(_MONTHS)})\.?"
_ORDINAL_DAY = rf"{_NUMERIC_DAY}(?P<ordinal>st|nd|rd|th)?"
_OPTIONAL_YEAR = rf"(?:(?:, ?| ){_YEAR})?"
_NAMED_MONTH_FIRST = re.compile(rf"{_NAMED_MONTH} {_ORDINAL_DAY}{_OPTIONAL_YEAR}")
_NAMED_DAY_FIRST = re.compile(
    rf"(?:the )?{_ORDINAL_DAY} (?:of )?{_NAMED_MONTH}{_OPTIONAL_YEAR}"
)
_WEEKDAY = re.compile(
    rf"(?:(?P<direction>next|last|previous|this|on) )?"
    rf"(?P<weekday>{'|'.join(_WEEKDAYS)})\.?"
)
_PERIOD = re.compile(r"(?P<direction>next|last|previous) (?P<unit>day|week|month|year)")
_ANCHORED_OFFSET = re.compile(
    r"(?P<offset>.+?) (?P<direction>before|after|from) (?P<anchor>.+)"
)
_TODAY_OFFSET = re.compile(r"(?P<offset>.+) (?P<direction>ago|earlier|later|hence)")
_OFFSET_TERM = re.compile(
    r"(?P<number>[0-9]+|[a-z]+(?:[ -][a-z]+)?) (?P<unit>days?|weeks?|months?|years?)\b"
)
_OFFSET_SEPARATOR = re.compile(r" and |, ?(?:and )?| ")


def parse(s: str, today: date | None = None) -> date:
    """Parse an English date expression using today as the reference date.

    Raise ValueError for unrecognized expressions or impossible dates.
    """
    reference = date.today() if today is None else today
    expression = " ".join(s.casefold().split())
    try:
        return _parse(expression, reference)
    except (ValueError, OverflowError, RecursionError) as error:
        raise ValueError(f"Cannot parse date: {s!r}") from error


def _parse(expression: str, today: date) -> date:
    if expression in _RELATIVE_DAYS:
        return today + timedelta(days=_RELATIVE_DAYS[expression])

    if match := _WEEKDAY.fullmatch(expression):
        difference = _WEEKDAYS[match["weekday"]] - today.weekday()
        direction = match["direction"]
        if direction == "next":
            difference = difference % 7 or 7
        elif direction in ("last", "previous"):
            difference = -(-difference % 7 or 7)
        elif direction != "this":
            difference %= 7
        return today + timedelta(days=difference)

    if match := _PERIOD.fullmatch(expression):
        sign = 1 if match["direction"] == "next" else -1
        return _apply_offset(today, f"1 {match['unit']}", sign)

    if match := _ANCHORED_OFFSET.fullmatch(expression):
        sign = -1 if match["direction"] == "before" else 1
        return _apply_offset(_parse(match["anchor"], today), match["offset"], sign)

    if match := _TODAY_OFFSET.fullmatch(expression):
        sign = -1 if match["direction"] in ("ago", "earlier") else 1
        return _apply_offset(today, match["offset"], sign)

    if expression.startswith("in "):
        return _apply_offset(today, expression[3:], 1)

    return _parse_absolute(expression, today.year)


def _parse_absolute(expression: str, default_year: int) -> date:
    for pattern in (_YEAR_FIRST, _MONTH_FIRST, _NAMED_MONTH_FIRST, _NAMED_DAY_FIRST):
        match = pattern.fullmatch(expression)
        if match is None:
            continue

        day = int(match["day"])
        ordinal = match.groupdict().get("ordinal")
        if ordinal:
            suffix = "th"
            if day % 100 not in (11, 12, 13):
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            if ordinal != suffix:
                raise ValueError("Incorrect ordinal suffix")

        month_text = match["month"]
        month = int(month_text) if month_text.isdigit() else _MONTHS[month_text]
        year_text = match["year"]
        year = int(year_text) if year_text else default_year
        if year_text and len(year_text) == 2:
            year += 2000 if year < 69 else 1900
        return date(year, month, day)

    raise ValueError("Unrecognized date format")


def _apply_offset(base: date, offset: str, sign: int) -> date:
    counts = dict.fromkeys(("day", "week", "month", "year"), 0)
    position = 0
    while True:
        match = _OFFSET_TERM.match(offset, position)
        if match is None:
            raise ValueError("Expected a quantity and time unit")
        counts[match["unit"].removesuffix("s")] += _parse_quantity(match["number"])
        if match.end() == len(offset):
            break
        separator = _OFFSET_SEPARATOR.match(offset, match.end())
        if separator is None:
            raise ValueError("Invalid offset separator")
        position = separator.end()

    months = sign * (12 * counts["year"] + counts["month"])
    days = sign * (7 * counts["week"] + counts["day"])
    if months:
        year, month_index = divmod(base.year * 12 + base.month - 1 + months, 12)
        month = month_index + 1
        base = date(year, month, min(base.day, monthrange(year, month)[1]))
    return base + timedelta(days=days)


def _parse_quantity(text: str) -> int:
    if text.isdigit():
        return int(text)
    if text in ("a", "an"):
        return 1
    if text in _SMALL_NUMBERS:
        return _SMALL_NUMBERS[text]

    tens, _, ones = text.replace("-", " ").partition(" ")
    if tens in _TENS:
        if not ones:
            return _TENS[tens]
        value = _SMALL_NUMBERS.get(ones, 0)
        if 1 <= value <= 9:
            return _TENS[tens] + value
    raise ValueError("Unrecognized offset quantity")
