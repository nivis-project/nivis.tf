---
# nivistf-4uyx
title: Deployment, README and acceptance checklist
status: in-progress
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T15:02:52Z
parent: nivistf-wrli
blocked_by:
    - nivistf-c6h5
    - nivistf-7yhs
    - nivistf-bwlv
    - nivistf-2yto
---

## Scope

- `amplify.yml` with `baseDirectory: public` and the Hugo version pinned to the
  same single source the dev shell reads.
- `README.md`: how to run locally, where content lives, where tokens live, how
  to add a section, how to add a project.
- Work through the acceptance checklist in section 11 of the briefing and
  record the result.
- Collect the open points from section 12 of the briefing into the pull request
  description. Do not decide them.

## Open points for the maintainer

1. Verify the code samples and the comparison table against the repositories.
2. Confirm hosting. Amplify is assumed because the domain shows an Amplify
   placeholder.
3. Confirm the colored mark versus the original grey `#4d4d4d` logo.
4. Confirm or replace the per-project mark parameters.
5. Whether the site should grow beyond one page. The structure allows it and
   does not build it.

## Done when

- [ ] Every box in the briefing's acceptance checklist is ticked or has a
      recorded reason
- [ ] `amplify.yml` builds with the pinned Hugo and publishes `public/`
- [ ] The README answers all five questions above
- [ ] The open points are written up for the maintainer

## Briefing

Sections 2, 11 and 12.
