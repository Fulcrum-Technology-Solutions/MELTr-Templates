#!/usr/bin/env python3
"""Validate MELTr template metadata schemas, path consistency, and .j2 contents."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml
from jinja2 import TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
from jsonschema import ValidationError, validate

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

SCHEMAS = {
    "vendor.meta.yaml": "vendor.schema.json",
    "product.meta.yaml": "product.schema.json",
    "collection.json": "collection.schema.json",
    "template.meta.yaml": "template.schema.json",
}

SKIP_DIRS = {"archive", "examples", ".git", "__pycache__", "node_modules"}


def load_schema(schema_name: str) -> dict:
    with open(SCHEMA_DIR / schema_name) as f:
        return json.load(f)


def validate_schema_file(filepath: Path, schema_name: str) -> bool:
    schema = load_schema(schema_name)
    with open(filepath) as f:
        if filepath.suffix == ".json":
            data = json.load(f)
        else:
            data = yaml.safe_load(f)
    try:
        validate(instance=data, schema=schema)
        print(f"[OK] schema {filepath}")
        return True
    except ValidationError as e:
        print(f"[FAIL] schema {filepath}: {e.message}")
        return False


def relative_under_templates(filepath: Path, templates_root: Path) -> Path | None:
    try:
        return filepath.resolve().relative_to(templates_root.resolve())
    except ValueError:
        return None


def validate_vendor_meta(filepath: Path, templates_root: Path) -> bool:
    rel = relative_under_templates(filepath, templates_root)
    if rel is None or len(rel.parts) != 2:
        print(f"[FAIL] path {filepath}: vendor.meta.yaml must live at templates/<vendor>/")
        return False
    vendor_dir = rel.parts[0]
    with open(filepath) as f:
        data = yaml.safe_load(f) or {}
    vendor = data.get("vendor")
    if vendor != vendor_dir:
        print(
            f"[FAIL] path {filepath}: vendor={vendor!r} does not match directory {vendor_dir!r}"
        )
        return False
    print(f"[OK] path {filepath}")
    return True


def validate_product_meta(filepath: Path, templates_root: Path) -> bool:
    rel = relative_under_templates(filepath, templates_root)
    if rel is None or len(rel.parts) != 3:
        print(f"[FAIL] path {filepath}: product.meta.yaml must live at templates/<vendor>/<product>/")
        return False
    vendor_dir, product_dir = rel.parts[0], rel.parts[1]
    with open(filepath) as f:
        data = yaml.safe_load(f) or {}
    ok = True
    if data.get("vendor") != vendor_dir:
        print(
            f"[FAIL] path {filepath}: vendor={data.get('vendor')!r} does not match directory {vendor_dir!r}"
        )
        ok = False
    if data.get("product") != product_dir:
        print(
            f"[FAIL] path {filepath}: product={data.get('product')!r} does not match directory {product_dir!r}"
        )
        ok = False
    if ok:
        print(f"[OK] path {filepath}")
    return ok


def validate_template_meta(filepath: Path, templates_root: Path) -> bool:
    rel = relative_under_templates(filepath, templates_root)
    if rel is None or len(rel.parts) != 4:
        print(
            f"[FAIL] path {filepath}: template meta must live at "
            "templates/<vendor>/<product>/<data_source>/<name>.meta.yaml"
        )
        return False
    vendor_dir, product_dir, data_source_dir, filename = rel.parts
    with open(filepath) as f:
        data = yaml.safe_load(f) or {}
    ok = True
    expected = {
        "vendor": vendor_dir,
        "product": product_dir,
        "data_source": data_source_dir,
    }
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            print(
                f"[FAIL] path {filepath}: {key}={data.get(key)!r} does not match directory {expected_value!r}"
            )
            ok = False

    stem = filename[: -len(".meta.yaml")]
    j2_path = filepath.with_name(f"{stem}.j2")
    if not j2_path.exists():
        print(f"[FAIL] pair {filepath}: missing companion template {j2_path.name}")
        ok = False

    if ok:
        print(f"[OK] path {filepath}")
    return ok


def validate_jinja_template(filepath: Path) -> bool:
    """Syntax-check a log template. Parse only — never render HTML."""
    source = filepath.read_text(encoding="utf-8")
    if not source.strip():
        print(f"[FAIL] content {filepath}: template is empty")
        return False
    # SandboxedEnvironment + parse(): no HTML render surface (not a Flask app).
    env = SandboxedEnvironment(autoescape=True)
    try:
        env.parse(source)
    except TemplateSyntaxError as e:
        print(f"[FAIL] content {filepath}: Jinja2 syntax error: {e}")
        return False
    print(f"[OK] content {filepath}")
    return True


def validate_collection(filepath: Path, templates_root: Path) -> bool:
    rel = relative_under_templates(filepath, templates_root)
    if rel is None or len(rel.parts) != 3:
        print(f"[FAIL] path {filepath}: collection.json must live at templates/<vendor>/<product>/")
        return False

    product_dir = filepath.parent
    with open(filepath) as f:
        data = json.load(f)

    ok = True
    templates = data.get("templates") or []
    if not templates:
        print(f"[FAIL] collection {filepath}: templates list is empty")
        ok = False

    seen = set()
    for entry in templates:
        if not isinstance(entry, str) or not entry.strip():
            print(f"[FAIL] collection {filepath}: invalid template entry {entry!r}")
            ok = False
            continue
        if entry in seen:
            print(f"[FAIL] collection {filepath}: duplicate template entry {entry!r}")
            ok = False
            continue
        seen.add(entry)

        j2_path = product_dir / f"{entry}.j2"
        meta_path = product_dir / f"{entry}.meta.yaml"
        if not j2_path.exists():
            print(f"[FAIL] collection {filepath}: missing template file {j2_path.relative_to(templates_root)}")
            ok = False
        if not meta_path.exists():
            print(f"[FAIL] collection {filepath}: missing metadata file {meta_path.relative_to(templates_root)}")
            ok = False

    for j2_path in sorted(product_dir.rglob("*.j2")):
        if any(part in SKIP_DIRS for part in j2_path.parts):
            continue
        rel_entry = j2_path.relative_to(product_dir).with_suffix("").as_posix()
        if rel_entry not in seen:
            print(
                f"[FAIL] collection {filepath}: {rel_entry} exists on disk but is not listed in collection.json"
            )
            ok = False

    if ok:
        print(f"[OK] collection {filepath}")
    return ok


def should_skip(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts if path != root else ()
    return any(part in SKIP_DIRS for part in rel_parts)


def main() -> int:
    root = Path.cwd()
    templates_root = root / "templates"
    if not templates_root.is_dir():
        print("[FAIL] templates/ directory not found; run from repository root")
        return 1

    success = True

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        if should_skip(current, root):
            dirnames[:] = []
            continue
        # Keep walking non-template dirs only to find schemas? No — only validate under templates/
        if current != root and "templates" not in current.relative_to(root).parts:
            # Still walk into templates from root; skip other top-level trees early
            if current.parent == root and current.name != "templates":
                dirnames[:] = []
                continue

        for filename in filenames:
            filepath = current / filename
            if not relative_under_templates(filepath, templates_root):
                continue

            if filename == "vendor.meta.yaml":
                if not validate_schema_file(filepath, "vendor.schema.json"):
                    success = False
                if not validate_vendor_meta(filepath, templates_root):
                    success = False
            elif filename == "product.meta.yaml":
                if not validate_schema_file(filepath, "product.schema.json"):
                    success = False
                if not validate_product_meta(filepath, templates_root):
                    success = False
            elif filename == "collection.json":
                if not validate_schema_file(filepath, "collection.schema.json"):
                    success = False
                if not validate_collection(filepath, templates_root):
                    success = False
            elif filename.endswith(".meta.yaml"):
                if not validate_schema_file(filepath, "template.schema.json"):
                    success = False
                if not validate_template_meta(filepath, templates_root):
                    success = False
            elif filename.endswith(".j2"):
                if not validate_jinja_template(filepath):
                    success = False
                meta = filepath.with_name(filepath.stem + ".meta.yaml")
                if not meta.exists():
                    print(f"[FAIL] pair {filepath}: missing companion metadata {meta.name}")
                    success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
