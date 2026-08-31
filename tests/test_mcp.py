# SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Test the optional FastMCP integration."""

from __future__ import annotations

import typing

from unittest.mock import Mock

import fastmcp

from fastmcp.exceptions import ToolError

import pytest

import lintkit

if typing.TYPE_CHECKING:
    import pathlib


@pytest.fixture(scope="module")
def file_default(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path]:
    """Create one default check file shared by the MCP tool cases."""
    path = tmp_path_factory.mktemp("mcp") / "default.py"
    _ = path.write_text("def test_run_example():\n    pass\n")
    return (path,)


@pytest.fixture(scope="module")
def file_explicit(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Create one explicit check directory shared by the MCP tool cases."""
    directory = tmp_path_factory.mktemp("mcp-explicit")
    path = directory / "nested" / "explicit.py"
    path.parent.mkdir()
    _ = path.write_text("def miss_example():\n    pass\n")
    return directory


@pytest.mark.parametrize(
    (
        "tool_arguments",
        "enable",
        "disable",
        "files_default",
        "files_reader",
    ),
    (
        (
            [],
            None,
            None,
            lintkit.cli.files.default.Recursive(".py"),
            lintkit.cli.files.reader.Default(),
        ),
        (
            ["--enable", "check", "rules", "--disable", "rules"],
            ["check", "rules"],
            ["rules"],
            lintkit.cli.files.default.Default(),
            lintkit.cli.files.reader.Recursive(".py"),
        ),
    ),
)
@pytest.mark.parametrize(
    ("name_arguments", "name"),
    (([], "TEST"), (["--name", "Custom"], "Custom")),
)
@pytest.mark.parametrize(
    ("transport_arguments", "run_arguments"),
    (
        ([], {"transport": "stdio", "show_banner": False}),
        (
            [
                "--transport",
                "http",
                "--host",
                "127.0.0.1",
                "--port",
                "9000",
                "--path",
                "/lint",
                "--stateful",
                "--no-host-origin-protection",
                "--allowed-host",
                "one.example",
                "--allowed-origin",
                "https://one.example",
            ],
            {
                "transport": "http",
                "show_banner": False,
                "host": "127.0.0.1",
                "port": 9000,
                "path": "/lint",
                "stateless": False,
                "host_origin_protection": False,
                "allowed_hosts": ["one.example"],
                "allowed_origins": ["https://one.example"],
            },
        ),
    ),
)
def test_cli_dispatch(  # noqa: PLR0913, PLR0917
    tool_arguments: list[str],
    enable: list[str] | None,
    disable: list[str] | None,
    files_default: lintkit.cli.files.default.Base,
    files_reader: lintkit.cli.files.reader.Base,
    name_arguments: list[str],
    name: str,
    transport_arguments: list[str],
    run_arguments: dict[str, object],
    file_default: tuple[pathlib.Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test independent MCP CLI options compose into exact dispatch calls.

    Args:
        tool_arguments:
            Tool-selection CLI arguments.
        enable:
            Expected enabled tools.
        disable:
            Expected disabled tools.
        files_default:
            Default-file provider passed through the CLI.
        files_reader:
            File reader passed through the CLI.
        name_arguments:
            Server-name CLI arguments.
        name:
            Expected server name.
        transport_arguments:
            Transport CLI arguments.
        run_arguments:
            Expected server run arguments.
        file_default:
            Shared default file used by the recursive provider.
        monkeypatch:
            Pytest fixture used to replace server startup.
    """
    factory = Mock(wraps=lintkit.mcp.server)
    run = Mock()
    monkeypatch.setattr(lintkit.mcp, "server", factory)
    monkeypatch.setattr(fastmcp.FastMCP, "run", run)
    monkeypatch.chdir(file_default[0].parent)
    try:
        expected_default = tuple(files_default())
    except lintkit.error.FilesMissingError:
        expected_default = None
    lintkit.cli.main(
        version="0.0.1",
        files_default=files_default,
        files_reader=files_reader,
        args=["mcp", *tool_arguments, *name_arguments, *transport_arguments],
    )

    factory.assert_called_once_with(
        enable,
        disable,
        files_default=expected_default,
        files_reader=files_reader,
        name=name,
    )
    run.assert_called_once_with(**run_arguments)


@pytest.mark.parametrize(
    "option",
    (
        ["--host", "127.0.0.1"],
        ["--port", "9000"],
        ["--path", "/lint"],
        ["--stateful"],
        ["--host-origin-protection"],
        ["--no-host-origin-protection"],
        ["--allowed-host", "one.example"],
        ["--allowed-origin", "https://one.example"],
    ),
)
def test_stdio_rejects_http_options(
    option: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test every HTTP-only option under stdio.

    Args:
        option:
            One HTTP-only CLI option and any required value.
        capsys:
            Pytest fixture used to capture the parser error.
    """
    with pytest.raises(SystemExit) as exception:
        lintkit.cli.main(
            version="0.0.1",
            args=["mcp", *option],
        )
    assert (
        exception.value.code,
        "HTTP options require --transport http" in capsys.readouterr().err,
    ) == (2, True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool",
    ("check", "rules", "examples"),
)
@pytest.mark.parametrize(
    ("files_default", "files_reader", "expected"),
    (
        (
            lintkit.cli.files.default.Recursive(".py"),
            lintkit.cli.files.reader.Default(),
            "TEST0",
        ),
        (
            lintkit.cli.files.default.Default(),
            lintkit.cli.files.reader.Recursive(".py"),
            "TEST1",
        ),
    ),
)
async def test_tools(  # noqa: PLR0913, PLR0917
    tool: str,
    files_default: lintkit.cli.files.default.Base,
    files_reader: lintkit.cli.files.reader.Base,
    expected: str,
    file_default: tuple[pathlib.Path],
    file_explicit: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test each tool returns its relevant rule data.

    Args:
        tool:
            Registered tool to call.
        files_default:
            Default-file provider used by the server.
        files_reader:
            File reader used by the server.
        expected:
            Rule token expected in the returned data.
        file_default:
            Shared default file used by the recursive provider.
        file_explicit:
            Shared explicit directory used by the check tool.
        monkeypatch:
            Pytest fixture used to set the provider's working directory.
    """
    monkeypatch.chdir(file_default[0].parent)
    try:
        configured_default = tuple(files_default())
    except lintkit.error.FilesMissingError:
        configured_default = None
    arguments = (
        {"files": [str(file_explicit)]}
        if configured_default is None and tool == "check"
        else {}
    )
    async with fastmcp.Client(
        lintkit.mcp.server(
            files_default=configured_default,
            files_reader=files_reader,
        )
    ) as client:
        result = await client.call_tool(tool, arguments)

    assert expected in result.data


@pytest.mark.asyncio
async def test_check_required_files() -> None:
    """Test check requires files when the server has no file defaults."""
    async with fastmcp.Client(lintkit.mcp.server()) as client:
        with pytest.raises(ToolError, match="files"):
            _ = await client.call_tool("check", {})


def test_empty_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test server construction fails when project rules were not imported."""
    monkeypatch.setattr(lintkit.registry, "_registry", {})

    with pytest.raises(
        lintkit.error.RegistryEmptyError,
        match=r"Import project rules before lintkit\.mcp\.server\(\)\.",
    ):
        _ = lintkit.mcp.server()
