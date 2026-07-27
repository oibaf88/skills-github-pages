# Changelog

This changelog records meaningful portfolio changes. Dates describe repository milestones; deployment is verified separately.

## [2.0.0] - 2026-07-26

Status: release candidate on `codex/portfolio-v2-20260726`. The version is only confirmed live after merge, deployment and route verification.

### Added

- Employer-facing homepage narrative and consolidated visual system.
- Public evidence-linked CV at `/cv/`.
- Blog index and version notes for PsychApp, Domain Mail and Portfolio v2.
- Honest PsychApp v0.1 retrospective preserving the original 2026-06-25 post.
- `robots.txt`, `sitemap.xml`, this changelog, a security disclosure policy and a newsletter privacy notice.
- Python 3.14.6 quality gates for the backend, internal links and full Jekyll build.
- Version-controlled hardened Supabase `ev-api-proxy` Edge Function and function configuration.

### Security

- Fixed-origin HTTPS proxy targets with path-prefix allowlists.
- Rejection of protocol-relative, traversal, backslash and control-character path variants, including encoded forms.
- Manual redirect handling to prevent upstream credential forwarding.
- Request and response size limits plus upstream timeouts.
- DOM rendering with nodes and `textContent` for API and CSV-derived values.
- Exact newsletter consent, bounded inputs, compatible Supabase fields and idempotent email upsert.
- Generic internal errors while preserving normal HTTP error status codes.
- Minimal newsletter records with no browser fingerprint and duplicate-safe insertion.
- Restricted Supabase trigger-function execution and immutable function search paths.

### Removed

- GitHub Skills tutorial steps and workflows.
- Duplicate static Pages workflow and `.nojekyll` conflict.
- Archived Markdown 404 page and three embedded-source 404 artifacts.
- Duplicate `signup.html`, obsolete Render/Fly email notes and the archived email-system template.
- Unpublished duplicate email-system post source.

### Retained deliberately

- Existing historical blog posts without rewriting their original claims or dates.
