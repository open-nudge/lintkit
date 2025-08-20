# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Unified `Value` type allowing rule application over multiple datatypes.

Warning:
    `YAML` __is already wrapped with `Value`__ during
    data loading, no need to do it explicitly.

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


@dataclasses.dataclass
class Pointer:
    """Pointer to the source code.

    Warning:
        This class is not intended to be used directly.
        It is used internally by the `Value` class to represent
        line and column numbers.

    Attributes:
        value:
            Line or column number, or None if not available.
            If None, it is represented as "-".

    """

    value: int | None = None

    def __str__(self) -> str:  # pyright: ignore [reportImplicitOverride]
        """Return string representation of the pointer.

        Returns:
            String representation of the pointer value, or `"-"` if `None`.

        """
        if self.value is None:
            return "-"
        return str(self.value)

    def __bool__(self) -> bool:
        """Check if the pointer has a value.

        Returns:
            `True` if the pointer has a value, `False` if it is `None`.

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


class Value(wrapt.ObjectProxy):  # pyright: ignore [reportUntypedBaseClass]
    """Pointer to a specific location in the code.

    Note:
        This `class` acts as a "perfect proxy" for end users
        by utilising [`wrapt`](https://github.com/GrahamDumpleton/wrapt)
        (which means wrapped `value` should be usable just like
        the original one).

    Warning:
        Use `Value.from_python`, `Value.from_toml` when returning
        values from rules based on `loader.Python` and `loader.TOML`
        respectively.

    Attributes:
        value:
            Value to check against the rules.
        start_line:
            Line number (represented as a `Pointer`).
        start_column:
            Column number (represented as a `Pointer`).
        end_line:
            End line number (represented as a `Pointer`).
        end_column:
            End column number (represented as a `Pointer`).

    """

    def __init__(  # noqa: PLR0913
        self,
        value: typing.Any = None,
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

    def __repr__(self) -> str:  # pyright: ignore [reportImplicitOverride]
        """Unique representation of the value.

        Returns:
            Fully described Value including its code location.

        """
        return (
            f"Value(value={self.__wrapped__!s}, comment={self._self_comment}, "
            f"start_line={self._self_start_line}, start_column={self._self_start_column}, "
            f"end_line={self._self_end_line}, end_column={self._self_end_column})"
        )

    @staticmethod
    def from_python(value: typing.Any, node: ast.AST) -> Value:
        """Create a `Value` from Python's `ast.AST` node.

        Returns:
            Given `python` node represented as `Value`.
        """
        return Value(
            value=value,
            start_line=_optional_get(node, "lineno"),
            start_column=_optional_get(node, "col_offset"),
            end_line=_optional_get(node, "end_lineno"),
            end_column=_optional_get(node, "end_col_offset"),
        )

    if available.TOML:

        @staticmethod
        def from_toml(item: typing.Any) -> Value:
            """Create a `Value` from `tomlkit` `Item`.

            Warning:
                Multiline `ignore`s or skips are not supported
                for `TOML`.

            Warning:
                `Value` will contain no line/column info
                (as it is unavailable in `tomlkit`), but
                propagates `comment` to other elements of the
                system which allows it to be used for line ignoring.

            Returns:
                Given `tomlkit` `Item` represented as `Value`.
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
        def _from_yaml(value: typing.Any, node: typing.Any) -> Value:
            """Create a Value from a modified ruamel.YAML node.

            Note:
                This method is used internally and __should not be
                used directly__ unlike their `toml` and `python`
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
