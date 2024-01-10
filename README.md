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

<details>
<summary>NixOs</summary>

```nix
{ lib, pkgs, ... }:
with lib;
let
  beku = (import (pkgs.fetchFromGitHub {
    owner = "stackabletech";
    repo = "beku.py";
    rev = "145e8210f5786b8128e3af43f60b61f065cc2c39";
    hash = "sha256-hLaIY4BE+VIMeKmS3JLOZy87OC2VuQtbX/NCIbQr2p4="; # use lib.fakeHash to find new hashes when upgrading
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

</details>

<details>
<summary>Nix Shell</summary>

```nix
let
  beku = pkgs.callPackage (pkgs.fetchFromGitHub {
    owner = "stackabletech";
    repo = "beku.py";
    rev = "145e8210f5786b8128e3af43f60b61f065cc2c39";
    hash = "sha256-hLaIY4BE+VIMeKmS3JLOZy87OC2VuQtbX/NCIbQr2p4="; # use lib.fakeHash to find new hashes when upgrading
  } + "/beku.nix") {};
in pkgs.mkShell {
  buildInputs = with pkgs; [
    beku
    # ...
  ];

  # ...
}
```

</details>

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
