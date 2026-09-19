import os
import sys

SOURCE_FILES = ["*.cpp", "DSP/*.cpp"]
INCLUDE_DIRS = [".", "DSP"]
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
JUKEBOX_SDK_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("JUKEBOX_SDK_DIR", os.path.join(PROJECT_DIR, "..", ".."))
))
OTHER_COMPILER_FLAGS = "-Wall -O3"

with open(os.path.join(JUKEBOX_SDK_DIR, "version.txt"), encoding="ascii") as sdk_version_file:
    sdk_version = sdk_version_file.read().splitlines()
if not sdk_version[0].startswith("JukeboxSDK_500_") or "TargetVersion=5.0" not in sdk_version:
    raise RuntimeError("Maremba requires Jukebox SDK 5.0")

sys.path.insert(0, os.path.abspath(os.path.join(JUKEBOX_SDK_DIR, "Tools", "Build")))

import buildconfig
buildconfig.RACK_EXTENSION_NAME = "Maremba"
buildconfig.SOURCE_FILES = SOURCE_FILES
buildconfig.JUKEBOX_SDK_DIR = os.path.normpath(JUKEBOX_SDK_DIR)
buildconfig.INCLUDE_DIRS = INCLUDE_DIRS
buildconfig.OTHER_COMPILER_FLAGS = OTHER_COMPILER_FLAGS

import subprocess
test_runner = os.path.join(PROJECT_DIR, "Tests", "run_all_tests.sh")
if os.path.exists(test_runner):
    print(">>> Running pre-build verification test suite <<<")
    # A hung test (e.g. a voice that never frees) must fail the build, not stall it.
    res = subprocess.run([test_runner], cwd=PROJECT_DIR, timeout=1800)
    if res.returncode != 0:
        raise RuntimeError(f"Pre-build verification failed with exit code {res.returncode}")

import build
build.doBuild(sys.argv)

import re
import shutil

def get_declared_version():
    info_path = os.path.join(PROJECT_DIR, "info.lua")
    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            match = re.search(r'version_number\s*=\s*"([^"]+)"', f.read())
            if match:
                return match.group(1)
    return "1.0.0f1"

# When building universal45, create the versioned package with the build number in the filename
version = get_declared_version()
env_build = os.environ.get("BUILD_NUMBER")
if env_build:
    base_match = re.match(r'^(\d+\.\d+\.\d+)', version)
    base = base_match.group(1) if base_match else version
    version = f"{base}f{env_build}"

u45_std = os.path.join(PROJECT_DIR, "Output", "Universal45", "Maremba.u45")
if os.path.exists(u45_std):
    u45_versioned = os.path.join(PROJECT_DIR, "Output", "Universal45", f"Maremba-{version}.u45")
    shutil.copy2(u45_std, u45_versioned)
    print(f">>> Output package with build number: {u45_versioned} <<<")
    
    # Also stage in Release/<version>/ directory
    release_dir = os.path.join(PROJECT_DIR, "Release", version)
    os.makedirs(release_dir, exist_ok=True)
    shutil.copy2(u45_std, os.path.join(release_dir, f"Maremba-{version}.u45"))
    print(f">>> Staged release artifact: {os.path.join(release_dir, f'Maremba-{version}.u45')} <<<")

try:
    from Design.render_panels import generate_docs_previews
    print(">>> Automatically updating documentation previews in docs/ <<<")
    generate_docs_previews()
except Exception as e:
    print(f"Warning: Failed to update docs previews: {e}")


