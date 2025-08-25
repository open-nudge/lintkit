# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Core module providing rule defining capabilities.

When creating a new rule, one should inherit from a specific
`Rule` subclass, namely:

- [`lintkit.rule.Node`][] for a rule that is applied on a node
- [`lintkit.rule.File`][] for a rule that is applied on a whole file
- [`lintkit.rule.All`][] for a rule that has a check applied on all files

Tip:
    Check out [Advanced tutorial](/lintkit/tutorials/advanced)
    and [File tutorial](/lintkit/tutorials/file) to see all of them
    in real life examples.

"""

from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    import pathlib

    from collections.abc import Iterable
    from re import Pattern

    from ._ignore import Span


from . import error as e
from . import registry, settings
from ._value import Value

T = typing.TypeVar("T")


class Rule(abc.ABC):
    """Base class for all `rule`s.

    Warning:
        This class __should not be used directly__.
        Use [`lintkit.rule.Node`][],
        [`lintkit.rule.File`][] or
        [`lintkit.rule.All`][].

    """

    code: int | None = None
    """Integer code assigned to the rule.

    Warning:
        Specifying this value constitutes `rule` creation!
        Without it, such class acts as a shared functionality.

    Example:
        ```python
        import lintkit

        # Can further inherit from it to create complex rules.
        class NotRule(lintkit.rule.Node):
            pass

        # Is a Rule, cause `code` argument is provided
        class Rule(NotRule, code=0):
            pass
        ```

    """

    file: pathlib.Path | None = None
    """Path to the loaded file.

    Note:
        You may want to use this variable directly within `values` method.

    Info:
        Will be populated by appropriate [`lintkit.loader.Loader`][] subclass,
        initially `None`. It is of type
        [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

    """

    _ignore_line: Pattern[str] | None = None
    """Regex pattern used to ignore a specific line for this rule.

    Note:
        When the rule is created (when `code` was provided) it is always
        set to appropriate
        [`re.Pattern`](https://docs.python.org/3/library/re.html#re.Pattern)
        based on [`lintkit.settings.ignore_line`][]

    """

    _lines: list[str] | None = None
    """Content split by lines. Used in multiple places, hence cached.

    Info:
        Will be populated by [`lintkit.loader`][], initially `None`.

    """

    _ignore_spans: list[Span] | None = None
    """Text spans where the rules should be ignored.

    Info:
        Will be populated by [`lintkit.loader`][], initially `None`.

    """

    @abc.abstractmethod
    def values(self) -> Iterable[Value[typing.Any]]:
        """Function returning values to check against.

        Tip:
            Check out any tutorial
            (e.g. [Basic tutorial](/lintkit/tutorials/basic))
            for a usage example.

        Warning:
            __This is the core function which should always
            be implemented for each rule.__

        Yields:
            Values to be checked against this rule.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def check(self, value: Value[typing.Any]) -> bool:
        """Perform the check on a certain `value`.

        Tip:
            Check out any tutorial
            (e.g. [Basic tutorial](/lintkit/tutorials/basic))
            for a usage example.

        Note:
            This method is inherited from [`lintkit.check.Check`][]

        Args:
            value:
                Value to check.

        Returns:
            `True` if rule is violated, `False` otherwise.
        """
        raise NotImplementedError

    def description(self) -> str:  # pragma: no cover
        """Description of the rule.

        Note:
            You can use this method to provide end users
            with human readable description of the rule.

        Returns:
            Description of the rule.
        """
        return "No description provided."

    def __init_subclass__(
        cls,
        *,
        code: int | None = None,
    ) -> None:
        """Initialize the class (__not instance!__).

        Info:
            This method is defined so the user can pass `code`
            as an argument during inheritance.

        Warning:
            `code` has to uniquely identify the `rule`!

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
            specific methods to be shared by other rules.

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
            `__init__` is called internally by the framework,
            linter/rule creators __should not__ use it directly.

        """
        if self.code is None:
            raise e.CodeMissingError(self)

    # Refactoring this method might break pyright
    # (e.g. verifying attributes are set will not be picked up
    # if done in a separate helper method).
    def ignored(self, value: Value[T]) -> bool:  # noqa: C901
        """Check if the value should be ignored by this `rule`.

        Info:
            This function is called internally by `lintkit`
            framework.

        `Value` is ignored if:

        - file contains whole file ignore/`noqa`
            (as defined by [`lintkit.settings.ignore_file`][]
        - its line is in the ignore/`noqa` spans
            (as defined by [`lintkit.settings.ignore_span_start`][]
            and [`lintkit.settings.ignore_span_end`][])
        - its line matches the [`lintkit.settings.ignore_line`][] regex
            (per-line ignore/`noqa`)

        Args:
            value:
                [`lintkit.Value`] to be possibly ignored.

        Returns:
            `True` if the [`lintkit.Value`] should be ignored
            for whatever reason.

        """
        # Branch below should never run (all necessary attributes)
        # would be instantiated before this call.
        # - Cannot use `any` due to pyright not understanding this check
        # - Cannot refactor as `pyright` will not catch it
        if (
            self._ignore_line is None
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
            return self._ignore_line.search(value._self_comment) is not None  # noqa: SLF001  # pragma: no cover

        start_line = pointer.value
        if start_line is not None:
            for span in self._ignore_spans:
                if start_line in span:
                    return True
            return (
                self._ignore_line.search(self._lines[start_line - 1])
                is not None
            )

        # This might happen when there is no comment, nor line number available
        # An example would be JSON and `Value` created directly
        return False  # pragma: no cover

    def error(
        self,
        message: str,
        value: Value[T],
    ) -> bool:
        """Output an error message.

        Info:
            This method is called internally by `lintkit`
            framework.

        This function uses [`lintkit.settings.output`][] to output
        (however this operation is defined)
        rule violations (usually some sort of printing to `stdout`,
        e.g. standard `print` or [`rich`](https://github.com/Textualize/rich)
        colored `stdout`).

        Warning:
            This method likely contains side-effects (printing)!

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

    @abc.abstractmethod
    def __call__(self) -> Iterable[bool]:
        """Calls this `rule` on a given entity.

        Info:
            This method is implemented by concrete subclasses
            ([`lintkit.rule.Node`][],
            [`lintkit.rule.File`][],
            [`lintkit.rule.All`][])

        Info:
            This method is called internally by `lintkit`
            framework.

        Yields:
            `True` if a given [`lintkit.Value`][] (or a grouping of them,
                depending on the type of `rule`) violates the rule,
                `False` otherwise.

        """
        raise NotImplementedError


class Node(Rule, abc.ABC):
    """Rule that is applied on a node (e.g. Python `dict` in a parsed program).

    Note:
        This class is used to define fine-grained rules and is
        likely to be used the most commonly.

    """

    @abc.abstractmethod
    def message(self, value: Value[typing.Any]) -> str:
        """Message to output when the rule is violated.

        Note:
            You can use offending [`lintkit.Value`][] to display
            more information about the violation. [`lintkit.Value`][]
            can hold different objects depending
            on the [`lintkit.Node.values`][] (directly) and
            on the [`lintkit.loader`][] mixin (indirectly).

        Args:
            value:
                Value which violated the rule.

        Returns:
            String message to output when the rule is violated.

        """
        raise NotImplementedError

    def __call__(self) -> Iterable[bool]:  # pyright: ignore[reportImplicitOverride]
        """Calls this `rule` on a specific node.

        Note:
            This method is called by the framework, linter creators
            __should not use it directly__.

        Info:
            This method has side effects (see [`lintkit.rule.Rule.error`][])

        Tip:
            Check out [Basic tutorial](/lintkit/tutorials/basic)
            to see an example usage of this `rule`.

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

    Warning:
        Use [`lintkit.rule.File`][] or [`lintkit.rule.All`][] as concrete
        implementations of this class.
    """

    @abc.abstractmethod
    def message(self) -> str:
        """Message to output when the rule is violated.

        Note:
            This message is per-file (which you can access
            by `self.file`) or per all files, hence
            there is no [`lintkit.Value`][] argument as it is
            not applicable.

        Tip:
            You can keep necessary data from any step (e.g.
            [`lintkit.rule.File.values`][]) within `self`
            and use them here.

        Returns:
            Message to output when the rule is violated.

        """
        raise NotImplementedError

    def finalize(self, n_fails: int) -> bool:
        """Final `check` of the rule.

        Tip:
            You can think of this method as a
            [`lintkit.rule.Node.check`][] but for
            [`lintkit.rule.All`][] and [`lintkit.rule.All`][]

        Info:
            After the rule is called
            across all objects (all files ([`lintkit.rule.File`][]
            or all nodes in a file ([`lintkit.rule.All`][]))),
            this method allows to make a decision whether
            to error or not.

        Tip:
            You can keep necessary data from any step (e.g.
            [`lintkit.rule.All.check`][]) within `self`
            and use them here.

        Args:
            n_fails:
                Number of failures encountered during `__call__`.

        Returns:
            `True` if the rule should raise an error, `False` otherwise.
            Default: error out if `n_fails > 0`.

        """
        return n_fails > 0

    def __init__(self) -> None:
        """Initialize the rule.

        Attributes:
            n_fails:
                Number of failures raised by the `rule`.
                It is set to zero after each call to
                `[`lintkit.rule.File.finalize`][]`.

        """
        super().__init__()

        self.n_fails: int = 0

    def __call__(self) -> Iterable[typing.Literal[False]]:  # pyright: ignore[reportImplicitOverride]
        """Call this `rule` on all `values`.

        Note:
            This method is called by the framework, creators __should not__
            use it directly.

        Warning:
            This method accumulates failures from `[lintkit.rule.File.check]`
            instead of raising each one, which allows you to make a decision
            based on the aggregated number of failures
            (see `[`lintkit.rule.File.finalize`][]`).

        Returns:
            Always `False` (no matter the `check` output) to make the
            interface compatible with [`lintkit.rule.Node`][]

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

        Info:
            This method is called after all `values` are checked
            and allows to make a decision whether to raise an error
            or not based on the number of failures.

        Note:
            This method is ran after each `File` (if the object is am `All`)
            or after all `Node`s (if the object is a `File`).

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
    """Rule that is applied __on a whole file__.

    Checks run across __all elements within a certain file__
    (e.g. all [`ast.AST`](https://docs.python.org/3/library/ast.html#ast.AST)
    nodes in a `python` file).

    Note:
        The error can be raised __after encountering all elements__
        (unlike [`lintkit.rule.Node`][] which raises an error as soon
        as it finds a violation).

    Tip:
        See [File tutorial](/lintkit/tutorials/file) for a usage example.

    Tip:
        [`lintkit.rule.File.finalize`][] is effectively a place where you
        decide what to do with accumulated errors.
    """


class All(_NotNode, abc.ABC):
    """Rule that is applied __on a all files__.

    Checks run across __all elements across all files__
    (e.g. all [`ast.AST`](https://docs.python.org/3/library/ast.html#ast.AST)
    nodes in __all__ `python` file).

    Note:
        The error can be raised __after encountering all elements__
        (unlike [`lintkit.rule.Node`][] which raises an error as soon
        as it finds a violation).

    Tip:
        See [File tutorial](/lintkit/tutorials/file) for a usage example.

    Tip:
        [`lintkit.rule.File.finalize`][] is effectively a place where you
        decide what to do with accumulated errors.
    """
