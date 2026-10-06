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
      # Weight 300 is deliberately absent. The design names it, but no element
      # applies font-weight: 300, so the browser never requests Hind-Light and
      # it was 90 KB of deploy weight nothing used. Add it back when something
      # actually sets that weight.
      fontFaces = [
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

      # axe-core is not packaged in nixpkgs. Fetched as a fixed-output
      # derivation with a pinned hash, which is exactly how nixpkgs fetches
      # every other source: reproducible, and network only on a machine that
      # has never built it. Browsers still come from nixpkgs and are never
      # downloaded at test time.
      axeCore =
        pkgs:
        pkgs.fetchurl {
          url = "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js";
          sha256 = "1qvmggpdja8qdq3rklafxg1d8dyvnrk3nwni595nziq1xjfws4dm";
        };

      # Hind is an Indic typeface: 1006 glyphs for 434 codepoints, most of the
      # excess being Devanagari conjuncts an English site never renders. Full
      # Hind Regular is 97 KB as woff2; subset to the ranges below it is 16 KB.
      #
      # The ranges are explicit rather than "Latin", because the page uses a
      # Greek theta in the mark formula and a rightwards arrow in the comparison
      # table. A naive Latin-1 subset drops both, and the failure is silent: the
      # text renders from a fallback face or as a notdef box. tests/checks/
      # font-coverage.py asserts every character the page renders is covered.
      fontSubset = builtins.concatStringsSep "," [
        "U+0000-00FF" # Latin-1, including the middle dot
        "U+0100-017F" # Latin Extended-A
        "U+0370-03FF" # Greek, for the theta in the mark formula
        "U+2000-206F" # General punctuation, including the ellipsis
        "U+2070-209F" # Super- and subscripts
        "U+20A0-20BF" # Currency
        "U+2100-214F" # Letterlike
        "U+2190-21FF" # Arrows, including the one in the comparison table
        "U+2200-22FF" # Mathematical operators
        "U+FEFF"
        "U+FFFD"
      ];

      siteFonts =
        pkgs:
        pkgs.runCommand "nivis-tf-fonts"
          {
            nativeBuildInputs = [
              pkgs.woff2
              (pkgs.python3.withPackages (ps: [
                ps.fonttools
                ps.brotli
              ]))
            ];
          }
          (
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
              pyftsubset "$src" \
                --unicodes='${fontSubset}' \
                --layout-features='kern,liga,calt' \
                --output-file="$TMPDIR/${f.file}.ttf"
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
          pythonEnv = pkgs.python3.withPackages (ps: [
            ps.pyyaml
            ps.fonttools
            ps.brotli
          ]);

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

          # The briefing's acceptance checklist, executable. Also fails if a
          # checklist item names a check that no longer exists, so the list
          # cannot drift away from the gate.
          release =
            pkgs.runCommand "check-release"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/release.sh src
                touch "$out"
              '';

          html =
            pkgs.runCommand "check-html"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pkgs.html5validator
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/html.sh src
                touch "$out"
              '';

          links =
            pkgs.runCommand "check-links"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/links.sh src
                touch "$out"
              '';

          # The project's one hard architectural rule, enforced.
          separation =
            pkgs.runCommand "check-separation"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/separation.sh src
                touch "$out"
              '';

          font-coverage =
            pkgs.runCommand "check-font-coverage"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                # The SOURCE fonts, so the check can tell a subset regression
                # from a glyph the typeface never had.
                mkdir -p "$TMPDIR/sources"
                cp ${pkgs.google-fonts}/share/fonts/truetype/Hind-*.ttf "$TMPDIR/sources/" || true
                cp ${pkgs.ibm-plex}/share/fonts/truetype/IBMPlexMono-*.ttf "$TMPDIR/sources/" || true
                export FONT_SOURCES="$TMPDIR/sources"
                ${stageSrc}
                bash src/tests/checks/font-coverage.sh src
                touch "$out"
              '';

          metadata =
            pkgs.runCommand "check-metadata"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pythonEnv
                ];
              }
              ''
                ${stageSrc}
                bash src/tests/checks/metadata.sh src
                touch "$out"
              '';

          contrast = script "contrast" [ pythonEnv ];

          warm-is-a-fill = script "warm-is-a-fill" [ pkgs.gnugrep ];

          # The browser suite. Browsers come from nixpkgs through
          # PLAYWRIGHT_BROWSERS_PATH and are never downloaded at test time.
          e2e =
            pkgs.runCommand "check-e2e"
              {
                nativeBuildInputs = [
                  pkgs.hugo
                  pkgs.playwright-test
                  pythonEnv
                ];
                PLAYWRIGHT_BROWSERS_PATH = pkgs.playwright-driver.browsers;
                PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";
                AXE_PATH = axeCore pkgs;
                # The e2e suite identifies a palette by comparing the resolved
                # --ground against these, rather than guessing from a serialised
                # colour string. Taken from data/tokens.yaml so there is still
                # one source.
                TOKENS_JSON = builtins.toJSON {
                  ground = {
                    light = "oklch(0.975 0.008 275)";
                    dark = "oklch(0.17 0.03 275)";
                  };
                };
              }
              ''
                ${stageSrc}
                cd src
                # --minify, because that is what amplify.yml deploys. Testing
                # the unminified page means testing an artifact nobody serves.
                hugo --minify --destination "$TMPDIR/public" --cacheDir "$TMPDIR/cache" \
                  --environment production > "$TMPDIR/build.log" 2>&1 \
                  || { cat "$TMPDIR/build.log" >&2; exit 1; }
                export SITE_DIR="$TMPDIR/public"
                export HOME="$TMPDIR"
                playwright test --config tests/e2e/playwright.config.js
                touch "$out"
              '';

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

      # Resolving URLs needs the network, so this cannot be a flake check. Run it
      # before a release. Pretending a sandboxed check proves a URL is reachable
      # would be the dishonest option, so the two are separate on purpose.
      apps = forAllSystems (pkgs: {
        check-links-live = {
          type = "app";
          program = toString (
            pkgs.writeShellScript "check-links-live" ''
              set -euo pipefail
              out=$(mktemp -d)
              trap 'rm -rf "$out"' EXIT
              ${pkgs.hugo}/bin/hugo --minify --destination "$out/public" --environment production >/dev/null
              echo "==> resolving every link in the built site"
              ${pkgs.lychee}/bin/lychee --no-progress --include-fragments "$out/public"
            ''
          );
        };
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
