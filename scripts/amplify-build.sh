#!/usr/bin/env bash
set -euo pipefail

NIX_VERSION="2.35.6"
NIX_INSTALLER_SHA256="6f7bf206efb54cd4941fb274930dbc74fdfc16fcb06757ef261c8d7d69cfd60e"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

as_root() {
  if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi
}

declare -A PACKAGE=([curl]=curl [git]=git [tar]=tar [xz]=xz [sha256sum]=coreutils [find]=findutils)

missing_tools() {
  missing=()
  for tool in curl git tar xz sha256sum find; do
    command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
  done
}

missing_tools
if [ "${#missing[@]}" -gt 0 ] && command -v dnf >/dev/null 2>&1; then
  packages=()
  for tool in "${missing[@]}"; do packages+=("${PACKAGE[$tool]}"); done
  echo "amplify-build: installing ${packages[*]} for ${missing[*]}"
  as_root dnf install -y -q "${packages[@]}" >/dev/null
  missing_tools
fi
if [ "${#missing[@]}" -gt 0 ]; then
  echo "amplify-build: missing tools: ${missing[*]}" >&2
  exit 1
fi

export USER="${USER:-$(id -un)}"

if ! command -v nix >/dev/null 2>&1 && [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
  . "$HOME/.nix-profile/etc/profile.d/nix.sh"
fi

if ! command -v nix >/dev/null 2>&1; then
  started=$(date +%s)
  as_root mkdir -p -m 0755 /nix /etc/nix
  as_root chown "$(id -u)" /nix
  printf 'experimental-features = nix-command flakes\nbuild-users-group =\n' | as_root tee /etc/nix/nix.conf >/dev/null
  installer="$(mktemp)"
  curl -sSfL "https://releases.nixos.org/nix/nix-${NIX_VERSION}/install" -o "$installer"
  echo "${NIX_INSTALLER_SHA256}  ${installer}" | sha256sum -c --quiet -
  sh "$installer" --no-daemon --yes
  rm -f "$installer"
  . "$HOME/.nix-profile/etc/profile.d/nix.sh"
  echo "amplify-build: installed Nix ${NIX_VERSION} in $(($(date +%s) - started))s"
fi

started=$(date +%s)
out="$(nix --extra-experimental-features 'nix-command flakes' build \
  --no-link --print-out-paths --print-build-logs \
  "git+file://${ROOT}?shallow=1#site")"
echo "amplify-build: built ${out} in $(($(date +%s) - started))s"

rm -rf public
cp -rL "$out" public
chmod -R u+w public
echo "amplify-build: published $(find public -type f | wc -l) files to public/"
