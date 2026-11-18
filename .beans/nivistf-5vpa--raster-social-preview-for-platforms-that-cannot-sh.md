---
# nivistf-5vpa
title: Raster social preview for platforms that cannot show SVG
status: todo
type: feature
created_at: 2026-11-18T15:23:02Z
updated_at: 2026-11-18T15:23:02Z
blocked_by:
    - nivistf-b93t
---

og:image and twitter:image point at social.svg. Mastodon, Discourse, Slack, LinkedIn and X show no image for an SVG preview, so a shared link to nivis.tf arrives without one.

Render the generated social.svg to a 1200x630 PNG in the Nix build with resvg and the site Hind faces, and point the sharing metadata at it with og:image:width and og:image:height. The PNG stays generated from the mark, so it cannot fall behind when the mark changes. README decision 7 records why it was SVG; this is the follow-up it invites.
