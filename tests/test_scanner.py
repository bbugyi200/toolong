from __future__ import annotations

from pathlib import Path

from bbugyi_toolong.core import Classification, Thresholds
from bbugyi_toolong.scanner import count_newlines, scan


def test_count_newlines_matches_wc_semantics(tmp_path: Path) -> None:
    with_trailing_newline = tmp_path / "with.py"
    with_trailing_newline.write_bytes(b"one\ntwo\n")
    without_trailing_newline = tmp_path / "without.py"
    without_trailing_newline.write_bytes(b"one\ntwo")

    assert count_newlines(with_trailing_newline) == 2
    assert count_newlines(without_trailing_newline) == 1


def test_scan_includes_hidden_files_and_language_globs(tmp_path: Path) -> None:
    (tmp_path / "visible.py").write_text("\n" * 2)
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "module.py").write_text("\n" * 3)
    (tmp_path / "lib.rs").write_text("\n" * 4)
    (tmp_path / "notes.txt").write_text("\n" * 20)

    results = scan(tmp_path, ("*.py", "*.rs"), Thresholds(10, 7, 2))

    assert [Path(result.path).name for result in results] == ["module.py", "lib.rs", "visible.py"]
    assert [result.classification for result in results] == [
        Classification.FYI,
        Classification.FYI,
        Classification.OK,
    ]


def test_scan_does_not_follow_symlinks(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "inside.py").write_text("\n" * 5)
    (tmp_path / "linked-dir").symlink_to(real, target_is_directory=True)
    (tmp_path / "linked-file.py").symlink_to(real / "inside.py")

    results = scan(tmp_path, ("*.py",), Thresholds(10, 7, 4))

    assert [Path(result.path).name for result in results] == ["inside.py"]
