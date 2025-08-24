# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Core module providing rule defining capabilities.

When creating a new rule, one should subclass a specific
`Rule` subclass, namely:

- `Node` for a rule that is applied on a node
- `File` for a rule that is applied on a whole file
- `All` for a rule that has a check applied on all files

"""

from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    import pathlib

    from collections.abc import Iterable
    from re import Pattern

    from ._ignore import Span

from . import check, loader, registry, settings
from . import error as e
from ._value import Value

T = typing.TypeVar("T")


class Rule(loader.Loader, check.Check, abc.ABC):
    """Base Rule class of `lintkit`.

    Allows to quickly define new linters based on:

    - a target type
    - a code
    - configuration

    """

    code: int | None = None
    """Code of the rule (see `__subclass_init__` for an example).

    Note:
        Specificuing this value constitutes `rule` creation.

    """

    ignore_line: Pattern[str] | None = None
    """Regex pattern used to ignore a specific line for this rule.

    Note:
        After initialization (after providing `code`) it is always
        set to some `re.Pattern` based on `settings.ignore_line`

    """

    content: str | None = None
    """Loaded file content (see `loader` module for more information)."""

    file: pathlib.Path | None = None
    """Path to the loaded file (see `loader` module for more information)."""

    _lines: list[str] | None = None
    """Content split by lines. Used in multiple places, hence cached."""

    _ignore_spans: list[Span] | None = None
    """Text spans where the rules should be ignored."""

    @abc.abstractmethod
    def values(self) -> Iterable[Value[typing.Any]]:
        """Function returning values (e.g. `ast.Node`) to check against.

        Warning:
            __This is the core function which should always
            be implemented for each rule__

        Yields:
            Values to be checked against the rule.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(self) -> Iterable[bool]:
        """Calls this `rule` on a given entity.

        Note:
            This method is implemented by concrete subclasses
            (e.g. `Node` or `File`)

        Yields:
            `True` if a given entity violates the rule, `False` otherwise.

        """
        raise NotImplementedError

    def __init_subclass__(
        cls,
        *,
        code: int | None = None,
    ) -> None:
        """Register the rule under specific code.

        Warning:
            `code` has to uniquely identify the `rule`.

        Example:
        ```python
        import lintkit


        # Pass the code as an argument
        class MyRule(lintkit.rule.Node, code=42):
            pass
        ```

        Warning:
            When `code` is provided it will define the `rule`.
            Before that you can subclass `Rule` and implement
            specific methods to later be shared by other rules.

        Example:
        ```python
        import lintkit

        # code argument not provided, this is
        # still an interface, not a rule
        class SharedFunctionality(lintkit.rule.Node):
            @classmethod
            def shared_functionality(cls):
                # Define your shared functionality

        # actual rule
        class Rule(SharedFunctionality, code=21):
            pass
        ```

        Raises:
            lintkit.error.CodeNegativeError:
                If `code` is negative.
            lintkit.error.CodeExistsError:
                If a rule with the same `code` already exists.

        Args:
            code:
                Code to assign for the rule.

        """
        # Code actually defines the rule
        if code is not None:
            registry._add(cls, code)  # noqa: SLF001

    def __init__(self) -> None:
        """Initialize the rule.

        Warning:
            This method is called by the framework, creators __should not__
            use it directly.

        """
        if self.code is None:
            raise e.CodeMissingError(self)

    def error(
        self,
        message: str,
        value: Value[T],
    ) -> bool:
        """Print an error message.

        This function uses `output` to print (however
        this operation is defined) eventual rule violations.

        Note:
            This function is called internally by `lintkit`
            framework.

        Args:
            message:
                message to print
            value:
                `Value` instance which violated the rule.
                Used to obtain (eventual) line information.

        Returns:
            bool: Always True as the error was raised
        """
        printer = settings._output()  # noqa: SLF001

        printer(
            # This might be error prone for multiple linters defined
            # as the same package.
            name=settings._name(),  # noqa: SLF001 # pyright: ignore[reportCallIssue]
            code=self.code,
            message=message,
            file=self.file,
            start_line=value._self_start_line,  # noqa: SLF001
            start_column=value._self_start_column,  # noqa: SLF001
            end_line=value._self_end_line,  # noqa: SLF001
            end_column=value._self_end_column,  # noqa: SLF001
        )
        return True

    # Refactoring this method might break pyright
    # (e.g. verifying attributes are set will not be picked up
    # if done in a separate helper method).
    def ignored(self, value: Value[T]) -> bool:  # noqa: C901
        """Check if the value should be ignored by this `rule`.

        Note:
            This function is called internally by `lintkit`
            framework.

        `Value` is ignored if:

        - its line is in the ignore spans
        - its line matches the `settings.ignore_line` regex
        - line comment (e.g. for `TOML` matches the `settings.ignore_line`
            regex)

        Args:
            value:
                Value to check

        Returns:
            `True` if the value should be ignored.
        """
        # Branch below should never run (all necessary attributes)
        # would be instantiated before this call.
        # - Cannot use `any` due to pyright not understanding this check
        # - Cannot refactor as `pyright` will not catch it
        if (
            self.ignore_line is None
            or self._ignore_spans is None
            or self._lines is None
        ):  # pragma: no cover
            raise e.LintkitInternalError

        pointer = value._self_start_line  # noqa: SLF001
        if not pointer:
            if value._self_comment is None:  # noqa: SLF001
                return False
            # Currently used for TOML comments
            # Some additional tests might be necessary
            return self.ignore_line.search(value._self_comment) is not None  # noqa: SLF001  # pragma: no cover

        start_line = pointer.value
        if start_line is not None:
            for span in self._ignore_spans:
                if start_line in span:
                    return True
            return (
                self.ignore_line.search(self._lines[start_line - 1]) is not None
            )

        # This might happen when there is no comment, nor line number available
        # An example would be JSON and `Value` created directly
        return False  # pragma: no cover

    @property
    def description(self) -> str:  # pragma: no cover
        """Description of the rule.

        Note:
            You can use this method to provide end users
            with human readable description of the rule.

        Returns:
            Description of the rule.
        """
        return "No description provided."

    @classmethod
    def _run_load(
        cls,
        file: pathlib.Path,
        content: str,
        lines: list[str],
        ignore_spans: list[Span],
    ) -> None:
        """Load contents of the file.

        Note:
            File is read once per a set of `rule`s to improve performance.
            Rest of the arguments are reassigned which should be fast
            as it is only moving references to the objects.
            See `loader` module implementation for more information.

        Args:
            file:
                File to load
            content:
                Content of the file
            lines:
                Lines of the file
            ignore_spans:
                Spans containing lines to ignore in the file

        """
        # It is enough to compare the files as the full path
        # is unique (while multiple files can have the same content)
        file_changed = cls.file is None or file != cls.file
        if file_changed or not cls.should_cache():
            cls.load(file, content)
        cls.file = file
        cls.content = content
        cls._lines = lines
        cls._ignore_spans = ignore_spans

    @classmethod
    def _run_reset(cls) -> None:
        """Reset data injected into `rule`s."""
        cls.content = None
        cls.file = None
        cls._lines = None
        cls._ignore_spans = None
        cls.reset()


class Node(Rule, abc.ABC):
    """Rule that is applied on a node (e.g. Python `dict` in a parsed program).

    Note:
        This class is used to define fine-grained rules and is
        likely to be used the most commonly.

    """

    @abc.abstractmethod
    def message(self, value: typing.Any) -> str:
        """Message to output when the rule is violated.

        Note:
            You can use `value` to access the `Node` object that violated
            the rule. `value` can hold different objects depending
            on the mixins (e.g. `ast.AST` of `Python` or `YAML` node).

        Args:
            value:
                Value which violated the rule.

        Returns:
            Message to output when the rule is violated.

        """
        raise NotImplementedError

    def __call__(self) -> Iterable[bool]:  # pyright: ignore[reportImplicitOverride]
        """Calls this the `rule` on a node.

        Note:
            This method is called by the framework, creators __should not__
            use it directly.

        Note:
            This method has side effects (outputting errors according to
            `settings.output`).

        Yields:
            `True` if a given node violates the rule, `False` otherwise.

        """
        for value in self.values():
            if self.ignored(value):
                yield False
            else:
                error = self.check(value)
                if not error:
                    yield False
                else:
                    yield self.error(self.message(value), value)


class _NotNode(Rule, abc.ABC):
    """Base class for rules that are not applied on a node.

    Use `File` or `All` as concrete implementations of this class.
    """

    @abc.abstractmethod
    def message(self) -> str:
        """Message to output when the rule is violated.

        Note:
            This message is per-file (which you can access
            by `self.file`) or per all files, hence
            there is no `value` argument as it is not applicable.

        Args:
            value:
                Value which violated the rule.

        Returns:
            Message to output when the rule is violated.

        """
        raise NotImplementedError

    def finalize(self, n_fails: int) -> bool:
        """Finalize the rule check.

        After the `rule` is called across all objects
        (e.g. all files or all nodes in a file),
        this method allows to make a decision whether
        to error or not.

        Args:
            n_fails:
                Number of failures raised by the `rule`.

        Returns:
            `True` if the rule should raise an error, `False` otherwise.
            Default: raise if `n_fails > 0`.

        """
        return n_fails > 0

    def __init__(self) -> None:
        """Initialize the rule.

        Attributes:
            n_fails:
                Number of failures raised by the `rule`.
                It is reset after each call to `__call__`.

        """
        super().__init__()

        self.n_fails: int = 0

    def __call__(self) -> Iterable[bool]:  # pyright: ignore[reportImplicitOverride]
        """Call this `rule` on all `values`.

        Note:
            This method is called by the framework, creators __should not__
            use it directly.

        This method accumulates failures instead of raising each one,
        which allows you to make a decision based on the aggregated
        number of failures.

        Returns:
            bool: whether this linter raised an error or not

        """
        for value in self.values():
            # This line is checked, implicit else is not
            if not self.ignored(value):  # pragma: no branch
                fail = self.check(value)
                if fail:
                    self.n_fails += 1

        yield False

    def _run_finalize(self) -> bool:
        """Finalize the rule check.

        This method is called after all `values` are checked
        and allows to make a decision whether to raise an error
        or not based on the number of failures.

        Note:
            This method is ran after each `File` (if the object is a `File`)
            or after all `Node`s (if the object is a `Node`).

        Returns:
            `True` if the rule should raise an error, `False` otherwise.
            Default: raise if `n_fails > 0`.

        """
        fail = self.finalize(self.n_fails)
        self.n_fails = 0
        if fail:
            return self.error(self.message(), value=Value())
        return False


class File(_NotNode, abc.ABC):
    """Rule that is applied on a whole file.

    Checks run across all elements within file, while
    the error can be raised after encountering all elements
    (unlike `Node` which raises an error as soon as it finds
    a violation).
    """


class All(_NotNode, abc.ABC):
    """Rule that is applied on a __all__ files.

    Checks run across all elements of all files, while
    the error can be raised after encountering all elements
    (unlike `Node` which raises an error as soon as it finds
    a violation or `File` which raises an error after each file).
    """
