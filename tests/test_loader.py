# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test non-Python loaders of `lintkit`."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import pytest

import lintkit


def test_config(request: pytest.FixtureRequest) -> None:
    """Run all registered rules on a folder with config files.

    `data` folder contains an example `.json`, `.yaml`, and `.toml` files.

    Args:
        request: Fixture request to get the path of the test file.

    """
    for fail, rule in lintkit.run(  # pyright: ignore[reportGeneralTypeIssues]
        *list((request.path.parent / "data").glob("*")),
        output=True,
    ):
        # Config rules have codes in the range 201-299
        # No other rule should match for these config files.
        # see conftest.py for details.
        if fail:
            # Bandit false positive
            assert 200 < rule.code < 300  # noqa: PLR2004  # nosemgrep: B101


def test_file_loader(request: pytest.FixtureRequest) -> None:
    """Run all registered rules on a file loader.

    The only matching rule should be `FileNameCheck` with code `301` which
    verifies the file name should not be `test_loader.py`.

    Args:
        request: Fixture request to get the path of the test file.

    """
    for fail, rule in lintkit.run(request.path, output=True, end_mode="first"):  # pyright: ignore[reportGeneralTypeIssues]
        # File name only rules have codes in the range 301-399
        # see conftest.py for details.
        if fail:
            # Bandit false positive
            assert 300 < rule.code < 400  # noqa: PLR2004  # nosemgrep: B101
