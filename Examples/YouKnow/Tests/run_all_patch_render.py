#!/usr/bin/env python3
"""Compile, render, and optionally level-calibrate every public patch."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from validate_patches import PROJECT, PUBLIC, read_patch


LEVELS_PATH = PROJECT / "Design" / "preset_levels.json"
TARGET_PEAK = 0.18
TARGET_RMS = 0.04
MIN_GAIN = 1.0 / 8.0
MAX_GAIN = 8.0
MEASUREMENT = re.compile(
    r"^OK:\s+(.*?)\s+peak ([0-9.]+) rms ([0-9.]+) hash [0-9a-f]+$"
)


def manifest_row(path: Path, unity_level: bool = False, aging: float = 0.5) -> str:
    values, _ = read_patch(path)
    if unity_level:
        values["presetGain"] = 0.5
    fields = [path.relative_to(PUBLIC).as_posix()]
    for name, value in values.items():
        number = int(value) if isinstance(value, bool) else value
        fields.append(f"{name}={number}")
    fields.append(f"_aging={aging}")
    if unity_level:
        fields.append("_measureUnity=1")
    return "\t".join(fields)


def write_level_table(output: str, patches: list[Path], aging: float) -> None:
    measurements = {}
    for line in output.splitlines():
        match = MEASUREMENT.fullmatch(line)
        if match:
            name, peak, rms = match.groups()
            measurements[name] = (float(peak), float(rms))
    expected = {path.relative_to(PUBLIC).as_posix() for path in patches}
    assert set(measurements) == expected, "level calibration render set differs"

    trims = {}
    audit = {}
    gain_db = []
    for name in sorted(measurements):
        peak, rms = measurements[name]
        assert peak > 0.0 and rms > 0.0
        gain = min(TARGET_PEAK / peak, TARGET_RMS / rms)
        gain = max(MIN_GAIN, min(MAX_GAIN, gain))
        travel = (math.log2(gain) + 3.0) / 6.0
        travel = max(0.0, min(1.0, travel))
        trims[name] = round(travel, 9)
        audit[name] = {
            "raw_peak": peak,
            "raw_rms": rms,
            "gain_db": round(20.0 * math.log10(gain), 4),
        }
        gain_db.append(audit[name]["gain_db"])

    # Some patches need a hand attenuation on top of the Aging 0% measurement:
    # a trim that sits on the +18 dB clamp can still exceed the peak ceiling
    # once Aging is at its shipping 50%. Those decisions live in "adjustments"
    # and are *not* re-derivable from this render, so carry them across a
    # recalibration instead of silently discarding them.
    adjustments = {}
    if LEVELS_PATH.exists():
        previous = json.loads(LEVELS_PATH.read_text(encoding="utf-8"))
        adjustments = {
            name: entry for name, entry in previous.get("adjustments", {}).items()
            if name in trims
        }
    for name, entry in adjustments.items():
        before = entry.get("preset_gain_before")
        if before is not None and abs(trims[name] - float(before)) > 1e-9:
            raise SystemExit(
                f"{name}: measured trim moved to {trims[name]} but its recorded "
                f"adjustment was taken from {before}; re-take the adjustment")
        trims[name] = float(entry["preset_gain_after"])

    data = {
        "format": 1,
        "method": "fixed C3/G3/C4 chord, 3 s, 48 kHz; cap peak and RMS",
        "measurement_aging": aging,
        "target_peak": TARGET_PEAK,
        "target_rms": TARGET_RMS,
        "gain_range_db": [-18.0618, 18.0618],
        "preset_gain": trims,
        "measurements": audit,
    }
    if adjustments:
        data["adjustments"] = adjustments
    LEVELS_PATH.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Calibrated {len(trims)} patches to peak <= {TARGET_PEAK:.2f} and "
        f"RMS <= {TARGET_RMS:.2f}; trim range {min(gain_db):.2f} to "
        f"{max(gain_db):.2f} dB; wrote {LEVELS_PATH}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--calibrate-levels", action="store_true",
        help="measure with unity Preset Level and rewrite the deterministic trim table",
    )
    modes.add_argument(
        "--stress-levels", action="store_true",
        help="check low and high six-note maximum-velocity chords below full scale",
    )
    parser.add_argument(
        "--aging", type=float,
        help="Aging percent, 0..100 (default: 50 for validation, 0 for calibration)",
    )
    args = parser.parse_args()
    aging_percent = args.aging if args.aging is not None else (
        0.0 if args.calibrate_levels else 50.0)
    if not math.isfinite(aging_percent) or not 0.0 <= aging_percent <= 100.0:
        parser.error("--aging must be a finite percentage from 0 to 100")
    aging = aging_percent / 100.0
    patches = sorted(PUBLIC.rglob("*.repatch"))
    assert patches, "no public patches found"
    print(f"Rendering {len(patches)} patches at Aging {aging_percent:g}%", flush=True)
    manifest = "\n".join(
        manifest_row(path, unity_level=args.calibrate_levels, aging=aging)
        for path in patches
    ) + "\n"

    with tempfile.TemporaryDirectory(prefix="youknow-all-patch-") as temporary:
        binary = Path(temporary) / "youknow-all-patch-render"
        subprocess.run(
            [
                os.environ.get("CXX", "clang++"),
                "-std=c++17",
                "-O3",
                "-DNDEBUG",
                "-Wall",
                "-Wextra",
                "-Wpedantic",
                "-Werror",
                str(PROJECT / "Tests" / "AllPatchRenderContract.cpp"),
                str(PROJECT / "DSP" / "YouKnowEngine.cpp"),
                str(PROJECT / "DSP" / "YouKnowChorus.cpp"),
                "-o",
                str(binary),
            ],
            check=True,
            cwd=PROJECT,
        )
        if args.calibrate_levels:
            completed = subprocess.run(
                [str(binary)], input=manifest, text=True, cwd=PROJECT,
                capture_output=True,
            )
            if completed.returncode != 0:
                print(completed.stdout, end="")
                print(completed.stderr, end="", file=os.sys.stderr)
                return completed.returncode
            write_level_table(completed.stdout, patches, aging)
            return 0
        if args.stress_levels:
            for argument, label in (
                ("--stress-low", "Low six-note stress"),
                ("--stress-high", "High six-note stress"),
            ):
                completed = subprocess.run(
                    [str(binary), argument], input=manifest, text=True, cwd=PROJECT,
                    capture_output=True,
                )
                if completed.returncode != 0:
                    print(completed.stdout, end="")
                    print(completed.stderr, end="", file=os.sys.stderr)
                    return completed.returncode
                measurements = [
                    (match.group(1), float(match.group(2)))
                    for line in completed.stdout.splitlines()
                    if (match := MEASUREMENT.fullmatch(line))
                ]
                assert len(measurements) == len(patches), (
                    f"{label} render set differs"
                )
                name, peak = max(measurements, key=lambda row: row[1])
                print(
                    f"{label}: {len(measurements)}/{len(patches)} patches below "
                    f"full scale; maximum peak {peak:.6f} ({name})"
                )
            return 0
        return subprocess.run([str(binary)], input=manifest, text=True, cwd=PROJECT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
