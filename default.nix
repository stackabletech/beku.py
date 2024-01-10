{ pkgs ? import <nixpkgs> {} }:

{
  beku = pkgs.callPackage ./beku.nix {};
}
