#!/usr/bin/env python3
"""Panel and GUI-definition sanity for Maremba (port of YouKnow's check).

The universal45 package is rendered at Reason Studios from GUI2D alone
(device_2D.lua, hdgui_2D.lua and the 5x PNGs), while a local build installs the
hand-maintained GUI/Output/gui.lua with GUI/Output/HD. Neither path is exercised
by the DSP tests, so every mistake here surfaces only as a cloud build failure
or a GUI rejection: 1/5-scale art in GUI2D (JB-1), panels bound to nodes that do
not exist (JB-2), unused images in the package (JB-18), a local GUI that differs
from the shipped one (JB-22).

The Lua files are evaluated with the SDK's Lua 5.1 (or a `lua` on PATH) and a
recording `jbox` mock, so helper functions and table layouts need no parsing.
Checks:
  - panel backdrops: 3770 HD px wide, 345 * device_height_ru tall (folded 150);
  - every device_2D strip divides into its frames, on the 5x grid;
  - every widget lies inside its own panel, clear of the 25 HD px side margins,
    and no two widgets (or a static decoration and a widget) overlap;
  - every hdgui_2D node resolves in the matching device_2D panel, panels bind
    S_backdrop, and device_2D declares no node that hdgui_2D leaves unbound;
  - every GUI2D PNG is referenced by device_2D.lua or is a Reason_* preview;
  - GUI/Output/gui.lua declares the same widgets, at the same places, with the
    same images and options as hdgui_2D.lua + device_2D.lua;
  - GUI2D art and its GUI/Output/HD twin are pixel-identical;
  - every sound property, CV input and audio output has exactly the widgets it
    should (motherboard_def.lua), and the stock routing symbols are unmodified.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent
GUI2D = PROJECT / "GUI2D"
HD = PROJECT / "GUI" / "Output" / "HD"
SDK = Path(os.environ.get("JUKEBOX_SDK_DIR", PROJECT.parent.parent)).expanduser()

Q = 5                      # authoring resolution: 1 logical unit is 5 HD pixels
WIDTH = 754                # logical panel width (3770 HD px)
RACK_UNIT = 69             # logical rack unit (345 HD px)
FOLDED_HEIGHT = 30         # logical folded height (150 HD px)
# The GUI design guidelines require an empty 25 HD px margin along the left and
# right edges of every panel, clear of anything that responds to input.
SIDE_MARGIN = 25 / Q
PANELS = ("front", "folded_front", "back", "folded_back")

PREVIEW_PREFIXES = ("Reason_Icon128x128", "Reason_Navigator", "Reason_Palette",
                    "Reason_TrackListIcon")
PREVIEW_FACES = ("front_root", "front_folded_root", "back_root", "back_folded_root")
# Images Reason reads by name from a local build's HD folder.
LOCAL_IMPLICIT = {"DeviceIcon.png", "DeviceNavigator.png", "DeviceNavigatorFolded.png",
                  "DevicePaletteImage.png", "DeviceTrackListThumbnail.png"}

# Reason Studios' stock routing symbols (RE2D_Stock_Graphics_1_1.zip,
# Decorations/), committed byte for byte; docs/ASSET_PROVENANCE.md.
STOCK_ROUTING_ICONS = {
    "Routing_Icon_White_01_1frames.png":
        "638b4b491632d4c3df9293943feb3f0faa2c61f840ae15f30e847cf80cdddc38",
    "Routing_Icon_White_02_1frames.png":
        "4bb34ecc958ac44c30f95298b2229a20800355f839f67c0012e96c00c8fe5f8a",
}

# Widgets whose look comes from Reason's own furniture in the local gui.lua
# format, so only GUI2D names an image for them.
FURNITURE_KINDS = {"patch_browse_group", "device_name", "placeholder",
                   "audio_output_socket", "cv_input_socket"}
# Options compared between hdgui_2D and gui.lua besides binding and position.
COMPARED_OPTIONS = ("show_remote_box", "show_automation_rect", "center", "text_style",
                    "fg_color", "loader_alt_color", "fx_patch")

LUA_DRIVER = r"""
local path = arg[1]
jbox = setmetatable({}, { __index = function(_, name)
    return function(args) return { __jbox = name, args = args } end
end })
local env = setmetatable({}, { __index = _G })
local chunk = assert(loadfile(path))
setfenv(chunk, env)
chunk()

local function encode(value)
    local kind = type(value)
    if kind == "boolean" then return tostring(value) end
    if kind == "number" then
        if value ~= value or value == math.huge or value == -math.huge then return "null" end
        return string.format("%.17g", value)
    end
    if kind == "string" then
        return '"' .. (value:gsub('[%c"\\]', function(c)
            return string.format("\\u%04x", c:byte())
        end)) .. '"'
    end
    if kind ~= "table" then return "null" end
    local count, sequence = 0, true
    for key in pairs(value) do
        count = count + 1
        if type(key) ~= "number" then sequence = false end
    end
    local parts = {}
    if sequence and count == #value then
        for i = 1, #value do parts[i] = encode(value[i]) end
        return "[" .. table.concat(parts, ",") .. "]"
    end
    for key, item in pairs(value) do
        if type(item) ~= "function" then
            parts[#parts + 1] = encode(tostring(key)) .. ":" .. encode(item)
        end
    end
    return "{" .. table.concat(parts, ",") .. "}"
end
io.write(encode(env))
"""

_LUA_CACHE = {}


class CheckError(Exception):
    pass


def find_lua():
    for candidate in (SDK / "Tools" / "Build" / "Lua" / "Mac" / "lua",
                      SDK / "Tools" / "Build" / "Lua" / "Win" / "lua.exe"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    for name in ("lua5.1", "lua"):
        found = shutil.which(name)
        if found:
            return found
    raise CheckError("no Lua interpreter: set JUKEBOX_SDK_DIR or put lua5.1 on PATH")


def load_lua(path):
    """Evaluate a Lua file against the jbox mock; its globals as Python data."""
    path = Path(path)
    if path not in _LUA_CACHE:
        result = subprocess.run([find_lua(), "-", str(path)], input=LUA_DRIVER,
                                capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            raise CheckError(f"{path.relative_to(PROJECT)} failed to evaluate: "
                             f"{result.stderr.strip()}")
        _LUA_CACHE[path] = json.loads(result.stdout)
    return _LUA_CACHE[path]


def call(value, name=None):
    return isinstance(value, dict) and "__jbox" in value and (name is None or value["__jbox"] == name)


def entries(table):
    """(key, value) pairs of a table decoded from Lua (dict or list)."""
    if isinstance(table, dict):
        return list(table.items())
    if isinstance(table, list):
        return [(str(index + 1), item) for index, item in enumerate(table)]
    return []


class Node:
    def __init__(self, name, x, y):
        self.name, self.x, self.y = name, x, y   # logical units
        self.path = None
        self.frames = 1
        self.size = None                         # logical (w, h) for size nodes

    def rect(self):
        """Logical (x0, y0, x1, y1) of one frame, or None for an imageless node."""
        if self.size:
            return (self.x, self.y, self.x + self.size[0], self.y + self.size[1])
        if not self.path:
            return None
        image = GUI2D / f"{self.path}.png"
        if not image.is_file():
            return None
        width, height = Image.open(image).size
        return (self.x, self.y, self.x + width / Q, self.y + height / self.frames / Q)


def device_nodes(panel):
    """{name: Node} for every node of a device_2D panel table, at absolute offsets."""
    nodes = {}

    def visit(table, base_x, base_y):
        for key, value in entries(table):
            if key.isdigit():
                # An image entry of the enclosing node, or an unnamed group.
                if isinstance(value, dict) and ("path" in value or "size" in value):
                    continue
                visit(value, base_x, base_y)
                continue
            if key == "offset" or not isinstance(value, (dict, list)):
                continue
            offset = value.get("offset", [0, 0]) if isinstance(value, dict) else [0, 0]
            node = Node(key, base_x + offset[0] / Q, base_y + offset[1] / Q)
            for image_key, image in entries(value):
                if image_key.isdigit() and isinstance(image, dict):
                    if "path" in image:
                        node.path = image["path"]
                        node.frames = int(image.get("frames", 1))
                    elif "size" in image:
                        node.size = (image["size"][0] / Q, image["size"][1] / Q)
            nodes[key] = node
            visit(value, node.x, node.y)

    visit(panel, 0, 0)
    return nodes


def load_device():
    device = load_lua(GUI2D / "device_2D.lua")
    return {name: device_nodes(device.get(name, {})) for name in PANELS}


def device_height_ru():
    info = (PROJECT / "info.lua").read_text(encoding="utf-8")
    match = re.search(r"^\s*device_height_ru\s*=\s*(\d+)", info, re.M)
    if not match:
        raise CheckError("info.lua declares no device_height_ru")
    return int(match.group(1))


def panel_height(name):
    return FOLDED_HEIGHT if name.startswith("folded") else RACK_UNIT * device_height_ru()


def hdgui_widgets(hdgui):
    """{panel: [widget call]} from hdgui_2D.lua."""
    result = {}
    for name in PANELS:
        panel = hdgui.get(name)
        if not call(panel, "panel"):
            raise CheckError(f"hdgui_2D.lua: {name} is not a jbox.panel")
        result[name] = [widget for _, widget in entries(panel["args"].get("widgets", []))]
    return result


def check_backdrops(device, failures):
    """GUI2D backdrops are the 5x art: 3770 wide, whole rack units tall."""
    for name in PANELS:
        backdrop = device[name].get("S_backdrop")
        if not backdrop or not backdrop.path:
            failures.append(f"device_2D.lua {name}: no S_backdrop image")
            continue
        image = GUI2D / f"{backdrop.path}.png"
        if not image.is_file():
            failures.append(f"device_2D.lua {name}: backdrop {image.name} is missing")
            continue
        size = Image.open(image).size
        expected = (WIDTH * Q, panel_height(name) * Q)
        if size != expected:
            failures.append(f"GUI2D/{image.name} is {size[0]}x{size[1]}, "
                            f"expected {expected[0]}x{expected[1]} (5x authoring size)")


def check_strips(device, failures):
    """Every referenced strip exists and divides into whole 5x frames."""
    checked = 0
    for name in PANELS:
        for node in device[name].values():
            if not node.path:
                continue
            image = GUI2D / f"{node.path}.png"
            if not image.is_file():
                failures.append(f"{name}/{node.name}: GUI2D/{node.path}.png is missing")
                continue
            width, height = Image.open(image).size
            checked += 1
            if height % node.frames:
                failures.append(f"{name}/{node.name}: {node.path} is {height} px tall, "
                                f"not divisible into {node.frames} frames")
            elif width % Q or (height // node.frames) % Q:
                failures.append(f"{name}/{node.name}: {node.path} frame "
                                f"{width}x{height // node.frames} is off the 5x grid")
    return checked


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def check_bounds(device, widgets, failures):
    """Widgets inside their own panel, clear of the side margins and of each other."""
    placed = 0
    for name in PANELS:
        width, height = WIDTH, panel_height(name)
        rects = []
        for widget in widgets[name]:
            node_name = widget["args"].get("graphics", {}).get("node")
            node = device[name].get(node_name)
            if node is None:
                continue                   # reported by check_nodes
            rect = node.rect()
            if rect is None:
                failures.append(f"{name}/{node_name}: no image or size to place")
                continue
            placed += 1
            kind = widget["__jbox"]
            x0, y0, x1, y1 = rect
            label = f"{name}/{node_name} at ({x0:g}, {y0:g}) sized {x1 - x0:g}x{y1 - y0:g}"
            if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
                failures.append(f"{label} falls outside the {width}x{height} {name} panel")
            elif kind != "static_decoration" and (x0 < SIDE_MARGIN or x1 > width - SIDE_MARGIN):
                failures.append(f"{label} enters the {SIDE_MARGIN:g}-unit side margin")
            for other_kind, other_name, other in rects:
                if overlaps(rect, other):
                    failures.append(f"{name}: {node_name} ({kind}) overlaps "
                                    f"{other_name} ({other_kind})")
            rects.append((kind, node_name, rect))
    return placed


def check_nodes(device, hdgui, widgets, failures):
    """hdgui_2D binds exactly the nodes device_2D declares, panel by panel."""
    resolved = 0
    for name in PANELS:
        nodes = device[name]
        args = hdgui[name]["args"]
        if args.get("graphics", {}).get("node") != "S_backdrop":
            failures.append(f"hdgui_2D.lua {name}: panel graphics node is "
                            f"{args.get('graphics', {}).get('node')!r}, not 'S_backdrop'")
        bound = {"S_backdrop"}
        origin = args.get("cable_origin", {}).get("node") if isinstance(args.get("cable_origin"), dict) else None
        if name == "folded_back" and not origin:
            failures.append("hdgui_2D.lua folded_back: no cable_origin node")
        if origin:
            bound.add(origin)
            if origin not in nodes:
                failures.append(f"hdgui_2D.lua {name}: cable_origin {origin} not in device_2D")
        for widget in widgets[name]:
            node_name = widget["args"].get("graphics", {}).get("node")
            if node_name in bound:
                failures.append(f"hdgui_2D.lua {name}: node {node_name} is bound twice")
            bound.add(node_name)
            if node_name in nodes:
                resolved += 1
            else:
                failures.append(f"hdgui_2D.lua {name}: {widget['__jbox']} node "
                                f"{node_name} not declared in device_2D.{name}")
        for node_name in sorted(set(nodes) - bound):
            failures.append(f"device_2D.lua {name}: node {node_name} is not bound in hdgui_2D.lua")
    return resolved


def check_gui2d_inventory(device, failures):
    """Nothing ships in GUI2D that device_2D does not use (Reason_* previews aside)."""
    referenced = {f"{node.path}.png" for nodes in device.values()
                  for node in nodes.values() if node.path}
    previews = {f"{prefix}_{face}_Panel.png" for prefix in PREVIEW_PREFIXES
                for face in PREVIEW_FACES}
    present = {path.name for path in GUI2D.glob("*.png")}
    for name in sorted(present - referenced - previews):
        failures.append(f"GUI2D/{name} is referenced by nothing in device_2D.lua")
    for name in sorted(previews - present):
        failures.append(f"GUI2D/{name}: Reason preview image is missing")
    return len(present)


def gui_image(args):
    for key in ("animation", "background", "image"):
        value = args.get(key)
        if call(value):
            return value["args"].get("path"), int(value["args"].get("frames", 1))
    return None


def signature(panel, kind, args, x, y, image, size, margins):
    options = tuple((key, json.dumps(args.get(key), sort_keys=True))
                    for key in COMPARED_OPTIONS if key in args)
    return (panel, kind, args.get("value") or args.get("socket"), args.get("index"),
            round(x, 3), round(y, 3), image, size, margins, options)


def check_local_gui(device, hdgui, widgets, failures):
    """GUI/Output/gui.lua (local builds) matches the GUI2D definition (shipped)."""
    gui = load_lua(PROJECT / "GUI" / "Output" / "gui.lua")
    shipped, local = set(), set()
    for name in PANELS:
        nodes = device[name]
        for widget in widgets[name]:
            args = widget["args"]
            node = nodes.get(args.get("graphics", {}).get("node"))
            if node is None:
                continue
            kind = widget["__jbox"]
            image = None if kind in FURNITURE_KINDS or kind == "patch_name" else (node.path, node.frames)
            size = node.size if kind == "patch_name" else None
            bounds = args.get("graphics", {}).get("hit_boundaries")
            margins = (tuple(bounds.get(side, 0) / Q for side in ("left", "top", "right", "bottom"))
                       if bounds else None)
            shipped.add(signature(name, kind, args, node.x, node.y, image, size, margins))

        panel = gui.get(name)
        if not call(panel, "panel"):
            failures.append(f"gui.lua: {name} is not a jbox.panel")
            continue
        panel_args = panel["args"]
        backdrop = panel_args.get("backdrop")
        expected_backdrop = nodes["S_backdrop"].path if "S_backdrop" in nodes else None
        if not call(backdrop, "image") or backdrop["args"].get("path") != expected_backdrop:
            failures.append(f"gui.lua {name}: backdrop is not {expected_backdrop}")
        if name == "folded_back":
            origin = nodes.get("S_cable_origin")
            local_origin = panel_args.get("cable_origin")
            if not origin or local_origin != [origin.x, origin.y]:
                failures.append(f"gui.lua folded_back: cable_origin {local_origin} differs from device_2D")
        for _, widget in entries(panel_args.get("widgets", [])):
            args = widget["args"]
            kind = widget["__jbox"]
            x, y = args.get("transform", [0, 0])
            image = None if kind in FURNITURE_KINDS or kind == "patch_name" else gui_image(args)
            size = (args.get("width"), args.get("height")) if kind == "patch_name" else None
            bounds = args.get("margins")
            margins = (tuple(bounds.get(side, 0) for side in ("left", "top", "right", "bottom"))
                       if bounds else None)
            local.add(signature(name, kind, args, x, y, image, size, margins))
            path = gui_image(args)
            if path and not (HD / f"{path[0]}.png").is_file():
                failures.append(f"gui.lua {name}: GUI/Output/HD/{path[0]}.png is missing")
        if expected_backdrop and not (HD / f"{expected_backdrop}.png").is_file():
            failures.append(f"GUI/Output/HD/{expected_backdrop}.png is missing")
    for item in sorted(shipped - local, key=str):
        failures.append(f"only in hdgui_2D/device_2D: {item}")
    for item in sorted(local - shipped, key=str):
        failures.append(f"only in GUI/Output/gui.lua: {item}")
    return len(local)


def check_twins(failures):
    """Art present in both GUI2D and GUI/Output/HD is the same image."""
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
            failures.append(f"{source.name}: GUI2D is {left.size}, GUI/Output/HD is {right.size}")
        elif left.convert("RGBA").tobytes() != right.convert("RGBA").tobytes():
            failures.append(f"{source.name}: GUI2D and GUI/Output/HD artwork differ")
    for path in sorted(HD.glob("*.png")):
        if path.name not in LOCAL_IMPLICIT and not (GUI2D / path.name).is_file():
            failures.append(f"GUI/Output/HD/{path.name} has no GUI2D counterpart")
    return twins


def check_routing_icons(failures):
    for name, digest in STOCK_ROUTING_ICONS.items():
        for folder in (GUI2D, HD):
            path = folder / name
            if not path.is_file():
                failures.append(f"{path.relative_to(PROJECT)} is missing")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                failures.append(f"{path.relative_to(PROJECT)} is not the stock Reason Studios file")


def check_coverage(widgets, failures):
    """Sound properties, CV inputs and audio outputs all have their widgets."""
    motherboard = load_lua(PROJECT / "motherboard_def.lua")
    bound = [widget["args"].get("value") or widget["args"].get("socket")
             for name in PANELS for widget in widgets[name]]
    properties = motherboard["custom_properties"]["args"]["document_owner"]["properties"]
    sound = sorted(name for name, value in properties.items()
                   if call(value) and not value["__jbox"].startswith("performance_"))
    for name in sound:
        if f"/custom_properties/{name}" not in bound:
            failures.append(f"/custom_properties/{name} has no front or back panel widget")
    for group, kind in (("cv_inputs", "cv_input_socket"), ("audio_outputs", "audio_output_socket")):
        declared = {f"/{group}/{name}" for name in motherboard.get(group, {})}
        sockets = [widget["args"].get("socket") for name in PANELS
                   for widget in widgets[name] if widget["__jbox"] == kind]
        for socket in sorted(declared):
            if sockets.count(socket) != 1:
                failures.append(f"{socket} has {sockets.count(socket)} {kind} widgets, expected 1")
        for socket in sorted(set(sockets) - declared):
            failures.append(f"{kind} {socket} is not declared in motherboard_def.lua")
    return len(sound)


def main():
    failures = []
    try:
        device = load_device()
        hdgui = load_lua(GUI2D / "hdgui_2D.lua")
        widgets = hdgui_widgets(hdgui)
        check_backdrops(device, failures)
        strips = check_strips(device, failures)
        placed = check_bounds(device, widgets, failures)
        resolved = check_nodes(device, hdgui, widgets, failures)
        files = check_gui2d_inventory(device, failures)
        local = check_local_gui(device, hdgui, widgets, failures)
        twins = check_twins(failures)
        check_routing_icons(failures)
        sound = check_coverage(widgets, failures)
    except CheckError as error:
        failures.append(str(error))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"\n{len(failures)} panel geometry problem(s)")
        return 1
    print(f"Maremba panels: {device_height_ru()}U backdrops at 5x; {strips} strips on the "
          f"5x grid; {placed} widgets inside their panels and margins with no overlaps; "
          f"{resolved} hdgui nodes resolve; {files} GUI2D files all used; gui.lua matches "
          f"({local} widgets); {twins} GUI2D/HD twins identical; {sound} sound properties "
          f"bound; stock routing symbols intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
