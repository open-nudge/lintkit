# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test unchecked `lintkit.check` functionality."""

from __future__ import annotations

import lintkit


class Contains(lintkit.check.Contains):
    """Example `Contains` check."""

    def keys(self) -> tuple[str, ...]:  # pyright: ignore[reportImplicitOverride]
        """Dummy keys which are not present in `lintkit.Value`."""
        return ("this", "bla")


class NotContains(lintkit.check.invert(Contains)):  # pyright: ignore[reportImplicitAbstractClass]
    """Inverted `Contains` check."""


def test_invert() -> None:
    """Test that `invert` works as expected."""
    obj = NotContains()  # pyright: ignore[reportAbstractUsage]
    # this: 1 does not contain "this": "bla", hence should return True
    # Bandit false positive
    assert obj.check(lintkit.Value({"this": 1}))  # nosemgrep: B101
