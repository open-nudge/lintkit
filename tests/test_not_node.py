# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test `File` and `All` rules in `lintkit`."""

from __future__ import annotations

import collections
import typing

import pytest

import lintkit

_dict_failing_rule_2_and_3 = {"this": {"test": 1}}


@pytest.mark.parametrize("end_mode", ("first", "all"))
def test_not_node(
    end_mode: typing.Literal["first", "all"],
    request: pytest.FixtureRequest,
) -> None:
    """Run `File` and `All` rules on a file with a dictionary.

    Note:
        This test is currently hardcoded with three files.
        In case of `All` rule it should fail once per all files,
        in case of `File` rule should fail for each file.

    Args:
        end_mode:
            Mode of the `lintkit.run` function, either `first` or `all`.
            If `first`, only the first match of each rule is returned.
            If `all`, all matches are returned.
        request:
            Request fixture to access the test context.

    """
    n_files = 3

    _dict_failing_rule_2_and_3 = {
        "this": {"test": 1},
    }

    fails = collections.defaultdict(int)

    for fail, rule in lintkit.run(  # pyright: ignore[reportGeneralTypeIssues]
        [request.path] * n_files, output=True, end_mode=end_mode
    ):
        if fail:
            fails[rule.code] += 1

    if end_mode == "first":
        # Single fail of `File rule
        assert fails[101] == 1
        # No fails of `All` rule as it does not finish
        assert fails[102] == 0
    else:
        # As many `File` fails as files
        assert fails[101] == n_files
        # One `All` fail as it is able to finish through all files
        assert fails[102] == 1
