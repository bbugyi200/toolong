"""Filesystem traversal and wc-compatible line counting."""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterator, Sequence
from pathlib import Path

from bbugyi_toolong.core import FileResult, Thresholds, classify

_CHUNK_SIZE = 1024 * 1024


def count_newlines(path: Path) -> int:
    """Count newline bytes, matching ``wc -l`` semantics."""

    count = 0
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK_SIZE):
            count += chunk.count(b"\n")
    return count


def iter_files(directory: Path, includes: Sequence[str]) -> Iterator[Path]:
    """Yield matching regular files recursively without following symlinks."""

    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                yield from iter_files(Path(entry.path), includes)
            elif entry.is_file(follow_symlinks=False) and any(
                fnmatch.fnmatchcase(entry.name, pattern) for pattern in includes
            ):
                yield Path(entry.path)


def scan(
    directory: Path, includes: Sequence[str], thresholds: Thresholds
) -> tuple[FileResult, ...]:
    """Scan a directory and return deterministic results sorted by path."""

    paths = sorted(iter_files(directory, includes), key=lambda path: str(path))
    return tuple(
        FileResult(
            path=str(path),
            line_count=(line_count := count_newlines(path)),
            classification=classify(line_count, thresholds),
        )
        for path in paths
    )
