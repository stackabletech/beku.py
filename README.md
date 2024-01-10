# beku

Version: 0.0.9

## Installation

We recommend to use [pipx](https://pypa.github.io/pipx/):

```sh
pipx install beku-stackabletech
```

But you can also use `pip`:

```sh
# from PyPI
pip install beku-stackabletech
# from GitHub
pip install git+https://github.com/stackabletech/beku.py.git@master
```

Or via Nix:

```nix
{ lib, pkgs, ... }:
with lib;
let
  beku = (import (pkgs.fetchFromGitHub {
    owner = "stackabletech";
    repo = "beku.py";
    rev = "062defa4da2ec504c38d3a21916e871fd95d03f6"; # commit hash
    hash = "sha256-Oq8BhByYDptD84551Rodi6T7MwI8e/6dxIX7p0xNK+A="; # use lib.fakeHash to find new hashes when upgrading
  }) {}).beku;
in
{
  packages = with pkgs; [
    beku
    # ...
  ];

  // ...
}
```

## Usage

```sh
cd <stackable operator directory>
rm -rf tests/_work && beku
cd tests/_work && kubectl kuttl test
```

Also see the `examples` folder.

## Description

Fast Kuttl tests expander for Stackable integration tests.

```sh
beku -i tests/test-definition.yaml -t tests/templates/kuttl -k tests/kuttl-test.yaml.jinja2 -o tests/_work
```

## Release a new version

Update the version in:

* `pyproject.toml`
* `version.py`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

```sh
rm -rf dist/
python -m build --wheel .
twine upload dist/*
```
