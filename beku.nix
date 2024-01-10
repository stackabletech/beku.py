{ python3 }:

python3.pkgs.buildPythonApplication {
  pname = "beku-stackabletech";
  version = "0.0.9";

  format = "pyproject";

  src = builtins.path {
    path = ./.;
    name = "beku-stackabletech";
  };

  nativeBuildInputs = [
    python3.pkgs.setuptools
  ];

  propagatedBuildInputs = [
    python3.pkgs.jinja2
    python3.pkgs.pyyaml
  ];
}

