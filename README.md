# toolong

`toolong` enforces graduated line-count limits so source files stay manageable for humans and coding agents.

Install the package with `uv tool install bbugyi-toolong`, then scan Python files with:

```console
toolong src 1000 850 700
```

Use repeatable `--include` options for other languages, or `--files-only` when feeding offending paths to another
command. Full project documentation will accompany the first release.
