#!/usr/bin/env python3
"""Generate a zackees/manifest.json Catalog for ffmpeg-bins2 artifacts.

Given a directory of built artifacts named ``<platform-key>.zip`` (see
PLATFORM_TUPLES below), emit a Catalog document with real ``sha256``,
``size_bytes`` and CDN ``urls`` for each platform.

Example:
    python scripts/gen_manifest.py \\
        --version 8.0.0 \\
        --base-url https://cdn.example/ffmpeg/8.0.0 \\
        --artifacts 8.0.0 \\
        --out manifest.json
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional

# platform-key -> manifest platform tuple. Keep in sync with static-ffmpeg's
# static_ffmpeg/manifest.py::get_platform_tuple and README "Targets" table.
PLATFORM_TUPLES: Dict[str, Dict[str, str]] = {
    "win_x64": {"os": "windows", "arch": "x86_64"},
    "win_arm64": {"os": "windows", "arch": "arm64"},
    "darwin_x64": {"os": "macos", "arch": "x86_64"},
    "darwin_arm64": {"os": "macos", "arch": "arm64"},
    "linux_x64": {"os": "linux", "arch": "x86_64", "libc": "glibc"},
    "linux_arm64": {"os": "linux", "arch": "arm64", "libc": "glibc"},
    "linux_x64_musl": {"os": "linux", "arch": "x86_64", "libc": "musl"},
    "linux_arm64_musl": {"os": "linux", "arch": "arm64", "libc": "musl"},
}


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file_d:
        for chunk in iter(lambda: file_d.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_platforms(
    artifacts_dir: str, base_url: str, ext: str = "zip"
) -> List[dict]:
    """Build the ``platforms`` list from artifacts present on disk."""
    platforms = []
    for key, tup in PLATFORM_TUPLES.items():
        filename = f"{key}.{ext}"
        path = os.path.join(artifacts_dir, filename)
        if not os.path.exists(path):
            print(f"skip {key}: {path} not found", file=sys.stderr)
            continue
        platforms.append(
            {
                "platform": tup,
                "asset": {
                    "filename": filename,
                    "sha256": sha256_of(path),
                    "size_bytes": os.path.getsize(path),
                    "media_type": "application/zip",
                    "urls": [f"{base_url.rstrip('/')}/{filename}"],
                },
            }
        )
    return platforms


def build_catalog(
    version: str,
    platforms: List[dict],
    published_at: Optional[str] = None,
) -> dict:
    release: Dict[str, object] = {"version": version, "platforms": platforms}
    if published_at:
        release["published_at"] = published_at
    return {
        "kind": "Catalog",
        "schema_version": 1,
        "tool": "ffmpeg",
        "channels": {"latest-stable": version},
        "releases": [release],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--base-url", required=True, help="CDN base URL for this version")
    parser.add_argument("--artifacts", required=True, help="dir containing <key>.zip files")
    parser.add_argument("--ext", default="zip")
    parser.add_argument("--published-at", default=None)
    parser.add_argument("--out", default="-", help="output path, or - for stdout")
    args = parser.parse_args()

    platforms = build_platforms(args.artifacts, args.base_url, args.ext)
    if not platforms:
        print("error: no artifacts found", file=sys.stderr)
        return 1
    catalog = build_catalog(args.version, platforms, args.published_at)
    text = json.dumps(catalog, indent=2) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        with open(args.out, "w", encoding="utf-8") as file_d:
            file_d.write(text)
        print(f"wrote {args.out} ({len(platforms)} platforms)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
