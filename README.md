# nldate

`nldate.parse` turns an English date expression into a `datetime.date`.

```python
from datetime import date
from nldate import parse

parse("two weeks from tomorrow", today=date(2026, 11, 7))
# datetime.date(2026, 11, 22)
```

`today` defaults to the local date. Parsing ignores letter case and extra
whitespace. Unrecognized expressions and impossible dates raise `ValueError`.

| Input | Examples |
| --- | --- |
| Calendar dates | `2025-12-01`, `12/1/2025`, `December 1st, 2025`, `1 Dec 2025` |
| Relative days and weekdays | `tomorrow`, `next Tuesday`, `last Fri.`, `this Monday` |
| Relative offsets | `in 3 days`, `two weeks ago`, `1 year and 2 months after yesterday` |

Year-last numeric dates use month/day order. Dates without a year use the
reference year. Two-digit years `00` through `68` map to 2000–2068 and `69`
through `99` map to 1969–1999.

`next` and `last` weekdays are strictly after and before the reference date.
`this` uses the reference date's Monday–Sunday week. An unqualified weekday
uses the first matching day on or after the reference date.

Offsets apply years and months first, clamping to the last day of the target
month when needed, then apply weeks and days. Quantities can be digits, `a` or
`an`, or English numbers from zero through ninety-nine.

## Development

```sh
uv run pytest
uv run mypy src/
uv run ruff check
uv run ruff format --check
```
