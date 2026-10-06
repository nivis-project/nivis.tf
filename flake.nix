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
            hugo --minify --destination "$TMPDIR/public" --cacheDir "$TMPDIR/cache"
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            cp -r "$TMPDIR/public" "$out"
            runHook postInstall
          '';
        };
      });

      checks = forAllSystems (
        pkgs:
        let
          # A check is a script under tests/checks/ run against the source tree.
          # Keeping them as scripts rather than inline Nix means a contributor
          # can run one directly, and the failure message is the script's own.
          script =
            name: deps:
            pkgs.runCommand "check-${name}" { nativeBuildInputs = deps; } ''
              cd ${self}
              bash tests/checks/${name}.sh .
              touch "$out"
            '';
        in
        {
          hugo-version-pin = pkgs.runCommand "check-hugo-version-pin" { } ''
            if [ "${pkgs.hugo.version}" != "${hugoVersion}" ]; then
              echo "nixpkgs Hugo is ${pkgs.hugo.version} but .hugo-version pins ${hugoVersion}" >&2
              echo "update .hugo-version and amplify.yml together, never one alone" >&2
              exit 1
            fi
            touch "$out"
          '';

          hugo-extended = script "hugo-extended" [ pkgs.hugo ];

          hugo-math = script "hugo-math" [ pkgs.hugo ];

          hugo-version-single-source = script "hugo-version-single-source" [ pkgs.gnugrep ];

          css-colors = script "css-colors" [ pkgs.gnugrep ];

          snippets = script "snippets" [ pkgs.python3 ];

          # Runs the formatter and compares bytes, so it needs a writable tree.
          snippets-unformatted =
            pkgs.runCommand "check-snippets-unformatted"
              {
                nativeBuildInputs = [
                  pkgs.nixfmt
                  pkgs.findutils
                  pkgs.diffutils
                ];
              }
              ''
                cp -r ${self} src && chmod -R u+w src
                bash src/tests/checks/snippets-unformatted.sh src
                touch "$out"
              '';

          tokens =
            pkgs.runCommand "check-tokens"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pkgs.python3
                ];
              }
              ''
                cp -r ${self} src && chmod -R u+w src
                bash src/tests/checks/tokens.sh src
                touch "$out"
              '';

          # The fixtures build real Hugo sites, which needs a writable tree.
          unit =
            pkgs.runCommand "check-unit"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pkgs.python3
                ];
              }
              ''
                cp -r ${self} src && chmod -R u+w src
                bash src/tests/checks/unit.sh src
                touch "$out"
              '';

          build = pkgs.runCommand "check-build" { nativeBuildInputs = [ pkgs.hugo ]; } ''
            # Hugo writes a build lock next to the source, so the read-only
            # store path has to be copied before it can be built.
            cp -r ${self} src && chmod -R u+w src && cd src
            # Hugo exits 0 on a deprecation or a missing-layout warning. The
            # site must build silent, so the warnings are the failure condition.
            hugo --minify --destination "$TMPDIR/public" --cacheDir "$TMPDIR/cache" 2>&1 | tee "$TMPDIR/log"
            if grep -qE "^(WARN|ERROR)" "$TMPDIR/log"; then
              echo "build: Hugo emitted warnings; the site must build silent" >&2
              exit 1
            fi
            touch "$out"
          '';
        }
      );

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
            # snippets/ is content, not code. Two of its files are .nix: one is
            # a fragment that is not valid Nix on its own, and the other is a
            # complete flake whose exact formatting is the approved copy. The
            # formatter rewrote both the first time it ran over them, which is
            # a silent edit to what the page shows a reader.
            find "$@" -name '*.nix' -not -path '*/.*' -not -path '*/snippets/*' -print0 \
              | xargs -0 -r nixfmt
          '';
        }
      );
    };
}
