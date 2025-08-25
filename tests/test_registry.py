# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test the lintkit registry functionality."""

from __future__ import annotations

import lintkit


def test_inject() -> None:
    """Check injecting a rule into all rules works correctly."""
    dummy_value = 21

    lintkit.registry.inject("lintkit_testing_attribute", dummy_value)

    for rule in lintkit.registry.rules():
        # It should be available after `inject`,
        # static analyser cannot infer it though

        # Bandit false positive
        assert rule.lintkit_testing_attribute == dummy_value  # pyright: ignore[reportAttributeAccessIssue]  # nosemgrep: B101
