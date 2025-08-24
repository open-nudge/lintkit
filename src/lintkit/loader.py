# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Module defining loaders for various file types."""

from __future__ import annotations

import abc
import ast
import collections
import functools
import json
import typing

from . import available
from ._value import Value

if typing.TYPE_CHECKING:
    import pathlib

    from collections.abc import Callable

_last_loader_index: int = -1
"""Last index of the loader, used to create unique indices for each."""


def _create_loader_index() -> int:
    """Create a unique index for each loader.

    This function allows loaders to keep data uniquely.

    Returns:
        A unique index for the loader, incremented by one.
    """
    global _last_loader_index  # noqa: PLW0603
    _last_loader_index += 1
    return _last_loader_index


class Loader(abc.ABC):
    """Base class for all loaders."""

    _loader_data: typing.ClassVar[
        collections.defaultdict[int, collections.defaultdict[str, typing.Any]]
    ] = collections.defaultdict(lambda: collections.defaultdict(lambda: None))
    """Where all the data is stored internally."""

    _loader_index: int = _create_loader_index()
    """Unique index for each Loader class."""

    @classmethod
    @abc.abstractmethod
    def skip(cls, file: pathlib.Path, content: str) -> bool:
        """Skip loading based on the file path or content.

        Args:
            file:
                The path to the file being checked.
            content:
                The content of the file as a string.

        Returns:
            `True` if the file should be skipped, `False` otherwise.

        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def should_cache(cls) -> bool:
        """Check if the data is already loaded and cached.

        Note:
            Unlike `skip` this method is dependent on class
            attributes (e.g. loaded `data`) not external
            factors.

        Returns:
            `True` if the data is already loaded and cached,
            `False` otherwise.

        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def load(cls, file: pathlib.Path, content: str) -> None:
        """Load the content of the file into some attribute.

        Tip:
            You should only use `content` if possible to load
            the data, as it is already loaded into memory.

        Args:
            file:
                The path to the file being loaded.
            content:
                The content of the file as a string.

        """
        raise NotImplementedError

    @classmethod
    def getitem(cls, key: str) -> typing.Any:
        """Get an item from the loader's data.

        Warning:
            If the item is not found an error is raised.

        Note:
            This is a convenience method to hide internal
            caching mechanism and allow natural access
            to the underlying data.

        Args:
            key:
                The key to retrieve the value for.
        """
        return Loader._loader_data[cls._loader_index][key]

    @classmethod
    def setitem(cls, key: str, value: typing.Any) -> None:
        """Set an item in the loader's data.

        Note:
            This is a convenience method to hide internal
            caching mechanism and allow natural access
            to the underlying data.

        Args:
            key:
                The key to set the value for.
            value:
                The value to set for the given key.
        """
        Loader._loader_data[cls._loader_index][key] = value

    @classmethod
    def reset(cls) -> None:
        """Reset the loader's data."""
        Loader._loader_data = collections.defaultdict(
            lambda: collections.defaultdict(lambda: None)
        )


class File(Loader):
    """Load whole `file`.

    If this `loader` is used, you will likely work directly
    on a `pathlib.Path` object, hence this `load` is essentially a no-op.

    Note:
        As `rule` already has the `file` attribute, this loader
        is mostly used to express intent.

    """

    _loader_index: int = _create_loader_index()

    @classmethod
    def skip(cls, _: pathlib.Path, __: str) -> bool:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
        """Never skip loading.

        Important:
            If you wish to target a file with specific extension
            you can update this method, see below.

        Example:
            ```python
            import lintkit


            class PythonFile(lintkit.loader.File):
                def skip(cls, filename: pathlib.Path, _: str) -> bool:
                    return filename.suffix != ".py"
            ```

        Args:
            _:
                The path to the file being checked (not used by default).
            __:
                The content of the file (not used by default).

        Returns:
            `False` always, as this loader should never be skipped.

        """
        return False

    @classmethod
    def should_cache(cls) -> bool:  # pyright: ignore [reportImplicitOverride]
        """Never cache this loader."""
        return False

    @classmethod
    def load(cls, _: pathlib.Path, __: str) -> None:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
        """Do not load anything.

        Args:
            _:
                The path to the file being loaded (not used).
            __:
                The content of the file (not used).

        """


class Python(Loader):
    """Loader of `Python` files providing access to `ast` of the source code.

    Usage of this loader allows you to work with the elements of the
    abstract syntax tree (e.g., functions, classes, etc.) of the Python code.

    A couple of attributes are available for you to use:

    - `self.ast`: The root of the abstract syntax tree.
    - `self.nodes_direct`: A list of nodes that are direct
        children of the root.
    - `self.nodes_recursive`: A list of all nodes in the tree,
        including nested ones.
    - `self.nodes_map`: A dictionary mapping node types to
        objects of that type. If the `node` type is not present
        in the dictionary, an empty list is returned.

    Note:
        Parsed `ast` is cached, but still might be slower
        than targeted loaders.

    """

    _loader_index: int = _create_loader_index()

    @classmethod
    def skip(cls, file: pathlib.Path, _: str) -> bool:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
        """Skip loading if the file is not a Python file.

        Args:
            file:
                The path to the file being checked.
            _:
                The content of the file (not used).

        Returns:
            `True` if the file is not a Python file (i.e., does not
            have a `.py` extension), `False` otherwise.

        """
        return file.suffix != ".py"

    @classmethod
    def should_cache(cls) -> bool:  # pyright: ignore [reportImplicitOverride]
        """Check if the `ast` is already present.

        Returns:
            `True` if the [`ast`](https://docs.python.org/3/library/ast.html)
            is already loaded and cached, `False` otherwise.
        """
        return Python.getitem("ast") is not None

    @classmethod
    def load(cls, _: pathlib.Path, content: str) -> None:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
        """Load the content of the Python file and cache the AST.

        Note:
            The loaded data is saved under the `ast`, `nodes_direct`,
            `nodes_recursive`, and `nodes_map` keys.

        Args:
            _:
                The path to the file being loaded (not used).
            content:
                The content of the Python file as a string.

        Raises:
            SyntaxError: If the content is not valid Python code.
        """
        ast_ = ast.parse(content)
        nodes_direct = list(ast.iter_child_nodes(ast_))
        nodes_recursive = list(ast.walk(ast_))
        nodes_map = collections.defaultdict(list)
        for node in nodes_recursive:
            nodes_map[type(node)].append(node)

        cls.setitem("ast", ast_)
        cls.setitem("nodes_direct", nodes_direct)
        cls.setitem("nodes_recursive", nodes_recursive)
        cls.setitem("nodes_map", nodes_map)


class ConfigLoader(Loader, abc.ABC):
    """Load mixin for non-Python files.

    This mixin provides a common interface for loaders that
    handle non-Python files, such as JSON, TOML, and YAML.

    """

    @classmethod
    @abc.abstractmethod
    def _extensions(cls) -> set[str]:
        """Extensions of a given format.

        Returns:
            A set of file extensions that this loader can handle.
            For example, `{"json"}`, `{"yaml", "yml"}`, etc.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _load(cls, file: pathlib.Path, content: str) -> typing.Any:
        """Load the content of the file and return the parsed data.

        This method is class-specific and should be implemented
        by subclasses to handle the specific file format.

        Warning:
            The `file` argument is provided for context, but
            it is advised to use the `content` argument as
            it is already loaded into memory.

        Args:
            file:
                The path to the file being loaded.
            content:
                The content of the file as a string.

        Returns:
            The parsed data from the file.
        """
        raise NotImplementedError

    @classmethod
    def load(cls, file: pathlib.Path, content: str) -> None:  # pyright: ignore [reportImplicitOverride]
        """Load the content of the file and cache it.

        Note:
            The loaded data is saved under the `data` key.

        Args:
            file:
                The path to the file being loaded.
            content:
                The content of the file as a string.

        """
        cls.setitem("data", cls._load(file, content))

    @classmethod
    def should_cache(cls) -> bool:  # pyright: ignore [reportImplicitOverride]
        """Check if the `data` key is present.

        Returns:
            `True` if the `cache` is already there and load
            should not be re-executed, `False` otherwise.

        """
        return cls.getitem("data") is not None  # pragma: no cover

    @classmethod
    def skip(cls, file: pathlib.Path, _: str) -> bool:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
        """Skip loading if the file if it is not of the expected type.

        Note:
            Types are defined by their file extensions
            (e.g. `json`, `yaml`/`yml`, etc.) in non-abstract
            config classes like `JSON`, `YAML`, etc.

        Args:
            file:
                The path to the file being checked.
            _:
                The content of the file (not used).

        Returns:
            `True` if the file is not of the expected type,
            `False` otherwise.

        """
        return file.suffix not in cls._extensions()


class JSON(ConfigLoader):
    """Loader for `JSON` files."""

    _loader_index: int = _create_loader_index()

    @classmethod
    def _extensions(cls) -> set[str]:  # pyright: ignore [reportImplicitOverride]
        """`JSON` file extensions.

        Returns:
            `{".json"}`.

        """
        return {
            ".json",
        }

    @classmethod
    def _load(cls, _: pathlib.Path, content: str) -> typing.Any:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
        """Load the content of a `JSON` file.

        Args:
            _:
                The path to the file being loaded (not used).
            content:
                The content of the `TOML` file as a string.

        Returns:
            The parsed data from the `JSON` file.

        """
        return json.loads(content)


if available.TOML:
    from tomlkit import parse

    class TOML(ConfigLoader):
        """Loader for `TOML` files."""

        _loader_index: int = _create_loader_index()

        @classmethod
        def _extensions(cls) -> set[str]:  # pyright: ignore [reportImplicitOverride]
            """`TOML` file extensions.

            Returns:
                `{".toml"}`.

            """
            return {
                ".toml",
            }

        @classmethod
        def _load(cls, _: pathlib.Path, content: str) -> typing.Any:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
            """Load the content of a `TOML` file.

            Args:
                _:
                    The path to the file being loaded (not used).
                content:
                    The content of the `TOML` file as a string.

            Returns:
                The parsed data from the `TOML` file.

            """
            return parse(content)

else:  # pragma: no cover
    pass

if available.YAML:
    import ruamel.yaml

    P = typing.ParamSpec("P")
    T = typing.TypeVar("T")

    def _decorator(func: Callable[P, T]) -> Callable[P, Value[T]]:
        """Decorator to wrap the return value of a YAML tree in `Value`.

        Args:
            func:
                The function to be decorated, (some `construct_*` method
                of the `ValueConstructor`).

        """

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Value[T]:
            """Wrapper function to convert the return value to `Value`.

            Args:
                *args:
                    Positional arguments passed to the original function.
                **kwargs:
                    Keyword arguments passed to the original function.

            Returns:
                Anything returned by the original function wrapped in `Value`.
                Usually some sort of YAML node or value.

            """
            return Value._from_yaml(func(*args, **kwargs), args[1])  # noqa: SLF001

        return wrapper

    class _ValueConstructor(ruamel.yaml.constructor.RoundTripConstructor):  # pyright: ignore[reportUntypedBaseClass, reportAttributeAccessIssue]
        """Custom constructor for YAML that wraps values in `Value`."""

    # Wrap all `construct_*` methods of `_ValueConstructor`
    # with the decorator. Other options do not seem to work reliably.
    for attribute in dir(_ValueConstructor):
        if attribute.startswith("construct_"):
            function = getattr(_ValueConstructor, attribute)
            setattr(
                _ValueConstructor,
                attribute,
                _decorator(function),
            )

    class YAML(ConfigLoader):
        """Loader for `YAML` files.

        Warning:
            This loader uses `ruamel.yaml` to parse YAML files.
            Each object is already wrapped with `Value`,
            hence you can use it directly.

        """

        _loader_index: int = _create_loader_index()

        _ruamel_yaml: ruamel.yaml.YAML = ruamel.yaml.YAML()
        _ruamel_yaml.Constructor = _ValueConstructor

        @classmethod
        def _extensions(cls) -> set[str]:  # pyright: ignore [reportImplicitOverride]
            """`YAML` file extensions.

            Returns:
                `{".yaml", ".yml"}`.

            """
            return {".yaml", ".yml"}

        @classmethod
        def _load(cls, _: pathlib.Path, content: str) -> None:  # pyright: ignore [reportImplicitOverride, reportIncompatibleMethodOverride]
            """Load the content of a YAML file.

            Args:
                _:
                    The path to the file being loaded (not used).
                content:
                    The content of the YAML file as a string.

            Returns:
                The parsed data from the YAML file.

            """
            return YAML._ruamel_yaml.load(content)

else:  # pragma: no cover
    pass
