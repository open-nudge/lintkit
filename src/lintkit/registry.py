# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Module containing registered rules and functions to update/discover them.

Warning:
    Provided functions are __read-only__, registry itself
    is managed automatically during `rule` creation.

"""

from __future__ import annotations

import re
import typing

from . import error, settings

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from .rule import Rule

_registry: dict[int, Rule] = {}


def codes() -> tuple[int, ...]:
    """Get all registered rule codes.

    Returns:
        A tuple of all registered rule codes.

    """
    return tuple(_registry.keys())


def rules() -> tuple[Rule, ...]:
    """Get all registered rules.

    Returns:
        A tuple of all registered rules.

    """
    return tuple(_registry.values())


def inject(attribute: str, value: typing.Any) -> None:
    """Inject an attribute into all rules.

    Tip:
        This is useful for injecting custom attributes into all rules,
        such as a custom configuration or a shared resource.

    Example:
    ```python
    import lintkit

    config = {"example": "value"}

    # Now all rules can access config and use it
    lintkit.registry.inject("config", config)
    ```

    Args:
        attribute:
            The name of the attribute to inject.
        value:
            The value to inject.

    """
    for rule in _registry.values():
        setattr(type(rule), attribute, value)


def query(
    include_codes: Iterable[int] | None = None,
    exclude_codes: Iterable[int] | None = None,
) -> Iterator[Rule]:
    """Query the registry for rules.

    Warning:
        `exclude` takes precedence over `include`

    Example:
    ```python
    import lintkit

    for rule in lintkit.registry.query(exclude_codes=[1, 2, 3]):
        print(rule.code, rule.description)
    ```

    Args:
        include_codes:
            The codes of the rules to include, if any.
        exclude_codes:
            The codes of the rules to exclude, if any.
            (takes precedence over `include_codes`).
        file_only:
            Whether to only return file-based rules.

    Returns:
        An iterator over the rules that match the query.

    """
    codes = _process(_registry.keys(), include_codes, exclude_codes)
    return (rule for code, rule in _registry.items() if code in codes)


# This function is used by `Rule` class to register itself
def _add(rule: type[Rule], code: int) -> None:  # pyright: ignore [reportUnusedFunction]
    """Add a rule to the registry.

    Note:
        This function is not intended to be used directly.
        `_rule.Rule` will call it once the class is defined
        and `code` is set there.

    Raises:
        lintkit.error.CodeNegativeError:
            If `code` is negative.
        lintkit.error.CodeExistsError:
            If a rule with the same `code` already exists.

    Args:
        rule:
            The rule to add.
        code:
            The code of the rule.

    """
    if code < 0:
        raise error.CodeNegativeError(code, rule)
    if code in _registry:
        raise error.CodeExistsError(code, rule, _registry[code])

    # Save state useful in `Rule` methods
    rule.code = code
    rule.ignore_line = re.compile(
        settings.ignore_line.format(
            name=settings._name(),  # noqa: SLF001
            code=code,
        ),
    )

    # Saving __instance__ of the rule, __not class__!
    _registry[code] = rule()


def _process(
    whole: Iterable[int],
    include: Iterable[int] | None,
    exclude: Iterable[int] | None,
) -> set[int]:
    """Process the query based on include and exclude iterables.

    Warning:
        `exclude` takes precedence over `include`

    Args:
        whole:
            The whole set of items to consider.
        include:
            The items to include, if any.
        exclude:
            The items to exclude, if any.

    Returns:
        The set of items that match the query.

    """
    return (set(whole) if include is None else set(include)).difference(
        set(exclude) if exclude else set()
    )
