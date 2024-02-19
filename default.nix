{ pkgs ? import <nixpkgs> { } }:

pkgs.python3Packages.buildPythonPackage rec {
  pname = "sqlite-integrated";
  version = "0.0.6";
  src = ./.;
  doCheck = false;
  propagatedBuildInputs = [
    pkgs.python3Packages.pandas
  ];
}
