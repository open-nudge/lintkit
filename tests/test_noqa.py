# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test `noqa`/`ignore` strings functionality.

Note:
    Each `function` is named `miss*` as this is the regex
    defined in `conftest` which __should match__
    `TestNoqa` rule in `conftest.py` IF there was no
    `noqa` strings.

Warning:
    Please note there should be __no matches__ in
    this module due to provided `noqa`/`ignore` strings.

"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import pytest

import lintkit


# Note: noqa has to be enabled for ruff via lint.external
# Same line noqa
def miss1() -> None:  # noqa: TEST1
    """Dummy function."""


# Multiline noqa
# noqa-start: TEST0, TEST1, TEST2
def miss2() -> None:
    """Dummy function."""


def miss3() -> None:
    """Dummy function."""


# noqa-end: TEST2, TEST1, TEST0


def test_noqa(
    request: pytest.FixtureRequest,
) -> None:
    """Run registered rules on this file.

    No `error` should be raised by the rules, as
    the `noqa` strings overwrite all of the `TestNoqa` rule
    matches.

    Args:
        request:
            Request fixture to access the test context.

    """
    for fail, _ in lintkit.run([request.path], output=True):  # pyright: ignore[reportGeneralTypeIssues]
        # Bandit false positive
        assert not fail  # nosemgrep: B101
