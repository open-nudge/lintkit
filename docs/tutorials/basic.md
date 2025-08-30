<!--
SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

# Basic linter

In this introductory tutorial you will learn how to:

- create a basic linter using `lintkit`
- create a few basic rules verifying
    [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

## Your first rule

Firstly create a file called `rules.py` with the following content:

```python
import typing

import lintkit

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

# Define the name for our linter
lintkit.settings.name = "MYLINTER"

class NameDefined(lintkit.loader.TOML, lintkit.rule.Node, code=1):
    """Checks if `name` property is defined in `pyproject.toml`"""

    # Should always return `Value` or `None`
    def values(self) -> Iterable[lintkit.Value[str | None]]:
        """Yield `project.name` from `pyproject.toml`.

        Note:
            It might not be available, hence we are checking
            for `None` values.

        """
        # Appropriate `TOML` data will be loaded later
        data = self.getitem("data")

        # Unpack and yield safely project.name field
        project = data.get("project")
        if project is None:
            yield lintkit.Value()
        else:
            name = project.get("name")
            if name is None:
                yield lintkit.Value()
            else:
                yield lintkit.Value.from_toml(name)

    def message(self, _: lintkit.Value[str | None]) -> str:
        # No need to use `lintkit.Value` here
        return "Field 'project.name' was not defined"

    def check(self, value: lintkit.Value[str | None]) -> bool:
        return value is not None

```

Please note the following elements:

- [`lintkit.settings.name`][] attribute specifies the name our
    linter will have (used when outputting errors or defining
    in-code ignores).
- [`lintkit.loader.TOML`][] will load `toml` file __and__
    save it as a state under `data`
- Access to `loader` created attributes should __always__ be performed by
    [`lintkit.loader.Loader.getitem`][]
- [`lintkit.rule.Node`][] specifies we are interested in `node`/content
    of the data (as opposed to the raw contents of the file or
    all `TOML` files). Check out [File linters](file.md) for more information.
- `code=1` specifies __numeric value associated with this rule__.
    It will later be displayed as a concatenation of
    [`lintkit.settings.name`][] and `code`, in our case
    `"MYLINTER1"`. Many linters have their own codes (or group of codes),
    for example [`ruff`](https://docs.astral.sh/ruff/rules/).
- One has to define
    [`values`][lintkit.rule.Rule.values] (yielding values to check),
    [`message`][lintkit.rule.Node.message] (message to display in case
    of rule violation), and [`check`][lintkit.check.Check.check]
    (what does it mean to check the `value`, actual rule)
- [`lintkit.Value`][] is a transparent proxy object as
    defined by [`wrapt`](https://wrapt.readthedocs.io/en/master/)
    (`lintkit.Value[str]` should be treated as plain `str`).
    __This transparent proxy carries important information
    (like comment associated with the line) which is used by
    [`lintkit`][] pipelines__

> [!NOTE]
> Why `values` method yields? Linter creators can return
> __multiple__ values, which, in turn, will be `check`ed __one by one__.
> Check out [Advanced tutorial](advanced.md) for an example.

This rule will enable us to verify whether `pyproject.toml` contains
necessary `[project]` section with field `name`, so this file
would not raise an error:

```toml
[project]

name = "my super linter"
```

while this one would:

```toml
[project]

nnname = "typos happen :("
```

## Making the rules reusable

You may have noticed, that the following would
also pass the linter check:

```toml
[project]

name = 213
```

while the `name` field in Python's `pyproject.toml` can only be `string`.
We could try to add appropriate verification like so:

```python
...

def check(self, value: lintkit.Value[str | None]) -> bool:
    return value is not None and isinstance(value, str)
```

but that would have its own downsides:

- we are verifying two things in one rule
- it is not extensible (what if we want to check something else)?

> [!TIP]
> As a rule of thumb, try to make your linters follow
> "one check, one rule" formula.

Instead, [`lintkit`][] provides a way to reuse `rule` elements via inheritance
(change original contents of the file to these):

```python
import typing

import lintkit

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

# Define the name for our linter
lintkit.settings.name = "MYLINTER"

class PyProjectNameLoader(lintkit.loader.TOML, lintkit.rule.Node):
    """Safely loads `project.name` property of `pyproject.toml."""

    def values(self) -> Iterable[lintkit.Value[str] | None]:
        """Yield `project.name` from `pyproject.toml`.

        Note:
            It might not be available, hence we are checking
            for `None` values.

        """
        # Appropriate `TOML` data will be loaded earlier
        data = self.getitem("data")

        # Unpack and yield safely project.name field
        project = data.get("project")
        if project is None:
            yield None
        else:
            name = project.get("name")
            if name is None:
                yield None
            else:
                yield lintkit.Value.from_toml(name)

# Concrete definitions of the rules

class NameExists(PyProjectNameLoader, code=1):
    """Checks if `name` property is defined in `pyproject.toml`"""

    def check(self, value: lintkit.Value[str | None]) -> bool:
        return value is not None

    def message(self, _: lintkit.Value[str | None]) -> str:
        return "Field 'project.name' was not defined"

class NameIsString(PyProjectNameLoader, code=2):
    """Checks if `name` property is of type `str`."""

    def check(self, value: lintkit.Value[str | None]) -> bool:
        return isinstance(value, str)

    def message(self, value: lintkit.Value[str | None]) -> str:
        return f"Field 'project.name' is not a string (got {type(value)}"

class NameNoWhitespaces(PyProjectNameLoader, code=3):
    """Checks if `name` is below has no spaces."""

    def check(self, value: lintkit.Value[str | None]) -> bool:
        return isinstance(value, str) and not any(c.isspace() for c in s)

    def message(self, _: lintkit.Value[str | None]) -> str:
        return "Field 'project.name' contains whitespaces"

# Let's add one simple rule for fun
class NameIsShort(PyProjectNameLoader, code=4):
    """Checks if `name` is below `10` characters."""

    def check(self, value: lintkit.Value[str | None]) -> bool:
        return isinstance(value, str) and len(value) < 10

    def message(self, v: lintkit.Value[str | None]) -> str:
        return f"Field 'project.name' is too long ({len(v)} > 10 chars)"
```

> [!IMPORTANT]
> `rule` is defined __when__ you pass its `code`. Before all subclasses
> are considered a reusable elements by \[`lintkit`\][]
> (in our case `PyProjectNameLoader`).

## Running the linter

First, let's define an example `pyproject.toml`
we would like to lint:

```toml
[project]

name = "That is a long incorrect project name"
```

Now you can run `linter` on `pyproject.toml`
(assuming all files are in the same `folder`), create a file
called `run.py`:

```python
import sys

import lintkit

import rules

if __name__ == "__main__":
    # Iterable of files has to be provided
    sys.exit(lintkit.run(["pyproject.toml"]))
```

> [!TIP]
> You can use `sys.exit` directly with the return code
> of [`lintkit.run`][] as it will return `True` __if any
> rule fails__.

Run it:

```shell
> python run.py
```

And you should see the following output (exact file path might differ):

```shell
/pyproject.toml:-:- MYLINTER3: Field 'project.name' contains whitespaces
/pyproject.toml:-:- MYLINTER4: Field 'project.name' is too long (38 > 10 chars )
```

> [!NOTE]
> Currently `TOML` does not support line and column numbers (that's why `-`)
> unlike `YAML` and `Python`. Check out [`lintkit.loader`][] if you want
> to find out more.

## Next steps

Check one of the following tutorials to learn more about
what you can do with `lintkit`:

- [Configuring linter](configure.md) via
    [`loadfig`](https://github.com/open-nudge/loadfig)
    (or other tool); __continuation of this tutorial__
- [Advanced linter for Python code](advanced.md)
- [File linters](file.md)
