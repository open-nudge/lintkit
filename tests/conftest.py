# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

# pyright: reportImplicitOverride=false, reportIncompatibleMethodOverride=false

"""Define lintkit rules for testing purposes."""

from __future__ import annotations

import abc
import ast
import typing

import lintkit

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

lintkit.settings.name = "TEST"

REGEXES = [
    "test_run.*",
    "miss.*",
]

# Base rules


class Message:
    """Dummy message class for rules.

    Outputted messages are not used by the test suite
    and it is provided for compatibility reasons only.

    """

    def message(self, _: lintkit.Value | None = None) -> str:
        """Return an empty message.

        Args:
            _: Value to process (not used in this case).

        Returns:
            An empty string as the message.

        """
        return ""


class Regex(Message, lintkit.check.Regex):
    """Basic `check` with different regexes.

    Separation of this `check` allows us to define rules
    easier and follow DRY principles.

    """

    def regex(self) -> str:
        """Return regex based on the rule's `code`.

        Returns:
            Regex string corresponding to the rule's `code`.

        """
        # code will be defined when the rule itself is defined
        return REGEXES[self.code]  # pyright: ignore[reportAttributeAccessIssue]


class Python(lintkit.loader.Python, abc.ABC):
    """Loader of `Python` code.

    It is used as the currently most complex loader.
    """

    @abc.abstractmethod
    def klass(self) -> type[ast.AST]:
        """`ast` class in which we are interested in this rule.

        Returns:
            Specific type of the `ast.AST` subclass we are interested in.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def process_node(self, node: ast.AST) -> str:
        """Stringify node of interest.

        Might be `node.name` or other stringified attribute.

        Args:
            node:
                Node to process.

        Returns:
            `string` representation of the node.
        """
        raise NotImplementedError

    def values(self) -> Iterable[lintkit.Value]:
        """Yield `Value` representations of a given `node`.

        Yields:
            `Value` representation of node(s).

        """
        nodes = self.getitem("nodes_map")[self.klass()]
        for node in nodes:
            yield lintkit.Value.from_python(self.process_node(node), node)


# Node rules


class TestNode(Regex, Python, lintkit.rule.Node):
    """Basic rule ran on each `Node`.

    - Takes all Python `function`s
    - Returns their names
    - If they match `Regex` yield `error`

    """

    def klass(self) -> type[ast.AST]:
        """`class` of interest for this rule.

        Returns:
            `ast.FunctionDef` class.
        """
        return ast.FunctionDef

    def process_node(self, node: ast.AST) -> lintkit.Value:
        """Process `node` and return its name.

        Args:
            node:
                Node to process.

        Returns:
            Name of the node (`function` specifically).

        """
        # Technically not all nodes have name, BUT
        # all nodes used in the tests currently do.
        # WARNING: might be error-prone, possibly specify exact type
        return node.name  # pyright: ignore[reportAttributeAccessIssue]


class TestRun(TestNode, code=0):
    """Rule to test basic `run`."""


class TestNoqa(TestNode, code=1):
    """Rule to test `noqa` strings (should be largely ignored)."""


# Not Node rules


class Contains(lintkit.check.Contains):
    """Check if a given `Value` contains these keys."""

    def keys(self) -> tuple[str, ...]:
        """Keys to check for the `Value`.

        Returns:
            Tuple of keys to check in the `Value`.

        """
        return ("this", "test")


class TestNotNode(Message, Python, Contains):
    """Rule to test `rule.File` and `rule.All` functionalities."""

    def klass(self) -> type[ast.AST]:
        """`class` of interest for this rule.

        Returns:
            `ast.Dict` class.
        """
        return ast.Dict

    def process_node(self, node: ast.Dict) -> dict[str, dict[str, int]]:
        """Mocked `process_node` method.

        Targeting `ast.Dict` nodes named `this`,
        otherwise returns empty dictionary.

        Args:
            node: Node to process.

        """
        # Additional checks should be here, but for this test cases
        # based on /data folder the line below will __always__ have values
        # as long as the /data does not change
        if node.keys[0].value == "this":  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            return {"this": {"test": 1}}
        return {}


class TestFile(TestNotNode, lintkit.rule.File, code=101):
    """Rule to test `rule.File` functionality."""


class TestAll(TestNotNode, lintkit.rule.All, code=102):
    """Rule to test `rule.All` functionality."""


# Non-python loaders


class ConfigBase(Message, Contains):
    """Base class for non-Python `configuration` loaders.

    It provides a common interface for loaders that do not
    use Python's `ast` module, such as JSON, TOML, and YAML.

    """


class JSON(ConfigBase, lintkit.loader.JSON, lintkit.rule.Node, code=201):
    """Rule to test JSON loader functionality."""

    def values(self) -> Iterable[lintkit.Value]:
        """Yield wrapped data from the loader.

        Yields:
            `Value` representation of the loaded JSON data.

        """
        # Check data/foo.toml, it should contain a nested structure
        yield lintkit.Value(self.getitem("data"))


class YAML(ConfigBase, lintkit.loader.YAML, lintkit.rule.Node, code=204):
    """Rule to test YAML loader functionality."""

    def values(self) -> Iterable[lintkit.Value]:
        """Yield the `data` from the loader.

        Warning:
            No need to wrap YAML data in `Value` as it is already
            wrapped internally.

        Yields:
            `Value` representation of the loaded YAML data.

        """
        yield self.getitem("data")


class TOML(ConfigBase, lintkit.loader.TOML, lintkit.rule.Node, code=202):
    """Rule to test TOML loader functionality."""

    def values(self) -> Iterable[lintkit.Value]:
        """Yield wrapped data via `from_toml` method.

        Yields:
            `Value` representation of the loaded YAML data.

        """
        # Check data/foo.toml, it should contain a nested structure
        yield lintkit.Value.from_toml(self.getitem("data"))


# File name only rules


class FileNameCheck(
    Message,
    lintkit.check.Regex,
    lintkit.loader.File,
    lintkit.rule.Node,
    code=301,
):
    """Rule validating the file name."""

    def regex(self) -> str:
        """Regex to match the file name.

        Returns:
            `test_loader.py` as the expected file name.
        """
        return "test_loader.py"

    def values(self) -> Iterable[lintkit.Value]:
        """Yield the file name as a `Value`.

        Yields:
            `Value` representation of the file name.
        """
        yield lintkit.Value(str(self.file))
