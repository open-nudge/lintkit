# SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Private FastMCP tool and server construction."""

from __future__ import annotations

import types
import typing

import fastmcp

from .. import cli as command
from .. import error, registry, settings
from ..cli.files import reader
from . import _check

if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def server(
    enable: Iterable[str] | None = None,
    disable: Iterable[str] | None = None,
    *,
    files_default: Iterable[str | Path] | None = None,
    files_reader: reader.Base | None = None,
    **mcp_kwargs: typing.Any,
) -> typing.Any:
    """Create and configure one FastMCP server.

    Args:
        enable:
            Tool names to expose as an allowlist.
        disable:
            Tool names to hide after applying the allowlist.
        files_default:
            Paths used when an MCP `check` call omits `files`. `None` keeps
            `files` required. Defaults are captured during construction.
        files_reader:
            Reader applied to explicit paths and captured defaults. `None`
            preserves the selected paths unchanged.
        **mcp_kwargs:
            FastMCP constructor keyword arguments. Caller values override
            lintkit defaults.

    Returns:
        A new configured FastMCP server.

    Raises:
        lintkit.error.RegistryEmptyError:
            If project rules were not imported before server construction.

    """
    name = settings._name()  # noqa: SLF001
    rule_names = tuple(f"{name}{code}" for code in registry.codes())
    if not rule_names:
        raise error.RegistryEmptyError
    if files_reader is None:  # pragma: no branch
        files_reader = reader.Default()
    mcp_kwargs.setdefault("name", name)
    instance = fastmcp.FastMCP(**mcp_kwargs)
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    tools = (
        (
            _check.check(files_default, files_reader),
            "check",
            "Validate files against linting rules.",
        ),
        (_rules, "rules", "List rules with their descriptions."),
        (_examples, "examples", "List examples related to the rules."),
    )
    for function, tool_name, description in tools:
        _ = instance.tool(
            _typed(function, rule_names),
            name=tool_name,
            description=description,
            tags={"lintkit", name, tool_name},
            annotations=annotations,
            run_in_thread=False,
        )
    if enable is not None:
        _ = instance.enable(names=set(enable), components={"tool"}, only=True)
    if disable is not None:
        _ = instance.disable(names=set(disable), components={"tool"})
    return instance


def _typed(
    function: typing.Callable[..., str], names: tuple[str, ...]
) -> typing.Callable[..., str]:
    """Clone a wrapper with a closed rule-name annotation.

    Args:
        function:
            Plain tool wrapper to clone.
        names:
            Registered full rule names captured for this server.

    Returns:
        A fresh function with a runtime `Literal` for `names`.

    """
    cloned = types.FunctionType(
        function.__code__,
        function.__globals__,
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )
    cloned.__kwdefaults__ = function.__kwdefaults__
    cloned.__doc__ = function.__doc__
    cloned.__annotations__ = typing.get_type_hints(function)
    literal = typing.Literal.__getitem__(names)  # pyright: ignore[reportAttributeAccessIssue]
    cloned.__annotations__["names"] = list[literal] | None
    return cloned


def _rules(names: list[str] | None = None) -> str:
    """Return the rendered rules table.

    Args:
        names:
            Full, case-sensitive rule names to list. `None` lists all rules.

    Returns:
        Rendered rules table.

    """
    return command.rules(names)


def _examples(names: list[str] | None = None) -> str:
    """Return rendered rule examples.

    Args:
        names:
            Full, case-sensitive rule names to display. `None` uses registry
            order.

    Returns:
        Rendered examples.

    """
    return command.examples(names)
