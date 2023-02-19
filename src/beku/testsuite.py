"""Expand kuttl tests from templates."""
import logging
import os
import re
from dataclasses import dataclass, field
from functools import cached_property
from itertools import product, chain
from os import walk, path, makedirs
from shutil import copy2
from typing import Dict, List, TypeVar, Type, Tuple

from jinja2 import Environment, FileSystemLoader
from yaml import safe_load


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
                source = path.join(root, file_name)
                dest = ""
                f_mode = os.stat(source).st_mode
                if file_name.endswith(".j2"):
                    logging.debug("Render template %s to %s", file_name, dest)
                    dest = path.join(
                        tc_root, root[len(td_root) + 1:], file_name[:-3:])
                    self._expand_template(file_name, dest, test_env)
                else:
                    dest = path.join(
                        tc_root, root[len(td_root) + 1:], file_name)
                    logging.debug("Copy file %s to %s", file_name, dest)
                    copy2(source, dest)
                # restore file permissions (especially the executable bit is important here)
                logging.debug("Update file mode for %s", dest)
                os.chmod(dest, f_mode)

    def _expand_template(self, template_file: str, dest: str, env: Environment) -> None:
        logging.debug("Expanding template %s", template_file)
        template = env.get_template(template_file)
        with open(dest, encoding="utf8", mode="w") as stream:
            print(
                template.render({"test_scenario": {"values": self.values}}), file=stream)


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


TTestSuite = TypeVar(    # pylint: disable=invalid-name
    "TTestSuite", bound="TestSuite")


@dataclass(frozen=True)
class TestSuite:
    """Test suite template."""
    source: str = field()
    test_cases: List[TestCase] = field(default_factory=list)

    def __post_init__(self) -> None:
        with open(self.source, encoding="utf8") as stream:
            tin = safe_load(stream)
            dimensions = [
                TestDimension(d["name"], d["values"]) for d in tin["dimensions"]
            ]
            test_def = [
                TestDefinition(t["name"], t["dimensions"]) for t in tin["tests"]
            ]
            self.test_cases.extend(self._build(dimensions, test_def))

    @classmethod
    def _build(
            cls: Type[TTestSuite], dims: List[TestDimension], tests: List[TestDefinition]
    ) -> List[TestCase]:
        """
        >>> TestSuite._build([TestDimension(name='trino', values=['234', '235'])],
        ... [TestDefinition(name='smoke', dimensions=['trino'])])
        [TestCase(name='smoke', values={'trino': '234'}, name='smoke_trino-234'), \
        TestCase(name='smoke', values={'trino': '235'}, name='smoke_trino-235')]
        """
        result = []
        for test in tests:
            used_dims = [d for d in dims if d.name in test.dimensions]
            expanded_test_dims: List[List[Tuple[str, str]]] = [
                d.expand() for d in used_dims
            ]
            for tc_dim in product(*expanded_test_dims):
                result.append(TestCase(name=test.name, values=dict(tc_dim)))
        return result

    def __repr__(self) -> str:
        return f"TestSuite(source={self.source})"

    def expand(self, template_dir: str, output_dir: str, kuttl_tests: str) -> int:
        """Expand test suite."""
        logging.info("Expanding test suite from %s", self.source)
        self._sanity_checks(template_dir, kuttl_tests)
        _mkdir_ignore_exists(output_dir)
        self._expand_kuttl_tests(output_dir, kuttl_tests)
        for test_case in self.test_cases:
            test_case.expand(template_dir, output_dir)
        return 0

    def _sanity_checks(self, template_dir: str, kuttl_tests: str) -> None:
        for test_case in self.test_cases:
            td_root = path.join(template_dir, test_case.name)
            if not path.isdir(td_root):
                raise ValueError(
                    f"Test definition directory not found [{td_root}]")
        if not path.isfile(kuttl_tests):
            raise ValueError(
                f"Kuttl test config template not found [{kuttl_tests}]")

    def _expand_kuttl_tests(self, output_dir: str, kuttl_tests: str) -> None:
        env = Environment(loader=FileSystemLoader(path.dirname(kuttl_tests)))
        kt_base_name = path.basename(kuttl_tests)
        template = env.get_template(kt_base_name)
        kt_dest_name = re.sub(r"\.j(inja)?2$", "", kt_base_name)
        # Compatibility warning: Assume output_dir ends with 'tests' and remove
        # it from the destination file
        dest = path.join(path.dirname(output_dir), kt_dest_name)
        kuttl_vars = {
            "testinput": {
                "tests": [{"name": tn} for tn in {tc.name for tc in self.test_cases}]
            }
        }
        logging.debug("kuttl vars %s", kuttl_vars)
        with open(dest, encoding="utf8", mode="w") as stream:
            print(template.render(kuttl_vars), file=stream)


def _mkdir_ignore_exists(dir_name: str) -> None:
    try:
        logging.debug("Creating directory %s", dir_name)
        makedirs(dir_name)
    except FileExistsError:
        pass
