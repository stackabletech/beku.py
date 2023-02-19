"""Main entry point."""
from argparse import ArgumentParser, Namespace
from os import path
import logging
from .version import __version__
from .testsuite import TestSuite


def parse_cli_args() -> Namespace:
    """Parse command line args."""
    parser = ArgumentParser(
        description="Kuttl test expander for the Stackable Data Platform")
    parser.add_argument(
        "-v",
        "--version",
        help="Display application version",
        action='version',
        version=f'%(prog)s {__version__}'
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
    return logging.INFO


def main() -> int:
    """Main"""
    cli_args = parse_cli_args()
    logging.basicConfig(
        encoding="utf-8", level=_cli_log_level(cli_args.log_level))
    test_suite = TestSuite(cli_args.test_definition)
    # Compatibility warning: add 'tests' to output_dir
    output_dir = path.join(cli_args.output_dir, "tests")
    return test_suite.expand(cli_args.template_dir, output_dir, cli_args.kuttl_test)
