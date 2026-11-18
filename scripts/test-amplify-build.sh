#!/usr/bin/env bash
set -euo pipefail

IMAGE="${AMPLIFY_TEST_IMAGE:-public.ecr.aws/amazonlinux/amazonlinux:2023}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

command -v docker >/dev/null || { echo "test-amplify-build: docker is required" >&2; exit 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mkdir "$work/src"
git ls-files -z --cached --others --exclude-standard \
  | while IFS= read -r -d '' f; do [ -e "$f" ] && printf '%s\0' "$f"; done \
  | xargs -0 cp --parents -t "$work/src"
git -C "$work/src" init -q
git -C "$work/src" add -A
git -C "$work/src" -c user.name=test -c user.email=test@localhost commit -q -m snapshot

echo "==> local build of the same tree"
want="$(nix build --no-link --print-out-paths "git+file://$work/src#site")"
want_hash="$(nix hash path "$want")"

cat > "$work/inside.sh" <<'EOF'
set -euo pipefail
dnf install -y -q git >/dev/null
git clone -q --depth 1 file:///src /work
cd /work
[ "$(git rev-parse --is-shallow-repository)" = true ]
started=$(date +%s)
bash scripts/amplify-build.sh
echo "TOTAL_SECONDS=$(($(date +%s) - started))"
export USER="${USER:-$(id -un)}"
. "$HOME/.nix-profile/etc/profile.d/nix.sh"
fail=0
for f in $(grep -o 'href=/fonts/[^ >]*' public/index.html | sed 's|href=/||'); do
  [ -f "public/$f" ] || { echo "MISSING $f"; fail=1; }
done
[ -n "$(grep -o 'href=/fonts/' public/index.html)" ] || { echo "NO_PRELOADS"; fail=1; }
[ -f public/fonts/Hind-OFL.txt ] || { echo "MISSING fonts/Hind-OFL.txt"; fail=1; }
if ls /nix/store | grep -q google-fonts; then echo "GOOGLE_FONTS_IN_STORE"; fail=1; fi
echo "STORE_SIZE=$(du -sh /nix/store | cut -f1)"
echo "PUBLIC_HASH=$(nix hash path public)"
exit $fail
EOF

echo "==> amplify-build.sh in $IMAGE"
docker run --rm -v "$work/src:/src:ro" -v "$work/inside.sh:/inside.sh:ro" "$IMAGE" \
  bash /inside.sh | tee "$work/log"

got_hash="$(sed -n 's/^PUBLIC_HASH=//p' "$work/log")"
if [ "$got_hash" != "$want_hash" ]; then
  echo "test-amplify-build: FAIL container public/ is $got_hash, local build is $want_hash" >&2
  exit 1
fi
echo "test-amplify-build: ok, the container published the same tree as the local build ($want_hash)"
