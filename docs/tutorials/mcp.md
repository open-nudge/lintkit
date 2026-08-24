<!--
SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

# Serve a linter with MCP

Install the optional MCP dependency in your linter dependencies:

```console
pip install "lintkit[mcp]"
```

Your lintkit-based CLI gets the `mcp` subcommand only when FastMCP is
installed. Start the server with the default standard input and output
transport:

```console
lintkit mcp
```

The server exposes the `check`, `rules`, and `examples` tools with the following
properties:

- each tool has one `names` selector
- omit `names` to select all registered rules
- `check` accepts explicit `files`; under `lintkit mcp`, omitting them uses the
  defaults configured by the linter's `lintkit.cli.main` call.

Values must be exact, case-sensitive full names,
such as `MYLINTER10`; names are not converted to uppercase.

Use `--enable` as an allowlist or `--disable` as a tool blocklist
(by default all tools are enabled):

```console
lintkit mcp --enable check rules --disable rules
```

The example exposes only `check` because disabling a tool has final
precedence.

Start a stateless HTTP server with explicit network and origin controls:

```console
lintkit mcp --transport http --host 127.0.0.1 --port 8000 --path /mcp \
  --host-origin-protection --allowed-host localhost \
  --allowed-origin https://example.com
```

Repeat `--allowed-host` and `--allowed-origin` to add values. Use
`--no-host-origin-protection` to disable protection explicitly. HTTP remains
stateless unless you add the legacy `--stateful` option. These HTTP options
are rejected with the default `stdio` transport.

Use `--name` to replace the default server name, which is the linter name:

```console
lintkit mcp --name "Project linter"
```

## Build or mount the server

Import your project rules before you create the server. Rule classes register
themselves during import. Server construction raises
[`lintkit.error.RegistryEmptyError`][] when no rules are registered.

```python
from fastmcp import FastMCP

import lintkit
import my_linter.rules  # noqa: F401

my_linter_server = lintkit.mcp.server()

parent = FastMCP("My project")
parent.mount(my_linter_server, namespace="lint")
```

The parent server exposes the tools as `lint_check`, `lint_rules`, and
`lint_examples`. Each call to [`lintkit.mcp.server`][] creates an independent
server, so visibility settings do not leak between parent applications.
Each server also captures the registered full names in its three tool schemas.
Rules imported later appear only in a new server.

A directly constructed server requires `files` in every `check` call. To make
that input optional, provide defaults when constructing it:

```python
my_linter_server = lintkit.mcp.server(
    files_default=("src", "tests"),
)
```

When a client omits `files`, `check` uses this captured snapshot. An explicitly
provided list takes precedence, including an empty list. One-shot iterables,
such as `Path.rglob()`, are materialized once and can be reused across calls.

The factory uses the linter name by default. You can explicitly provide
`instructions` and pass other supported FastMCP constructor arguments
directly:

```python
custom_server = lintkit.mcp.server(
    name="Project linter",
    instructions="Check project files with the registered project rules.",
    strict_input_validation=True,
)
```

Call `run` or mount the returned FastMCP instance yourself when you need
deployment settings that the lintkit CLI does not expose.
