# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Unified `Value` type allowing rule application over multiple datatypes.

Warning:
    Multiline `ignore`s or skips are not supported
    for `TOML` due to `tomlkit` not returning line numbers
    of items.

Users should be mostly concerned about `Value` class, which wraps
items on a per-loader base and should be used with `Python`
nodes or `TOML` items (see `from_python` and `from_toml` class
methods).

Example:
```python
```

"""

from __future__ import annotations

import dataclasses
import typing

import wrapt

from . import available

if typing.TYPE_CHECKING:
    import ast

T = typing.TypeVar("T")


class Value(wrapt.ObjectProxy, typing.Generic[T]):  # pyright: ignore [reportUntypedBaseClass]
    """`Value` used by rules for verification.

    Note:
        Instance of this type should __always__ be returned from
        [`lintkit.rule.Rule.values`][]

    Tip:
        You should use objects of this class __just like you would
        use the `value` directly.__ as it is a "perfect proxy".
        Its other functionalities __are used internally__ (e.g. `Pointer`)

    Can be essentially anything (e.g. `dict` from parsed `JSON`,
    `string` value from that `dict` or some other rule created value).

    It is later used by the pipeline to verify whether this value
    complies with the `Rule` itself.

    Tip:
        Use creation static methods (
        [`lintkit.Value.from_python`][],
        [`lintkit.Value.from_toml`][],
        or [`lintkit.Value.from_json`][]
        ) when returning
        values from rules inheriting from
        [`lintkit.loader.Python`][],
        [`lintkit.loader.TOML`][] or
        [`lintkit.loader.JSON`][]
        respectively.

    Caution:
        `YAML` __is already wrapped by [`lintkit.Value`][]__ during
        when using [`lintkit.loader.YAML`][], no need to process
        them within `values` function.

    Note:
        This `class` acts as a "perfect proxy" for end users
        by utilising [`wrapt`](https://github.com/GrahamDumpleton/wrapt)
        (which means wrapped `value` should be usable just like
        the original one).


    Attributes:
        value (typing.Any):
            Value to check against the rules.
        comment (str | None):
            Source code comment related to the object, if any.
            __Used internally__
        start_line (Pointer):
            Line number (represented as a `Pointer`).
            __Used internally__
        start_column (Pointer):
            Column number (represented as a `Pointer`).
            __Used internally__
        end_line (Pointer):
            End line number (represented as a `Pointer`).
            __Used internally__
        end_column (Pointer):
            End column number (represented as a `Pointer`).
            __Used internally__

    """

    def __init__(  # noqa: PLR0913
        self,
        value: T = None,
        start_line: Pointer | None = None,
        start_column: Pointer | None = None,
        end_line: Pointer | None = None,
        end_column: Pointer | None = None,
        comment: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(value)

        if start_line is None:
            start_line = Pointer()
        if start_column is None:
            start_column = Pointer()
        if end_line is None:
            end_line = Pointer()
        if end_column is None:
            end_column = Pointer()

        self._self_start_line: Pointer = start_line
        self._self_start_column: Pointer = start_column
        self._self_end_line: Pointer = end_line
        self._self_end_column: Pointer = end_column
        self._self_comment: str | None = comment
        self._self_metadata: dict[str, typing.Any] = kwargs

    @staticmethod
    def from_python(value: T, node: ast.AST) -> Value[T]:
        """Create a `Value` from Python's `ast.AST` node.

        Arguments:
            value:
                Some `Python` plain object.
            node:
                Python's [`ast`](https://docs.python.org/3/library/ast.html)
                `Node` which corresponds to the `value`.

        Returns:
            Provided value with its respective Python node.

        """
        return Value(
            value=value,
            start_line=_optional_get(node, "lineno"),
            start_column=_optional_get(node, "col_offset"),
            end_line=_optional_get(node, "end_lineno"),
            end_column=_optional_get(node, "end_col_offset"),
        )

    @staticmethod
    def from_json(value: T) -> Value[T]:
        """Create a `Value` from `JSON` values.

        Note:
            As `JSON` does not support comments,
            only `value` is necessary.

        Warning:
            Due to no comments, all ignore lines
            are currently ignored and __only file exclusions__
            are available.

        Arguments:
            value:
                Some object, usually plain `Python` after parsing
                `JSON` via
                [standard `json`](https://docs.python.org/3/library/json.html)
                library.

        Returns:
            `JSON` parsed data as a `Value`

        """
        return Value(value=value)

    if available.TOML:

        @staticmethod
        def from_toml(item: typing.Any) -> Value[typing.Any]:
            """Create a `Value` from `tomlkit` `Item`.

            Warning:
                Multiline `ignore`s or skips are not supported
                for `TOML` __due to the lack of line numbers__.

            Warning:
                `Value` will contain no line/column info
                (as it is unavailable in
                [`tomlkit`](https://tomlkit.readthedocs.io)), but
                propagates `comment` field to other elements of the
                system which allows it to be used for line ignoring.

            Returns:
                `tomlkit.Item` represented as `Value`.

            """
            return Value(
                # Principially items may not have an `unwrap` method, e.g.
                # https://tomlkit.readthedocs.io/en/latest/api/#tomlkit.items.Key
                # though it is available for most of the items,
                value=item.unwrap() if hasattr(item, "unwrap") else item,
                comment=item.trivia.comment
                if hasattr(item, "trivia")
                else None,
            )

    else:  # pragma: no cover
        pass

    if available.YAML:

        @staticmethod
        def _from_yaml(value: T, node: typing.Any) -> Value[T]:
            """Create a Value from a modified ruamel.YAML node.

            Note:
                This method is used internally and __should not be
                used directly__ unlike `toml` and `python` or `JSON`
                counterparts.

            Returns:
                `YAML` element wrapped with `Value`.

            """
            return Value(
                value=value,
                start_line=_optional_get(node, "start_mark", "line", offset=1),
                start_column=_optional_get(
                    node, "start_mark", "column", offset=1
                ),
                end_line=_optional_get(node, "end_mark", "line", offset=1),
                end_column=_optional_get(node, "end_mark", "column", offset=1),
                style=getattr(node, "style", None),
            )

    else:  # pragma: no cover
        pass


@dataclasses.dataclass
class Pointer:
    """Pointer to the source code (e.g. `start_line`).

    Tip:
        You are unlikely to need to use objects of this
        class __at all__.

    Warning:
        This class is (usually) not intended to be instantiated directly.
        It is used internally by the `Value` class to represent
        line and column numbers as a lightweight wrapper.

    Attributes:
        value:
            Line or column number, or `None` if not available.
            If `None`, it is represented as "-".

    """

    value: int | None = None

    def __str__(self) -> str:  # pyright: ignore [reportImplicitOverride]
        """String representation of the pointer.

        Returns:
            String representation of the pointer value, or `"-"` if `None`.

        """
        if self.value is None:
            return "-"
        return str(self.value)

    def __bool__(self) -> bool:
        """Check if the pointer has a `value`.

        Returns:
            `True` if the pointer has a `value`, `False` if it is `None`.

        """
        return self.value is not None

    def __add__(self, other: int) -> Pointer:
        """Add an integer to the pointer value.

        Allows to offset the pointer by a specific number
        (usually for compatibility reasons between different
        libraries and formats).

        Args:
            other: Integer to add to the pointer value.

        Returns:
            A new `Pointer` instance with the updated value.

        """
        if self.value is None:
            return Pointer()  # pragma: no cover
        return Pointer(self.value + other)


def _optional_get(
    node: typing.Any, *attributes: str, offset: int = 0
) -> typing.Any | None:
    """Recursively obtain a given attribute and transform it to `Pointer`.

    Args:
        node:
            Node from which to obtain attributes.
        *attributes:
            Names of the attributes to obtain (if these exist).
        offset:
            Pointer offset for the value, if any
            (useful in `YAML` 0-indexed positioning).

    """
    current = node
    for attribute in attributes:
        current = getattr(current, attribute, None)
        if current is None:  # pragma: no cover
            return Pointer()

    return Pointer(current) + offset
