{
  description = "fleet monitoring";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (system:
  let
    pkgs = nixpkgs.legacyPackages.${system};
    python_packages = with pkgs; [
      (
        python311.withPackages(
          ps: with ps; [
            colorama
          ]
        )
      )
    ];
    system_packages = with pkgs; [
      # optional system packages
    ];
  in {
    #defaultPackage = packages.fleet;
    devShells.default = pkgs.mkShell rec {
      packages = system_packages ++ python_packages;

      # Environment variables
      FLEET_MACHINES="cosmo dale marten may pintsize";
      FLEET_REPO_URL="https://gitlab.com/api/v4/projects/OleMussmann%2Fnixos/repository/commits";
      FLEET_PAT_TOKEN="";
    };
  });
}
