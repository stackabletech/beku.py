from typing import Dict, List, TypeVar, Type, Tuple
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from itertools import product, chain
from jinja2 import Environment, FileSystemLoader
from os import walk, path, makedirs
from shutil import copy2
from sys import exit
from yaml import safe_load
import logging
import re
import os


__version_info__ = (0, 0, 5)
__version__ = ".".join(map(str, __version_info__))


def ansible_lookup(loc: str, what: str) -> str:
    """
    Lookup an environment variable (what) and return it's contents if any.
    Simulates the Ansible `lookup()` function which is made available by Ansible Jinja templates.
    Raises an exception if `loc` is not `env`.
    """
    if not loc is 'env':
        raise ValueError("Can only lookup() in 'env'")
    result = ""
    try:
        result = os.environ[what]
    except KeyError:
        pass
    return result


@dataclass
class TestCase:
    name: str
    values: Dict[str, str]
    tid: str = field(init=False)

    def __post_init__(self):
        self.tid = "_".join(
            chain(
                [self.name],
                ["-".join([x, self.values.get(x)])
                 for x in self.values.keys()],
            )
        )

    def expand(self, template_dir: str, target_dir: str) -> None:
        logging.info(f"Expanding test case id [{self.tid}]")
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
            for d in dirs:
                _mkdir_ignore_exists(
                    path.join(tc_root, root[len(td_root) + 1:], d))
            for f in files:
                source = path.join(root, f)
                dest = ""
                f_mode = os.stat(source).st_mode
                if f.endswith(".j2"):
                    logging.debug(f"Render template {f} to {dest}")
                    dest = path.join(tc_root, root[len(td_root) + 1:], f[:-3:])
                    self._expand_template(f, dest, test_env)
                else:
                    dest = path.join(tc_root, root[len(td_root) + 1:], f)
                    logging.debug(f"Copy file {f} to {dest}")
                    copy2(source, dest)
                # restore file permissions (especially the executable bit is important here)
                logging.debug(f"Update file mode for {dest}")
                os.chmod(dest, f_mode)

    def _expand_template(self, template: str, dest: str, env: Environment) -> None:
        logging.debug(f"Expanding template {template}")
        t = env.get_template(template)
        with open(dest, encoding="utf8", mode="w") as stream:
            print(
                t.render({"test_scenario": {"values": self.values}}), file=stream)


@dataclass
class TestDimension:
    name: str
    values: List[str]

    def expand(self) -> List[Tuple[str, str]]:
        return [(self.name, v) for v in self.values]


@dataclass
class TestDefinition:
    name: str
    dimensions: List[str]


TTestSuite = TypeVar("TTestSuite", bound="TestSuite")


@dataclass
class TestSuite:
    source: str
    test_cases: List[TestCase]

    def __init__(self, source: str) -> None:
        self.source = source
        with open(source, encoding="utf8") as stream:
            tin = safe_load(stream)
            dimensions = [
                TestDimension(d["name"], d["values"]) for d in tin["dimensions"]
            ]
            test_def = [
                TestDefinition(t["name"], t["dimensions"]) for t in tin["tests"]
            ]
            self.test_cases = self._build(dimensions, test_def)

    @classmethod
    def _build(
        cls: Type[TTestSuite], dims: List[TestDimension], tests: List[TestDefinition]
    ) -> List[TestCase]:
        """
        >>> TestSuite._build([TestDimension(name='trino', values=['234', '235'])],
        ... [TestDefinition(name='smoke', dimensions=['trino'])])
        [TestCase(name='smoke', values={'trino': '234'}, name='smoke_trino-234'), TestCase(name='smoke', values={'trino': '235'}, name='smoke_trino-235')]
        """
        result = []
        for t in tests:
            used_dims = [d for d in dims if d.name in t.dimensions]
            expanded_test_dims: List[List[Tuple[str, str]]] = [
                d.expand() for d in used_dims
            ]
            for tc_dim in product(*expanded_test_dims):
                result.append(TestCase(name=t.name, values=dict(tc_dim)))
        return result

    def __repr__(self) -> str:
        return f"TestSuite(source={self.source})"

    def expand(self, template_dir: str, output_dir: str, kuttl_tests: str) -> int:
        logging.info(f"Expanding test suite from {self.source}")
        self._sanity_checks(template_dir, output_dir, kuttl_tests)
        _mkdir_ignore_exists(output_dir)
        self._expand_kuttl_tests(output_dir, kuttl_tests)
        for test_case in self.test_cases:
            test_case.expand(template_dir, output_dir)
        return 0

    def _sanity_checks(
        self, template_dir: str, output_dir: str, kuttl_tests: str
    ) -> None:
        for tc in self.test_cases:
            td_root = path.join(template_dir, tc.name)
            if not path.isdir(td_root):
                raise ValueError(
                    f"Test definition directory not found [{td_root}]")
        if not (path.isfile(kuttl_tests)):
            raise ValueError(
                f"Kuttl test config template not found [{kuttl_tests}]")

    def _expand_kuttl_tests(self, output_dir: str, kuttl_tests: str) -> None:
        env = Environment(loader=FileSystemLoader(path.dirname(kuttl_tests)))
        kt_base_name = path.basename(kuttl_tests)
        t = env.get_template(kt_base_name)
        kt_dest_name = re.sub(r"\.j(inja)?2$", "", kt_base_name)
        # Compatibility warning: Assume output_dir ends with 'tests' and remove
        # it from the destination file
        dest = path.join(path.dirname(output_dir), kt_dest_name)
        kuttl_vars = {
            "testinput": {
                "tests": [{"name": tn} for tn in {tc.name for tc in self.test_cases}]
            }
        }
        logging.debug(f"kuttl vars {kuttl_vars}")
        with open(dest, encoding="utf8", mode="w") as stream:
            print(t.render(kuttl_vars), file=stream)


def parse_cli_args() -> Namespace:
    parser = ArgumentParser(
        description="Kuttl test expander for the Stackable Data Platform")
    parser.add_argument(
        "-v",
        "--version",
        help="Display application version",
        action='version',
        version='%(prog)s {version}'.format(version=__version__)
    )

    parser.add_argument(
        "-i",
        "--test_definition",
        help="Test definition file.",
        type=str,
        required=False,
        default="tests/test-definition.yaml",
    )
    parser.add_argument(
        "-t",
        "--template_dir",
        help="Folder with test templates.",
        type=str,
        required=False,
        default="tests/templates/kuttl",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Output folder for the expanded test cases.",
        type=str,
        required=False,
        default="tests/_work",
    )

    parser.add_argument(
        "-l",
        "--log_level",
        help="Set log level.",
        type=str,
        required=False,
        choices=["debug", "info"],
        default="info",
    )

    parser.add_argument(
        "-k",
        "--kuttl_test",
        help="Kuttl test suite definition file.",
        type=str,
        required=False,
        default="tests/kuttl-test.yaml.jinja2",
    )

    return parser.parse_args()


def _cli_log_level(cli_arg: str) -> int:
    if cli_arg == "debug":
        return logging.DEBUG
    else:
        return logging.INFO


def _mkdir_ignore_exists(path: str) -> None:
    try:
        logging.debug(f"Creating directory {path}")
        makedirs(path)
    except FileExistsError:
        pass


def main() -> int:
    cli_args = parse_cli_args()
    logging.basicConfig(
        encoding="utf-8", level=_cli_log_level(cli_args.log_level))
    ts = TestSuite(cli_args.test_definition)
    # Compatibility warning: add 'tests' to output_dir
    output_dir = path.join(cli_args.output_dir, "tests")
    return ts.expand(cli_args.template_dir, output_dir, cli_args.kuttl_test)


if __name__ == "__main__":
    exit(main())
