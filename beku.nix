{ python3 }:
with python3;
let
  manifest = (pkgs.lib.importTOML ./pyproject.toml).project;
in
pkgs.buildPythonApplication {
  pname = manifest.name;
  version = manifest.version;

  format = "pyproject";

  src = builtins.path {
    path = ./.;
    name = manifest.name;
  };

  nativeBuildInputs = with pkgs; [
    setuptools
  ];

  propagatedBuildInputs = with pkgs; [
    jinja2
    pyyaml
  ];
}

