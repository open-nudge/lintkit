# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for lintkit.run function."""

from __future__ import annotations

import typing

import pytest

import lintkit


@pytest.mark.parametrize("include_codes", ((1, 2, 3), None))
@pytest.mark.parametrize(
    "exclude_codes", (lintkit.registry.codes(), (2, 3), None)
)
def test_run_codes(
    include_codes: tuple[int, ...] | None,
    exclude_codes: tuple[int, ...] | None,
    request: pytest.FixtureRequest,
) -> None:
    """Test that run function respects include and exclude codes.

    Note:
        `exclude_codes` takes precedence over `include_codes`.

    Args:
        include_codes:
            Rule codes to include in the run.
        exclude_codes:
            Rule codes to exclude from the run.
        request:
            Pytest fixture request object
            (used to get the path to the test file).

    """
    for fail, rule in lintkit.run(  # pyright: ignore[reportGeneralTypeIssues]
        [request.path],
        include_codes=include_codes,
        exclude_codes=exclude_codes,
        output=True,
    ):
        if fail:
            assert rule.code == 0


@pytest.mark.parametrize("output", ("rich", "stdout", None))
def test_run_output_smoke(
    output: str | None,
    request: pytest.FixtureRequest,
) -> None:
    """Smoke test `output` change in `lintkit.run`.

    Args:
        output:
            Output `function` to use in the run.
            If `None`, the default output will be used.
        request:
            Pytest fixture request object
            (used to get the path to the test file).

    """
    lintkit.settings.output = (
        getattr(lintkit.output, output) if output is not None else None
    )

    _ = lintkit.run([request.path])


@pytest.mark.parametrize("end_mode", ("first", "all"))
def test_run_mode(
    end_mode: typing.Literal["first", "all"],
    request: pytest.FixtureRequest,
) -> None:
    """Test that run function respects end mode.

    Args:
        end_mode:
            End mode to use in the run.
            Can be either "first" (stop at first error)
            or "all" (output every error).
        request:
            Pytest fixture request object
            (used to get the path to the test file).

    """
    fails_counter = 0
    for fail, rule in lintkit.run(  # pyright: ignore[reportGeneralTypeIssues]
        [request.path, "README.md"],
        end_mode=end_mode,
        output=True,
    ):
        if fail and rule.code == 0:
            fails_counter += 1

    if end_mode == "first":
        # By definition only single fail should be returned
        assert fails_counter == 1
    else:
        # All fails should be returned (as many as files)
        # See test_not_node.py for details
        assert fails_counter == 3  # noqa: PLR2004
