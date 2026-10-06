---
# nivistf-4uyx
title: Deployment, README and acceptance checklist
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T15:16:04Z
parent: nivistf-wrli
blocked_by:
    - nivistf-c6h5
    - nivistf-7yhs
    - nivistf-bwlv
    - nivistf-2yto
openspec-link: openspec/changes/archive/2026-10-06-deployment-acceptance
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

## Summary of Changes

Shipped as OpenSpec change `deployment-acceptance`, capability
`release-readiness`. The last epic.

Auditing the briefing's twelve-item checklist against the gate, item by item
rather than assuming it was covered, found two things nothing verified:

- "All seven snippets render highlighted and match the files byte for byte" was
  proven for ONE fixture sample. The same words, a much weaker claim. It is
  exactly the kind of gap that survives review because a test exists and its
  name sounds right. All seven real snippets are now compared against their
  files.
- `amplify.yml` had no check at all. The gate verified the Hugo version was
  single-sourced in the repository, but nothing verified the deployment
  configuration actually read it, published `public`, or built with --minify.

The checklist is now executable and, more importantly, cannot drift from the
gate. Each item names the check that proves it, and `release` asserts that check
exists in flake.nix. Deleting `separation` makes the checklist item "no copy in
layouts" report as unproven, rather than the list quietly describing a gate that
no longer matches it. Without that, a checklist is a document that slowly stops
being true, and the failure is silent: somebody consults it to decide whether a
concern is covered and is told yes by a list nobody reconciled.

One item stays manual and is printed as outstanding on every pass rather than
counted as done: whether the README explains things clearly. A person has to
judge that; counting it because the check passed would be the same dishonesty
this project has had to correct several times.

Five probes: an altered snippet, a wrong published directory, a hardcoded
version, a version source that was only a comment, and a removed check. The
fourth exposed a weakness in the check itself: it matched `.hugo-version`
anywhere in the file, including in the comment explaining the rule, so a config
that mentioned the file while hardcoding a version would have passed. It now
requires a command that reads it.
