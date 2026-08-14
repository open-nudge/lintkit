# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Global `lintkit` settings.

## General

Info:
    Variables in this module are crucial and
    __should be set by the linter creator__.

Example:
    ```python
    import lintkit

    lintkit.settings.name = "MYLINTER"

    # Now # MYLINTER: 223 could be used to ignore error 223
    lintkit.settings.ignore_line = ".* MYLINTER: .*{name}{code}.*"
    lintkit.settings.ignore_file = ".* MYLINTER-FILE: .*{name}{code}.*"
    ```

Warning:
    Some variables __might__ be defined by end-users, but it is
    relatively uncommon. Is someone adjusts a linter
    __it is possible__ to only adjust these settings to change
    linter behavior.

## Ignore options

`lintkit` allows users to define three different ignores:

- per line (like `# noqa: CODE`) as defined by
    [`lintkit.settings.ignore_line`][]
- per file (like `# noqa-file: CODE`) as defined by
    [`lintkit.settings.ignore_file`][]
- span of lines (e.g. from `20` to `80`) as defined by
    [`lintkit.settings.ignore_span_start`][] and
    [`lintkit.settings.ignore_span_end`][]

See a YAML example for a file ignore:

Example:
    ```yaml
    ---
    # Ignore linter rules 12 and 37 for the whole file
    # noqa-file: MYLINTER12
    my:
        yaml:
            - "example"
            - "file"
    ```

or per-line and span for `Python`:

Example:
    ```python
    # rule 27 ignored here
    def foo():  # noqa: MYLINTER27
        pass


    # Ignore rule 13 for the next 5 lines
    # noqa-start: MYLINTER13
    def bar() -> None:
        print("I would violate rule 13 >:(")


    def baz() -> str:
        return "Hate rule 13 let me out :("


    # noqa-end: MYLINTER13
    ```

"""

from __future__ import annotations

from . import error
from . import output as output_module

name: str | None = None
"""The name of the linter (`str`).

Warning:
    Has to be set before linter usage, usually
    done at the level of `linter` module creation,
    __not by the end user__ (user of linter).

"""

output: output_module.Output | None = None
"""The configured output functor.

By default (if `None`), will use [`lintkit.output.Rich`][lintkit.output.Rich]
if the `rich` library is installed, otherwise
[`lintkit.output.Stdout`][].

Note:
    A custom [`lintkit.output.Output`][] subclass instance might be provided
    by the creator or user.

Tip:
    [`lintkit.output.JSON`][] accumulates records during a run and prints one
    complete JSON array when the runner finalizes it.

"""

ignore_line: str = ".* noqa: .*{name}{code}(?!\\d).*"
"""The regex pattern registering a line to be ignored.

Note:
    By default will match any line containing ` noqa: {name}{code}`,
    possibly with multiple errors on the same line, e.g.
    ```# noqa: E123, E456``` or ```# noqa: E123 E456 E789```.
"""

ignore_file: str = ".* noqa-file: [^\n]*{name}{code}(?!\\d).*[^\n]*"
"""The regex pattern indicating the error should be ignored in the whole file.

Note:
    By default will match any line containing ` noqa-file: {name}{code}`,
    possibly with multiple errors on the same line, e.g.
    ```# noqa-file: E123, E456``` or ```# noqa-file: E123 E456 E789```.
"""

ignore_span_start: str = ".* noqa-start: .*{name}{code}(?!\\d).*"
"""The regex pattern registering start of ignoring.

Warning:
    User has to provide `ignore_span_end` otherwise an error will
    be raised.

Note:
    By default will match any line containing `# noqa-start: {name}{code}`,
    possibly with multiple errors on the same line, e.g.
    ```# noqa: E123, E456``` or ```# noqa: E123 E456 E789```.
"""

ignore_span_end: str = ".* noqa-end: .*{name}{code}(?!\\d).*"
"""The regex pattern registering a line to be ignored.

Warning:
    User has to provide `ignore_span_start`, otherwise this
    `noqa` will have no effect.

Note:
    By default will match any line containing `# noqa-end: {name}{code}`,
    possibly with multiple errors on the same line, e.g.
    ```# noqa: E123, E456``` or ```# noqa: E123 E456 E789```.
"""


# Used internally by `rule.Rule`
def _name() -> str:  # pyright: ignore[reportUnusedFunction]
    """Get the linter name.

    Returns:
        The linter name

    Raises:
        LinterNameMissingError: If the linter name is not set
    """
    if name is None:
        raise error.NameMissingError
    return name


# Used internally by `rule.Rule`
def _output() -> output_module.Output:  # pyright: ignore[reportUnusedFunction]
    """Get the output functor.

    Returns:
        The configured output functor, or a new default functor.
    """
    if output is None:
        return output_module._default()  # noqa: SLF001
    return output
