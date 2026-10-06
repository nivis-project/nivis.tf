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

      # The design uses four Hind weights and two IBM Plex Mono weights, and no
      # others. Both typefaces are packaged in nixpkgs as TrueType, so the build
      # converts them to woff2 rather than the repository carrying binaries:
      # a font update becomes a lock bump, and licences stay tracked by nixpkgs.
      # Listing the weights explicitly means adding one is a decision somebody
      # makes, not a side effect of a package update.
      fontFaces = [
        {
          family = "Hind";
          weight = 300;
          file = "Hind-Light";
        }
        {
          family = "Hind";
          weight = 400;
          file = "Hind-Regular";
        }
        {
          family = "Hind";
          weight = 500;
          file = "Hind-Medium";
        }
        {
          family = "Hind";
          weight = 600;
          file = "Hind-SemiBold";
        }
        {
          family = "IBM Plex Mono";
          weight = 400;
          file = "IBMPlexMono-Regular";
        }
        {
          family = "IBM Plex Mono";
          weight = 500;
          file = "IBMPlexMono-Medium";
        }
      ];

      siteFonts =
        pkgs:
        pkgs.runCommand "nivis-tf-fonts" { nativeBuildInputs = [ pkgs.woff2 ]; } (
          ''
            mkdir -p "$out"
          ''
          + nixpkgs.lib.concatMapStrings (f: ''
            src=""
            for d in ${pkgs.google-fonts}/share/fonts/truetype ${pkgs.ibm-plex}/share/fonts/truetype; do
              if [ -f "$d/${f.file}.ttf" ]; then src="$d/${f.file}.ttf"; fi
            done
            if [ -z "$src" ]; then
              echo "font ${f.file}.ttf not found in google-fonts or ibm-plex" >&2
              exit 1
            fi
            cp "$src" "$TMPDIR/${f.file}.ttf"
            woff2_compress "$TMPDIR/${f.file}.ttf"
            cp "$TMPDIR/${f.file}.woff2" "$out/${f.file}.woff2"
          '') fontFaces
        );

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
            (pkgs.python3.withPackages (ps: [ ps.pyyaml ]))
            pkgs.jujutsu
            pkgs.git
            pkgs.nixfmt
          ];

          PLAYWRIGHT_BROWSERS_PATH = pkgs.playwright-driver.browsers;
          PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";

          shellHook = ''
            # static/fonts is generated and gitignored; see the css-pipeline
            # change. Without this, `hugo server` falls back to the system face.
            mkdir -p static/fonts
            cp -f ${siteFonts pkgs}/*.woff2 static/fonts/ 2>/dev/null || true
            chmod u+w static/fonts/*.woff2 2>/dev/null || true
            if [ "$(hugo version | sed -n 's/.*v\([0-9.]*\).*/\1/p')" != "${hugoVersion}" ]; then
              echo "warning: dev shell Hugo is not ${hugoVersion}, the version pinned in .hugo-version" >&2
            fi
          '';
        };
      });

      packages = forAllSystems (pkgs: {
        default = self.packages.${pkgs.stdenv.hostPlatform.system}.site;

        fonts = siteFonts pkgs;

        site = pkgs.stdenv.mkDerivation {
          pname = "nivis-tf-site";
          version = "0.1.0";
          src = self;
          nativeBuildInputs = [ pkgs.hugo ];
          buildPhase = ''
            runHook preBuild
            # Fonts are built from nixpkgs rather than committed, so they are
            # staged into static/ just before the build. See the css-pipeline
            # change's design note.
            mkdir -p static/fonts
            cp ${siteFonts pkgs}/*.woff2 static/fonts/
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
          # PyYAML is needed by the checks that compare the page against the
          # data files, so the environment is defined once rather than per check.
          pythonEnv = pkgs.python3.withPackages (ps: [ ps.pyyaml ]);

          # Fonts are built from nixpkgs rather than committed, so anything that
          # builds the site has to stage them first. One place, so a new check
          # cannot forget and silently test a fontless page.
          stageSrc = ''
            cp -r ${self} src && chmod -R u+w src
            mkdir -p src/static/fonts
            cp ${siteFonts pkgs}/*.woff2 src/static/fonts/
          '';

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

          snippets = script "snippets" [ pythonEnv ];

          theming =
            pkgs.runCommand "check-theming"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/theming.sh src
                touch "$out"
              '';

          syntax =
            pkgs.runCommand "check-syntax"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/syntax.sh src
                touch "$out"
              '';

          # Replays the briefing's acceptance criterion literally: it really
          # adds a project, rebuilds, and diffs layouts/ and assets/.
          acceptance =
            pkgs.runCommand "check-acceptance"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                  pkgs.diffutils
                  pkgs.gnugrep
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/acceptance.sh src
                touch "$out"
              '';

          sections =
            pkgs.runCommand "check-sections"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/sections.sh src
                touch "$out"
              '';

          page-chrome =
            pkgs.runCommand "check-page-chrome"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/page-chrome.sh src
                touch "$out"
              '';

          assets =
            pkgs.runCommand "check-assets"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                  pkgs.gnugrep
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/assets.sh src
                touch "$out"
              '';

          mark =
            pkgs.runCommand "check-mark"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                  pkgs.gnugrep
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/mark.sh src
                touch "$out"
              '';

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
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/tokens.sh src
                touch "$out"
              '';

          # The fixtures build real Hugo sites, which needs a writable tree.
          unit =
            pkgs.runCommand "check-unit"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/unit.sh src
                touch "$out"
              '';

          build = pkgs.runCommand "check-build" { nativeBuildInputs = [ pkgs.hugo ]; } ''
            # Hugo writes a build lock next to the source, so the read-only
            # store path has to be copied before it can be built.
            ${stageSrc}
            cd src
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
