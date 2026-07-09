# FFmpeg full-feature build reference (conan-center `ffmpeg`, 8.x)

Source: `conan-io/conan-center-index` `recipes/ffmpeg/all/conanfile.py` (read 2026-07-09).
`config.yml` ships versions **8.1.2** and **7.1.5**.

## The important finding: defaults are already GPL + nonfree

You never set `gpl`/`nonfree` directly — the recipe derives them (conanfile.py ~L567):

- `--enable-gpl`   ⇐ `with_libx264` OR `with_libx265` OR `postproc`(7.x only)
- `--enable-nonfree` ⇐ `with_libfdk_aac` OR (`with_ssl` != False AND a gpl trigger)

With **defaults**, `with_libx264`, `with_libx265`, `with_libfdk_aac`, `with_ssl=openssl`
are all on ⇒ the default build is **`--enable-gpl --enable-nonfree`** with a very full
codec set: x264, x265, fdk-aac, vpx, aom, dav1d, svtav1, mp3lame, opus, vorbis,
openh264, openjpeg, webp, freetype, zlib/bzip2/lzma/iconv.

> `--enable-nonfree` output is **non-redistributable** (fdk-aac's license is
> GPL-incompatible). Owner-authorized private use only.

## Default-False options worth flipping (no system deps, safe cross-platform)

`with_libxml2` (DASH), `with_fontconfig`, `with_fribidi`, `with_harfbuzz`, `with_soxr`,
`with_libjxl`. Heavier/newer (enable later if wanted): `with_openapv` (8.x), `with_whisper`
(8.x, pulls whisper-cpp), `with_zeromq`, `with_sdl` (ffplay), `with_vulkan`.

## Linux system-dependency options (build-host must have dev packages)

`with_vaapi`, `with_vdpau`, `with_xcb`, `with_xlib`, `with_libalsa`, `with_pulse`
default **True** on Linux and pull `*/system` recipes — the runner needs
`libva-dev libvdpau-dev libxcb*-dev libx11-dev libasound2-dev libpulse-dev` or the
build errors. **On stock/musl/headless CI, disable these** (they are Linux-only options).

## Per-platform notes

- **Windows ARM64**: recipe forces `with_libsvtav1=False` — leave it off.
- **macOS**: Apple frameworks (appkit/avfoundation/coreimage/audiotoolbox/videotoolbox)
  default on, no external deps. Cross x86_64→arm64 auto-disables the audiotoolbox outdev.
- **musl/Alpine**: disable the Linux system-dep options above; codecs cross-compile fine
  (nasm only needed on x86/x86_64).

## Recipe ceiling (needs a forked recipe to exceed)

No nvenc/ffnvcodec, QSV/libmfx, AMF, OpenCL (CUDA hardcoded off). No libass/subtitles,
theora, speex, xvid, rav1e, srt, rist, zimg, libvmaf, libplacebo, libbluray, etc.

## Maximal option delta (if building a custom recipe)

```
with_libxml2=True with_fontconfig=True with_fribidi=True with_harfbuzz=True
with_soxr=True with_libjxl=True
# and for CI portability on Linux:
with_vaapi=False with_vdpau=False with_xcb=False with_xlib=False
with_libalsa=False with_pulse=False
```
