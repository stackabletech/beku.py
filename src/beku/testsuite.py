"""Expand kuttl tests from templates."""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from functools import cached_property
from itertools import product, chain
from os import walk, path, makedirs
from shutil import copy2
from typing import Dict, List, Tuple, Any

from jinja2 import Environment, FileSystemLoader
from yaml import safe_load

PATTERN_EXTENSION_JINJA: str = r"\.j(inja)?2$"


def ansible_lookup(loc: str, what: str) -> str:
    """
    Lookup an environment variable (what) and return it's contents if any.
    Simulates the Ansible `lookup()` function which is made available by Ansible Jinja templates.
    Raises an exception if `loc` is not `env`.
    """
    if loc != 'env':
        raise ValueError("Can only lookup() in 'env'")
    result = ""
    try:
        result = os.environ[what]
    except KeyError:
        pass
    return result


@dataclass(frozen=True)
class TestFile:
    """An input test file, not a template."""
    dest_dir: str
    source_dir: str
    file_name: str

    def build_destination(self) -> str:
        """Copies the file name to the destination directory.
        Returns the destination file name.
        """
        source = path.join(self.source_dir, self.file_name)
        dest = path.join(self.dest_dir, self.file_name)
        logging.debug("Copy file %s to %s", source, dest)
        copy2(source, dest)
        logging.debug("Update file mode for %s", dest)
        f_mode = os.stat(source).st_mode
        os.chmod(dest, f_mode)
        return dest


@dataclass(frozen=True)
class TestTemplate:
    """An Jinja 2 template"""
    dest_dir: str
    source_dir: str
    file_name: str
    env: Environment
    values: Dict[str, str]

    def build_destination(self) -> str:
        """Renders the template to file in the destination directory. The resulting file has the same name as the template
        but with the .j2 or .jinja2 ending removed.
        Returns the rendered file name.
        """
        source = path.join(self.source_dir, self.file_name)
        dest = path.join(self.dest_dir, re.sub(
            PATTERN_EXTENSION_JINJA, "", self.file_name))
        logging.debug("Render template %s to %s", source, dest)
        template = self.env.get_template(self.file_name)
        with open(dest, encoding="utf8", mode="w") as stream:
            print(
                template.render({"test_scenario": {"values": self.values}}), file=stream)
        logging.debug("Update file mode for %s", dest)
        f_mode = os.stat(source).st_mode
        os.chmod(dest, f_mode)
        return dest


def test_source_with_context(file_name: str, source_dir: str, dest_dir: str, env: Environment,
                             values: Dict[str, str]) -> TestFile | TestTemplate:
    if re.search(PATTERN_EXTENSION_JINJA, file_name):
        return TestTemplate(file_name=file_name, source_dir=source_dir, dest_dir=dest_dir, env=env, values=values)

    return TestFile(file_name=file_name, source_dir=source_dir, dest_dir=dest_dir)


@dataclass(frozen=True)
class TestCase:
    """Test case definition."""
    name: str
    values: Dict[str, str]

    @cached_property
    def tid(self) -> str:
        """Return the test id."""
        return "_".join(
            chain(
                [self.name],
                [f"{k}-{v}" for k, v in self.values.items()],
            )
        )

    def expand(self, template_dir: str, target_dir: str) -> None:
        """Expand test case."""
        logging.info("Expanding test case id [%s]", self.tid)
        td_root = path.join(template_dir, self.name)
        tc_root = path.join(target_dir, self.name, self.tid)
        _mkdir_ignore_exists(tc_root)
        test_env = Environment(
            loader=FileSystemLoader(path.join(template_dir, self.name)),
            trim_blocks=True
        )
        test_env.globals['lookup'] = ansible_lookup
        sub_level: int = 0
        for root, dirs, files in walk(td_root):
            sub_level += 1
            if sub_level == 5:
                # Sanity check
                raise ValueError("Maximum recursive level (5) reached.")
            for dir_name in dirs:
                _mkdir_ignore_exists(
                    path.join(tc_root, root[len(td_root) + 1:], dir_name))
            for file_name in files:
                test_source = test_source_with_context(file_name, root, path.join(tc_root, root[len(td_root) + 1:]),
                                                       test_env, self.values)
                test_source.build_destination()


@dataclass(frozen=True)
class TestDimension:
    """Test dimension."""
    name: str
    values: List[str]

    def expand(self) -> List[Tuple[str, str]]:
        """Return a list of tuples in the form of (<dimension>, <value>)"""
        return [(self.name, v) for v in self.values]


@dataclass(frozen=True)
class TestDefinition:
    """Test case definition."""
    name: str
    dimensions: List[str]


@dataclass
class TestSuitePatchDimension:
    name: str
    expr: str

    @classmethod
    def from_dict(cls, _dict: Dict[str, str]) -> TestSuitePatchDimension:
        if not _dict["name"]:
            raise ValueError(
                "Test patch dimensions must have a [name] property")

        return TestSuitePatchDimension(**_dict)

    def patch_dim_values(self, dim: TestDimension) -> TestDimension:
        if self.expr == 'last':
            patched_values = [dim.values[-1]]
        elif self.expr == 'first':
            patched_values = [dim.values[0]]
        else:
            patched_values = [v for v in dim.values if v.find(self.expr) != -1]
        return TestDimension(name=dim.name, values=patched_values)


@dataclass
class TestSuitePatch:
    test: str
    patch_dimensions: List[TestSuitePatchDimension]

    @classmethod
    def from_dict(cls, _dict: Dict[str, Any]) -> TestSuitePatch:
        if not _dict["test"]:
            raise ValueError("Test patches must have a [test] property")
        return TestSuitePatch(test=_dict['test'],
                              patch_dimensions=[TestSuitePatchDimension.from_dict(p) for p in
                                                _dict.get('dimensions', [])])

    def patch(self, test_name: str, dims: List[TestDimension]) -> List[TestDimension]:
        result = []
        for _pd in self.patch_dimensions:
            try:
                to_patch_dim = next((d for d in dims if _pd.name == d.name))
                result.append(_pd.patch_dim_values(to_patch_dim))
            except StopIteration as exc:
                raise ValueError(
                    f"Cannot find dimension [{_pd.name}] to patch in test [{test_name}]") from exc
        return result


@dataclass(frozen=True)
class TestSuite:
    name: str
    select: List[str]
    patch: List[TestSuitePatch]

    @classmethod
    def from_dict(cls, _dict: Dict[str, Any]) -> TestSuite:
        if not _dict["name"]:
            raise ValueError("Test suites must have a [name] property")
        return TestSuite(name=_dict['name'], select=_dict.get('select', []),
                         patch=[TestSuitePatch.from_dict(p) for p in _dict.get('patch', [])])

    def select_tests(self, tests: List[TestDefinition]) -> List[TestDefinition]:
        """Return tests that match the selection list and discard all others. Return the given tests if the selection
        list is empty.
        """
        if self.select:
            result = []
            for input_test in tests:
                if input_test.name in self.select:
                    result.append(input_test)
            return result
        return tests

    def patch_dimensions(self, test_name: str, dims: List[TestDimension]) -> List[TestDimension]:
        if self.patch:
            result = []
            for test_patch in self.patch:
                if test_patch.test == test_name:
                    result.append(test_patch.patch(test_name, dims))
        return dims


@dataclass(frozen=True)
class EffectiveTestSuite:
    """Test suite template."""
    name: str = field()
    test_cases: List[TestCase] = field(default_factory=list)


def expand(suite: str, effective_test_suites: List[EffectiveTestSuite], template_dir: str, output_dir: str,
           kuttl_tests: str) -> int:
    """Expand test suite."""
    try:
        ets = next(
            (s for s in effective_test_suites if suite == s.name))
        _sanity_checks(ets.test_cases, template_dir, kuttl_tests)
        _mkdir_ignore_exists(output_dir)
        _expand_kuttl_tests(ets.test_cases, output_dir, kuttl_tests)
        for test_case in ets.test_cases:
            test_case.expand(template_dir, output_dir)
    except StopIteration as exc:
        raise ValueError(
            f"Cannot expand test suite [{suite}] because cannot find it in [{kuttl_tests}]") from exc
    return 0


def _expand_kuttl_tests(test_cases, output_dir: str, kuttl_tests: str) -> None:
    """Generate the kuttl-tests.yaml file and fill in paths to tests."""
    env = Environment(loader=FileSystemLoader(path.dirname(kuttl_tests)))
    kt_base_name = path.basename(kuttl_tests)
    template = env.get_template(kt_base_name)
    kt_dest_name = re.sub(PATTERN_EXTENSION_JINJA, "", kt_base_name)
    # Compatibility warning: Assume output_dir ends with 'tests' and remove
    # it from the destination file
    dest = path.join(path.dirname(output_dir), kt_dest_name)
    kuttl_vars = {
        "testinput": {
            "tests": [{"name": tn} for tn in {tc.name for tc in test_cases}]
        }
    }
    logging.debug("kuttl vars %s", kuttl_vars)
    with open(dest, encoding="utf8", mode="w") as stream:
        print(template.render(kuttl_vars), file=stream)


def renderer_from_file(file_name: str) -> List[EffectiveTestSuite]:
    with open(file_name, encoding="utf8") as stream:
        return renderer_from_stream(stream)


def renderer_from_stream(stream) -> List[EffectiveTestSuite]:
    tin = safe_load(stream)
    dimensions = [
        TestDimension(d["name"], d["values"]) for d in tin["dimensions"]
    ]
    test_def = [
        TestDefinition(t["name"], t["dimensions"]) for t in tin["tests"]
    ]

    test_suites = [TestSuite(name="default", select=[], patch=[])]
    if "suites" in tin:
        test_suites = [
            TestSuite.from_dict(t) for t in tin["suites"]
        ]
    return _resolve_effective_test_suites(dimensions, test_def, test_suites)


def _resolve_effective_test_suites(
        dims: List[TestDimension], tests: List[TestDefinition], suites: List[TestSuite]
):
    effective_test_suites = []
    for suite in suites:
        test_cases = []
        for test in suite.select_tests(tests):
            used_dims = [d for d in dims if d.name in test.dimensions]
            effective_dimensions = suite.patch_dimensions(
                test.name, used_dims)
            expanded_test_dims: List[List[Tuple[str, str]]] = [
                d.expand() for d in effective_dimensions
            ]
            test_cases.extend(
                [TestCase(name=test.name, values=dict(tc_dim)) for tc_dim in product(*expanded_test_dims)])
        effective_test_suites.append(EffectiveTestSuite(
            name=suite.name, test_cases=test_cases))
    return effective_test_suites


def _mkdir_ignore_exists(dir_name: str) -> None:
    try:
        logging.debug("Creating directory %s", dir_name)
        makedirs(dir_name)
    except FileExistsError:
        pass


def _sanity_checks(test_cases, template_dir: str, kuttl_tests: str) -> None:
    for test_case in test_cases:
        td_root = path.join(template_dir, test_case.name)
        if not path.isdir(td_root):
            raise ValueError(
                f"Test definition directory not found [{td_root}]")
    if not path.isfile(kuttl_tests):
        raise ValueError(
            f"Kuttl test config template not found [{kuttl_tests}]")
