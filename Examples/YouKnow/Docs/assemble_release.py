#!/usr/bin/env python3
"""Assemble one version's complete handoff in a single target directory.

Everything a release needs lands in `Release/<version>/`: the universal U45,
the Shop front/back/thumbnail images and PDF manual (written there by
`Docs/build_release_materials.py`), the changelog and release evidence, a
build manifest and `SHA256SUMS`. Run it after `python3 build45.py universal45`
and `uv run Docs/build_release_materials.py`:

    python3 Docs/assemble_release.py

It refuses a U45 built for another version or from other sources: every
archived source file must match its working-tree bytes, and no compiled source
may be newer than the archive. Only the expected artifacts are hashed; anything
else in the directory is reported and left out. Standard library only.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


DOCS = Path(__file__).resolve().parent
PROJECT = DOCS.parent
PRODUCT = "YouKnow"
PRODUCT_ID = "cz.protocodus.YouKnow"
UNIVERSAL = PROJECT / "Output" / "Universal45" / f"{PRODUCT}.u45"
IMAGES = (f"{PRODUCT}_Front.png", f"{PRODUCT}_Back.png", f"{PRODUCT}_Thumbnail_800.png")
MANUAL = f"{PRODUCT}_User_Manual.pdf"
COPIED = {"CHANGELOG.md": PROJECT / "CHANGELOG.md",
          "RELEASE_EVIDENCE.md": DOCS / "RELEASE_EVIDENCE.md"}
CHIPS = tuple(f"chip_binaries/{configuration}/{PRODUCT}{bits}.ll"
              for configuration in ("Testing", "Deployment") for bits in (32, 64))
# Sources the SDK compiles into the chips (build45.py SOURCE_FILES and headers).
COMPILED_PATTERNS = ("*.cpp", "*.h", "DSP/*.cpp", "DSP/*.h", "DSP/*.inc")


def declared_version(info_lua):
    match = re.search(r'^version_number\s*=\s*"([^"]+)"', info_lua, re.MULTILINE)
    assert match, "info.lua has no version_number"
    return match.group(1)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(*arguments):
    return subprocess.run(["git", *arguments], cwd=PROJECT, check=True,
                          capture_output=True, text=True).stdout.strip()


def upstream_revision():
    sync = (PROJECT / "DSP" / "SYNC.md").read_text(encoding="utf-8")
    match = re.search(r"Synchronized on \S+ from .*?`([0-9a-f]{40})`", sync, re.DOTALL)
    return match.group(1) if match else None


def archived_source(member):
    """The working-tree file an archive member was copied from, if any."""
    if member.startswith("chip_binaries/") or member == "version.txt":
        return None
    for candidate in (PROJECT / member, PROJECT / "Resources" / member):
        if candidate.is_file():
            return candidate
    raise AssertionError(f"the U45 member {member} has no source file")


def verify_universal(version):
    """Check the U45 against the current sources; return its facts."""
    assert UNIVERSAL.is_file(), f"build the U45 first: {UNIVERSAL} is missing"
    with zipfile.ZipFile(UNIVERSAL) as archive:
        assert archive.testzip() is None, "the U45 archive is corrupt"
        members = archive.namelist()
        archived = declared_version(archive.read("info.lua").decode("utf-8"))
        assert archived == version, (
            f"the U45 declares {archived}, but info.lua declares {version}; rebuild it")
        missing = [chip for chip in CHIPS if chip not in members]
        assert not missing, f"the U45 lacks chip binaries: {missing}"
        stale = [member for member in members
                 if (source := archived_source(member)) is not None
                 and source.read_bytes() != archive.read(member)]
        assert not stale, f"the U45 differs from the current sources; rebuild it: {stale[:5]}"
        chips = {chip: {"bytes": len(data), "sha256": sha256(data)}
                 for chip in CHIPS for data in (archive.read(chip),)}
        facts = {
            "members": len(members),
            "source_matches": sum(1 for member in members if archived_source(member)),
            "patches": sum(1 for name in members if name.endswith(".repatch")),
            "sdk": " ".join(archive.read("version.txt").decode("utf-8").split()),
            "chip_binaries": chips,
        }
    built = UNIVERSAL.stat().st_mtime
    compiled = sorted({path for pattern in COMPILED_PATTERNS for path in PROJECT.glob(pattern)})
    newer = [str(path.relative_to(PROJECT)) for path in compiled if path.stat().st_mtime > built]
    assert not newer, f"compiled sources changed after the U45 was built; rebuild it: {newer}"
    facts["compiled_sources"] = {str(path.relative_to(PROJECT)): sha256(path.read_bytes())
                                 for path in compiled}
    return facts


def main():
    version = declared_version((PROJECT / "info.lua").read_text(encoding="utf-8"))
    target = PROJECT / "Release" / version
    target.mkdir(parents=True, exist_ok=True)
    facts = verify_universal(version)
    for name in (*IMAGES, MANUAL):
        assert (target / name).is_file(), (
            f"{target / name} is missing; run `uv run Docs/build_release_materials.py`")

    u45_name = f"{PRODUCT}-{version}.u45"
    shutil.copyfile(UNIVERSAL, target / u45_name)
    for name, source in COPIED.items():
        shutil.copyfile(source, target / name)
    (target / "README.md").write_text(
        f"# {PRODUCT} {version}\n\n"
        f"Product: `{PRODUCT_ID}`; requires Reason 14 / SDK target 5.0.\n"
        f"Upstream DSP: `{upstream_revision()}`.\n\n"
        "This directory is the complete handoff for this version:\n\n"
        f"- `{u45_name}` - universal build-service archive (upload this)\n"
        f"- `{IMAGES[0]}`, `{IMAGES[1]}` - Shop front and back panel views\n"
        f"- `{IMAGES[2]}` - 1:1 Shop product thumbnail\n"
        f"- `{MANUAL}` - user manual with license, privacy and provenance notices\n"
        "- `CHANGELOG.md`, `RELEASE_EVIDENCE.md` - changes and validation record\n"
        "- `build-manifest.json`, `SHA256SUMS` - source identity and checksums\n"
        "- `validation/` - supporting logs, when retained\n\n"
        "A local U45 is not a cloud build or Shop acceptance; those are recorded\n"
        "separately. Verify integrity with `shasum -a 256 -c SHA256SUMS` here.\n",
        encoding="utf-8")

    artifacts = sorted([u45_name, *IMAGES, MANUAL, *COPIED, "README.md"])
    expected = {*artifacts, "build-manifest.json", "SHA256SUMS", ".DS_Store"}
    extra = sorted(path.name for path in target.iterdir()
                   if path.is_file() and path.name not in expected)
    # Untracked sources count: a build can compile files git does not hold.
    status = git("status", "--porcelain", "--", ".")
    manifest = {
        "product_id": PRODUCT_ID,
        "version": version,
        "sdk": facts.pop("sdk"),
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree_clean": status == "",
        "upstream_revision": upstream_revision(),
        "universal45": {
            "file": u45_name,
            "bytes": (target / u45_name).stat().st_size,
            "sha256": sha256((target / u45_name).read_bytes()),
            **facts,
        },
        "artifacts": {name: sha256((target / name).read_bytes()) for name in artifacts},
        "assembled_utc": datetime.now(timezone.utc).isoformat(),
    }
    (target / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    listed = sorted([*artifacts, "build-manifest.json"])
    (target / "SHA256SUMS").write_text(
        "".join(f"{sha256((target / name).read_bytes())}  {name}\n" for name in listed),
        encoding="utf-8")
    verified = subprocess.run(["shasum", "-a", "256", "-c", "SHA256SUMS"], cwd=target,
                              capture_output=True, text=True)
    assert verified.returncode == 0, verified.stdout + verified.stderr

    print(f"{PRODUCT} {version}: {len(listed) + 1} checksummed files in {target}")
    for name in listed:
        print(f"  {name}")
    if extra:
        print(f"note: not part of the handoff and not checksummed: {', '.join(extra)}")
    if status:
        print("note: the source tree has uncommitted or untracked changes; "
              "the manifest records the compiled source hashes")


if __name__ == "__main__":
    main()
