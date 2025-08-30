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
    import pathlib

    from .rule import Rule


class LintkitError(Exception):
    """Base class for all `lintkit` errors."""


class LintkitInternalError(LintkitError):
    """Internal `lintkit` error which should never be raised."""


@typing.final
class NotSubclassError(LintkitError):
    """Raised when the registered `rule` is not an appropriate subclass.

    Info:
        Created rule (via `code=<NUMBER>`) __has to inherit
        from [`lintkit.rule.Rule`][] __AND__ [`lintkit.loader.Loader`].

    Warning:
        Python's typing does not support intersection types,
        hence this is checked dynamically.

    Tip:
        This error is raised automatically by `lintkit`,
        no need for explicit raising.

    The following would be an offending call:

    ```python
    import lintkit


    # Does not inherit from `loader.Loader`
    class MyRule(lintkit.rule.Node, code=-1):
        pass
    ```

    """

    def __init__(self) -> None:
        """Initialize the error."""
        self.message = (
            "Rule has to inherit from both 'lintkit.rule.Rule' "
            "and 'lintkit.loader.Loader' classes (or subclasses)."
        )
        super().__init__(self.message)


@typing.final
class IgnoreRangeError(LintkitError):
    """Raised when the end of the ignore range is missing.

    Note:
        Informs the user when the `noqa-range`/range ignore
        was started in a file, but was not explicitly ended.

    Tip:
        This error is raised automatically by `lintkit` when rules are ran,
        no need for explicit raising.

    For this [`lintkit.settings.ignore_span_start`][] and
    [`lintkit.settings.ignore_span_end`][]:

    ```python
    import lintkit

    # Anything between igstart: <NAME><CODE> and igend: <NAME><CODE>
    lintkit.settings.ignore_span_start: str = ".* igstart: .*{name}{code}.*"
    lintkit.settings.ignore_span_end: str = ".* igend: .*{name}{code}.*"
    ```

    The following spans would throw `IgnoreRangeError`:

    ```python
    # igstart: BU137


    def foo():
        pass


    # Different error code!
    # igend: BU213


    # igstart: BU137
    def bar():
        pass


    # No igend at all!
    ```

    This would throw:

    ```python
    End of ignore range missing, please specify it.
    Start of the range was at line '0' with content: '# igstart: BU137'.
    ```

    Note:
        See `settings.ignore_span_start` and `settings.ignore_span_end`
        for more information.

    """

    def __init__(self, file: pathlib.Path, start: int, line: str) -> None:
        """Initialize the error.

        Args:
            file:
                File where the error occurred.
            start:
                The line number where the ignore range started.
            line:
                The content of the line where the ignore range
                started.

        """
        self.file = file
        self.start = start
        self.line = line

        self.message = (
            f"End of ignore range missing in: '{file}', please specify it. "
            f"Start of the range was at line '{start}' with content: '{line}'."
        )
        super().__init__(self.message)


@typing.final
class NameMissingError(LintkitError):
    """Raised when the linter's `lintkit.settings.name` was not set.

    Note:
        __Informs the linter creator__ `lintkit.settings.name` was not set,
        as this value should be predefined before end users use the linter.

    Error output:

    ```python
    Linter name missing (please set 'lintkit.settings.name' variable)
    ```

    """

    def __init__(self) -> None:
        """Initialize the error."""
        self.message = (
            "Linter name missing (please set 'lintkit.settings.name' variable)."
        )
        super().__init__(self.message)


@typing.final
class CodeNegativeError(LintkitError):
    """Raised when a rule with the same code already exists.

    Note:
        __Informs the linter creator__, that the rule's code
        was negative, which is not allowed.

    Example of offending code:

    ```python
    import lintkit


    class MyRule(lintkit.rule.Node, lintkit.loader.Loader, code=-1):
        pass
    ```

    which raises:

    ```python
    Rule 'MyRule' has code '-1' which should be a positive 'int'.
    ```

    """

    def __init__(self, code: int, rule: type[Rule]) -> None:
        """Initialize the error.

        Args:
            code:
                The negative code that was provided.
            rule:
                The offending rule.
        """
        self.code = code
        self.rule = rule

        self.message = (
            f"Rule '{type(rule).__name__}' has code '{code}' "
            f"which should be a positive 'int'."
        )
        super().__init__(self.message)


@typing.final
class CodeExistsError(LintkitError):
    """Raised when a rule with the same code already exists.

    Note:
        __Informs the linter creator__, that the rule code
        was already registered by another rule.

    Example of offending code:

    ```python
    import lintkit


    class FirstRule(lintkit.rule.Node, lintkit.loader.Loader, code=12):
        pass


    class SecondRule(lintkit.rule.Node, lintkit.loader.Loader, code=12):
        pass
    ```

    which raises:

    ```python
    Rule 'SecondRule' cannot be registered with code '12'
    as it is already taken by 'FirstRule'.
    ```

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
        self.code = code
        self.new_rule = new_rule
        self.old_rule = old_rule

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


    # Raised during instantiation,
    # usually during `lintkit.run` usage
    rule = MyRule()  # raises CodeMissingError
    ```

    which raises:

    ```python
    Rule 'MyRule' is missing a 'code' attribute
    (pass it during inheritance, e.g. 'MyRule(lintkit.rule.Node, code=2731)').
    ```

    """

    def __init__(self, rule: Rule) -> None:
        """Initialize the error.

        Args:
            rule:
                The rule that was not registered
                via `code` keyword argument.
        """
        self.rule = rule

        name = type(rule).__name__
        self.message = (
            f"Rule '{name}' is missing a 'code' attribute"
            "(pass it during inheritance, e.g. "
            f"'{name}(lintkit.rule.Node, code=2731)')."
        )
        super().__init__(self.message)
