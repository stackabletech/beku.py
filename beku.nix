{ python3 }:

let
  manifest = (python3.pkgs.lib.importTOML ./pyproject.toml).project;
in
python3.pkgs.buildPythonApplication {
  pname = manifest.name;
  version = manifest.version;

  format = "pyproject";

  src = builtins.path {
    path = ./.;
    name = manifest.name;
  };

  nativeBuildInputs = [
    python3.pkgs.setuptools
  ];

  propagatedBuildInputs = [
    python3.pkgs.jinja2
    python3.pkgs.pyyaml
  ];
}

