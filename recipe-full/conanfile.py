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
        # NOTE: self.requires(options=...) validates option names strictly, and
        # the ffmpeg recipe *deletes* platform-inapplicable options in its
        # config_options() (e.g. with_vaapi only exists on Linux/FreeBSD). So we
        # must only pass options that exist for the current OS -- passing a
        # deleted option is a hard error ("option 'with_vaapi' doesn't exist").
        opts = {}
        if self.settings.os in ("Linux", "FreeBSD"):
            # These pull */system recipes needing apt-installed dev packages
            # (libva-dev, libvdpau-dev, xcb/X11, alsa, pulse). conan's
            # package_manager mode is 'check' on CI so they fail unattended, and
            # musl/Alpine can't apt at all. Disable for portable builds.
            opts.update({
                "with_vaapi": False,
                "with_vdpau": False,
                "with_xcb": False,
                "with_xlib": False,
                "with_libalsa": False,
                "with_pulse": False,
            })
        elif self.settings.os == "Windows" and self.settings.get_safe("compiler") == "msvc":
            # The MSVC build env fails to resolve several deps via pkg-config
            # (aom, dav1d, and intermittently freetype2). The MinGW/GCC build
            # (windows-x64-gnu) uses msys2 pkg-config normally and gets the full
            # feature set, so this trim is MSVC-only. AV1 encode stays via
            # SVT-AV1; decode via ffmpeg's native decoder.
            opts["with_libaom"] = False
            opts["with_libdav1d"] = False
        self.requires(f"ffmpeg/{FFMPEG_VERSION}", options=opts)

    def package(self):
        ffmpeg = self.dependencies["ffmpeg"]
        src_bin = os.path.join(ffmpeg.package_folder, "bin")
        dst_bin = os.path.join(self.package_folder, "bin")
        for pattern in ("ffmpeg", "ffmpeg.exe", "ffprobe", "ffprobe.exe"):
            copy(self, pattern, src_bin, dst_bin, keep_path=False)

    def package_info(self):
        self.cpp_info.bindirs = ["bin"]
