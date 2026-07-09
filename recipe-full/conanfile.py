"""Full-feature FFmpeg build wrapper for static-ffmpeg / ffmpeg-bins2.

This is a thin Conan consumer that builds conan-center's `ffmpeg` with a
maximal, GPL + nonfree option set, then packages just the `ffmpeg`/`ffprobe`
executables. Options are tuned PER PLATFORM so the build succeeds on stock CI
runners (no system dev packages) and cross-compiles (musl / arm64 / win-arm64).

conan-center ffmpeg defaults are already `--enable-gpl --enable-nonfree` (x264,
x265, fdk-aac, openssl, vpx, aom, dav1d, svtav1, mp3lame, opus, vorbis,
openh264, openjpeg, webp). We only override the options that break unattended
builds; see docs/ffmpeg-options.md for the full reference.

forge builds this via `conan create ... --name ffmpeg-full --version <v>`.
"""

import os

from conan import ConanFile
from conan.tools.files import copy

FFMPEG_VERSION = "8.1.2"


class FfmpegFullConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    package_type = "application"

    def requirements(self):
        opts = {
            "with_programs": True,
            # Linux options that pull */system recipes needing apt-installed dev
            # packages (libva-dev, libvdpau-dev, xcb/X11, alsa, pulse). conan's
            # package_manager mode is 'check' on CI, so these fail unattended --
            # and musl/Alpine can't apt at all. Disable everywhere (inert on
            # non-Linux, where these options don't exist).
            "with_vaapi": False,
            "with_vdpau": False,
            "with_xcb": False,
            "with_xlib": False,
            "with_libalsa": False,
            "with_pulse": False,
            "with_libdrm": False,
        }
        if self.settings.os == "Windows":
            # conan-center libaom fails ffmpeg's configure on MSVC:
            # "aom >= 2.0.0 not found using pkg-config". AV1 encode still
            # available via SVT-AV1; decode via dav1d.
            opts["with_libaom"] = False
        self.requires(f"ffmpeg/{FFMPEG_VERSION}", options=opts)

    def package(self):
        ffmpeg = self.dependencies["ffmpeg"]
        src_bin = os.path.join(ffmpeg.package_folder, "bin")
        dst_bin = os.path.join(self.package_folder, "bin")
        for pattern in ("ffmpeg", "ffmpeg.exe", "ffprobe", "ffprobe.exe"):
            copy(self, pattern, src_bin, dst_bin, keep_path=False)

    def package_info(self):
        self.cpp_info.bindirs = ["bin"]
