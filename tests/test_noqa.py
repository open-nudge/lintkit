# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
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

import re

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


@pytest.mark.parametrize(
    ("pattern", "ignore"),
    (
        (lintkit.settings.ignore_line, "# noqa: RULE4"),
        (lintkit.settings.ignore_file, "# noqa-file: RULE4"),
        (lintkit.settings.ignore_span_start, "# noqa-start: RULE4"),
        (lintkit.settings.ignore_span_end, "# noqa-end: RULE4"),
    ),
)
def test_numeric_boundary(pattern: str, ignore: str) -> None:
    """Ensure ignore patterns distinguish numeric rule suffixes.

    Args:
        pattern:
            Public ignore pattern to test.
        ignore:
            Exact ignore text for rule 4.

    """
    regex = pattern.format(name="RULE", code=4)

    assert re.search(regex, ignore) is not None
    assert re.search(regex, f"{ignore}3") is None


@pytest.mark.parametrize(
    ("ignore_noqa", "expected_count"),
    ((False, 0), (True, 3)),
)
def test_noqa(
    request: pytest.FixtureRequest,
    ignore_noqa: bool,  # noqa: FBT001
    expected_count: int,
) -> None:
    """Run registered rules on this file.

    Matching `noqa` comments suppress `TestNoqa` matches by default.

    Args:
        request:
            Request fixture to access the test context.
        ignore_noqa:
            Whether to bypass `noqa` suppression.
        expected_count:
            Expected number of failed rules.

    """
    count = 0
    for fail, rule in lintkit.run(  # pyright: ignore[reportGeneralTypeIssues]
        [request.path], output=True, ignore_noqa=ignore_noqa
    ):
        if fail:
            assert rule.code == 1
            count += 1
    assert count == expected_count
