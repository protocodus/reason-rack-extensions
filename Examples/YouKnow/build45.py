import os
import sys


# Build configuration
SOURCE_FILES = ["*.cpp", "DSP/*.cpp"]
INCLUDE_DIRS = ["."]
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
JUKEBOX_SDK_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("JUKEBOX_SDK_DIR", os.path.join(PROJECT_DIR, "..", ".."))
))
# Upstream ships the DSP at -O3/IPO. The SDK links Rack translation units as
# bitcode but only applies its built-in -O2 pass, so request the same source-TU
# optimization tier here; the later target translation remains SDK-owned.
OTHER_COMPILER_FLAGS = "-Wall -O3"

with open(os.path.join(JUKEBOX_SDK_DIR, "version.txt"), encoding="ascii") as sdk_version_file:
    sdk_version = sdk_version_file.read().splitlines()
if not sdk_version[0].startswith("JukeboxSDK_500_") or "TargetVersion=5.0" not in sdk_version:
    raise RuntimeError("YouKnow requires Jukebox SDK 5.0")

sys.path.insert(0, os.path.abspath(os.path.join(JUKEBOX_SDK_DIR, "Tools", "Build")))

import buildconfig
buildconfig.RACK_EXTENSION_NAME = "YouKnow"
buildconfig.SOURCE_FILES = SOURCE_FILES
buildconfig.JUKEBOX_SDK_DIR = os.path.normpath(JUKEBOX_SDK_DIR)
buildconfig.INCLUDE_DIRS = INCLUDE_DIRS
buildconfig.OTHER_COMPILER_FLAGS = OTHER_COMPILER_FLAGS

import build
build.doBuild(sys.argv)
