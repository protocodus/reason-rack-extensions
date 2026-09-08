"""Rewrite the panel Lua widget coordinates from the renderer's own layout.

`Design/render_panels.py` derives every front-panel control position from what
the control has to print, so the positions are not stable numbers a human
should retype into three files. This script is the one writer: it takes the
node -> (x, y) map that `check_layout()` validates against and stamps it into
`GUI2D/device_2D.lua` and `GUI/Output/gui.lua` in place.

It only ever replaces coordinate pairs on lines that already declare a widget.
Structure, helper definitions, comments and ordering are left exactly as they
are, so this stays a refiner of hand-authored files rather than a generator
that owns them.

Run it after any layout change, then run `render_panels.py`, whose
`check_layout()` fails if a single node was missed:

    JUKEBOX_SDK_DIR=/path/to/SDK python3 Design/sync_panel_lua.py
    JUKEBOX_SDK_DIR=/path/to/SDK python3 Design/render_panels.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render_panels as R

PROJECT = Path(__file__).resolve().parent.parent
DEVICE_2D = PROJECT / "GUI2D" / "device_2D.lua"
GUI_LUA = PROJECT / "GUI" / "Output" / "gui.lua"

# gui.lua writes its wheels, knob and note lamp as inline jbox blocks keyed by
# the property they drive rather than by a node name, so they need this bridge
# back to the node names device_2D.lua uses.
# The folded panels declare the SAME header node names at their own, different
# coordinates, so any rewrite keyed on those names has to be confined to the
# full front panel or it silently drags the folded furniture along with it.
def front_span(text):
    """(start, end) of the front panel's declaration within a Lua source."""
    start = text.index("front = ")
    end = text.index("folded_front", start)
    return start, end


def in_front_only(text, rewrite):
    start, end = front_span(text)
    return text[:start] + rewrite(text[start:end]) + text[end:]


PROPERTY_NODES = {
    "pitchBend": "S_pitch_wheel",
    "modWheel": "S_mod_wheel",
    "portamento": "S_knob_portamento",
    "noteOn": "S_note_on",
}


def positions():
    """Every placed node, matching what render_panels.check_layout() expects."""
    placed = {node: (x, y) for node, _, _, x, y in R.all_widgets()}
    placed["S_placeholder"] = tuple(R.PLACEHOLDER_POS)
    placed.update({f"S_cv_input_{name}": (x, y)
                   for name, _, x, y in R.REAR_CV_INPUTS})
    placed.update({f'S_status_{item["name"]}': (item["x"], R.ENGINE_STATUS_Y)
                   for item in R.ENGINE_STATUS})
    key_mode_x = next(
        item["x"] for row in R.LAYOUT for _, _, _, controls in row["sections"]
        for item in controls if item["name"] == "keyMode")
    top = R.radio_top(R.body_top(R.LAYOUT[2]))
    placed.update({f"S_momentary_keyMode_{index}":
                   (key_mode_x, top + index * R.RADIO_PITCH)
                   for index in range(3)})
    placed.update(R.HEADER_NODES)
    return placed


def sync_device_2d(placed):
    """`S_node = helper(x, y` and `S_node = { offset = { x * Q, y * Q }`."""
    text = DEVICE_2D.read_text()
    seen = set()

    def call(match):
        node, helper, x, y = match.groups()
        if node not in placed:
            return match.group(0)
        seen.add(node)
        return f"{node} = {helper}({placed[node][0]}, {placed[node][1]}"

    text = re.sub(r"(S_[A-Za-z0-9_]+) = (\w+)\((-?[\d.]+), (-?[\d.]+)",
                  call, text)

    def offset(match):
        node, x, y = match.groups()
        if node not in placed:
            return match.group(0)
        seen.add(node)
        return (f"{node} = {{\n\t\t\toffset = "
                f"{{ {placed[node][0]} * Q, {placed[node][1]} * Q }}")

    text = in_front_only(text, lambda chunk: re.sub(
        r"(S_[A-Za-z0-9_]+) = \{\s*\n\s*offset = "
        r"\{ (-?[\d.]+) \* Q, (-?[\d.]+) \* Q \}", offset, chunk))

    # Each fader also names the cap art for its signal-stage colour.
    def cap(match):
        node, x, y = match.groups()
        return f'{node} = fader({x}, {y}, "{R.fader_path(node)}")'

    text = re.sub(r"(S_fader_\w+) = fader\((-?[\d.]+), (-?[\d.]+)"
                  r"(?:, \"[^\"]*\")?\)", cap, text)
    DEVICE_2D.write_text(text)
    return seen


def sync_gui_lua(placed):
    """`helper(x, y, "name")` calls plus inline `transform = { x, y }` blocks."""
    text = GUI_LUA.read_text()
    seen = set()

    def named(match):
        helper, x, y, name = match.groups()
        node = {"fader": "S_fader_", "toggle": "S_toggle_",
                "status": "S_status_"}[helper] + name
        if node not in placed:
            return match.group(0)
        seen.add(node)
        return f'{helper}({placed[node][0]}, {placed[node][1]}, "{name}"'

    text = re.sub(r"\b(fader|toggle|status)\((-?[\d.]+), (-?[\d.]+), \"(\w+)\"",
                  named, text)

    def indexed(match):
        x, y, name, index = match.groups()
        node = f"S_radio_{name}_{index}"
        if node not in placed:
            return match.group(0)
        seen.add(node)
        return f'radio({placed[node][0]}, {placed[node][1]}, "{name}", {index}'

    text = re.sub(r"\bradio\((-?[\d.]+), (-?[\d.]+), \"(\w+)\", (\d+)",
                  indexed, text)

    def reassert(match):
        x, y, index = match.groups()
        node = f"S_momentary_keyMode_{index}"
        seen.add(node)
        return f"active_reassert({placed[node][0]}, {placed[node][1]}, {index}"

    text = re.sub(r"\bactive_reassert\((-?[\d.]+), (-?[\d.]+), (\d+)",
                  reassert, text)

    # Each fader also names the cap art for its signal-stage colour.
    def cap(match):
        x, y, name, rest = match.groups()
        node = f"S_fader_{name}"
        return f'fader({x}, {y}, "{name}", "{R.fader_path(node)}"{rest})'

    text = re.sub(r"\bfader\((-?[\d.]+), (-?[\d.]+), \"(\w+)\""
                  r"(?:, \"[^\"]*\")?((?:, (?:true|false))*)\)", cap, text)

    # Reason's own header furniture. patch_name takes bare coordinates; the
    # browse group and device name are blocks identified by their jbox type.
    def patch_name(match):
        x, y, rest = match.groups()
        node = "S_patch_name"
        seen.add(node)
        return f"patch_name({placed[node][0]}, {placed[node][1]},{rest}"

    text = in_front_only(text, lambda chunk: re.sub(
        r"\bpatch_name\((-?[\d.]+), (-?[\d.]+),([^)]*)", patch_name, chunk))

    for jbox_type, node in (("patch_browse_group", "S_patch_browse_group"),
                            ("device_name", "S_device_name")):
        def furniture(match, node=node):
            seen.add(node)
            return (f"{match.group(1)}transform = "
                    f"{{ {placed[node][0]}, {placed[node][1]} }}")

        text = in_front_only(text, lambda chunk, jbox_type=jbox_type: re.sub(
            rf"(jbox\.{jbox_type}\{{\s*\n\s*)"
            r"transform = \{ -?[\d.]+, -?[\d.]+ \}", furniture, chunk))

    # Inline blocks: rewrite the transform that precedes a known property.
    def block(match):
        head, x, y, middle, name = match.groups()
        node = PROPERTY_NODES.get(name)
        if node is None or node not in placed:
            return match.group(0)
        seen.add(node)
        return (f"{head}{{ {placed[node][0]}, {placed[node][1]} }}"
                f"{middle}property(\"{name}\")")

    # The tempered body is essential: a plain lazy `.*?` walks past the end of
    # this widget and pairs one block's transform with a LATER block's
    # property, silently stamping the wrong coordinates on both.
    text = in_front_only(text, lambda chunk: re.sub(
        r"(transform = )\{ (-?[\d.]+), (-?[\d.]+) \}"
        r"((?:(?!transform = \{)[\s\S])*?value = )property\(\"(\w+)\"\)",
        block, chunk))
    GUI_LUA.write_text(text)
    return seen


def main():
    placed = positions()
    seen = sync_device_2d(placed) | sync_gui_lua(placed)
    missed = sorted(set(placed) - seen)
    if missed:
        raise SystemExit(f"not written to any Lua file: {missed}")
    print(f"synced {len(placed)} node positions into "
          f"{DEVICE_2D.name} and {GUI_LUA.name}")


if __name__ == "__main__":
    main()
