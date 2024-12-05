# beku

Version: 0.0.11-rc1

Fast [Kuttl](https://kuttl.dev/) tests expander for Stackable integration tests.

```sh
beku -i tests/test-definition.yaml -t tests/templates/kuttl -k tests/kuttl-test.yaml.jinja2 -o tests/_work
```

`beku` parses a test definition YAML file together with a directory of templated Kuttl test definitions.
From this it generates Kuttl test suites which can then be run with plain Kuttl.
This was built on top of Kuttl to support running tests with different version combinations of products, or slightly different features enabled,
without having to duplicate tests.

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
pip install git+https://github.com/stackabletech/beku.py.git@main
```

Or via NixOS and Nix Shell:

```nix
{ lib, pkgs, ... }:
with lib;
let
  beku = pkgs.callPackage(pkgs.fetchFromGitHub {
    owner = "stackabletech";
    repo = "beku.py";
    rev = "145e8210f5786b8128e3af43f60b61f065cc2c39";
    hash = "sha256-hLaIY4BE+VIMeKmS3JLOZy87OC2VuQtbX/NCIbQr2p4="; # use lib.fakeHash to find new hashes when upgrading
  } + "/beku.nix") {};
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

## Release a new version

Update the version in:

* `src/beku/version.py`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

```sh
rm -rf dist/
python -m build --sdist --wheel .
twine upload dist/*
```
