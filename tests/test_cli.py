from __future__ import annotations

import io
from pathlib import Path

import pytest

from bbugyi_toolong.cli import run


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


def invoke(args: list[str], *, environ: dict[str, str] | None = None) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = run(args, stdout=stdout, stderr=stderr, environ=environ or {})
    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_normal_output_and_exit_codes(tmp_path: Path) -> None:
    (tmp_path / "violation.py").write_text("\n" * 11)
    (tmp_path / "warning.py").write_text("\n" * 9)
    (tmp_path / "fyi.py").write_text("\n" * 6)
    (tmp_path / "ok.py").write_text("\n" * 2)

    exit_code, stdout, stderr = invoke([str(tmp_path), "10", "7", "4"])

    assert exit_code == 1
    assert stdout == ""
    assert f"VIOLATION: {tmp_path / 'violation.py'} has 11 lines (limit: 10)" in stderr
    assert f"WARNING: {tmp_path / 'warning.py'} has 9 lines" in stderr
    assert f"FYI: {tmp_path / 'fyi.py'} has 6 lines" in stderr
    assert "OK:" not in stderr
    assert "Found 1 file(s) exceeding line limit of 10" in stderr


def test_verbose_shows_ok_and_double_verbose_adds_diagnostics(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("\n" * 2)

    exit_code, _, stderr = invoke(["-vv", str(tmp_path), "10", "7", "4"])

    assert exit_code == 0
    assert f"OK: {tmp_path / 'ok.py'} has 2 lines" in stderr
    assert "Command-line arguments:" in stderr
    assert "Symlinks are not followed" in stderr


def test_files_only_is_sorted_unique_and_silent_on_stderr(tmp_path: Path) -> None:
    (tmp_path / "z.py").write_text("\n" * 6)
    (tmp_path / "a.py").write_text("\n" * 9)
    (tmp_path / "ok.py").write_text("\n" * 2)

    exit_code, stdout, stderr = invoke(
        ["--include", "*.py", "--include", "*.*", "--files-only", str(tmp_path), "10", "7", "4"]
    )

    assert exit_code == 0
    assert stdout.splitlines() == [str(tmp_path / "a.py"), str(tmp_path / "z.py")]
    assert stderr == ""


def test_rust_include(tmp_path: Path) -> None:
    (tmp_path / "lib.rs").write_text("\n" * 11)
    (tmp_path / "ignored.py").write_text("\n" * 11)

    exit_code, _, stderr = invoke(["--include", "*.rs", str(tmp_path), "10", "7", "4"])

    assert exit_code == 1
    assert "lib.rs" in stderr
    assert "ignored.py" not in stderr


@pytest.mark.parametrize(
    "args",
    [
        ["missing", "10", "7", "4"],
        [".", "nope", "7", "4"],
        [".", "0", "7", "4"],
        [".", "10", "10", "4"],
        [".", "10", "7", "7"],
    ],
)
def test_validation_errors_exit_one(args: list[str]) -> None:
    exit_code, stdout, stderr = invoke(args)

    assert exit_code == 1
    assert stdout == ""
    assert "ERROR: Error:" in stderr


def test_missing_argument_is_argparse_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        run([])

    assert error.value.code == 2
    assert "usage: toolong" in capsys.readouterr().err


def test_no_color_disables_color_on_tty(tmp_path: Path) -> None:
    (tmp_path / "large.py").write_text("\n" * 11)
    stderr = TtyBuffer()

    exit_code = run(
        [str(tmp_path), "10", "7", "4"],
        stdout=io.StringIO(),
        stderr=stderr,
        environ={"NO_COLOR": "1"},
    )

    assert exit_code == 1
    assert "\033[" not in stderr.getvalue()


def test_color_is_used_for_tty(tmp_path: Path) -> None:
    stderr = TtyBuffer()

    exit_code = run(
        [str(tmp_path), "10", "7", "4"],
        stdout=io.StringIO(),
        stderr=stderr,
        environ={},
    )

    assert exit_code == 0
    assert "\033[36mINFO\033[0m:" in stderr.getvalue()
