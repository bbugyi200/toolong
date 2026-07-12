from __future__ import annotations

import pytest

from bbugyi_toolong.core import (
    Classification,
    Counts,
    FileResult,
    Thresholds,
    classify,
    format_result,
    summary,
)


@pytest.fixture
def thresholds() -> Thresholds:
    return Thresholds(line=10, warning=7, info=4)


@pytest.mark.parametrize(
    ("line_count", "expected"),
    [
        (4, Classification.OK),
        (5, Classification.FYI),
        (7, Classification.FYI),
        (8, Classification.WARNING),
        (10, Classification.WARNING),
        (11, Classification.VIOLATION),
    ],
)
def test_classify_uses_strict_thresholds(
    thresholds: Thresholds, line_count: int, expected: Classification
) -> None:
    assert classify(line_count, thresholds) is expected


@pytest.mark.parametrize(
    "values",
    [(0, 7, 4), (10, 0, 4), (10, 7, 0), (10, 10, 4), (10, 7, 7)],
)
def test_thresholds_reject_invalid_values(values: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError):
        Thresholds(*values)


@pytest.mark.parametrize(
    ("classification", "expected"),
    [
        (Classification.VIOLATION, "VIOLATION: src/a.py has 12 lines (limit: 10)"),
        (
            Classification.WARNING,
            "WARNING: src/a.py has 12 lines (warning: 7, limit: 10)",
        ),
        (
            Classification.FYI,
            "FYI: src/a.py has 12 lines (info: 4, warning: 7) - will trigger warning soon",
        ),
        (Classification.OK, "OK: src/a.py has 12 lines"),
    ],
)
def test_format_result_matches_pylimit_core(
    thresholds: Thresholds, classification: Classification, expected: str
) -> None:
    result = FileResult("src/a.py", 12, classification)
    assert format_result(result, thresholds) == expected


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        (Counts(violations=2), ("error", "Found 2 file(s) exceeding line limit of 10", 1)),
        (Counts(warnings=3), ("warning", "Found 3 file(s) exceeding warning limit of 7", 0)),
        (Counts(infos=4), ("info", "Found 4 file(s) exceeding info limit of 4", 0)),
        (Counts(), ("info", "All files are within the info limit of 4", 0)),
    ],
)
def test_summary(thresholds: Thresholds, counts: Counts, expected: tuple[str, str, int]) -> None:
    assert summary(counts, thresholds) == expected
