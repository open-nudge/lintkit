# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""CLI subcommands."""

from __future__ import annotations

import pathlib
import typing

from .. import _run, error, registry, settings

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def check(
    files: Iterable[str | pathlib.Path],
    names: Iterable[str] | None = None,
    end_mode: typing.Literal["first", "all"] = "all",
) -> bool:
    """Check files with rules selected by full names.

    Args:
        files:
            Files to check.
        names:
            Full, case-sensitive rule names to check. `None` checks all rules.
        end_mode:
            Whether to stop after the first failure or run all rules.

    Returns:
        Whether any selected rule failed.

    """
    include_codes = None if names is None else _codes(names)
    # To satisfy the linter as it's not smart enough to infer it
    return (
        _run.run(
            (pathlib.Path(file).resolve() for file in files),
            include_codes,
            None,
            end_mode,
            output=False,
        )
        is True
    )


def rules(names: Iterable[str] | None = None) -> str:
    """Render selected registered rules.

    Args:
        names:
            Full, case-sensitive rule names to render. `None` renders all
            rules in registry order.

    Returns:
        Rendered rules table.

    """
    registered = {rule.code: rule for rule in registry.rules()}
    selected = registry.codes() if names is None else _codes(names)
    header = ("Name", "Description")
    rows: list[tuple[str, str]] = [header]
    rows.extend(
        (f"{settings._name()}{code}", registered[code].description())  # noqa: SLF001
        for code in selected
    )

    maximum_widths = tuple(
        max(len(str(row[i])) for row in rows) for i in range(len(header))
    )

    rendered = [
        " | ".join(
            column.ljust(maximum_widths[index])
            for index, column in enumerate(header)
        )
    ]
    rendered.append("-+-".join("-" * width for width in maximum_widths))
    rendered.extend(
        " | ".join(
            column.ljust(maximum_widths[index])
            for index, column in enumerate(row)
        )
        for row in rows[1:]
    )
    return "\n".join(rendered)


def examples(names: Iterable[str] | None = None) -> str:
    """Display usage examples for selected rules.

    Args:
        names:
            Full, case-sensitive rule names to display. `None` selects
            registry order.

    Returns:
        Rendered examples in selection order.

    """
    name = settings._name()  # noqa: SLF001
    rules = {rule.code: rule for rule in registry.rules()}
    selected_codes = registry.codes() if names is None else _codes(names)
    selected = (rules[code] for code in selected_codes)
    groups: list[str] = []
    for rule in selected:
        rule_examples = rule.examples()
        if rule_examples:
            groups.append(
                f"{name}{rule.code}:\n\n" + "\n\n".join(rule_examples)
            )

    return "\n\n".join(groups)


def _codes(names: Iterable[str]) -> Iterator[int]:
    """Convert full rule names to integer codes.

    Args:
        names:
            Full, case-sensitive rule names.

    Raises:
        lintkit.error.RuleNameError:
            If a name is not registered.

    Yields:
        Codes in caller order.

    """
    prefix = settings._name()  # noqa: SLF001
    registered = {f"{prefix}{code}": code for code in registry.codes()}
    for name in names:
        if name not in registered:  # pragma: no cover
            raise error.RuleNameError(name)
        yield registered[name]
