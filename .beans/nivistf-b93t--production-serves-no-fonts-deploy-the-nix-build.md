---
# nivistf-b93t
title: 'Production serves no fonts: deploy the Nix build'
status: completed
type: bug
priority: high
created_at: 2026-11-18T15:22:57Z
updated_at: 2026-11-19T11:31:00Z
openspec-link: openspec/changes/archive/2026-11-19-deploy-the-nix-build
---

https://nivis.tf/fonts/Hind-Regular.woff2 and the IBM Plex Mono faces return 404. Amplify builds with a bare Hugo, but the fonts only exist in the Nix build, so static/fonts is empty on deploy and readers get the system face.

Amplify should install Nix, run `nix build`, and publish that result, so the deployed artifact is the one `nix flake check` gated. Hind is fetched per file from the pinned google/fonts commit, because nixpkgs google-fonts is never cached (hydraPlatforms = []) and pulls the whole repository on every fresh machine.
