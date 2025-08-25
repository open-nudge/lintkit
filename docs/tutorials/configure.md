<!--
SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
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
... # rest of the file

# Let's add one simple rule for fun
class NameIsShort(PyProjectNameLoader, code=4):
    """Checks if `name` is below `N` characters."""
    def __init__(self):
        # Always call base constructor
        super().__init__()

        self.max_name_length = 10

    def check(self, value: lintkit.Value[str | None]) -> bool:
        # Change 10 to attribute
        return isinstance(value, str) and len(value) < self.max_name_length

    def message(self, v: lintkit.Value | None) -> str:
        return (
            f"Field 'project.name' is too long ({len(v)} > {name_length} chars)"
        )
```

Read on to see how to inject `max_name_length` attribute without passing
values to `__init__`

> [!TIP]
> [`lintkit.rule.Rule`][] is instantiated by [`lintkit.run`][] call
> and no arguments are passed.

## Update config

You will continue with previously define `pyproject.toml`,
add the following section to our linter:

```toml
[tool.mylinter]

include_codes = [2, 3, 4]
exclude_codes = [1, 2, 3]

max_name_lenth = 5
```

## Load and inject config

To load config of linter from `pyproject.toml` one can use
[`loadfig`](https://github.com/open-nudge/loadfig) project which
is no dependency library loading tool section from `pyproject.toml`.

You can install it with pip (or use your package manager like
[`uv`](https://github.com/astral-sh/uv)):

```shell
> pip install loadfig
```

> [!TIP]
> You can use any other config loading tool or write
> one yourself.

Now edit `run.py`:

```python
import sys

import loadfig
import lintkit

import rules

def main() -> None:
    # Simply specify name of the tool
    config: dict = loadfig.config("mylinter")

    # Add `max_name_length` attribute to all rules
    # Has to be run after `rules` are imported!
    lintkit.registry.inject(
        "max_name_length",
        # None if the value was not defined
        config.get("max_name_length", None),
    )

    # Run the linter with code inclusions and exclusions
    exit_code = lintkit.run(
        "pyproject.toml",
        include_rules=config.get("include_rules", None),
        exclude_rules=config.get("exclude_rules", None),
    )

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

Things you should note:

- [`lintkit.registry.inject`][] allows you to register variables
    (or whole configs) so they are available to __all rules__
- [`lintkit.run`][] gives you more flexibility (e.g.
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
