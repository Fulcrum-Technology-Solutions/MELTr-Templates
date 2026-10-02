#!/usr/bin/env python3
"""Fetch a vendor logo via Brandfetch Brand API and write it beside vendor.meta.yaml.

Requires BRANDFETCH_API_KEY (Bearer token from https://developers.brandfetch.com/).

Examples:
  BRANDFETCH_API_KEY=... python scripts/fetch_vendor_logo.py --vendor cisco --dry-run
  BRANDFETCH_API_KEY=... python scripts/fetch_vendor_logo.py --vendor cisco
  BRANDFETCH_API_KEY=... python scripts/fetch_vendor_logo.py --all-missing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = REPO_ROOT / "templates"
BRAND_API_PREFIX = "https://api.brandfetch.io/v2/brands/domain/"
# Hostnames we will download logo bytes from (Brand API asset hosts).
ALLOWED_DOWNLOAD_HOST_SUFFIXES = (
    "brandfetch.io",
    "brandfetch.com",
)


def website_domain(website: str) -> str | None:
    raw = (website or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    host = urlparse(raw).hostname
    if not host:
        return None
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    # Hostname only — no schemes/paths that could confuse URL construction
    if not host or any(ch in host for ch in ("/", "\\", ":", "@", " ")):
        return None
    return host


def require_https_url(url: str, *, allowed_host_suffixes: tuple[str, ...] | None = None) -> str:
    """Reject file:// and other schemes; optionally restrict host suffixes."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"refusing non-https URL scheme {parsed.scheme!r}")
    if parsed.username or parsed.password:
        raise ValueError("refusing URL with embedded credentials")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("refusing URL without hostname")
    if allowed_host_suffixes is not None:
        if not any(host == s or host.endswith("." + s) for s in allowed_host_suffixes):
            raise ValueError(f"refusing download host {host!r}")
    return url


def https_get(url: str, *, timeout: int, headers: dict[str, str]) -> bytes:
    """HTTPS-only GET using an opener without file:// support."""
    require_https_url(url)
    req = urllib.request.Request(url, headers=headers)
    # HTTPSHandler only — no FileHandler / FTPHandler (mitigates CWE-939).
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler())
    with opener.open(req, timeout=timeout) as resp:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        return resp.read()


def load_vendor_meta(vendor_id: str) -> tuple[Path, dict[str, Any]]:
    meta_path = TEMPLATES_ROOT / vendor_id / "vendor.meta.yaml"
    if not meta_path.is_file():
        raise FileNotFoundError(f"missing {meta_path}")
    data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    return meta_path, data


def brand_api_get(domain: str, api_key: str) -> dict[str, Any]:
    # Domain is hostname-validated; URL is composed from a fixed https prefix.
    safe_domain = urllib.parse.quote(domain, safe=".-")
    url = require_https_url(BRAND_API_PREFIX + safe_domain)
    body = https_get(
        url,
        timeout=30,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "MELTr-Templates-fetch-vendor-logo/1.0",
        },
    )
    return json.loads(body.decode("utf-8"))


def pick_logo_format(payload: dict[str, Any]) -> tuple[str, str] | None:
    """Return (src_url, extension) preferring icon/light PNG then SVG."""
    logos = payload.get("logos") or []
    # Prefer icon over logo/symbol; light over dark; png over svg/webp
    type_rank = {"icon": 0, "logo": 1, "symbol": 2}
    theme_rank = {"light": 0, "dark": 1}
    fmt_rank = {"png": 0, "svg": 1, "webp": 2, "jpeg": 3, "jpg": 3}

    candidates: list[tuple[tuple[int, int, int], str, str]] = []
    for entry in logos:
        ltype = (entry.get("type") or "").lower()
        theme = (entry.get("theme") or "").lower()
        for fmt in entry.get("formats") or []:
            src = fmt.get("src")
            ftype = (fmt.get("format") or "").lower()
            if not src or ftype not in fmt_rank:
                continue
            try:
                require_https_url(src, allowed_host_suffixes=ALLOWED_DOWNLOAD_HOST_SUFFIXES)
            except ValueError:
                continue
            rank = (
                type_rank.get(ltype, 9),
                theme_rank.get(theme, 9),
                fmt_rank[ftype],
            )
            ext = "jpg" if ftype == "jpeg" else ftype
            candidates.append((rank, src, ext))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    _, src, ext = candidates[0]
    return src, ext


def download_bytes(url: str) -> bytes:
    require_https_url(url, allowed_host_suffixes=ALLOWED_DOWNLOAD_HOST_SUFFIXES)
    return https_get(
        url,
        timeout=60,
        headers={"User-Agent": "MELTr-Templates-fetch-vendor-logo/1.0"},
    )

def process_vendor(vendor_id: str, *, api_key: str, dry_run: bool, force: bool) -> int:
    meta_path, data = load_vendor_meta(vendor_id)
    website = data.get("website") or ""
    domain = website_domain(str(website))
    if not domain:
        print(f"[SKIP] {vendor_id}: no usable website in vendor.meta.yaml", file=sys.stderr)
        return 1

    logo_name = f"{vendor_id}-logo.png"
    dest = meta_path.parent / logo_name
    if dest.is_file() and not force and not dry_run:
        print(f"[SKIP] {vendor_id}: {dest.name} already exists (use --force)")
        return 0

    print(f"[FETCH] {vendor_id} domain={domain}")
    try:
        payload = brand_api_get(domain, api_key)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[FAIL] {vendor_id}: Brand API HTTP {e.code}: {body[:200]}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[FAIL] {vendor_id}: {e}", file=sys.stderr)
        return 1

    picked = pick_logo_format(payload)
    if not picked:
        print(f"[FAIL] {vendor_id}: no logo formats in Brand API response", file=sys.stderr)
        return 1
    src, ext = picked
    # Always store as <vendor>-logo.<ext>; rename meta accordingly
    logo_name = f"{vendor_id}-logo.{ext}"
    dest = meta_path.parent / logo_name

    print(f"[OK] {vendor_id}: selected {src}")
    if dry_run:
        print(f"[DRY-RUN] would write {dest.relative_to(REPO_ROOT)} and set logo: {logo_name}")
        return 0

    try:
        content = download_bytes(src)
    except Exception as e:
        print(f"[FAIL] {vendor_id}: download failed: {e}", file=sys.stderr)
        return 1
    if not content:
        print(f"[FAIL] {vendor_id}: empty download", file=sys.stderr)
        return 1

    dest.write_bytes(content)
    data["logo"] = logo_name
    meta_path.write_text(
        yaml.safe_dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[OK] {vendor_id}: wrote {dest.relative_to(REPO_ROOT)} and updated meta")
    return 0


def vendors_missing_logo() -> list[str]:
    missing: list[str] = []
    for meta_path in sorted(TEMPLATES_ROOT.glob("*/vendor.meta.yaml")):
        data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        logo = data.get("logo")
        if not logo:
            missing.append(meta_path.parent.name)
            continue
        if not (meta_path.parent / Path(str(logo)).name).is_file():
            missing.append(meta_path.parent.name)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", action="append", dest="vendors", help="Vendor id (repeatable)")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Process vendors with no logo field or missing logo file",
    )
    parser.add_argument("--dry-run", action="store_true", help="Select asset but do not write")
    parser.add_argument("--force", action="store_true", help="Overwrite existing logo file")
    args = parser.parse_args()

    api_key = (os.environ.get("BRANDFETCH_API_KEY") or "").strip()
    if not api_key:
        print("BRANDFETCH_API_KEY is required", file=sys.stderr)
        return 2

    vendors: list[str] = list(args.vendors or [])
    if args.all_missing:
        vendors.extend(vendors_missing_logo())
    # de-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for v in vendors:
        if v not in seen:
            seen.add(v)
            ordered.append(v)

    if not ordered:
        print("Specify --vendor ID and/or --all-missing", file=sys.stderr)
        return 2

    failures = 0
    for vendor_id in ordered:
        failures += process_vendor(
            vendor_id, api_key=api_key, dry_run=args.dry_run, force=args.force
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
