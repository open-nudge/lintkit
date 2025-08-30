# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test `lintkit.error` functionality.

Each test simulates a specific error condition.

Warning:
    Comments in this file __are used during tests__
    (e.g. `noqa`). Make sure to not remove them
    if you are uncertain what they do.

"""

from __future__ import annotations

import typing

import pytest

import lintkit

if typing.TYPE_CHECKING:
    from collections.abc import Iterable


def test_name_missing(request: pytest.FixtureRequest) -> None:
    """Ensure an error occurs when `lintkit.settings.name` is not set.

    Args:
        request: Fixture request to get the path of the test file.
    """
    name = lintkit.settings.name
    lintkit.settings.name = None
    with pytest.raises(lintkit.error.NameMissingError):
        _ = lintkit.run([request.path])
    lintkit.settings.name = name


def test_incorrect_inheritance() -> None:
    """Verify error raised on negative rule code."""
    with pytest.raises(lintkit.error.NotSubclassError):

        class A(lintkit.rule.Node, code=0):  # pyright: ignore[reportImplicitAbstractClass, reportUnusedClass]
            """Dummy rule with invalid code type."""


def test_code_negative() -> None:
    """Verify error raised on negative rule code."""
    with pytest.raises(lintkit.error.CodeNegativeError):

        class A(lintkit.rule.Node, lintkit.loader.Loader, code=-1):  # pyright: ignore[reportImplicitAbstractClass, reportUnusedClass]
            """Dummy rule with invalid code type."""


def test_code_exists() -> None:
    """Verify error raised on rule code duplication."""
    with pytest.raises(lintkit.error.CodeExistsError):

        class A(lintkit.rule.Node, lintkit.loader.Loader, code=0):  # pyright: ignore[reportImplicitAbstractClass, reportUnusedClass]
            """Dummy rule with invalid code type."""


def test_code_missing() -> None:
    """Verify error raised if rule code not defined."""
    with pytest.raises(lintkit.error.CodeMissingError):  # noqa: PT012

        class B(lintkit.check.Contains, lintkit.loader.File, lintkit.rule.Node):
            """Dummy rule with invalid no code."""

            def keys(  # pragma: no cover # pyright: ignore[reportImplicitOverride]
                self,
            ) -> Iterable[str]:
                """Return dummy keys."""
                return ["a", "b", "c"]

            def values(  # pragma: no cover # pyright: ignore[reportImplicitOverride]
                self,
            ) -> Iterable[lintkit.Value[None]]:
                """Yield dummy values."""
                yield lintkit.Value()

            def message(  # pragma: no cover # pyright: ignore[reportImplicitOverride, reportIncompatibleMethodOverride]
                self, _: lintkit.Value[None]
            ) -> str:
                """Return dummy message."""
                return ""

        # Error is raised when the rule is instantiated
        # e.g. during `lintkit.run()`
        _ = B()


# noqa-start: TEST1
def test_wrong_ignore_range(request: pytest.FixtureRequest) -> None:
    """Verify error raised noqa-start has no noqa ending string.

    Args:
        request: Fixture request to get the path of the test file.

    """
    with pytest.raises(lintkit.error.IgnoreRangeError):
        _ = lintkit.run([request.path])
