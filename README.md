# ffmpeg-bins2

Full-feature **FFmpeg / FFprobe** binaries for [`static-ffmpeg`](https://github.com/zackees/static-ffmpeg),
built with [`zackees/forge`](https://github.com/zackees/forge) and cataloged in the
[`zackees/manifest.json`](https://github.com/zackees/manifest.json) format.

This is the successor to [`ffmpeg_bins`](https://github.com/zackees/ffmpeg_bins).

> **Backward compatibility:** `ffmpeg_bins` stays **frozen** — its `v*/‌*.zip`
> raw URLs are never moved, so older `static-ffmpeg` installs keep working
> forever. `ffmpeg-bins2` is additive; new installs resolve through the
> `manifest.json` here.

## Layout

```
manifest.json                 # Catalog (channels + releases -> per-platform assets)
<version>/<platform-key>.zip  # LFS-tracked artifacts, e.g. 8.0.0/linux_x64_musl.zip
```

Each artifact zip extracts to a single `<platform-key>/` folder containing
`ffmpeg`(`.exe`) and `ffprobe`(`.exe`) — matching the layout `static-ffmpeg`
extracts into `bin/<platform-key>/`.

## Targets

| platform-key | os | arch | libc |
|---|---|---|---|
| `win_x64`            | windows | x86_64 | – |
| `win_arm64`         | windows | arm64  | – |
| `darwin_x64`        | macos   | x86_64 | – |
| `darwin_arm64`      | macos   | arm64  | – |
| `linux_x64`         | linux   | x86_64 | glibc (runner default) |
| `linux_arm64`       | linux   | arm64  | glibc (runner default) |
| `linux_x64_musl`    | linux   | x86_64 | musl |
| `linux_arm64_musl`  | linux   | arm64  | musl |

Linux glibc builds use whatever glibc the forge runner ships; users on older
glibc can use the **musl** builds, which are statically self-contained.

## Distribution

Binaries live in Git LFS here, but clients download them over a **CDN-fronted
`www` site** (the `urls[]` in `manifest.json`), so there are no LFS/Release
bandwidth limits. Integrity is guaranteed by the `sha256` in each asset, which
the client verifies after download.

## Publishing a new version

1. Build all targets via forge (see `.github/workflows/build-ffmpeg-forge.yml`).
2. Drop the artifacts under `<version>/` and `git add` them (LFS-tracked).
3. Regenerate the catalog:
   ```bash
   python scripts/gen_manifest.py \
     --version <version> \
     --base-url https://<cdn>/ffmpeg/<version> \
     --artifacts <version> \
     --out manifest.json
   ```
4. Commit + push, then point `static-ffmpeg`'s `DEFAULT_MANIFEST_URL` (or a
   user's `STATIC_FFMPEG_MANIFEST_URL`) at the published `manifest.json`.

Existing installs are unaffected — they keep their pinned version; only fresh
installs pull the newest channel entry.

## Status

**Live.** `manifest.json` publishes real FFmpeg **8.1.2** (`--enable-gpl
--enable-nonfree`, full codec set) and `static-ffmpeg` resolves it by default.

| target | 8.1.2 |
|---|---|
| macOS x64 / arm64 | ✅ |
| glibc-Linux x64 / arm64 | ✅ |
| Windows x64 / arm64 | ⏳ blocked on [forge#10](https://github.com/zackees/forge/issues/10) (MSVC pkg-config) |
| musl x64 / arm64 | ⏳ blocked on [forge#10](https://github.com/zackees/forge/issues/10) (musl C++ toolchain) |

Windows/musl clients fall back to the legacy
[`ffmpeg_bins`](https://github.com/zackees/ffmpeg_bins) binaries until their
forge builds land. Delivery is via the [Release
assets](https://github.com/zackees/ffmpeg-bins2/releases) (Fastly CDN, no
bandwidth limit); the `8.1.2/` LFS copies are the archival source of truth.
Tracked in
[static-ffmpeg#20](https://github.com/zackees/static_ffmpeg/issues/20).
