# AGENTS.md

## Agent workflow

For non-trivial work, use Superpowers skills (not pasted playbook prompts):

| Task | Skill |
|------|-------|
| New feature / behavior change | `brainstorming` → `writing-plans` |
| Stubborn bug / test failure | `systematic-debugging` |
| Before claiming done | `verification-before-completion` |
| End-of-session learning | `session-retro` |

Global engineering defaults: `~/.cursor/rules/engineering-doctrine.mdc`. Trust code over docs — verify schemas and validation scripts against actual files.

## Spec & parity

| Field | Value |
|-------|-------|
| **SPEC_SOURCE** | JSON schemas in `schemas/` (`vendor` / `product` / `collection` / `template`) plus `python .github/scripts/validate_templates.py`. Use `template.schema.json` — not deprecated `meta.schema.json`. |
| **PARITY_MODE** | When pointed at a reference (schema, existing vendor/product layout, or registry path), that reference defines "done." Audit DONE / PARTIAL / MISSING against the 4-tier hierarchy; do not invent metadata fields. Name deliberate deviations in the PR. |
| **PLANNING_MODE** | No external reference → decompose with explicit acceptance criteria; those criteria define done. |

Global review gate: `~/.cursor/rules/review-gate.mdc` (≥2 specialists by risk). Silent-failure reviews: `silent-failure-hunter` skill.

## Project overview

Community-contributed Jinja2 templates and metadata for [MELTr OSS](https://github.com/Fulcrum-Technology-Solutions/MELTr). Templates are consumed by the MELTr CLI and entity registry. **LLM-assisted template creation is Enterprise-only** (web UI) — not available in OSS or this repo.

## 4-tier hierarchy

Strict directory + metadata structure:

| Level | Example | Metadata |
|-------|---------|----------|
| 1. Vendor | `paloalto/` | `vendor.meta.yaml` |
| 2. Product | `paloalto/firewall/` | `product.meta.yaml`, `collection.json` |
| 3. Data source | `paloalto/firewall/network/` | (directory only) |
| 4. Event type | `traffic.j2`, `traffic.meta.yaml` | `template_name.meta.yaml` |

Example path: `paloalto/firewall/network/traffic.j2`

## Schema conformance

All metadata must validate against JSON schemas in `schemas/`:

| Schema | File |
|--------|------|
| `vendor.schema.json` | `vendor.meta.yaml` |
| `product.schema.json` | `product.meta.yaml` |
| `collection.schema.json` | `collection.json` |
| `template.schema.json` | `template_name.meta.yaml` |

Use `template.schema.json` — **not** deprecated `meta.schema.json`.

## Validation

Before submitting a PR:

```bash
python .github/scripts/validate_templates.py
```

GitHub Actions runs the same validation on push/PR. Failures block merge. Validation also updates `TEMPLATES.yaml` index.

## Contributing checklist

See `CONTRIBUTING.md` for full process. Key requirements:

- All four metadata levels present where applicable
- Jinja2 templates (`.j2`) paired with `.meta.yaml`
- Nested objects (e.g. `documentation.resources`) match schema exactly
- No Enterprise-only feature references in OSS templates

## Related repos

| Repo | Role |
|------|------|
| [MELTr](../MELTr) | OSS engine that renders templates |
| [MELTr-Templates-UI](../MELTr-Templates-UI) | Public registry (`meltr.ftsc.cloud`) syncs from this repo |

## Non-obvious caveats

- Template path in API uses `/` separators (e.g. `paloalto/wildfire/threats`) — distinct from on-disk underscore naming in some Enterprise local paths.
- This repo is the **source of truth** for community templates; registry UI syncs from GitHub.
- Only create git commits when explicitly asked.
