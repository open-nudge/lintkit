# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Check mixins used for creation of `lintkit.rule` rules."""

from __future__ import annotations

import abc
import re
import typing

from collections.abc import Mapping

if typing.TYPE_CHECKING:
    from collections.abc import Hashable, Iterable

    from . import type_definitions

T = typing.TypeVar("T")


class Check(abc.ABC):
    """Base class for performing a `value` check."""

    @abc.abstractmethod
    def check(self, value: typing.Any) -> bool:
        """Perform the check on a certain `value`.

        Args:
            value:
                Value to check.

        Returns:
            `True` if rule is violated, `False` otherwise.
        """
        raise NotImplementedError


class Regex(Check, abc.ABC):
    """Check if the value matches a regex pattern."""

    @abc.abstractmethod
    def regex(self) -> str:
        """Return the regex pattern to match against.

        Returns:
            Regex pattern to match against.

        """
        raise NotImplementedError

    def regex_flags(self) -> int:
        """Additional `flags` value to pass to `re.search`.

        Note:
            This method is optional and can be overridden to provide
            different `flags` value.

        Note:
            See
            [python documentation](https://docs.python.org/3/library/re.html#flags)
            for more information.

        Returns:
            No flag by default (`0` or `re.NOFLAG`, see
            [here](https://docs.python.org/3/library/re.html#re.NOFLAG)
            for more information).
        """
        return re.NOFLAG

    def check(self, value: str) -> bool:  # pyright: ignore[reportImplicitOverride]
        """Check if the node matches the regex pattern.

        Note:
            [`re.search`](https://docs.python.org/3/library/re.html#re.search)
            is used to perform the check.

        Args:
            value:
                Value to check.

        Returns:
            True if the `value` matches the regex pattern,
            False otherwise.

        """
        return (
            re.search(self.regex(), value, flags=self.regex_flags()) is not None
        )


class Contains(Check, abc.ABC):
    """Check if the value contains a subitems as specified by `keys`.

    This allows users to check if a value contains a specific subitem.

    Example implementation:

    ```python
    class ContainsAB(Contains):
        def keys(self):
            return ["a", "b"]
    ```

    Now every item supporting `__getitem__` and `__contains__` methods can be
    checked for containing `value["a"]["b"]`, for example:

        ```python
        contains = {"a": {"b": 1}}
        does_not_contain = {"a": {"c": 1}}

        assert ContainsAB().check(contains) is True
        assert ContainsAB().check(does_not_contain) is False
        ```

    """

    @abc.abstractmethod
    def keys(self) -> Iterable[Hashable]:
        """Return the keys to check for.

        For example, if the returned keys are `["a", "b", "c"]`, the check
        will be performed as follows:

        ```python
        value["a"]["b"]["c"]
        ```

        Returns:
            Keys to check for.

        """
        raise NotImplementedError

    def check(self, value: type_definitions.GetItem) -> bool:  # pyright: ignore[reportImplicitOverride]
        """Check if the node contains the word.

        Args:
            value:
                Value implementing `__getitem__` and `__contains__` methods,
                e.g. `dict`.

        Returns:
            bool:
                True if the value has `keys` in the order specified by the
                `keys` method, False otherwise.

        """
        current_value = value
        for key in self.keys():
            if (
                not isinstance(current_value, Mapping)
                or key not in current_value
            ):
                return False
            current_value = current_value[key]

        return True


# Change to protocol here
def invert(check: type[Check]) -> type[Check]:
    """Function inverting a given `Check` class.

    Example:
    ```python
    class ContainsAB(invert(Contains)):
        def keys(self):
            return ["a", "b"]
    ```

    This will create a check that verifies if the value does not
    contain the specified keys.

    """

    class InvertedCheck(check):
        """Inverted version of the given `Check` class."""

        def check(self, value: typing.Any) -> bool:  # pyright: ignore[reportImplicitOverride]
            """Reverse the check result of the original class.

            Args:
                value:
                    Value to check.
            """
            return not super().check(value)  # pyright: ignore[reportAbstractUsage]

    return InvertedCheck
