from datetime import date

import pytest

from nldate import parse

TODAY = date(2026, 11, 7)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2024-02-29", date(2024, 2, 29)),
        ("2025/12/01", date(2025, 12, 1)),
        ("12/1/25", date(2025, 12, 1)),
        ("03/04/2026", date(2026, 3, 4)),
        ("12-01-2025", date(2025, 12, 1)),
        ("December 1st, 2025", date(2025, 12, 1)),
        ("  dec.   1,  2025  ", date(2025, 12, 1)),
        ("1 December 2025", date(2025, 12, 1)),
        ("the 21st of SEPT. 2026", date(2026, 9, 21)),
        ("November 3rd", date(2026, 11, 3)),
        ("12/31", date(2026, 12, 31)),
    ],
)
def test_absolute_dates(expression: str, expected: date) -> None:
    assert parse(expression, today=TODAY) == expected


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("today", date(2026, 11, 7)),
        ("TOMORROW", date(2026, 11, 8)),
        ("yesterday", date(2026, 11, 6)),
        ("the day after tomorrow", date(2026, 11, 9)),
        ("day before yesterday", date(2026, 11, 5)),
        ("next Tuesday", date(2026, 11, 10)),
        ("last Tue.", date(2026, 11, 3)),
        ("this Tuesday", date(2026, 11, 3)),
        ("Saturday", date(2026, 11, 7)),
        ("next Saturday", date(2026, 11, 14)),
        ("last Saturday", date(2026, 10, 31)),
        ("on Sunday", date(2026, 11, 8)),
        ("next week", date(2026, 11, 14)),
        ("last month", date(2026, 10, 7)),
    ],
)
def test_reference_dates(expression: str, expected: date) -> None:
    assert parse(expression, today=TODAY) == expected


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("in 3 days", date(2026, 11, 10)),
        ("3 days ago", date(2026, 11, 4)),
        ("3 days from now", date(2026, 11, 10)),
        ("two weeks from tomorrow", date(2026, 11, 22)),
        ("a week before next Tuesday", date(2026, 11, 3)),
        ("5 days before December 1st, 2025", date(2025, 11, 26)),
        ("1 year and 2 months after yesterday", date(2028, 1, 6)),
        ("one year and two months after yesterday", date(2028, 1, 6)),
        ("1 week, 2 days, and 1 month before 2026-11-07", date(2026, 9, 28)),
        ("in one month 2 days", date(2026, 12, 9)),
        ("twenty-one days ago", date(2026, 10, 17)),
        ("3 days after 2 weeks before today", date(2026, 10, 27)),
        ("in 0 days", date(2026, 11, 7)),
    ],
)
def test_relative_offsets(expression: str, expected: date) -> None:
    assert parse(expression, today=TODAY) == expected


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 month after January 31, 2024", date(2024, 2, 29)),
        ("1 month before March 31, 2025", date(2025, 2, 28)),
        ("1 year after February 29, 2024", date(2025, 2, 28)),
        ("1 day and 1 month after January 31, 2024", date(2024, 3, 1)),
        ("1 day before 2025-01-01", date(2024, 12, 31)),
    ],
)
def test_calendar_boundaries(expression: str, expected: date) -> None:
    assert parse(expression, today=TODAY) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "   ",
        "sometime soon",
        "2025-02-29",
        "2026-13-01",
        "November 31",
        "December 11st, 2025",
        "November 7, 2026 extra",
        "2 hours ago",
        "in -2 days",
        "in 2 days and",
        "in 2 days,, 1 week",
        "a week before something",
        "one day after 9999-12-31",
        "one month before 0001-01-01",
    ],
)
def test_invalid_dates(expression: str) -> None:
    with pytest.raises(ValueError):
        parse(expression, today=TODAY)


def test_today_defaults_to_local_date() -> None:
    before = date.today()
    result = parse("today")
    assert result in (before, date.today())
