"""Pure line-count classification logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Classification(Enum):
    """A file's relationship to the configured thresholds."""

    OK = "OK"
    FYI = "FYI"
    WARNING = "WARNING"
    VIOLATION = "VIOLATION"


@dataclass(frozen=True)
class Thresholds:
    """Ordered, positive line-count thresholds."""

    line: int
    warning: int
    info: int

    def __post_init__(self) -> None:
        for name, value in (
            ("line_limit", self.line),
            ("warning_limit", self.warning),
            ("info_limit", self.info),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be a positive integer, got: {value}")
        if self.warning >= self.line:
            raise ValueError(
                f"warning_limit ({self.warning}) must be less than line_limit ({self.line})"
            )
        if self.info >= self.warning:
            raise ValueError(
                f"info_limit ({self.info}) must be less than warning_limit ({self.warning})"
            )


@dataclass(frozen=True)
class FileResult:
    """The line count and classification for one file."""

    path: str
    line_count: int
    classification: Classification


@dataclass(frozen=True)
class Counts:
    """Aggregate result counts."""

    violations: int = 0
    warnings: int = 0
    infos: int = 0


def classify(line_count: int, thresholds: Thresholds) -> Classification:
    """Classify a count using strict greater-than threshold semantics."""

    if line_count > thresholds.line:
        return Classification.VIOLATION
    if line_count > thresholds.warning:
        return Classification.WARNING
    if line_count > thresholds.info:
        return Classification.FYI
    return Classification.OK


def count_results(results: tuple[FileResult, ...]) -> Counts:
    """Aggregate non-OK classifications."""

    return Counts(
        violations=sum(r.classification is Classification.VIOLATION for r in results),
        warnings=sum(r.classification is Classification.WARNING for r in results),
        infos=sum(r.classification is Classification.FYI for r in results),
    )


def format_result(result: FileResult, thresholds: Thresholds) -> str:
    """Format the pylimit-compatible core of a classification line."""

    path = result.path
    count = result.line_count
    if result.classification is Classification.VIOLATION:
        return f"VIOLATION: {path} has {count} lines (limit: {thresholds.line})"
    if result.classification is Classification.WARNING:
        return (
            f"WARNING: {path} has {count} lines "
            f"(warning: {thresholds.warning}, limit: {thresholds.line})"
        )
    if result.classification is Classification.FYI:
        return (
            f"FYI: {path} has {count} lines "
            f"(info: {thresholds.info}, warning: {thresholds.warning}) "
            "- will trigger warning soon"
        )
    return f"OK: {path} has {count} lines"


def summary(counts: Counts, thresholds: Thresholds) -> tuple[str, str, int]:
    """Return summary level, message, and process exit code."""

    if counts.violations:
        return (
            "error",
            f"Found {counts.violations} file(s) exceeding line limit of {thresholds.line}",
            1,
        )
    if counts.warnings:
        return (
            "warning",
            f"Found {counts.warnings} file(s) exceeding warning limit of {thresholds.warning}",
            0,
        )
    if counts.infos:
        return (
            "info",
            f"Found {counts.infos} file(s) exceeding info limit of {thresholds.info}",
            0,
        )
    return "info", f"All files are within the info limit of {thresholds.info}", 0
