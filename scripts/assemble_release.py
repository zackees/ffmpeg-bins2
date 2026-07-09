#!/usr/bin/env python3
"""Repackage forge build artifacts into static-ffmpeg client zips.

forge uploads one archive per target containing the built ffmpeg-full package
(ffmpeg/ffprobe under a bin/ dir). The static-ffmpeg client, however, downloads
a zip that extracts to a folder named after its *platform key* (win32 / darwin /
darwin_arm64 / linux / linux_arm64) containing the executables. This script
bridges the two: it finds ffmpeg/ffprobe in each downloaded artifact and repacks
them into `<zipkey>.zip` with the correct internal folder.

Usage:
    python scripts/assemble_release.py --artifacts <download_dir> --out <out_dir>

<download_dir> is expected to contain one subdirectory per forge platform whose
name contains the forge platform token (e.g. ".../forge-...-linux-x64-musl/...").
"""

import argparse
import os
import shutil
import sys
import zipfile
from typing import Dict, Optional, Tuple

# forge platform token -> (client zip basename, internal folder = client
# platform key). Windows always keys to "win32", Linux to "linux"/"linux_arm64"
# regardless of libc (one libc per machine); the manifest tuple picks the right
# zip.
TARGETS: Dict[str, Tuple[str, str]] = {
    "windows-x64": ("win_x64", "win32"),
    "windows-arm64": ("win_arm64", "win32"),
    "macos-x64": ("darwin_x64", "darwin"),
    "macos-arm64": ("darwin_arm64", "darwin_arm64"),
    "linux-x64-musl": ("linux_x64_musl", "linux"),
    "linux-arm64-musl": ("linux_arm64_musl", "linux_arm64"),
    "linux-x64": ("linux_x64", "linux"),
    "linux-arm64": ("linux_arm64", "linux_arm64"),
}

# Longest tokens first so "linux-x64-musl" matches before "linux-x64".
_ORDERED_TOKENS = sorted(TARGETS, key=len, reverse=True)


def find_exe(root: str, stem: str) -> Optional[str]:
    """Find an executable named stem or stem.exe anywhere under root."""
    for dirpath, _dirs, files in os.walk(root):
        for candidate in (stem, stem + ".exe"):
            if candidate in files:
                return os.path.join(dirpath, candidate)
    return None


def token_for_dir(name: str) -> Optional[str]:
    for token in _ORDERED_TOKENS:
        if token in name:
            return token
    return None


def assemble(artifacts_dir: str, out_dir: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    made = 0
    seen = set()
    for entry in sorted(os.listdir(artifacts_dir)):
        src = os.path.join(artifacts_dir, entry)
        if not os.path.isdir(src):
            continue
        token = token_for_dir(entry)
        if token is None or token in seen:
            continue
        zipkey, bindir = TARGETS[token]
        is_windows = bindir == "win32"
        ffmpeg = find_exe(src, "ffmpeg")
        ffprobe = find_exe(src, "ffprobe")
        if not ffmpeg or not ffprobe:
            print(f"WARN {token}: ffmpeg/ffprobe not found under {src}", file=sys.stderr)
            continue
        seen.add(token)
        out_zip = os.path.join(out_dir, f"{zipkey}.zip")
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for exe_path, stem in ((ffmpeg, "ffmpeg"), (ffprobe, "ffprobe")):
                arc = f"{bindir}/{stem}{'.exe' if is_windows else ''}"
                zf.write(exe_path, arc)
        made += 1
        print(f"{zipkey}.zip  <- {token}  ({os.path.getsize(out_zip)} bytes)")
    print(f"assembled {made}/{len(TARGETS)} target zips into {out_dir}", file=sys.stderr)
    return 0 if made else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not os.path.isdir(args.artifacts):
        print(f"error: {args.artifacts} is not a directory", file=sys.stderr)
        return 1
    return assemble(args.artifacts, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
