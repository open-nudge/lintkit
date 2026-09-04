# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test package configuration."""

from __future__ import annotations

import typing

import pytest

import lintkit

if typing.TYPE_CHECKING:
    import pathlib


@pytest.fixture
def config_path(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a dedicated configuration file.

    Args:
        tmp_path:
            Temporary directory containing the configuration file.

    Returns:
        Path to the created configuration file.

    """
    path = tmp_path / ".linter.toml"
    _ = path.write_text(
        """shared = "root"
include_codes = [0, 1]
[TEST0]
value = "zero"
[TEST1]
value = "one"
""",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(("code", "value"), ((0, "zero"), (1, "one")))
def test_config(
    code: int,
    value: str,
    config_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test shared and per-rule configuration.

    Args:
        code:
            Code of the configured rule.
        value:
            Expected rule-specific value.
        config_path:
            Path to the dedicated configuration file.
        monkeypatch:
            Fixture used to start configuration lookup in that directory.

    """
    monkeypatch.chdir(config_path.parent)
    rule = next(lintkit.registry.query(include_codes=(code,)))

    assert (
        lintkit.config(),
        rule.config("value"),
        rule.config("missing"),
        rule.config("missing", "fallback"),
    ) == (
        {
            "shared": "root",
            "include_codes": [0, 1],
            "TEST0": {"value": "zero"},
            "TEST1": {"value": "one"},
        },
        value,
        None,
        "fallback",
    )
