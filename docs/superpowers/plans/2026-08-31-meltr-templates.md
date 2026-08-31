# MELTr-Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Copy LogForge-Templates into this repo, rebrand to MELTr, add a CI string gate, and leave collection versions unchanged.

**Architecture:** One-time `rsync` of the sibling LogForge-Templates tree (no git history). Mechanical identifier replace, then a second human/agent `rg` pass. Schema keys and 4-tier paths stay. This repo does not build `.mtb` files.

**Tech Stack:** Git, rsync, Python 3.10, PyYAML, jsonschema, GitHub Actions. Spec: `docs/superpowers/specs/2026-08-31-meltr-templates-design.md`.

## Global Constraints

- Copy only — do not `git push --force` LogForge-Templates history onto this remote
- Preserve `docs/superpowers/` already in this repo (spec + this plan)
- Schema **keys** and 4-tier paths unchanged; schema `$id` becomes `https://meltr.ftsc.cloud/schemas/{file}`
- Package extension in docs: `.mtb` (gzipped tar). No `.forge` accept-path
- Do **not** bump `collection.json` `version` fields
- Placeholder maintainers → `John Owen` / `jowen@ftsc.com`; leave existing John Owen rows and `examples/acme`
- Product name always **MELTr** (never MELTR / Meltr)
- No “formerly LogForge” copy
- String gate excludes `docs/superpowers/` and the gate script itself
- Do not delete GitHub `LogForge-Templates` (human, after merge)
- MELTr OSS `.mtb` install code is a **companion PR**, not this repo

---

## File map

| Area | Files |
|------|--------|
| Snapshot | Entire tree from `../LogForge-Templates/` except `.git` |
| Spec/plan (keep) | `docs/superpowers/specs/2026-08-31-meltr-templates-design.md`, this plan |
| Schema `$id` | `schemas/vendor.schema.json`, `product.schema.json`, `collection.schema.json`, `template.schema.json` |
| Maintainers + descriptions | `templates/**/collection.json`, `examples/acme/widget/collection.json` |
| Docs | `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `examples/README.md` |
| Index | `TEMPLATES.yaml` (regenerate; versions must match snapshot) |
| Gate | `scripts/check_legacy_strings.py`, `scripts/legacy_string_allowlist.txt`, `.github/workflows/string_gate.yml` |
| Validate | `.github/scripts/validate_templates.py` (unchanged logic) |

---

### Task 1: Copy LogForge-Templates tree

**Files:** all except `.git`; do not overwrite `docs/superpowers/`

- [ ] **Step 1: Confirm sibling source exists**

Run:

```bash
ls "../LogForge-Templates/templates" "../LogForge-Templates/schemas" "../LogForge-Templates/.github/scripts/validate_templates.py"
```

Expected: directories/files exist. If this workspace uses a different relative path, stop and fix the path.

- [ ] **Step 2: Rsync into this repo**

From repo root `MELTr-Templates`:

```bash
rsync -a --exclude '.git' --exclude 'docs/superpowers' \
  "../LogForge-Templates/" "./"
```

`--exclude 'docs/superpowers'` keeps the MELTr spec/plan. `rsync` does not delete extra files.

- [ ] **Step 3: Verify copy + spec still present**

```bash
test -f schemas/template.schema.json
test -f .github/scripts/validate_templates.py
test -f docs/superpowers/specs/2026-08-31-meltr-templates-design.md
git status --short | head
```

Expected: template tree present; spec still there.

- [ ] **Step 4: Commit the snapshot**

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore: snapshot LogForge-Templates tree (no history)

EOF
)"
```

---

### Task 2: Schema `$id` + collection.json maintainers/descriptions

**Files:** `schemas/*.schema.json`, `templates/**/collection.json`

**Produces:** `$id` URLs and placeholder maintainers per spec. Versions unchanged.

- [ ] **Step 1: Snapshot collection versions (before edits)**

```bash
python3 - <<'PY'
import json, pathlib
root = pathlib.Path("templates")
for p in sorted(root.rglob("collection.json")):
    data = json.loads(p.read_text())
    print(f"{p}: {data.get('version')}")
PY
```

Save the output. You will diff it after edits.

- [ ] **Step 2: Rewrite schema `$id` values**

```bash
python3 - <<'PY'
from pathlib import Path
for p in Path("schemas").glob("*.schema.json"):
    text = p.read_text()
    text = text.replace(
        "https://logforge.dev/schemas/",
        "https://meltr.ftsc.cloud/schemas/",
    )
    text = text.replace("LogForge templates", "MELTr templates")
    p.write_text(text)
    print("updated", p)
PY
```

- [ ] **Step 3: Rewrite collection.json placeholders and LogForge copy**

```bash
python3 - <<'PY'
import json
from pathlib import Path

PLACEHOLDER_NAMES = {"LogForge Community", "LogForge Templates"}

def rewrite(path: Path, touch_maintainers: bool) -> None:
    data = json.loads(path.read_text())
    desc = data.get("description") or ""
    data["description"] = desc.replace("LogForge", "MELTr")
    if touch_maintainers:
        for m in data.get("maintainers") or []:
            name = (m.get("name") or "").strip()
            email = (m.get("email") or "").strip().lower()
            if name in PLACEHOLDER_NAMES or "logforge" in email:
                m["name"] = "John Owen"
                m["email"] = "jowen@ftsc.com"
    path.write_text(json.dumps(data, indent=2) + "\n")
    print("updated", path)

for p in Path("templates").rglob("collection.json"):
    rewrite(p, touch_maintainers=True)
# examples/acme: Jane Example stays; still scrub LogForge in description if any
acme = Path("examples/acme/widget/collection.json")
if acme.exists():
    rewrite(acme, touch_maintainers=False)
PY
```

- [ ] **Step 4: Confirm versions unchanged**

Re-run the Step 1 printer. Diff against the saved list. Every `version` must match. If any bumped, revert that field.

- [ ] **Step 5: Commit**

```bash
git add schemas templates examples
git commit -m "$(cat <<'EOF'
refactor: MELTr schema ids and collection maintainers

EOF
)"
```

---

### Task 3: Docs, AGENTS, CONTRIBUTING, `.mtb`

**Files:** `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `examples/README.md`, any remaining copy under `.github/`

- [ ] **Step 1: List remaining hits**

```bash
rg -i 'logforge|\.forge' --glob '!docs/superpowers/**' --glob '!.git/**'
```

Expected: README, CONTRIBUTING, AGENTS, examples, maybe `TEMPLATES.yaml`, maybe `.meta.yaml` `documentation.resources`.

- [ ] **Step 2: Apply identifier map in those files**

| From | To |
|------|----|
| LogForge Templates / LogForge | MELTr Templates / MELTr |
| `pip install logforge` | `pip install meltr` |
| `logforge templates` / `logforge` CLI | `meltr templates` / `meltr` |
| `Fulcrum-Technology-Solutions/LogForge` | `Fulcrum-Technology-Solutions/MELTr` |
| `LogForge-Templates-UI` | `MELTr-Templates-UI` |
| `logforge.io` | `meltr.ftsc.cloud` |
| `.forge` | `.mtb` |
| `tar -xzf crowdstrike.forge` | `tar -xzf crowdstrike.mtb` |

Related-repos in `AGENTS.md` must name MELTr, MELTr-Templates-UI, `meltr.ftsc.cloud`. LLM authoring remains Enterprise-only.

Do not invent “formerly LogForge” sentences.

- [ ] **Step 3: Regenerated index**

```bash
python3 .github/scripts/update_templates_index.py
```

`TEMPLATES.yaml` `version` fields must still match Task 2 snapshot. `updated` timestamp will change — that is OK. Descriptions should say MELTr, not LogForge.

- [ ] **Step 4: Commit**

```bash
git add README.md CONTRIBUTING.md AGENTS.md examples TEMPLATES.yaml
git add -u
git commit -m "$(cat <<'EOF'
docs: rebrand Templates repo to MELTr and .mtb

EOF
)"
```

---

### Task 4: String gate + validate CI

**Files:**
- Create: `scripts/check_legacy_strings.py`
- Create: `scripts/legacy_string_allowlist.txt`
- Create: `.github/workflows/string_gate.yml`
- Modify: `.github/workflows/validate_templates.yml` (optional: also run on `schemas/**`)

- [ ] **Step 1: Allowlist (header only)**

Create `scripts/legacy_string_allowlist.txt`:

```
# Hard cut: no LogForge product strings. Empty allowlist.
# Format (unused): path-prefix:needle   or  re:<regex>
```

- [ ] **Step 2: Scanner**

Create `scripts/check_legacy_strings.py`:

```python
#!/usr/bin/env python3
"""Fail CI if LogForge / .forge product strings remain."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST_PATH = Path(__file__).with_name("legacy_string_allowlist.txt")

PATTERN = re.compile(r"logforge|LogForge|LOGFORGE|\.forge\b")

EXCLUDE_PREFIXES = ("docs/superpowers/",)
EXCLUDE_FILES = {
    "scripts/check_legacy_strings.py",
    "scripts/legacy_string_allowlist.txt",
}


def load_allowlist(path: Path) -> list[str]:
    rules: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rules.append(line)
    return rules


def line_allowed(rel_path: str, line_no: int, line: str, rules: list[str]) -> bool:
    for rule in rules:
        if rule.startswith("re:"):
            if re.search(rule[3:], line):
                return True
            continue
        if ":" in rule and not rule.startswith("http"):
            prefix, _, needle = rule.partition(":")
            if not rel_path.startswith(prefix.rstrip("/")):
                continue
            if needle.isdigit():
                if int(needle) == line_no:
                    return True
                continue
            if needle in line:
                return True
            continue
        if rule in line:
            return True
    return False


def _iter_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    files: list[Path] = []
    for rel in result.stdout.decode("utf-8").split("\0"):
        if not rel:
            continue
        path = ROOT / rel
        if path.is_file():
            files.append(path)
    return files


def collect_hits() -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path in _iter_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDE_FILES:
            continue
        if any(rel.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if PATTERN.search(line):
                hits.append((rel, line_no, line))
    return hits


def main() -> int:
    if not ALLOWLIST_PATH.is_file():
        print(f"Missing allowlist: {ALLOWLIST_PATH}", file=sys.stderr)
        return 2
    rules = load_allowlist(ALLOWLIST_PATH)
    violations: list[str] = []
    for rel_path, line_no, content in collect_hits():
        if line_allowed(rel_path, line_no, content, rules):
            continue
        violations.append(f"{rel_path}:{line_no}:{content}")
    if violations:
        print("Unexpected LogForge / .forge strings:\n", file=sys.stderr)
        for item in sorted(violations):
            print(f"  {item}", file=sys.stderr)
        print(f"\n{len(violations)} violation(s).", file=sys.stderr)
        return 1
    print("OK: no unexpected LogForge / .forge strings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Workflow**

Create `.github/workflows/string_gate.yml`:

```yaml
name: String gate

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  strings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v6
        with:
          python-version: "3.10"
      - run: python scripts/check_legacy_strings.py
```

- [ ] **Step 4: Run gate (expect fail until Task 3 leftovers are gone)**

```bash
python3 scripts/check_legacy_strings.py
```

Fix every printed path (Pass 2). Re-run until:

```
OK: no unexpected LogForge / .forge strings
```

- [ ] **Step 5: Validate metadata**

```bash
python3 -m pip install pyyaml jsonschema jinja2
python3 .github/scripts/validate_templates.py
```

Expected: all `[OK]`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts .github/workflows/string_gate.yml
git add -u
git commit -m "$(cat <<'EOF'
ci: fail on leftover LogForge / .forge strings

EOF
)"
```

---

## Done when

Spec acceptance criteria 1–6 hold. PR on `main`. Human deletes GitHub `LogForge-Templates` only after confirming the snapshot.

**Blocked / not this repo:** MELTr OSS `.forge` → `.mtb`; MELTr-Templates-UI sync + download filenames.
