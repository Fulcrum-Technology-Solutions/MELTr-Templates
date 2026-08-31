# MELTr-Templates (community content repo)

**Date:** 2026-08-31  
**Status:** Approved (brainstorming)  
**Repo:** MELTr-Templates  
**Source snapshot:** LogForge-Templates (one-time copy, no git history)  
**Companion:** `MELTr-Templates-UI/docs/superpowers/specs/2026-08-31-meltr-templates-ui-design.md`

## Goal

MELTr-Templates is the only living source of truth for community Jinja2 templates and metadata. After this lands, LogForge-Templates is deleted.

## Decisions (locked)

| Decision | Choice |
|----------|--------|
| Git | Copy current tree into this repo (fresh history). Do not push LogForge-Templates history. |
| LogForge-Templates after | Delete the GitHub repo (human step after merge). |
| Rebrand depth | Full catch: product strings, package extension, schema `$id`, docs, CI. Schema **keys** and 4-tier paths unchanged. |
| Package extension | `.mtb` (gzipped tar, same layout as old `.forge`). |
| Collection versions | Do **not** bump. Rebrand is not a template release. |
| Maintainer placeholders | `LogForge Community` / `LogForge Templates` + `@logforge.*` → `John Owen` / `jowen@ftsc.com`. Existing human rows and `examples/acme` (`Jane Example`) stay. |
| Schema `$id` | `https://meltr.ftsc.cloud/schemas/{file}` (identifier; serving the URL is Templates-UI). |
| Process | Mechanical string pass, then manual review of remaining hits, then CI string gate. |
| `.j2` files | Untouched unless a search hit. |

## Out of scope

- Git history from LogForge-Templates
- Schema key/shape changes (vendor / product / data_source / etc.)
- Collection version bumps
- Building `.mtb` tarballs (Templates-UI download endpoints)
- MELTr OSS `extract_forge_package` / `.forge` → `.mtb` (companion PR; same ship window)
- Templates-UI rebrand, Vercel/Supabase, DNS
- Deleting `Fulcrum-Technology-Solutions/LogForge-Templates` on GitHub (you do this after the copy is merged and confirmed)

## Approach

Copy LogForge-Templates into this empty repo (exclude `.git`). Mechanical replace by identifier class. Manual second pass. Add a CI string gate. Keep `python .github/scripts/validate_templates.py` as the schema/layout check.

Do not rewrite README/CONTRIBUTING from scratch. Do not keep LogForge-Templates as upstream.

## Identifier map

| Class | From | To |
|-------|------|----|
| Product name | LogForge / LogForge Templates | MELTr / MELTr Templates |
| CLI / pip | `logforge`, `pip install logforge` | `meltr`, `pip install meltr` |
| Engine repo | `Fulcrum-Technology-Solutions/LogForge` | `Fulcrum-Technology-Solutions/MELTr` |
| Registry UI repo | `LogForge-Templates-UI` | `MELTr-Templates-UI` |
| Registry host | `logforge.io` | `meltr.ftsc.cloud` |
| Schema `$id` | `https://logforge.dev/schemas/{file}` | `https://meltr.ftsc.cloud/schemas/{file}` |
| Package extension | `.forge` | `.mtb` |
| Maintainer placeholders | LogForge Community / LogForge Templates + `@logforge.*` | John Owen / jowen@ftsc.com |
| Humans already correct | John Owen / jowen@ftsc.com | leave |
| Example fixture | Jane Example / jane@example.com | leave |
| 4-tier paths, schema keys | — | unchanged |

No “formerly LogForge” leftover copy.

## Two-pass process

**Pass 1 (mechanical)**  
`rg -i 'logforge|\.forge'` over the copied tree. Replace by class above.

**Pass 2 (manual)**  
Review every remaining hit. Typical leftovers: `TEMPLATES.yaml` descriptions, GitHub issue/PR templates, workflow display names, `entities/` comments, `documentation.resources` inside `.meta.yaml`.

**CI gate (after pass 2)**  
Fail CI on `logforge` / `LogForge` / `LOGFORGE` / `.forge` except the gate script and this spec (under `docs/superpowers/`). Empty allowlist.

## What stays

- 4-tier hierarchy (`vendor/product/data_source/event_type`)
- JSON schemas’ property names and validation rules
- `vendor.yaml` inside vendor packages (built by Templates-UI)
- Collection `version` values from the snapshot
- Validation entrypoint: `python .github/scripts/validate_templates.py`

## Package format

`.mtb` is a gzipped tar of a vendor tree (same contents as `.forge`). Document that in README. This repo does not emit the file; the registry does.

Hard cut: no `.forge` accept-path in docs or examples.

## Same-window companions (not this repo)

If these lag, `meltr templates install` against the new registry will mismatch extensions.

| Repo | Change |
|------|--------|
| MELTr OSS | `.forge` → `.mtb`; rename `extract_forge_package` and related identifiers |
| MELTr-Templates-UI | Download `Content-Disposition` filename `*.mtb`; sync `GITHUB_REPO_NAME=MELTr-Templates` |

No dual-extension compatibility.

## Acceptance criteria

1. Tree is a copy of current LogForge-Templates (minus `.git`), then rebranded per the identifier map.
2. `rg -i 'logforge|\.forge'` over the repo excluding `docs/superpowers/` and the string-gate script returns **no** hits.
3. String-gate CI job fails the PR if those strings return.
4. `python .github/scripts/validate_templates.py` exits 0. Collection `version` fields match the snapshot.
5. README, CONTRIBUTING, AGENTS related-repos point at MELTr, MELTr-Templates-UI, and `meltr.ftsc.cloud`. CLI examples use `meltr`.
6. Package-format docs describe `.mtb` as gzipped tar.

## Implementation approach

Single PR on this repo after the file copy: rebrand + string gate + validate. No migration shims. You delete LogForge-Templates on GitHub after this PR is on `main` and the snapshot looks right.
