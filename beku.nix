{ python3, pkgs }:
let
  # I wish there was a better way. If the command fails, it is very hard to see 
  # that the problem is here. Perhaps there is some way to evaluate it in python
  # and reference __version__ directly?
  version = builtins.readFile (pkgs.runCommand "foo" { src = [ ./src ]; } ''
    grep -E '^__version__' $src/beku/version.py | grep -o '".*"' | tr -d \" > $out
  '');
  manifest = (pkgs.lib.importTOML ./pyproject.toml).project;
in
python3.pkgs.buildPythonApplication {
  pname = manifest.name;
  # The version is no longer set in pyproject.toml, so we have to jump through
  # hoops to extract it from a python script.
  # version = manifest.version;
  inherit version;

  format = "pyproject";

  src = builtins.path {
    path = ./.;
    name = manifest.name;
  };

  nativeBuildInputs = with python3.pkgs; [
    setuptools
  ];

  propagatedBuildInputs = with python3.pkgs; [
    jinja2
    pyyaml
  ];
}


