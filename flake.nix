{
  description = "nivis.tf, the public website for the Nivis project";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      hugoVersion = nixpkgs.lib.fileContents ./.hugo-version;
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.hugo
            pkgs.nodejs
            pkgs.playwright-driver
            pkgs.lychee
            pkgs.python3
            pkgs.jujutsu
            pkgs.git
            pkgs.nixfmt
          ];

          PLAYWRIGHT_BROWSERS_PATH = pkgs.playwright-driver.browsers;
          PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";

          shellHook = ''
            if [ "$(hugo version | sed -n 's/.*v\([0-9.]*\).*/\1/p')" != "${hugoVersion}" ]; then
              echo "warning: dev shell Hugo is not ${hugoVersion}, the version pinned in .hugo-version" >&2
            fi
          '';
        };
      });

      packages = forAllSystems (pkgs: {
        default = self.packages.${pkgs.stdenv.hostPlatform.system}.site;

        site = pkgs.stdenv.mkDerivation {
          pname = "nivis-tf-site";
          version = "0.1.0";
          src = self;
          nativeBuildInputs = [ pkgs.hugo ];
          buildPhase = ''
            runHook preBuild
            hugo --minify --destination "$TMPDIR/public"
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            cp -r "$TMPDIR/public" "$out"
            runHook postInstall
          '';
        };
      });

      checks = forAllSystems (pkgs: {
        hugo-version-pin = pkgs.runCommand "hugo-version-pin" { } ''
          if [ "${pkgs.hugo.version}" != "${hugoVersion}" ]; then
            echo "nixpkgs Hugo is ${pkgs.hugo.version} but .hugo-version pins ${hugoVersion}" >&2
            echo "update .hugo-version and amplify.yml together, never one alone" >&2
            exit 1
          fi
          touch "$out"
        '';
      });

      formatter = forAllSystems (
        pkgs:
        pkgs.writeShellApplication {
          name = "fmt";
          runtimeInputs = [
            pkgs.nixfmt
            pkgs.findutils
          ];
          text = ''
            if [ "$#" -eq 0 ]; then
              set -- .
            fi
            find "$@" -name '*.nix' -not -path '*/.*' -print0 | xargs -0 -r nixfmt
          '';
        }
      );
    };
}
