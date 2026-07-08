"""Main entry point."""

import logging
from argparse import ArgumentParser, Namespace
from os import path
from shutil import rmtree

from beku.kuttl import renderer_from_file, expand
from .version import __version__


def parse_cli_args() -> Namespace:
    """Parse command line args."""
    parser = ArgumentParser(description="Kuttl test expander for the Stackable Data Platform")
    parser.add_argument(
        "-v", "--version", help="Display application version", action="version", version=f"%(prog)s {__version__}"
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

    parser.add_argument(
        "-c",
        "--common_dir",
        help="Folder with common test step templates/files that are rendered into EVERY generated "
        "test case (in addition to the test's own steps). Lets shared steps such as a teardown live "
        "in a single place instead of being copied into each test. Defaults to a 'commons' folder "
        "next to the test templates (i.e. <template_dir>/commons); skipped if that folder does not "
        "exist, so this is a no-op unless you create it.",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-s",
        "--suite",
        help="Name of the test suite to expand. Default: default",
        type=str,
        required=False,
        default="default",
    )

    parser.add_argument(
        "-n",
        "--namespace",
        help="Name of the namespace to use for tests. Default: kuttl-<test name sha256>",
        type=str,
        required=False,
    )

    return parser.parse_args()


def _cli_log_level(cli_arg: str) -> int:
    if cli_arg == "debug":
        return logging.DEBUG
    return logging.INFO


def main() -> int:
    """Main"""
    cli_args = parse_cli_args()
    logging.basicConfig(encoding="utf-8", level=_cli_log_level(cli_args.log_level))
    effective_test_suites = renderer_from_file(cli_args.test_definition)
    rmtree(path=cli_args.output_dir, ignore_errors=True)
    # Compatibility warning: add 'tests' to output_dir
    output_dir = path.join(cli_args.output_dir, "tests")
    # Default the common steps directory to a 'commons' folder next to the test templates. It is
    # rendered into every test case if present, and silently skipped otherwise (so this stays a no-op
    # for repositories that don't opt in by creating it).
    common_dir = cli_args.common_dir if cli_args.common_dir is not None else path.join(cli_args.template_dir, "commons")
    return expand(
        cli_args.suite,
        effective_test_suites,
        cli_args.template_dir,
        output_dir,
        cli_args.kuttl_test,
        cli_args.namespace,
        common_dir,
    )
