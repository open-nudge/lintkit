# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""`lintkit` custom errors.

These errors __should not be caught__, but
rather used to inform:

- `linter` developers about common mistakes they
made during rules creation (__most common__)
- `linter` users about common mistakes they made
(e.g. incorrect `noqa` ignores usage)

For the first example we might have:

```python
import ast
import lintkit


class MyRule(
    lintkit.check.Regex,
    lintkit.loader.Python,
    lintkit.rule.Node,
    code="123",  # offending line (should be an integer)
):
    def regex(self):
        return ".*"  # match everything

    def values(self):
        nodes = self.getitem("nodes_map")[ast.ClassDef]
        for node in nodes:
            yield lintkit.Value.from_python(node.name, node)
```

which raises:

```python
lintkit.error.CodeNotIntegerError:
    Rule 'MyRule' has code '123' which is of type 'str',
    but should be a positive `integer` .
```

while the second example might be (file being linted):

```python
def bar():
    pass


# noqa-start: MYRULE10
def foo():
    pass


# No noqa-end specified
```

which raises:

```python
lintkit.error.IgnoreRangeError:
    End of ignore range missing, please specify it.
    Start of the range was at line `4` with content: `# noqa-start: MYRULE10`.
```

"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .rule import Rule


class LintkitError(Exception):
    """Base class for all `lintkit` errors."""


class LintkitInternalError(LintkitError):
    """Internal `lintkit` error which should never be raised."""


@typing.final
class IgnoreRangeError(LintkitError):
    """Raised when the end of the ignore range is missing.

    Informs the user when the noqa-range was started in a file,
    but was not explicitly ended.

    Note:
        See `settings.ignore_range_start` and `settings.ignore_range_end`
        for more information.

    """

    def __init__(self, start: int, line: str) -> None:
        """Initialize the error.

        Args:
            start:
                The line number where the ignore range started.
            line:
                The content of the line where the ignore range
                started.

        """
        self.message = (
            "End of ignore range missing, please specify it. "
            f"Start of the range was at line `{start}` with content: {line}."
        )
        super().__init__(self.message)


@typing.final
class NameMissingError(LintkitError):
    """Raised when the linter's `lintkit.settings.name` was not set.

    Note:
        Informs the linter creator `lintkit.settings.name` was not set,
        as this value should be predefined before end users use the linter.

    """

    def __init__(self) -> None:
        """Initialize the error."""
        self.message = (
            "Linter name missing (please set `lintkit.settings.name` variable)."
        )
        super().__init__(self.message)


@typing.final
class CodeNegativeError(LintkitError):
    """Raised when a rule with the same code already exists.

    Note:
        Informs the linter creator, that his rule's code
        was negative, which is not allowed.

    """

    def __init__(self, code: int, rule: type[Rule]) -> None:
        """Initialize the error.

        Args:
            code:
                The negative code that was provided.
            rule:
                The offending rule.
        """
        self.message = (
            f"Rule '{type(rule).__name__}' has code '{code}' "
            f"which should be a positive `integer`."
        )
        super().__init__(self.message)


@typing.final
class CodeExistsError(LintkitError):
    """Raised when a rule with the same code already exists.

    Note:
        Informs the linter creator, that his rule code
        was already registered by another rule.

    """

    def __init__(self, code: int, new_rule: type[Rule], old_rule: Rule) -> None:
        """Initialize the error.

        Args:
            code:
                The code shared between the two rules.
            new_rule:
                The new rule that was trying to be registered
                under the same code.
            old_rule:
                The rule that was registered previously.

        """
        self.message = (
            f"Rule '{type(new_rule).__name__}' cannot be registered with code '{code}' "
            f"as it is already taken by '{type(old_rule).__name__}'."
        )
        super().__init__(self.message)


@typing.final
class CodeMissingError(LintkitError):
    """Raised when a given rule was not registered.

    This error is raised when the user did not specify
    `code` argument during class creation but tried to
    create an instance of the rule.

    Example of `register` usage:

    ```python
    import lintkit


    class MyRule(
        lintkit.check.Regex,
        lintkit.loader.JSON,
        lintkit.rule.Node,
        # code=2731  # this should be provided
    ):
        pass  # Implementation omitted


    rule = MyRule()  # raises CodeMissingError
    ```

    """

    def __init__(self, rule: Rule) -> None:
        """Initialize the error.

        Args:
            rule:
                The rule that was not registered
                via `code` keyword argument.
        """
        name = type(rule).__name__
        self.message = (
            f"Rule '{name}' is missing a `code` attribute"
            "(pass it during inheritance, e.g. "
            f"`{name}(lintkit.rule.Node, code=2731)`)."
        )
        super().__init__(self.message)
