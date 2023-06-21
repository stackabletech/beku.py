# beku

Version: 0.0.6

## Installation

    pip install git+https://github.com/stackabletech/beku.py.git@0.0.6

## Usage

    cd <stackable operator directory>
    rm -rf tests/_work && beku
    cd tests/_work && kubectl kuttl test

## Description

Fast Kuttl tests expander for Stackable integration tests.

    beku -i tests/test-definition.yaml -t tests/templates/kuttl -k tests/kuttl-test.yaml.jinja2 -o tests/_work

## Release a new version

Update the version in:

* `pyptoject.toml`
* `version.py`
* `README.md`

Update the CHANGELOG.
Commit and tag.
Build and publish:
    rm -rf dist/
    python -m build --wheel .
    twine upload dist/*
