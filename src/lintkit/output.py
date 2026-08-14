# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Out-of-the-box output functors for the linter.

## Default

Note:
    This module provides a default functor, which chooses
    [`Rich`][lintkit.output.Rich]
    to display linter output (if available) with
    [`Stdout`][lintkit.output.Stdout] fallback.

Text outputs follow this format:

```python
"<FILE>:<LINE>:<COLUMN> <RULE-TYPE><RULE-CODE>: <MESSAGE>"
```

For example:
```python
"/home/user1/foo.py:27:31  SUPERULE12: This line is not super, use `super`"
```

## Custom

To change the default output you can use one of the provided options, e.g.:

```python
import lintkit

lintkit.settings.output = lintkit.output.Stdout()
```

Custom outputs subclass [`Output`][lintkit.output.Output] and implement both
the call and finalization stages:

```python
import pathlib

import lintkit


class MyOutput(lintkit.output.Output):
    def __call__(
        self,
        name: str,
        code: int,
        message: str,
        file: pathlib.Path | None = None,
        start_line: int | None = None,
        start_column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
    ) -> None:
        print("ERROR!")
        # Or anything else you want


lintkit.settings.output = MyOutput()
```

Custom subclasses that override `__init__()` must call `super().__init__()` to
initialize the inherited context state.

Note:
    You don't have to use all values (e.g. `end_line`); use only the values
    you find necessary. Provided output functors do not use `end_line` nor
    `end_column` even if these are present.

The runner calls the functor for each violation and calls `finalize()` once
when the run ends. This allows outputs such as [`JSON`][lintkit.output.JSON]
to accumulate records and serialize one complete result at finalization.

An output can also be used temporarily and will restore the previously
configured output when its context exits:

```python
with lintkit.output.JSON() as output:
    assert lintkit.settings.output is output
    lintkit.run(("a.py", "b.py"))
```

Warning:
    Different loaders might not provide some location values. Custom outputs
    should handle `None` for unavailable files, lines, and columns.

"""

from __future__ import annotations

import abc
import json
import typing

if typing.TYPE_CHECKING:
    import pathlib
    import types

from . import available, settings


class Output(abc.ABC):
    """Interface implemented by stateful linter outputs."""

    def __init__(self) -> None:
        """Initialize output context state.

        Note:
            Custom subclasses that override `__init__()` must call this method
            with `super().__init__()`.

        """
        self._previous_outputs: list[Output | None] = []

    def __enter__(self) -> typing.Self:
        """Install this instance as the active output.

        Returns:
            This output instance.

        """
        self._previous_outputs.append(settings.output)
        settings.output = self
        return self

    def __exit__(
        self,
        _: type[BaseException] | None,
        __: BaseException | None,
        ___: types.TracebackType | None,
    ) -> typing.Literal[False]:
        """Finish the outermost session and restore the previous output.

        Args:
            exception_type:
                Type of the exception raised by the context body, if any.
            exception:
                Exception raised by the context body, if any.
            traceback:
                Traceback for the exception raised by the context body, if
                any.

        Returns:
            `False`, so exceptions are never suppressed.

        """
        previous = self._previous_outputs.pop()
        if self._previous_outputs:
            settings.output = previous
            return False

        try:
            settings.output = self
            self.finalize()
        finally:
            settings.output = previous
        return False

    @abc.abstractmethod
    def __call__(  # noqa: PLR0913, PLR0917
        self,
        name: str,
        code: int,
        message: str,
        file: pathlib.Path | None = None,
        start_line: int | None = None,
        start_column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
    ) -> None:
        """Process one rule violation.

        Args:
            name:
                Name of the linter (equal to `lintkit.settings.name`).
            code:
                Numerical code of the rule.
            message:
                Rule violation message.
            file:
                Path to the file where the violation occurred, if available.
            start_line:
                Start line number of the violation, if available.
            start_column:
                Start column number of the violation, if available.
            end_line:
                End line number of the violation, if available.
            end_column:
                End column number of the violation, if available.

        """
        raise NotImplementedError

    def finalize(self) -> None:
        """Finalize and emit any accumulated output.

        Pass-through by default.

        """
        return


class Stdout(Output):
    """Output each linter message to standard output using `print`."""

    @typing.override
    def __call__(
        self,
        name: str,
        code: int,
        message: str,
        file: pathlib.Path | None = None,
        start_line: int | None = None,
        start_column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
    ) -> None:
        """Print one linter message.

        Info:
            Default `output` if [`rich`](https://github.com/Textualize/rich)
            is not available.

        Args:
            name:
                Name of the linter (equal to `lintkit.settings.name`).
            code:
                Numerical code of the rule.
            message:
                Rule violation message.
            file:
                Path to the file where the violation occurred, if available.
            start_line:
                Start line number of the violation, if available.
            start_column:
                Start column number of the violation, if available.
            end_line:
                End line number of the violation, if available (unused).
            end_column:
                End column number of the violation, if available (unused).

        """
        line = start_line if start_line is not None else "-"
        column = start_column if start_column is not None else "-"
        print(  # noqa: T201
            f"{file or 'ALL'}:{line}:{column}: {name}{code}: {message}",
        )


if available.RICH:
    import rich

    class Rich(Output):
        """Output each linter message to standard output using `rich`."""

        @typing.override
        def __call__(
            self,
            name: str,
            code: int,
            message: str,
            file: pathlib.Path | None = None,
            start_line: int | None = None,
            start_column: int | None = None,
            end_line: int | None = None,
            end_column: int | None = None,
        ) -> None:
            """Print one richly formatted linter message.

            Info:
                Default `output` functor (if `rich` library is available).

            Note:
                See [here](https://github.com/Textualize/rich) for more
                information about the `rich` library.

            Tip:
                You can install compatible `rich` using `extras`,
                e.g. `pip install lintkit[rich]` or
                `pip install lintkit[output]`.

            Args:
                name:
                    Name of the linter (equal to `lintkit.settings.name`).
                code:
                    Numerical code of the rule.
                message:
                    Rule violation message.
                file:
                    Path to the file where the violation occurred, if
                    available.
                start_line:
                    Start line number of the violation, if available.
                start_column:
                    Start column number of the violation, if available.
                end_line:
                    End line number of the violation, if available (unused).
                end_column:
                    End column number of the violation, if available (unused).

            """
            line = start_line if start_line is not None else "-"
            column = start_column if start_column is not None else "-"
            rich.print(
                f"[bold]{file or 'ALL'}[/bold]:{line}[cyan]:[/cyan]{column}: [bold red]{name}{code}[/bold red] {message}",  # noqa: E501
            )

else:  # pragma: no cover
    pass


class JSON(Output):
    """Accumulate violations and output one valid JSON array."""

    def __init__(self) -> None:
        """Initialize an empty result collection."""
        super().__init__()
        self._results: list[dict[str, str | int | None]] = []

    @typing.override
    def __call__(
        self,
        name: str,
        code: int,
        message: str,
        file: pathlib.Path | None = None,
        start_line: int | None = None,
        start_column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
    ) -> None:
        """Accumulate one violation record.

        Args:
            name:
                Name of the linter (equal to `lintkit.settings.name`).
            code:
                Numerical code of the rule.
            message:
                Rule violation message.
            file:
                Path to the file where the violation occurred, if available.
            start_line:
                Start line number of the violation, if available.
            start_column:
                Start column number of the violation, if available (unused).
            end_line:
                End line number of the violation, if available (unused).
            end_column:
                End column number of the violation, if available (unused).

        """
        self._results.append(
            {
                "code": f"{name}{code}",
                "message": message,
                "file": str(file.resolve()) if file is not None else None,
                "line": start_line,
            }
        )

    @typing.override
    def finalize(self) -> None:
        """Print all accumulated records as one pretty JSON array."""
        print(json.dumps(self._results, indent=2))  # noqa: T201


# Used internally by `settings` when finding the appropriate output venue
def _default() -> Output:  # pyright: ignore[reportUnusedFunction]
    """Create the default output functor.

    Returns:
        A new rich output when `rich` is installed, otherwise a new standard
            output.

    """
    if available.RICH:
        return Rich()
    return Stdout()  # pragma: no cover
