{
  description = "fleet monitoring";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (system:
  let
    my_name = "fleet";
    my_version = "0.0.1";
    py = with pkgs; python311;
    pypkgs = with pkgs; python311Packages;
    pkgs = nixpkgs.legacyPackages.${system};
    python_packages = with pkgs; [
      (
        py.withPackages(
          ps: with ps; [
            colorama
          ]
        )
      )
    ];
    system_packages = with pkgs; [
      # optional system packages
    ];
  in rec {
    devShells.default = pkgs.mkShell rec {
      packages = system_packages ++ python_packages;

      # Environment variables
      FLEET_MACHINES="cosmo dale bubbles may pintsize";
      FLEET_REPO_URL="https://gitlab.com/api/v4/projects/OleMussmann%2Fnixos/repository/commits";
      FLEET_PAT_TOKEN="";
    };
    defaultPackage = packages.fleet;
    packages.default = with pypkgs; buildPythonPackage {
      name = my_name;
      version = my_version;
      src = ./.;
      propagatedBuildInputs = python_packages;
    };
    apps.default = { type = "app"; program = "${self.packages."${system}".default}/bin/fleet.py"; };
  });
}
