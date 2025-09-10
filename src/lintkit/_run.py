# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Module containing runner for all registered rules."""

from __future__ import annotations

import pathlib
import typing
import warnings

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


from . import _ignore, registry
from . import rule as r


# Changing to overload: https://typing.python.org/en/latest/spec/overload.html
# does not help basedpyright unfortunately
def run(  # noqa: PLR0913
    files: Iterable[pathlib.Path | str],
    include_codes: Iterable[int] | None = None,
    exclude_codes: Iterable[int] | None = None,
    end_mode: typing.Literal["first", "all"] = "all",
    output: bool = False,  # noqa: FBT001, FBT002
    warn: bool = False,  # noqa: FBT001, FBT002
) -> Iterator[tuple[bool, r.Rule]] | bool:
    """Run all the rules on a given file.

    Caution:
        This function has two modes; one returns `bool`
        indicating whether __any rule raised any error__
        (the default), the second one returns
        __all rules and their error codes__ via an `iterator`.

    Tip:
        Use `output=False` if you create a custom linter
        and __only want to return the appropriate exit code__
        (most common usage)

    An example of minimal linter:

    Example:
        ```python
        import sys

        import lintkit

        # Mini linter over two files
        # Assuming appropriate rules were already defined


        def linter(files: tuple[str]):
            sys.exit(lintkit.run(files))


        linter(("a.py", "~/user/goo.py"))
        ```

    An example of iteration:

    Example:
        ```python
        import lintkit

        for failed, rule in lintkit.run(
            ("file.yml", "another.yml"), output=True
        ):
            print(f"Rule {rule} returned with an exit code {failed}")
        ```

    Tip:
        `output=True` (iteration mode) allows to gather general
        statistics from each rule and adjust the output to your
        liking.

    Warning:
        `exclude_codes` takes precedence over `include_codes`!

    Args:
        files:
            Files to lint.
        include_codes:
            A set of rule codes to include. If `None`, all rules are included.
        exclude_codes:
            A set of rule codes to ignore. If `None`, no rules are ignored.
            Warning: `exclude_codes` takes precedence over `include_codes`.
        end_mode:
            Whether to stop after the first error or run all rules.
            By default runs all rules.
        output:
            If `True`, returns an iterator over all rules and their outputs.
            If `False`, returns whether any rule raised an error.
        warn:
            If `True`, warn about UnicodeDecodeError when encountering
            files `lintkit` is unable to read. Default: `False`
            (skips the file silently).

    Returns:
        An iterator over all rules and their outputs OR a boolean indicating
            whether any rule raised an error.
    """
    generator_or_callable = _run(
        files,
        include_codes=include_codes,
        exclude_codes=exclude_codes,
        end_mode=end_mode,
        warn=warn,
    )
    if output:
        return generator_or_callable
    # Exhaust iterator and return whether any rule raised an error
    errored = False
    for result in generator_or_callable:
        if result[0]:
            errored = True
    return errored


def _run(  # noqa: C901, PLR0912
    files: Iterable[pathlib.Path | str],
    include_codes: Iterable[int] | None = None,
    exclude_codes: Iterable[int] | None = None,
    end_mode: typing.Literal["first", "all"] = "all",
    warn: bool = False,  # noqa: FBT001, FBT002
) -> Iterator[tuple[bool, r.Rule]]:
    """Internal function to run the rules on files.

    Note:
        This function was separated in order to provide a generator
        OR a `return` value in the `run` function.

    Warning:
        `exclude_codes` takes precedence over `include_codes`.

    Args:
        files:
            Files to lint.
        include_codes:
            A set of rule codes to include. If `None`, all rules are included.
        exclude_codes:
            A set of rule codes to ignore. If `None`, no rules are ignored.
        end_mode:
            Whether to stop after the first error or run all rules.
        warn:
            If `True`, warn about UnicodeDecodeError when encountering
            files `lintkit` is unable to read. Default: `False`
            (skips the file silently).

    Yields:
        Rule and whether it raised an error.
    """
    rules = list(
        registry.query(include_codes=include_codes, exclude_codes=exclude_codes)
    )

    for file in files:
        path = pathlib.Path(file)

        output = _load(path, warn)

        # This error may not be raised depending on the files being read
        if output is None:  # pragma: no cover
            continue

        lines, content = output

        # Setup and load necessary data for each rule
        for rule in rules:
            # Rule will have `skip` as it inherits from both Loader and Rule
            if rule.skip(path, content) or _ignore.file(rule, content):  # pyright: ignore[reportAttributeAccessIssue]
                continue
            # Rule will have `_run_load` due to above
            rule._run_load(  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                path,
                content,
                lines,
                ignore_spans=list(_ignore.spans(path, rule, lines)),
            )
            for fail in rule():
                yield fail, rule
                if fail and end_mode == "first":
                    return
            if isinstance(rule, r.File):
                fail = rule._run_finalize()  # noqa: SLF001
                yield fail, rule
                if fail and end_mode == "first":
                    return

    for rule in rules:
        # Rule will have `_run_load` as it inherits from both Loader and Rule
        rule._run_reset()  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]

    for rule in (rule for rule in rules if isinstance(rule, r.All)):
        fail = rule._run_finalize()  # noqa: SLF001
        yield fail, rule
        if fail and end_mode == "first":
            return  # pragma: no cover


def _load(
    path: pathlib.Path,
    warn: bool,  # noqa: FBT001
) -> tuple[list[str], str] | None:
    """Load contents in `path`.

    Args:
        path:
            File to load
        warn:
            If `True`, warn about UnicodeDecodeError when encountering
            files `lintkit` is unable to read. Default: `False`
            (skips the file silently).

    Returns:
        Error status and loaded lines and whole (unsplitted content).

    """
    try:
        return _read(path)
    # This error may not be raised depending on the files being read
    except UnicodeDecodeError as _:  # pragma: no cover
        if warn:  # pragma: no cover
            warnings.warn(
                f"File '{path}' could not be loaded.",
                category=UnicodeWarning,
                stacklevel=4,
            )
        return None


def _read(file: pathlib.Path) -> tuple[list[str], str]:
    """Setup the file for linting.

    Args:
        file: The file to be linted

    Returns:
        Tuple which contains:
            - The file path
            - File content line by line
    """
    content = file.read_text()
    lines = content.split("\n")
    return lines, content
