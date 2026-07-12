# toolong

[![CI](https://github.com/bbugyi200/toolong/actions/workflows/ci.yml/badge.svg)](https://github.com/bbugyi200/toolong/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/bbugyi-toolong.svg)](https://pypi.org/project/bbugyi-toolong/)
[![Python versions](https://img.shields.io/pypi/pyversions/bbugyi-toolong.svg)](https://pypi.org/project/bbugyi-toolong/)
[![License: MIT](https://img.shields.io/pypi/l/bbugyi-toolong.svg)](LICENSE)

`toolong` is a fast, dependency-free line-limit linter for any text-based source language. It applies graduated
thresholds so a file can become visible before it becomes a hard failure.

Small files are easier for people to review, navigate, test, and refactor. They also fit more readily into the context
windows used by coding agents and LLM tools, leaving more room for the task, related code, and test output. `toolong`
turns that shared maintainability constraint into a simple, automatable check.

## Quick start

Install the `toolong` command with [uv](https://docs.astral.sh/uv/):

```console
uv tool install bbugyi-toolong
```

Or install it with pipx or pip:

```console
pipx install bbugyi-toolong
# or, inside a virtual environment
python -m pip install bbugyi-toolong
```

Scan Python files under `src/`, failing when any file exceeds 1,000 lines:

```console
toolong src 1000 850 700
```

The three limits are the hard, warning, and informational thresholds, in that order. The default include pattern is
`*.py`.

## Usage

```text
toolong [-v]... [--include GLOB]... [--files-only] DIRECTORY LINE_LIMIT WARNING_LIMIT INFO_LIMIT
```

Patterns match file basenames and can be repeated. The scan is recursive, includes hidden files, and does not follow
symlinks or apply `.gitignore` rules.

For a Python project:

```console
toolong src 1000 850 700
toolong --include '*.py' --include '*.pyi' src 1000 850 700
```

For a Rust project:

```console
toolong --include '*.rs' crates 800 650 500
```

Use `-v` to include `OK` lines for files below every threshold. Use `-vv` for additional diagnostics about the scan.
Line counts follow `wc -l`: they count newline characters, so a final line without a trailing newline is not counted.

### Threshold semantics

Threshold comparisons are strict. A file exactly at a threshold does not enter that threshold's category.

| File length | Classification | Effect |
| --- | --- | --- |
| `> LINE_LIMIT` | `VIOLATION` | Hard failure |
| `> WARNING_LIMIT` | `WARNING` | Reported, but does not fail |
| `> INFO_LIMIT` | `FYI` | Early heads-up, but does not fail |
| `<= INFO_LIMIT` | `OK` | Shown only with `-v` |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | The scan completed with no violations; warnings and FYIs may still have been reported |
| `1` | A file exceeded the hard limit, the directory was invalid, or a threshold was invalid |
| `2` | Command-line usage error, such as a missing positional argument |

### Feed paths to another command

`--files-only` prints each unique file classified as a violation, warning, or FYI to stdout, in sorted order. It keeps
the normal scan's exit code and emits no log output, making it suitable for scripts:

```console
toolong --files-only src 1000 850 700 | xargs -r editor
```

When there are no files above the informational threshold, stdout is empty.

## Continuous integration

A small Justfile recipe keeps the project policy easy to run locally and in CI:

```just
toolong:
    uvx --from bbugyi-toolong toolong src 1000 850 700
```

Then call the same recipe from GitHub Actions:

```yaml
- uses: astral-sh/setup-uv@v4
- uses: extractions/setup-just@v3
- run: just toolong
```

Pin `bbugyi-toolong` to the version range appropriate for your project when reproducibility is important.

## Development

The repository uses [uv](https://docs.astral.sh/uv/) for environments and dependency installation, and
[just](https://just.systems/) as its task runner. From a clone:

```console
just install
just check
```

`just check` verifies formatting, runs Ruff and strict mypy, and executes the pytest suite. The package supports Python
3.10 through 3.14 and has no runtime dependencies.

## Releases

Commits and pull-request titles follow [Conventional Commits](https://www.conventionalcommits.org/). On every push to
`master`, release-please updates or opens a release pull request containing the next version and changelog. Merging
that pull request creates the GitHub release, builds and smoke-tests both distributions, and publishes
`bbugyi-toolong` to PyPI using trusted publishing (GitHub Actions OIDC), without a long-lived PyPI token.

## License

`toolong` is available under the [MIT License](LICENSE).
