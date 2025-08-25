# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Check `mixins` used for creation of `lintkit.rule` rules.

Info:
    This module is one of the three core modules used to define
    rules (this one __might be skipped__ though, as long as your
    [`lintkit.rule.Rule`][] implements `check` method).

Tip:
    Check out [Advanced tutorial](/lintkit/tutorials/advanced)
    for a usage example of [`lintkit.check`][] module.

"""

from __future__ import annotations

import abc
import re
import typing

from collections.abc import Mapping

if typing.TYPE_CHECKING:
    from collections.abc import Hashable, Iterable

    from . import type_definitions
    from ._value import Value

T = typing.TypeVar("T")


class Check(abc.ABC):
    """Base class (interface) for performing checks against `value`.

    Tip:
        This is an interface obtaining [`lintkit.Value`][]
        and returning `True` if the rule was broken.

    """

    @abc.abstractmethod
    def check(self, value: Value[typing.Any]) -> bool:
        """Perform the check on a certain `value`.

        Tip:
            Check out any tutorial
            (e.g. [Basic tutorial](/lintkit/tutorials/basic))
            for a usage example.

        Args:
            value:
                Value to check.

        Returns:
            `True` if rule is violated, `False` otherwise.
        """
        raise NotImplementedError


class Regex(Check, abc.ABC):
    """Check if the value matches a regex pattern.

    Note:
        This `class` uses Python's
        [`re.search`](https://docs.python.org/3/library/re.html#re.search)
        internally.

    Example:
        ```python
        class MyRegex(lintkit.check.Regex):
            def regex(self) -> str:
                return ".*"


        # Every string will match
        MyRegex().check("tout sera inclus")
        ```

    Tip:
        Check out [Advanced tutorial](/lintkit/tutorials/advanced)
        for another usage example of [`lintkit.check.Regex`][] class.

    """

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

        Info:
            See
            [`re` flags](https://docs.python.org/3/library/re.html#flags)
            for more information.

        Returns:
            Flag to apply for `re.search`; `0` by default, see `re.NOFLAG`
                [here](https://docs.python.org/3/library/re.html#re.NOFLAG)
                for more information.
        """
        return re.NOFLAG

    def check(self, value: Value[str | None]) -> bool:  # pyright: ignore[reportImplicitOverride]
        """Check if the node matches the regex pattern.

        Success:
            This method is already implemented for you and ready to use.

        Note:
            [`re.search`](https://docs.python.org/3/library/re.html#re.search)
            is used to perform the check, its result is checked against `None`.

        Args:
            value:
                Value to check.

        Returns:
            `True` if the `value` matches the regex pattern,
            `False` otherwise.

        """
        # Have to unpack `Value` due to re.compile checks allowing only str
        return (
            value.__wrapped__ is None
            or re.search(
                self.regex(),
                value.__wrapped__,  # pyright: ignore[reportUnknownArgumentType]
                flags=self.regex_flags(),
            )
            is not None
        )


class Contains(Check, abc.ABC):
    """Check if the value contains a subitems as specified by `keys`.

    This allows users to check if a value contains a specific subitem.

    Example:
        ```python
        class ContainsAB(Contains):
            def keys(self):
                return ["a", "b"]
        ```

    Now every item supporting `__getitem__` and `__contains__` methods can be
    checked for containing `value["a"]["b"]`, for example:

    Example:
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

    def check(  # pyright: ignore[reportImplicitOverride]
        self,
        value: Value[type_definitions.GetItem | None],
    ) -> bool:
        """Check if the `value` contains `keys`.

        Success:
            This method is already implemented for you and ready to use.

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
