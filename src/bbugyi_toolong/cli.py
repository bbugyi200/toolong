"""Command-line interface for toolong."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

from bbugyi_toolong.core import (
    Classification,
    Thresholds,
    count_results,
    format_result,
    summary,
)
from bbugyi_toolong.scanner import scan

_COLORS = {
    "debug": "\033[35m",
    "info": "\033[36m",
    "warning": "\033[33m",
    "error": "\033[31m",
}
_RESET = "\033[0m"


class Logger:
    """Minimal stderr logger with optional level colors."""

    def __init__(self, stream: TextIO, *, color: bool) -> None:
        self._stream = stream
        self._color = color

    def log(self, level: str, message: str) -> None:
        label = level.upper()
        if self._color:
            label = f"{_COLORS[level]}{label}{_RESET}"
        print(f"{label}: {message}", file=self._stream)


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""

    parser = argparse.ArgumentParser(
        prog="toolong",
        description="Enforce graduated line-count limits for source files.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument(
        "--include",
        action="append",
        metavar="GLOB",
        help="basename glob to include; repeatable (default: *.py)",
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="print only unique paths that exceed any threshold",
    )
    parser.add_argument("directory", help="directory to scan recursively")
    parser.add_argument("line_limit", help="hard line limit")
    parser.add_argument("warning_limit", help="warning threshold")
    parser.add_argument("info_limit", help="informational threshold")
    return parser


def _positive_integer(name: str, raw_value: str) -> int:
    if not raw_value.isdigit() or int(raw_value) <= 0:
        raise ValueError(f"{name} must be a positive integer, got: {raw_value}")
    return int(raw_value)


def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    environ: Mapping[str, str] = os.environ,
) -> int:
    """Run the CLI and return its exit code."""

    args = build_parser().parse_args(argv)
    color = stderr.isatty() and "NO_COLOR" not in environ
    logger = Logger(stderr, color=color)

    try:
        thresholds = Thresholds(
            line=_positive_integer("line_limit", args.line_limit),
            warning=_positive_integer("warning_limit", args.warning_limit),
            info=_positive_integer("info_limit", args.info_limit),
        )
    except ValueError as error:
        if not args.files_only:
            logger.log("error", f"Error: {error}")
        return 1

    directory = Path(args.directory)
    if not directory.is_dir():
        if not args.files_only:
            logger.log("error", f"Error: directory '{directory}' does not exist")
        return 1

    includes = tuple(args.include or ("*.py",))
    if not args.files_only:
        logger.log(
            "info",
            f"Checking files in '{directory}' matching {', '.join(includes)} for line limit of "
            f"{thresholds.line} (warning at {thresholds.warning}, info at {thresholds.info})...",
        )
        if args.verbose > 1:
            logger.log("debug", f"Command-line arguments: {list(argv or sys.argv[1:])}")
            logger.log("debug", "Symlinks are not followed; hidden files are included")

    try:
        results = scan(directory, includes, thresholds)
    except OSError as error:
        if not args.files_only:
            logger.log("error", f"Error: {error}")
        return 1

    if args.files_only:
        for path in sorted(
            {result.path for result in results if result.classification is not Classification.OK}
        ):
            print(path, file=stdout)
    else:
        for result in results:
            if result.classification is Classification.OK and not args.verbose:
                continue
            level = {
                Classification.OK: "debug",
                Classification.FYI: "info",
                Classification.WARNING: "warning",
                Classification.VIOLATION: "error",
            }[result.classification]
            logger.log(level, format_result(result, thresholds))

    level, message, exit_code = summary(count_results(results), thresholds)
    if not args.files_only:
        logger.log(level, message)
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Console-script entry point."""

    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
