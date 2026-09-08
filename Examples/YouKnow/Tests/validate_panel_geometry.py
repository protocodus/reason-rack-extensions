#!/usr/bin/env python3
"""Panel and GUI-definition sanity, without the SDK.

`Design/render_panels.py` performs the authoritative layout checks, but it needs
the Jukebox SDK and macOS fonts, so it cannot run on a hosted CI runner. Every
check here reads only files that are committed to this repository plus Pillow,
which means CI can run it on any machine and catch the class of mistake that
otherwise surfaces as a cloud build failure.

The check that motivates this file: a widget must fit the panel that declares
it. The folded panels are one rack unit tall and re-declare some of the node
names the full front panel uses, so a rewrite that is not panel-aware drags the
folded copy to the front panel's coordinates. That is valid Lua, it satisfies a
node-set comparison, and it fails the developer-site build at `render_gui` with
nothing more useful than "an internal error occurred". It happened on 1.0.0f10.
"""

import re
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent
GUI2D = PROJECT / "GUI2D"
HD = PROJECT / "GUI" / "Output" / "HD"

Q = 5  # authoring resolution: 1 logical unit is 5 device pixels
WIDTH, HEIGHT = 754, 552
FOLDED_HEIGHT = 30

PANEL_SIZES = {
    "front": (WIDTH, HEIGHT),
    "back": (WIDTH, HEIGHT),
    "folded_front": (WIDTH, FOLDED_HEIGHT),
    "folded_back": (WIDTH, FOLDED_HEIGHT),
}

# Frame counts the device_2D.lua helpers bake in. A widget's drawn height is its
# strip height divided by these, not the strip height itself.
HELPER_FRAMES = {
    "fader": 32, "toggle": 2, "knob": 63,
    "lamp": 2, "momentary_overlay": 2, "wheel": 64,
}
HELPER_PATHS = {
    "toggle": "Toggle", "knob": "Knob",
    "lamp": "Lamp", "momentary_overlay": "MomentaryOverlay",
}


def panel_bodies(source):
    """Split a Lua panel definition file into its four panel sections."""
    bodies = {}
    for name in PANEL_SIZES:
        match = re.search(rf"^{name} = ", source, re.M)
        if not match:
            continue
        rest = source[match.end():]
        followers = [re.search(rf"^{other} = ", rest, re.M)
                     for other in PANEL_SIZES if other != name]
        ends = [found.start() for found in followers if found]
        bodies[name] = rest[:min(ends)] if ends else rest
    return bodies


def widget_calls(body):
    """(node, helper, [args]) for every `S_node = helper(...)` in a section."""
    for node, helper, args in re.findall(
            r"(S_[A-Za-z0-9_]+)\s*=\s*(\w+)\(([^)]*)\)", body):
        yield node, helper, [a.strip().strip('"') for a in args.split(",")]


def check_panel_bounds(device, failures):
    """Every widget must fit inside the panel that declares it."""
    checked = 0
    for name, body in panel_bodies(device).items():
        width, height = PANEL_SIZES[name]
        for node, helper, fields in widget_calls(body):
            try:
                x, y = float(fields[0]), float(fields[1])
            except (ValueError, IndexError):
                continue
            if helper == "widget":
                path, frames = fields[2], int(fields[3])
            else:
                frames = HELPER_FRAMES.get(helper)
                path = HELPER_PATHS.get(helper)
                if path is None and len(fields) > 2:
                    path = fields[2]
            if not path or frames is None:
                continue

            image_path = GUI2D / f"{path}.png"
            if not image_path.is_file():
                failures.append(f"{name}/{node}: references missing image {path}.png")
                continue
            image = Image.open(image_path)
            if image.height % frames:
                failures.append(
                    f"{name}/{node}: {path} is {image.height} px, not divisible "
                    f"into {frames} frames")
                continue
            frame_w, frame_h = image.width / Q, image.height / frames / Q
            if x < 0 or y < 0 or x + frame_w > width or y + frame_h > height:
                failures.append(
                    f"{name}/{node}: {path} at ({x:g}, {y:g}) sized "
                    f"{frame_w:g}x{frame_h:g} falls outside the "
                    f"{width}x{height} {name} panel")
            checked += 1
    return checked


def check_node_sets(device, hdgui, failures):
    """device_2D.lua declares exactly the nodes hdgui_2D.lua binds."""
    declared = set(re.findall(r"\b(S_[A-Za-z0-9_]+)\s*=", device))
    used = set(re.findall(r'"(S_[A-Za-z0-9_]+)"', hdgui))
    for node in sorted(used - declared):
        failures.append(f"hdgui_2D.lua binds {node}, which device_2D.lua never declares")
    for node in sorted(declared - used):
        failures.append(f"device_2D.lua declares {node}, which hdgui_2D.lua never binds")
    return len(declared)


def check_assets_exist(device, failures):
    """Every literal image path in device_2D.lua resolves."""
    referenced = set(re.findall(r'path\s*=\s*"([^"]+)"', device))
    referenced |= {fields[2] for _, helper, fields in widget_calls(device)
                   if helper in {"widget", "fader", "wheel"} and len(fields) > 2}
    for name in sorted(referenced):
        if not (GUI2D / f"{name}.png").is_file():
            failures.append(f"device_2D.lua references GUI2D/{name}.png, which is absent")
    return len(referenced)


def check_gui_twins(failures):
    """GUI/Output/HD carries the same artwork GUI2D does.

    Widget strips are copied byte for byte; the panels are re-encoded from RGBA
    to RGB, so those are compared as pixels.
    """
    twins = 0
    for source in sorted(GUI2D.glob("*.png")):
        mirror = HD / source.name
        if not mirror.is_file():
            continue
        twins += 1
        if source.read_bytes() == mirror.read_bytes():
            continue
        left, right = Image.open(source), Image.open(mirror)
        if left.size != right.size:
            failures.append(f"{source.name}: GUI2D is {left.size}, HD is {right.size}")
        elif left.convert("RGB").tobytes() != right.convert("RGB").tobytes():
            failures.append(f"{source.name}: GUI2D and HD artwork differ")
    return twins


def check_version_consistency(failures):
    """Current declarations match info.lua; dated historical evidence may differ."""
    info = (PROJECT / "info.lua").read_text(encoding="utf-8")
    match = re.search(r'^version_number\s*=\s*"([^"]+)"', info, re.M)
    if not match:
        failures.append("info.lua has no version_number")
        return None
    version = match.group(1)
    version_pattern = r"(\d+\.\d+\.\d+[bdf]\d+)"
    documents = {
        "README.md": rf"^Production candidate `{version_pattern}`",
        "Docs/SHOP_COPY.md": rf"^- Candidate: `{version_pattern}`",
        "Docs/USER_GUIDE.md": rf"^Version {version_pattern}\s*$",
        "Docs/RELEASE_CHECKLIST.md": rf"^# YouKnow {version_pattern} release checklist$",
        "Docs/ASSET_PROVENANCE.md": rf"^Current candidate: YouKnow `{version_pattern}`",
    }
    for relative, pattern in documents.items():
        path = PROJECT / relative
        if not path.is_file():
            failures.append(f"{relative}: missing current-version document")
            continue
        declared = re.search(pattern, path.read_text(encoding="utf-8"), re.M)
        if not declared:
            failures.append(f"{relative}: missing current-version declaration")
        elif declared.group(1) != version:
            failures.append(
                f"{relative}: declares {declared.group(1)} but info.lua "
                f"declares {version}")
    return version


def main():
    failures = []
    device = (GUI2D / "device_2D.lua").read_text(encoding="utf-8")
    hdgui = (GUI2D / "hdgui_2D.lua").read_text(encoding="utf-8")

    widgets = check_panel_bounds(device, failures)
    nodes = check_node_sets(device, hdgui, failures)
    assets = check_assets_exist(device, failures)
    twins = check_gui_twins(failures)
    version = check_version_consistency(failures)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"\n{len(failures)} panel geometry problem(s)")
        return 1
    print(f"YouKnow panels: {widgets} widgets inside their own panels across "
          f"{len(PANEL_SIZES)} panels; {nodes} nodes agree between device_2D and "
          f"hdgui_2D; {assets} asset paths resolve; {twins} GUI2D/HD twins match; "
          f"prose agrees with info.lua {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
