# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test the public command-line interface."""

from __future__ import annotations

import json
import pathlib
import re

import pytest

import lintkit


@pytest.mark.parametrize(
    ("arguments", "names", "expected"),
    (
        (
            ["rules", "--names", "TEST0", "TEST1"],
            None,
            (0, ("TEST0", "TEST1"), False),
        ),
        (
            ["examples", "--names", "TEST0", "TEST1"],
            None,
            (0, ("TEST0", "TEST1"), False),
        ),
        (["examples"], ("TEST0",), (0, ("TEST0",), False)),
        (
            ["examples", "--names", "TEST1"],
            ("TEST0",),
            (0, ("TEST1",), False),
        ),
        (["rules", "--names"], None, (0, (), False)),
        (["rules", "--names", "UNKNOWN"], None, (2, (), True)),
    ),
)
def test_commands(
    arguments: list[str],
    names: tuple[str, ...] | None,
    expected: tuple[int, tuple[str, ...], bool],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test selection, configured defaults, overrides, and invalid names.

    Args:
        arguments:
            CLI arguments to process.
        names:
            Configured default rule names, or all rules when `None`.
        expected:
            Normalized exit status, rendered rule names, and error marker.
        capsys:
            Pytest fixture used to capture CLI output.

    """
    with pytest.raises(SystemExit) as exception:
        lintkit.cli.main(
            version="0.0.1",
            files_default=(),
            names=names,
            args=arguments,
        )
    captured = capsys.readouterr()
    rendered_names = tuple(re.findall(r"(?m)^TEST\d+(?=:\s|\s)", captured.out))
    assert (
        int(exception.value.code or 0),
        rendered_names,
        "invalid choice" in captured.err,
    ) == expected


@pytest.mark.parametrize(
    ("content", "expected"),
    (
        ("value = 1\n", (0, ())),
        (
            "def test_run_example():\n    pass\n",
            (
                1,
                (("TEST0", "", "example.py", 1),),
            ),
        ),
    ),
)
def test_json_check(
    content: str,
    expected: tuple[int, tuple[tuple[str, str, str, int], ...]],
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test JSON results and their corresponding process status.

    Args:
        content:
            Content of the checked file.
        expected:
            Normalized exit status and JSON records.
        tmp_path:
            Temporary directory used to create the checked file.
        capsys:
            Pytest fixture used to capture CLI output.

    """
    file = tmp_path / "example.py"
    _ = file.write_text(content)
    with pytest.raises(SystemExit) as exception:
        lintkit.cli.main(
            version="0.0.1",
            files_default=(),
            args=[
                "check",
                str(file),
                "--output",
                "json",
                "--names",
                "TEST0",
            ],
        )
    records = json.loads(capsys.readouterr().out)
    normalized = tuple(
        (
            record["code"],
            record["message"],
            pathlib.Path(record["file"]).name,
            record["line"],
        )
        for record in records
    )
    assert (int(exception.value.code or 0), normalized) == expected
