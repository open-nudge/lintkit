<!--
SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

# Model Context Protocol (MCP) server

Install the optional `mcp` dependency:

```sh
> pip install "lintkit[mcp]"
```

Your lintkit-based linter will now get the `mcp` command.
Start the server with the default `stdio` transport (you can change it
using flags):

```sh
> lintkit mcp
```

## Tools

The server exposes the same commands as `lintkit.cli.main` does
(`check`, `rules`, `examples`) as tools with the following
properties:

- omit `names` to select all rules (default)
- each tool has one `names` selector
- values must be exact, case-sensitive full names,
    such as `MYLINTER10`; names are not uppercased and the choices
    are properly typed as `typing.Literal`. These identifiers use
    `lintkit.settings.name.rule` for typing
- `check` accepts explicit `files`; under `lintkit mcp`, omitting them uses the
    defaults configured by the linter's `lintkit.cli.main` call
    (we advise to use a recursive one)

You can `--enable` and/or `--disable` (takes precedence) tools
(by default all tools are enabled):

```sh
> lintkit mcp --enable check rules --disable rules
```

## Server CLI options

Start a stateless HTTP server with explicit network and origin controls:

```sh
> lintkit mcp --transport http --host 127.0.0.1 --port 8000 --path /mcp \
  --host-origin-protection --allowed-host localhost \
  --allowed-origin https://example.com
```

Repeat `--allowed-host` and `--allowed-origin` to add values. Use
`--no-host-origin-protection` to disable protection explicitly. HTTP remains
stateless unless you add the legacy (since 2026-07-06 specification)
`--stateful` option.

Use `--name` to replace the default server name, which is
`lintkit.settings.name.tool` by default (different from the randomly generated
default of `fastmcp`).

```sh
> lintkit mcp --name "Project linter"
```

## Server settings

Import your project rules before you create the server.
Server construction raises
[`lintkit.error.RegistryEmptyError`][] when there are no rules found.

```python
from fastmcp import FastMCP

import lintkit

# Note rules import before server!
import my_linter.rules  # noqa: F401

my_linter_server = lintkit.mcp.server()

parent = FastMCP("My project")
parent.mount(my_linter_server, namespace="lint")
```

- the parent server exposes the tools as `lint_<TOOL>` (e.g. `lint_check`).
- each call to [`lintkit.mcp.server`][] creates an independent server

A directly constructed server requires `files` in every `check` call
(error is raised when these are not provided).

To make that input optional, provide defaults when constructing it:

```python
my_linter_server = lintkit.mcp.server(
    # If no files provided go over $CWD/src and $CWD/tests
    files_default=("src", "tests"),
    # Read all Python files
    files_reader=lintkit.cli.files.reader.Recursive(".py"),
)
```

> **NOTE:**
> The configured reader processes both the defaults and explicit MCP paths, so
> clients have their directories and Python files checked.

You can explicitly provide
`instructions` and pass other `fastmcp` constructor arguments
directly:

```python
custom_server = lintkit.mcp.server(
    name="Project linter",
    instructions="Check project files with the registered project rules.",
    strict_input_validation=True,
)
```

Finally you can run or mount the returned instance:

```python
# Run directly (blocking)
custom_server.run()

# Or mount in a parent server
parent = FastMCP("My project")
parent.mount(custom_server, namespace="lint")
```
