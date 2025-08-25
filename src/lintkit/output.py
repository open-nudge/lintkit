# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Out-of-the-box output functions for the linter.

## Default

Note:
    This module provides a default function, which
    chooses [`rich`](https://github.com/Textualize/rich)
    to display linter output (if available) with
    `stdout` fallback.

__All__ provided output functions follow this string output:

```python
"<FILE>:<LINE>:<COLUMN> <RULE-TYPE><RULE-CODE>: <MESSAGE>"
```

For example:
```python
"/home/user1/foo.py:27:31  SUPERULE12: This line is not super, use `super`"
```

## Custom

To change `default` output you can use one of the provided
options, e.g.:

```python
import lintkit

# To set `print` as the linter output.
lintkit.settings.output = lintkit.output.stdout
```

You can also define your own output function as long
as you use a function with the following signature:

```python
def my_output(
    *,
    name: str,
    code: int,
    message: str,
    file: pathlib.Path | None = None,
    start_line: int | None = None,
    start_column: int | None = None,
    end_line: int | None = None,
    end_column: int | None = None,
) -> None:
    pass
```

which should (somehow) output the linter results (e.g. to a file).

Note:
    You don't have to use all values (e.g. `end_line`),
    use only the values you find necessary (provided `output` functions do not
    use `end_line` nor `end_column` even if these are present.

Warning:
    Different `loader`s __might not__ provide some values
    (these which might be `None` above), your custom function
    should handle these cases.

"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import pathlib

    from . import type_definitions

from . import available


def stdout(  # noqa: PLR0913
    name: str,
    code: int,
    message: str,
    file: pathlib.Path | None = None,
    start_line: int | None = None,
    start_column: int | None = None,
    end_line: int | None = None,  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
    end_column: int | None = None,  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
) -> None:
    """Output linter message to `stdout` using `print`.

    Info:
        Default `output` if [`rich`](https://github.com/Textualize/rich)
        is not available.

    Args:
        name:
            Name of the linter (equal to `lintkit.settings.name`)
        code:
            Numerical code of specific rule (e.g. `12`).
        message:
            Error message of specific rule.
        file:
            Full path to the file where the error occurred.
        start_line:
            Start line number of the error, if any.
        start_column:
            Start column number of the error, if any.
        end_line:
            End line number of the error, if any (unused).
        end_column:
            End column number of the error, if any (unused).

    """
    print(  # noqa: T201
        f"{file or 'ALL'}:{start_line}:{start_column}: {name}{code}: {message}",
    )


if available.RICH:
    import rich as r

    def rich(  # noqa: PLR0913
        name: str,
        code: int,
        message: str,
        file: pathlib.Path | None = None,
        start_line: int | None = None,
        start_column: int | None = None,
        end_line: int | None = None,  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
        end_column: int | None = None,  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Output linter message to `stdout` using `rich`.

        Info:
            Default `output` function (if `rich` library
            is available).

        Note:
            See [here](https://github.com/Textualize/rich) for more
            information about the `rich` library.

        Tip:
            You can install compatible `rich` using `extras`,
            e.g. `pip install lintkit[rich]` or
            `pip install lintkit[output]`

        Args:
            name:
                Name of the linter (equal to `lintkit.settings.name`)
            code:
                Numerical code of specific rule (e.g. `12`).
            message:
                Error message of specific rule.
            file:
                Full path to the file where the error occurred.
            start_line:
                Start line number of the error, if any.
            start_column:
                Start column number of the error, if any.
            end_line:
                End line number of the error, if any (unused).
            end_column:
                End column number of the error, if any (unused).

        """
        r.print(
            f"[bold]{file or 'ALL'}[/bold]:{start_line}[cyan]:[/cyan]{start_column}: [bold red]{name}{code}[/bold red] {message}",  # noqa: E501
        )
else:  # pragma: no cover
    pass


# Used internally by `rule` when finding appropriate output venue
def _default() -> type_definitions.Output:  # pyright: ignore[reportUnusedFunction]
    """Get the default output function.

    Will return the `rich` output function if the `rich` library is installed,
    otherwise the `stdout` output function.

    Warning:
        This function is used internally and should not be called directly.

    Returns:
        The default output function
    """
    if available.RICH:
        return rich
    return stdout  # pragma: no cover
