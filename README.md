# beku

Version: 0.0.8

## Installation

We recommend to use [pipx](https://pypa.github.io/pipx/):

    pipx install beku-stackabletech

But you can also use `pip`:

    # from PyPI
    pip install beku-stackabletech
    # from GitHub
    pip install git+https://github.com/stackabletech/beku.py.git@master

## Usage

    cd <stackable operator directory>
    rm -rf tests/_work && beku
    cd tests/_work && kubectl kuttl test

Also see the `examples` folder.

## Description

Fast Kuttl tests expander for Stackable integration tests.

    beku -i tests/test-definition.yaml -t tests/templates/kuttl -k tests/kuttl-test.yaml.jinja2 -o tests/_work

## Release a new version

Update the version in:

* `pyproject.toml`
* `version.py`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

    rm -rf dist/
    python -m build --wheel .
    twine upload dist/*
