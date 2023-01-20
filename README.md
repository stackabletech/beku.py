# beku

## Installation

    pip install beku-stackabletech

## Usage

    cd <stackable operator directory>
    rm -rf tests/_work && beku
    cd tests/_work && kubectl kuttl test

## Description

Fast Kuttl tests expander for Stackable integration tests.

    beku -i tests/test-definition.yaml -t tests/templates/kuttl -k tests/kuttl-test.yaml.jinja2 -o tests/_work

## Build

    python -m build --sdist --wheel .
    twine upload dist/*

