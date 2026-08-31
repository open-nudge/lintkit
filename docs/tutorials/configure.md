<!--
SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

# Configure linter

This tutorial walks you through the steps to configure your linter.
We will start from the code in [the previous tutorial](./basic.md).

> [!WARNING]
> Gather code from the first [Basic linter](./basic.md)
> tutorial to follow along.

## Update rule to use config

One of the rules in previous tutorial has a magic number
which you might want to have customizable (e.g. by providing
linter configuration via `pyproject.toml`
like [`ruff`](https://docs.astral.sh/ruff/configuration/)).

Let's do this by adjusting `NameIsShort` rule first (leave rest
of the file as is):

```python
...  # rest of the file


# Let's add one simple rule for fun
class NameIsShort(PyProjectNameLoader, code=4):
    """Checks if `name` is below `N` characters."""

    def __init__(self):
        # Always call base constructor
        super().__init__()

        self.max_name_length = self.config("max_name_length", 10)

    def check(self, value: lintkit.Value[str | None]) -> bool:
        # Change 10 to attribute
        return isinstance(value, str) and len(value) > self.max_name_length

    def message(self, v: lintkit.Value | None) -> str:
        return (
            f"Field 'project.name' is too long "
            f"({len(v)} > {self.max_name_length} chars)"
        )
```

Read on to see how `max_name_length` is loaded without passing values to
`__init__`.

> [!TIP]
> \[`lintkit.rule.Rule`\][] is instantiated by \[`lintkit.run`\][] call
> and no arguments are passed.

## Update config

You will continue with previously define `pyproject.toml`,
add the following section to our linter:

```toml
[tool.mylinter]

include_codes = [4]

[tool.mylinter.MYLINTER4]

max_name_length = 5
```

## Load config

Lintkit can use [`loadfig`](https://github.com/open-nudge/loadfig) to load the
linter's tool section from `pyproject.toml`. Install the `config` extra:

You can install it with pip (or use your package manager like
[`uv`](https://github.com/astral-sh/uv)):

```shell
> pip install lintkit[config]
```

> [!TIP]
> Installing `lintkit[config]` enables both \[`lintkit.config`\][] and
> \[`lintkit.rule.Rule.config`\][]. Without the extra, neither API is exposed.

Now edit `run.py`:

```python
import sys

import lintkit

import rules


def main() -> None:
    # Loads [tool.mylinter], based on lowercase lintkit.settings.name
    config = lintkit.config()

    # Run the linter with code inclusions and exclusions
    exit_code = lintkit.run(
        ["pyproject.toml"],
        include_codes=config.get("include_codes", None),
        exclude_codes=config.get("exclude_codes", None),
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

Things you should note:

- `Rule.config()` reads only the nested table matching that rule's exact public
    name, such as `[tool.mylinter.MYLINTER4]`
- \[`lintkit.config`\][] returns the whole `[tool.mylinter]` table for shared
    options such as rule selection
- \[`lintkit.registry.inject`\][] remains available for unrelated custom
    resources that should be shared by __all rules__
- \[`lintkit.run`\][] gives you more flexibility (e.g.
    including or excluding code parts).

> [!NOTE]
> Exclusions take precedence over inclusions. In our case,
> the only included rule will be effectively `4`.

> [!TIP]
> You can use any other config loading tool or load
> the config directly using
> [standard `tomllib` library](https://docs.python.org/3/library/tomllib.html)

## Run

You can run the `run.py` file once again, this time the output
should be as follows:

```shell
/pyproject.toml:-:- MYLINTER4: Field 'project.name' is too long (38 > 5 chars)
```

## Next steps

Check one of the following tutorials to learn more about
what you can do with `lintkit`:

- Previous [basic tutorial](./basic.md) showcasing `lintkit` capabilities
- [Advanced linter for Python code](advanced.md)
- [File linters](file.md)
