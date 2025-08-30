<!--
SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

<!-- mkdocs remove start -->

<img align="left" width="256" height="256" src="logo.svg">

<!-- mkdocs remove end -->

<p align="center">
    <em> lintkit is a framework for building linters/code checking rules </em>
</p>

- __Multiple formats__: Python-first, but supports YAML, JSON and TOML
- __Comprehensive__: `noqa` comments,
    file skips and standardized pretty output
- __Quick__: Create and run custom rules in a few lines of code
- __Flexible__: Rules over file(s), their subelements and more
    (see [Files tutorial](https://open-nudge.github.io/lintkit/latest/tutorials/file))
- __Minimal__: Gentle learning curve - `<1000` lines of code,
    [tutorials](https://open-nudge.github.io/lintkit/latest/tutorials),
    [API reference](https://open-nudge.github.io/lintkit/latest/reference/lintkit)

______________________________________________________________________

<!-- mkdocs remove start -->

<!-- vale off -->

<!-- pyml disable-num-lines 30 line-length-->

<div align="center">

<a href="https://pypi.org/project/lintkit">![PyPI - Python Version](https://img.shields.io/pypi/v/lintkit?style=for-the-badge&label=release&labelColor=grey&color=blue)
</a>
<a href="https://pypi.org/project/lintkit">![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fopen-nudge%2Flintkit%2Fmain%2Fpyproject.toml&style=for-the-badge&label=python&labelColor=grey&color=blue)
</a>
<a href="https://opensource.org/licenses/Apache-2.0">![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)
</a>
<a>![Coverage Hardcoded](https://img.shields.io/badge/coverage-100%25-green?style=for-the-badge)
</a>
<a href="https://scorecard.dev/viewer/?uri=github.com/open-nudge/lintkit">![OSSF-Scorecard Score](https://img.shields.io/ossf-scorecard/github.com/open-nudge/lintkit?style=for-the-badge&label=OSSF)
</a>

</div>

<p align="center">
🚀 <a href="#quick-start">Quick start</a>
📚 <a href="https://open-nudge.github.io/lintkit">Documentation</a>
🤝 <a href="#contribute">Contribute</a>
👍 <a href="https://github.com/open-nudge/lintkit/blob/main/ADOPTERS.md">Adopters</a>
📜 <a href="#legal">Legal</a>
</p>

<!-- vale on -->

<!-- mkdocs remove end -->

## Quick start

> [!TIP]
> __Check out more examples ([here](https://open-nudge.github.io/lintkit/latest/tutorials))
> to get a better feel of `lintkit`__.

Below are __~`20` lines of code__ implementing custom linter with
__two rules__ and running it on three files:

```python
import lintkit

# Set the name of the linter
lintkit.settings.name = "NOUTILS"

class _NoUtils(lintkit.check.Regex, lintkit.loader.Python, lintkit.rule.Node):
    def regex(self):
        # Regex to match util(s) variations in function/class name
        return r"_?[Uu]til(s|ities)?"

    def values(self):
        # Yield class or function names from a Python file
        data = self.getitem("nodes_map")
        for node in data[self.ast_class()]:
            yield lintkit.Value.from_python(node.name, node)

    def message(self, _):
        return f"{self.ast_class()} name contains util(s) word"

# Concrete rules and their codes
# Disabling linter using noqas supported out of the box!
class ClassNoUtils(_NoUtils, code=0):  # noqa: NOUTILS0
    # ast type we want to focus on in this rule
    def ast_class(self):
        return ast.ClassDef

class FunctionNoUtils(_NoUtils, code=1):  # noqa: NOUTILS0
    def ast_class(self):
        return ast.FunctionDef

lintkit.run(["linter.py", "file1.py", "file2.py"])

# Example output
#/path/file1.py:23:17 NOUTILS0: ClassDef name contains util(s) word
#/path/file2.py:73:21 NOUTILS1: FunctionDef name contains util(s) word
```

## Installation

> [!TIP]
> You can use your favorite package manager like
> [`uv`](https://github.com/astral-sh/uv),
> [`hatch`](https://github.com/pypa/hatch)
> or [`pdm`](https://github.com/pdm-project/pdm)
> instead of `pip`.

```sh
> pip install lintkit
```

> [!NOTE]
> `lintkit` provides extras (`rich`, `toml`, `yaml`
> and `all` containing everything) to provide additional functionality.

```sh
# To create rules utilizing YAML
> pip install lintkit[rich, yaml]
```

## Learn

Check out the following links to learn more about `lintkit`:

- [Tutorials](https://open-nudge.github.io/lintkit/latest/tutorials)
- [API Reference](https://open-nudge.github.io/lintkit/latest/reference/lintkit)

## Contribute

We welcome your contributions! Start here:

- [Code of Conduct](/CODE_OF_CONDUCT.md)
- [Contributing Guide](/CONTRIBUTING.md)
- [Roadmap](/ROADMAP.md)
- [Changelog](/CHANGELOG.md)
- [Report security vulnerabilities](/SECURITY.md)
- [Open an Issue](https://github.com/open-nudge/lintkit/issues)

## Legal

- This project is licensed under the _Apache 2.0 License_ - see
    the [LICENSE](/LICENSE.md) file for details.
- This project is copyrighted by _open-nudge_ - the
    appropriate copyright notice is included in each file.

<!-- mkdocs remove end -->

<!-- md-dead-link-check: on -->
