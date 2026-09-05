#!/usr/bin/env python3
"""Build the complete deterministic YouKnow Reason GUI asset set.

The rack face is rendered directly at Reason's 5x authoring resolution. All
panel geometry, furniture, labels, and branding are drawn by this renderer;
no external reference bitmap is embedded.

`LAYOUT`, `REAR_CONTROLS`, and `REAR_CV_INPUTS` below define control geometry.
The silkscreen is drawn from them and `validate()` asserts that GUI2D and
GUI/Output place their widget nodes on the same panel coordinates, so a caption
can never drift away from the control it names.
"""

from pathlib import Path
import math
import os
import re
import shutil
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


Q = 5
WIDTH, HEIGHT = 754, 552
FOLDED_HEIGHT = 30
PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "GUI2D"
HD = PROJECT / "GUI" / "Output" / "HD"
SDK_ROOT = Path(os.environ.get("JUKEBOX_SDK_DIR", PROJECT.parents[1])).expanduser().resolve()
STANDARD_GUI2D = SDK_ROOT / "Examples" / "SimpleInstrument" / "GUI2D"

PANEL_FILES = {
    "Reason_GUI_front_root_Panel.png",
    "Reason_GUI_back_root_Panel.png",
    "Reason_GUI_folded_front_root_Panel.png",
    "Reason_GUI_folded_back_root_Panel.png",
}

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
# Reserve condensed lettering for the instrument wordmark. Operational text
# uses regular Arial, with bold Arial for section titles and the maker mark,
# so the 5x artwork stays readable in Reason's 1x rack view.
DISPLAY_FONT = FONT_DIR / "DIN Condensed Bold.ttf"
LABEL_FONT = FONT_DIR / "Arial.ttf"
SECTION_FONT = FONT_DIR / "Arial Bold.ttf"

# Matte blue-grey surfaces with clear white legends and coral/ice accents.
# Keep decoration quiet so controls remain distinct at actual rack size.
INK = (238, 241, 241)
MUTED = (184, 196, 202)
DIM = (119, 125, 122)
RED = (225, 119, 92)
ICE = (110, 193, 212)
PANEL = (39, 47, 53)
PANEL_DARK = (21, 28, 33)
EDGE_HIGHLIGHT = (76, 89, 96)
CAPTION = (235, 240, 242)
SCALE_INK = (192, 205, 211)
TICK_INK = (111, 130, 140)


# --- Control geometry, in logical (1x) units --------------------------------
# Widget sizes. Reason composites these strips over the backdrop, so the
# silkscreen has to reserve exactly this much room.
FADER_SIZE = (20, 88)
# Reason's standard pitch/mod wheel strips are 95 x 32640 HD pixels: 64
# frames, each 19 x 102 logical pixels.
WHEEL_SIZE = (19, 102)
KNOB_SIZE = 52
TOGGLE_SIZE = 20
LAMP_SIZE = 10
CV_JACK_SIZE = (15, 17)

# Handle travel inside a fader frame. hdgui_2D.lua repeats these as
# inset1/inset2/handle_size in HD pixels (x5) and gui.lua repeats them in
# logical units; validate() checks all three agree. If they drift, the drawn
# cap stops following the mouse.
FADER_MARGIN = 8
FADER_HANDLE = 14
FADER_TRAVEL = FADER_SIZE[1] - 2 * FADER_MARGIN - FADER_HANDLE

# Row band offsets, relative to a row's own top edge.
TITLE_H = 21
TITLE_OPTICAL_OFFSET = 0.5
HEAD_DY = 34          # caption above the control
BODY_H = 102
BOX_GAP = 10
GROUP_PADDING = 10
LABEL_GAP = 16
FRONT_HEADER_BOTTOM = 70

# Type sizes are logical (1x) pixels. Control captions stay at a uniform size;
# spacing checks reject crowded text instead of shrinking labels. Section
# titles and small scale legends retain bounded fitting for their own slots.
TITLE_SIZE = 12.0     # section title
CAPTION_SIZE = 10.5   # the word above a control
SCALE_SIZE = 9.0      # numbers and switch positions beside a fader
RADIO_SIZE = 9.5      # the word beside a radio button
CAPTION_FLOOR = 9.5
SCALE_FLOOR = 8.5

SIZES = {
    "fader": FADER_SIZE,
    "wheel": WHEEL_SIZE,
    "knob": (KNOB_SIZE, KNOB_SIZE),
    "toggle": (TOGGLE_SIZE, TOGGLE_SIZE),
    "wave_stack": (62, 52),
}


def px(value):
    if isinstance(value, tuple):
        return tuple(int(round(item * Q)) for item in value)
    return int(round(value * Q))


def font(size, display=False, strong=False):
    return ImageFont.truetype(str(DISPLAY_FONT if display else SECTION_FONT if strong else LABEL_FONT),
                              px(size))


def label(draw, xy, value, size, colour=INK, *, display=False, strong=False, anchor="mm"):
    face = font(size, display, strong)
    target_x, target_y = px(xy)
    bounds = draw.textbbox((0, 0), value, font=face, anchor=anchor)
    # Pillow's middle anchor follows font metrics rather than the visible ink.
    # Recenter the actual glyph bounds so legends from all three faces share a
    # true visual middle inside their headers and control slots.
    ink_x = (bounds[0] + bounds[2]) / 2
    ink_y = (bounds[1] + bounds[3]) / 2
    draw_x = target_x - ink_x if anchor[0] == "m" else target_x
    draw_y = target_y - ink_y if anchor[1] == "m" else target_y
    draw.text((draw_x, draw_y), value, fill=colour, font=face, anchor=anchor)


def text_width(value, size, display=False):
    """Rendered width in logical units."""
    return font(size, display).getlength(value) / Q


def contrast_ratio(foreground, background):
    def luminance(colour):
        channels = [value / 255 for value in colour]
        linear = [value / 12.92 if value <= 0.04045
                  else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def detents(*labels):
    """Scale captions for a stepped selector, listed from step 0 upwards.

    Step 0 is the bottom of the fader's travel, so the list reads bottom-up
    exactly like motherboard_def.lua's selector values.
    """
    last = len(labels) - 1
    return tuple((1.0 - index / last, text)
                 for index, text in enumerate(labels))


def span(low, mid, high):
    """Scale captions for a continuous control: bottom, middle, top."""
    return ((0.0, high), (0.5, mid), (1.0, low))


TEN = span("0", "5", "10")


def control(kind, name, x, caption, scale=None, ticks=5):
    return {"kind": kind, "name": name, "x": x, "caption": caption,
            "scale": scale, "ticks": ticks}


def fader(name, x, caption, scale=TEN, ticks=9):
    return control("fader", name, x, caption, scale, ticks)


def selector(name, x, caption, *labels):
    return control("fader", name, x, caption, detents(*labels), len(labels))


def wave_stack(x):
    return {
        "kind": "wave_stack", "name": "waveforms", "x": x,
        "caption": "", "scale": None, "ticks": 0,
        "properties": ("pulse", "saw"), "labels": ("PULSE", "SAW"),
    }


def fitted(text, room, ceiling, floor, display=False):
    """The largest size at or below `ceiling` that fits `room`."""
    size = ceiling
    while size > floor and text_width(text, size, display) > room:
        size -= 0.25
    return size


# --- Front panel layout -----------------------------------------------------
# Three generous rows: the tone-generating front half, filter/amplifier, and
# performance/setup controls. The 8RU height gives the controls their natural
# scale instead of asking every control to behave like a miniature annotation.
LAYOUT = [
    {
        "y": 80, "h": 144,
        "sections": [
            ("LFO", 10, 134, [
                fader("lfoRate", 40, "RATE"),
                fader("lfoDelay", 94, "DELAY"),
            ]),
            ("OSCILLATOR", 144, 392, [
                selector("range", 168, "RANGE", "16'", "8'", "4'"),
                fader("dcoLfo", 224, "LFO"),
                fader("pwm", 286, "PWM"),
                selector("pwmMode", 348, "SOURCE", "LFO", "MAN"),
            ]),
            ("MIXER", 402, 644, [
                wave_stack(416),
                fader("sub", 530, "SUB"),
                fader("noise", 600, "NOISE"),
            ]),
            ("HIGH PASS", 654, 744, [
                selector("highPass", 698, "", "BST", "1", "2", "3"),
            ]),
        ],
    },
    {
        "y": 234, "h": 144,
        "sections": [
            ("FILTER", 10, 294, [
                fader("cutoff", 31, "CUT"),
                fader("resonance", 76, "RES"),
                selector("envPolarity", 121, "POL", "+", "−"),
                fader("vcfEnv", 166, "ENV"),
                fader("vcfLfo", 211, "LFO"),
                fader("keyFollow", 256, "TRACK"),
            ]),
            ("AMPLIFIER", 304, 424, [
                selector("vcaMode", 339, "", "ENV", "GATE"),
                fader("vcaLevel", 386, "LEVEL"),
            ]),
            ("ENVELOPE", 434, 622, [
                fader("attack", 455, "ATT"),
                fader("decay", 499, "DEC"),
                fader("sustain", 543, "SUS"),
                fader("release", 587, "REL"),
            ]),
            ("CHORUS", 632, 744, [
                selector("chorus", 661, "", "OFF", "I", "II", "I+II"),
                fader("chorusNoise", 711, "HISS"),
            ]),
        ],
    },
    {
        "y": 388, "h": 154,
        "sections": [
            ("PERFORMANCE", 10, 366, [
                control("wheel", "pitchBend", 30, "BEND"),
                control("wheel", "modWheel", 88, "MOD"),
                fader("volume", 146, "VOLUME"),
                fader("benderDco", 204, "DCO"),
                fader("benderVcf", 262, "VCF"),
                fader("benderLfo", 320, "LFO"),
            ]),
            ("KEYBOARD", 376, 744, [
                control("knob", "portamento", 386, "GLIDE"),
                control("radio3", "keyMode", 448, "KEY MODE"),
                fader("transpose", 544, "SHIFT", span("−12", "0", "+12"), 5),
                fader("masterTune", 594, "TUNE", span("−50", "0", "+50")),
                fader("velocity", 646, "VEL"),
                fader("polyphony", 700, "VOICES",
                      ((1.0, "1"), (7 / 15, "8"), (0.0, "16")), 3),
            ]),
        ],
    },
]

REAR_INPUT_BOX = (60, 84, 360, 300)
REAR_OUTPUT_BOX = (394, 84, 694, 300)
REAR_ENGINE_BOX = (60, 316, 500, 518)
REAR_UNIT_BOX = (510, 316, 694, 518)
# Stock jack top-lefts; captions share the jack's horizontal centre.
REAR_CV_INPUTS = (
    ("note", "NOTE", 95, 155),
    ("gate", "GATE", 167, 155),
    ("cutoff", "CUTOFF", 239, 155),
    ("resonance", "RES", 311, 155),
    ("volume", "VOLUME", 95, 245),
    ("vca_level", "AMP", 167, 245),
    ("sub", "SUB", 239, 245),
    ("noise", "NOISE", 311, 245),
)
CV_CAPTION_SIZE = 12.0
CV_CAPTION_OFFSET = 22
REAR_CONTROLS = (
    {"kind": "radio", "name": "quality", "caption": "OVERSAMPLE",
     "x": 80, "center": 122, "top": 378,
     "labels": ("1x", "2x", "4x"), "remote": True, "automation": True},
    {"kind": "radio", "name": "vcfTanhMode", "caption": "SATURATION",
     "x": 188, "center": 230, "top": 378,
     "labels": ("EXACT", "FAST", "POLY"), "remote": True, "automation": True},
    {"kind": "radio", "name": "vcfFastEarlyMode", "caption": "EARLY MODEL",
     "x": 296, "center": 338, "top": 393,
     "labels": ("HERMITE", "CUBIC"), "remote": True, "automation": True},
    {"kind": "radio", "name": "vcfSolverMode", "caption": "FILTER SOLVER",
     "x": 404, "center": 446, "top": 378,
     "labels": ("MAX", "HIGH", "NORMAL"), "remote": True, "automation": True},
    {"kind": "fader", "name": "calibration", "caption": "CHARACTER",
     "x": 544, "center": 554, "top": 378,
     "scale": span("0", "100", "200%"), "ticks": 5,
     "remote": True, "automation": True},
    {"kind": "fader", "name": "aging", "caption": "AGING",
     "x": 636, "center": 646, "top": 378,
     "scale": span("0", "50", "100%"), "ticks": 5,
     "remote": True, "automation": True},
)
ENGINE_STATUS_SIZE = (56, 16)
ENGINE_STATUS_Y = 53
# Remote-controlled rear properties still need a read-only front representation
# for Reason's device-view contract. Editing stays exclusively on the rear.
ENGINE_STATUS = (
    {"name": "quality", "caption": "QUALITY", "x": 304, "preview": "1x"},
    {"name": "vcfTanhMode", "caption": "TANH", "x": 370,
     "preview": "POLY"},
    {"name": "vcfFastEarlyMode", "caption": "EARLY", "x": 436,
     "preview": "CUBIC"},
    {"name": "vcfSolverMode", "caption": "SOLVER", "x": 502,
     "preview": "NORMAL"},
    {"name": "calibration", "caption": "CHARACTER", "x": 568,
     "preview": "100%"},
    {"name": "aging", "caption": "AGING", "x": 634,
     "preview": "50%"},
)
PLACEHOLDER_POS = (347, 15)

# Radio clusters are laid out vertically so each position gets a full word.
KEY_MODE_LABELS = ("POLY 1", "POLY 2", "UNISON")
RADIO_PITCH = 29
RADIO_HIT_MARGIN = 1

# Header widgets, which sit outside the three control rows.
HEADER_NODES = {
    "S_patch_name": (330, 21),
    "S_patch_browse_group": (544, 17),
    "S_device_name": (610, 23),
    "S_note_on": (709, 51),
}

PREVIEW_PATCH_NAME = "Init"
# Preview the actual shipped patch instead of maintaining a second set of
# sound defaults. Stepped Rack properties store ordinals, continuous ones 0-1.
PREVIEW_VALUES = {
    item.attrib["property"]: ((item.text == "true")
                             if item.attrib["type"] == "boolean"
                             else float(item.text))
    for item in ET.parse(PROJECT / "Resources" / "Public" / "Init.repatch").findall(
        ".//Object[@name='custom_properties']/Value")
}
PREVIEW_MAXIMUM = {
    "keyMode": 2, "range": 2, "highPass": 3, "chorus": 3,
    "transpose": 24, "polyphony": 15,
}
PREVIEW_FRAME = {"aging": round(0.50 * 31)}
for name, value in PREVIEW_VALUES.items():
    frames = 2 if name in ("pulse", "saw") else 63 if name == "portamento" else 32
    PREVIEW_FRAME[name] = round(value * (frames - 1) / PREVIEW_MAXIMUM.get(name, 1))
PREVIEW_NODE_FRAME = {
    f"S_radio_keyMode_{int(PREVIEW_VALUES['keyMode'])}": 1,
    "S_radio_quality_0": 1,
    "S_radio_vcfTanhMode_2": 1,
    "S_radio_vcfFastEarlyMode_1": 1,
    "S_radio_vcfSolverMode_2": 1,
}


def body_top(row):
    return row["y"] + row["h"] - GROUP_PADDING - BODY_H


def widgets():
    """Every front-panel widget as (node, kind, name, x, y)."""
    for row in LAYOUT:
        body = body_top(row)
        for _, _, _, controls in row["sections"]:
            for item in row_controls(controls, body):
                yield item


def rear_widgets():
    """Controls intentionally kept off the performance face."""
    for item in REAR_CONTROLS:
        if item["kind"] == "fader":
            yield (f'S_fader_{item["name"]}', "fader", item["name"],
                   item["x"], item["top"])
            continue
        for index in range(len(item["labels"])):
            yield (f'S_radio_{item["name"]}_{index}', "toggle", item["name"],
                   item["x"], item["top"] + index * RADIO_PITCH)


def all_widgets():
    yield from widgets()
    yield from rear_widgets()


def centred_y(body, height):
    return body + (BODY_H - height) // 2


def radio_top(body):
    cluster_height = TOGGLE_SIZE + 2 * RADIO_PITCH
    return centred_y(body, cluster_height)


def row_controls(controls, body):
    for item in controls:
        kind, name, x = item["kind"], item["name"], item["x"]
        if kind == "radio3":
            top = radio_top(body)
            for index in range(3):
                yield (f"S_radio_{name}_{index}", "toggle", name,
                       x, top + index * RADIO_PITCH)
            continue
        if kind == "wave_stack":
            top = centred_y(body, SIZES["wave_stack"][1])
            for index, property_name in enumerate(item["properties"]):
                yield (f"S_toggle_{property_name}", "toggle", property_name,
                       x, top + index * (TOGGLE_SIZE + 12))
            continue
        if kind == "toggle":
            yield (f"S_toggle_{name}", "toggle", name,
                   x, centred_y(body, TOGGLE_SIZE))
        elif kind == "knob":
            yield (f"S_knob_{name}", "knob", name,
                   x, centred_y(body, KNOB_SIZE))
        elif kind == "wheel":
            yield (f"S_{'pitch_wheel' if name == 'pitchBend' else 'mod_wheel'}",
                   "wheel", name, x, centred_y(body, WHEEL_SIZE[1]))
        else:
            yield (f"S_fader_{name}", "fader", name,
                   x, centred_y(body, FADER_SIZE[1]))


def vertical_gradient(size, top, bottom, mode="RGB"):
    image = Image.new(mode, size)
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        amount = y / max(1, size[1] - 1)
        colour = tuple(round(a + (b - a) * amount) for a, b in zip(top, bottom))
        draw.line((0, y, size[0], y), fill=colour)
    return image


def base_panel(height=HEIGHT, rear=False):
    top = (25, 32, 38) if not rear else (25, 31, 36)
    bottom = (19, 25, 30) if not rear else (19, 25, 29)
    image = vertical_gradient((px(WIDTH), px(height)), top, bottom)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width - 1, image.height - 1), outline=(7, 9, 10), width=Q)
    draw.line((0, Q, image.width, Q), fill=(74, 77, 75), width=1)
    return image, ImageDraw.Draw(image)


def screw(draw, x, y):
    draw.ellipse(px((x - 3.2, y - 3.2, x + 3.2, y + 3.2)),
                 fill=(12, 14, 15), outline=(99, 102, 99), width=px(0.6))
    head = px((x - 2.5, y - 2.5, x + 2.5, y + 2.5))
    draw.ellipse(head, fill=(91, 94, 91), outline=(143, 145, 138),
                 width=px(0.45))
    draw.arc(head, 205, 330, fill=(31, 34, 34), width=px(0.7))
    draw.arc(head, 25, 150, fill=(190, 190, 178), width=px(0.45))
    draw.line(px((x - 1.7, y + 1.0, x + 1.7, y - 1.0)),
              fill=(15, 17, 18), width=px(0.7))
    draw.line(px((x - 1.45, y + 0.55, x + 1.45, y - 1.15)),
              fill=(132, 134, 128), width=px(0.25))


def screws(draw, height=HEIGHT):
    for x, y in ((5, 15), (749, 15), (5, height - 15), (749, height - 15)):
        screw(draw, x, y)


def section(draw, box, title, title_size=TITLE_SIZE):
    """Group controls with a quiet surface and a clear title."""
    x0, y0, _, _ = box
    draw.rounded_rectangle(px(box), radius=px(3), fill=PANEL)
    label(draw, (x0 + GROUP_PADDING, y0 + TITLE_H / 2 + TITLE_OPTICAL_OFFSET),
          title, title_size, strong=True, anchor="lm")


def fader_scale(draw, x, y, values, ticks, room):
    """Tick ladder and captions beside one fader, on its real handle travel."""
    # Generic 0-10 amounts need only position marks; preserve named selector
    # states, unit ranges and bipolar zero references.
    if values == TEN:
        values, ticks = (), 3
    centre = x + FADER_SIZE[0] / 2
    top = y + FADER_MARGIN + FADER_HANDLE / 2
    for index in range(ticks):
        yy = top + index * (FADER_TRAVEL / (ticks - 1))
        major = index in (0, ticks - 1) or ticks <= 5 or index == ticks // 2
        length = 4.0 if major else 2.2
        colour = SCALE_INK if major else TICK_INK
        draw.line(px((centre - 8.7, yy, centre - 8.7 + length, yy)),
                  fill=colour, width=px(0.9 if major else 0.65))

    size = min((fitted(text, room, SCALE_SIZE, SCALE_FLOOR)
                for _, text in values), default=SCALE_SIZE)
    for amount, text in values:
        label(draw, (centre - 10.4, top + amount * FADER_TRAVEL), text,
              size, SCALE_INK, anchor="rm")


def render_front():
    image, draw = base_panel()
    draw.rectangle(px((0, 0, WIDTH, FRONT_HEADER_BOTTOM)), fill=PANEL_DARK)
    label(draw, (20, 15), "PROTOCODUS", 14.0, ICE, strong=True, anchor="lm")
    label(draw, (20, 38), "YOUKNOW", 28.0, INK, display=True, anchor="lm")
    draw.rounded_rectangle(px((327, 16, 538, 39)), radius=px(2),
                           fill=(11, 19, 24), outline=(82, 103, 113), width=px(0.6))
    status_width, status_height = ENGINE_STATUS_SIZE
    for item in ENGINE_STATUS:
        x = item["x"]
        label(draw, (x + status_width / 2, 46), item["caption"], 8.0, MUTED)
    label(draw, (714, 42), "NOTE", 8.5, MUTED)
    screws(draw)

    for row in LAYOUT:
        y0, y1 = row["y"], row["y"] + row["h"]
        body = body_top(row)
        for title, x0, x1, controls in row["sections"]:
            section(draw, (x0, y0, x1, y1), title,
                    fitted(title, x1 - x0 - 20, TITLE_SIZE, 10.0))
            for item, (caption_room, scale_room) in zip(
                    controls, section_rooms(x0, x1, controls)):
                draw_caption(draw, item, y0)
                if item["kind"] == "fader" and item["scale"]:
                    fader_scale(draw, item["x"], centred_y(body, FADER_SIZE[1]), item["scale"],
                                item["ticks"], scale_room)
                if item["kind"] == "radio3":
                    draw_radio_labels(draw, item["x"], radio_top(body))
                if item["kind"] == "wave_stack":
                    draw_wave_labels(draw, item, body)

    save_panel(image, "Reason_GUI_front_root_Panel.png")
    return image


def draw_caption(draw, item, y0):
    if not item["caption"]:
        return
    label(draw, (caption_centre(item), y0 + HEAD_DY), item["caption"],
          CAPTION_SIZE, CAPTION)


def draw_wave_labels(draw, item, body):
    top = centred_y(body, SIZES["wave_stack"][1])
    for index, text in enumerate(item["labels"]):
        y = top + index * (TOGGLE_SIZE + 12) + TOGGLE_SIZE / 2
        label(draw, (item["x"] + TOGGLE_SIZE + 5, y), text,
              SCALE_SIZE, CAPTION, anchor="lm")


def draw_radio_labels(draw, x, top):
    for index, text in enumerate(KEY_MODE_LABELS):
        label(draw, (x + TOGGLE_SIZE + 4, top + index * RADIO_PITCH + TOGGLE_SIZE / 2),
              text, RADIO_SIZE, MUTED, anchor="lm")


def render_back():
    image, draw = base_panel(rear=True)
    draw.rectangle(px((0, 0, WIDTH, 66)), fill=PANEL_DARK)
    label(draw, (20, 15), "PROTOCODUS", 14.0, ICE, strong=True, anchor="lm")
    label(draw, (20, 40), "YOUKNOW", 28.0, INK, display=True, anchor="lm")
    screws(draw)
    section(draw, REAR_INPUT_BOX, "CV INPUTS")
    section(draw, REAR_OUTPUT_BOX, "AUDIO OUTPUTS")
    section(draw, REAR_ENGINE_BOX, "PROCESSING QUALITY")
    section(draw, REAR_UNIT_BOX, "UNIT MODEL")
    for name, title, x, y in REAR_CV_INPUTS:
        centre = x + CV_JACK_SIZE[0] / 2
        label(draw, (centre, y - CV_CAPTION_OFFSET), title,
              CV_CAPTION_SIZE, CAPTION, strong=True)
        if name == "note":
            label(draw, (centre, y + 33), "1 V/OCT", 9.5, MUTED)
    for x, title in ((494, "LEFT"), (584, "RIGHT")):
        label(draw, (x, 204), title, 12, CAPTION, strong=True)
    for item in REAR_CONTROLS:
        label(draw, (item["center"], 360), item["caption"], 10.0, CAPTION)
        if item["kind"] == "fader":
            fader_scale(draw, item["x"], item["top"], item["scale"],
                        item["ticks"], 42)
            continue
        for index, text in enumerate(item["labels"]):
            label(draw, (item["x"] + TOGGLE_SIZE + 6,
                         item["top"] + index * RADIO_PITCH + TOGGLE_SIZE / 2),
                  text if text[0].isdigit() else text.title(), 10.0, CAPTION, anchor="lm")
    label(draw, (280, 493), "SONG", 9.0, MUTED)
    label(draw, (554, 493), "PATCH", 9.0, MUTED)
    label(draw, (646, 493), "SONG", 9.0, MUTED)
    save_panel(image, "Reason_GUI_back_root_Panel.png")
    return image


def render_folded(front=True):
    image, draw = base_panel(FOLDED_HEIGHT, rear=not front)
    draw.rectangle(px((0, 0, WIDTH, 30)), fill=(17, 20, 21))
    label(draw, (17, 15), "YOUKNOW", 18.0, INK, display=True, anchor="lm")
    label(draw, (98, 15), "PROTOCODUS", 12.0, ICE, strong=True, anchor="lm")
    if front:
        draw.rounded_rectangle(px((297, 7, 507, 23)), radius=px(1.8),
                               fill=(5, 8, 8), outline=(58, 64, 63), width=px(0.45))
        label(draw, (719, 15), "NOTE", 8.0, MUTED)
    else:
        # Reason anchors folded cable bundles here. Make that anchor visible so
        # a connected folded device never appears to grow a cable from nowhere.
        cx, cy = 377, 15
        draw.ellipse(px((cx - 8, cy - 8, cx + 8, cy + 8)),
                     fill=(7, 9, 9), outline=(101, 105, 101), width=px(0.8))
        draw.ellipse(px((cx - 4.5, cy - 4.5, cx + 4.5, cy + 4.5)),
                     fill=(0, 1, 1), outline=(43, 47, 45), width=px(0.6))
    screw(draw, 5, 15)
    screw(draw, 749, 15)
    filename = "Reason_GUI_folded_front_root_Panel.png" if front else "Reason_GUI_folded_back_root_Panel.png"
    save_panel(image, filename)
    return image


def save_panel(image, canonical_name):
    gui2d = image.convert("RGBA")
    gui2d.save(OUT / canonical_name, optimize=True)


def fader_centre_y(frame, frames=32):
    return round(px(FADER_SIZE[1] - FADER_MARGIN - FADER_HANDLE / 2)
                 - frame / (frames - 1) * px(FADER_TRAVEL))


def fader_strip():
    frame_w, frame_h, frames = px(FADER_SIZE[0]), px(FADER_SIZE[1]), 32
    strip = Image.new("RGBA", (frame_w, frame_h * frames), (0, 0, 0, 0))
    for frame in range(frames):
        cell = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(cell)
        cx = frame_w // 2
        draw.rounded_rectangle((cx - px(2), px(2), cx + px(2), frame_h - px(2)),
                               radius=px(1.5), fill=(12, 14, 14, 255),
                               outline=(93, 116, 129, 220), width=px(0.7))
        draw.line((cx, px(4), cx, frame_h - px(4)),
                  fill=(57, 61, 59, 255), width=px(0.8))
        centre_y = fader_centre_y(frame, frames)
        cap_y = centre_y - px(FADER_HANDLE) // 2
        draw.rounded_rectangle((px(0.6), cap_y + px(1), frame_w - px(0.2),
                                cap_y + px(FADER_HANDLE) + px(2)),
                               radius=px(1), fill=(2, 3, 3, 125))
        cap = vertical_gradient((px(FADER_SIZE[0] - 2), px(FADER_HANDLE)),
                                (235, 241, 242, 255), (166, 187, 197, 255), "RGBA")
        mask = Image.new("L", cap.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cap.width - 1, cap.height - 1), radius=px(0.8), fill=255)
        cell.paste(cap, (px(1), cap_y), mask)
        draw = ImageDraw.Draw(cell)
        draw.rounded_rectangle((px(1), cap_y, frame_w - px(1), cap_y + px(FADER_HANDLE)),
                               radius=px(0.8), outline=(35, 37, 35, 235), width=px(0.5))
        draw.line((px(2), centre_y, frame_w - px(2), centre_y),
                  fill=RED + (255,), width=px(0.8))
        draw.line((px(2.2), cap_y + px(2), frame_w - px(2.2), cap_y + px(2)),
                  fill=(246, 241, 222, 120), width=px(0.35))
        strip.alpha_composite(cell, (0, frame * frame_h))
    return strip


def knob_strip():
    side, frames = px(KNOB_SIZE), 63
    scale = KNOB_SIZE / 40

    def k(value):
        return px(value * scale)

    strip = Image.new("RGBA", (side, side * frames), (0, 0, 0, 0))
    for frame in range(frames):
        cell = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        detent_draw = ImageDraw.Draw(cell)
        # Printed arc marks make the lone rotary control readable at a glance
        # and echo the fader ladders without consuming any extra panel space.
        for index in range(11):
            detent_angle = math.radians(-135 + index / 10 * 270)
            inner = k(17.0)
            outer = k(18.3 if index in (0, 5, 10) else 17.8)
            cx, cy = k(20), k(19)
            x0 = cx + math.sin(detent_angle) * inner
            y0 = cy - math.cos(detent_angle) * inner
            x1 = cx + math.sin(detent_angle) * outer
            y1 = cy - math.cos(detent_angle) * outer
            detent_draw.line((x0, y0, x1, y1),
                             fill=(219, 211, 188, 235),
                             width=k(0.55 if index in (0, 5, 10) else 0.35))
        shadow = Image.new("RGBA", cell.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse((k(5), k(6.5), k(37), k(38.5)), fill=(0, 0, 0, 180))
        cell.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(k(1.2))))
        draw = ImageDraw.Draw(cell)
        draw.ellipse((k(4), k(3), k(36), k(35)), fill=(12, 14, 14, 255), outline=(101, 99, 89, 255), width=k(0.7))
        for inset, colour in ((6, (48, 50, 47, 255)), (8, (28, 30, 29, 255)),
                              (10, (43, 44, 41, 255))):
            draw.ellipse((k(inset), k(inset - 1), k(40 - inset), k(39 - inset)), fill=colour)
        draw.ellipse((k(12), k(11), k(28), k(27)), fill=(32, 34, 33, 255), outline=(130, 126, 111, 210), width=k(0.5))
        angle = math.radians(-135 + frame / (frames - 1) * 270)
        cx, cy = k(20), k(19)
        ex = cx + math.sin(angle) * k(10.5)
        ey = cy - math.cos(angle) * k(10.5)
        draw.line((cx, cy, ex, ey), fill=INK + (255,), width=k(1.2))
        draw.ellipse((cx - k(1.2), cy - k(1.2), cx + k(1.2), cy + k(1.2)), fill=(18, 20, 19, 255))
        strip.alpha_composite(cell, (0, frame * side))
    return strip


def toggle_strip():
    side = px(TOGGLE_SIZE)
    scale = TOGGLE_SIZE / 15

    def t(value):
        return px(value * scale)

    strip = Image.new("RGBA", (side, side * 2), (0, 0, 0, 0))
    for frame in range(2):
        cell = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        draw = ImageDraw.Draw(cell)
        draw.rounded_rectangle((t(1.2), t(1.8), side - t(0.4), side - t(0.1)), radius=t(1.2), fill=(0, 0, 0, 110))
        top = (233, 241, 243, 255) if frame else (124, 148, 162, 255)
        bottom = (163, 188, 198, 255) if frame else (70, 92, 105, 255)
        face = vertical_gradient((t(12), t(11)), top, bottom, "RGBA")
        mask = Image.new("L", face.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, face.width - 1, face.height - 1), radius=t(0.8), fill=255)
        cell.paste(face, (t(1.5), t(1)), mask)
        draw = ImageDraw.Draw(cell)
        draw.rounded_rectangle((t(1.5), t(1), side - t(1.5), side - t(1.8)),
                               radius=t(0.8), outline=(25, 27, 26, 255), width=t(0.7))
        if frame:
            draw.line((t(3), t(3), side - t(3), t(3)), fill=RED + (255,), width=t(1))
        strip.alpha_composite(cell, (0, frame * side))
    return strip


def momentary_overlay_strip():
    """Two fully transparent frames for the active Key Mode hit surface."""
    side = px(TOGGLE_SIZE)
    return Image.new("RGBA", (side, side * 2), (0, 0, 0, 0))


def lamp_strip():
    side = px(LAMP_SIZE)
    strip = Image.new("RGBA", (side, side * 2), (0, 0, 0, 0))
    for frame in range(2):
        cell = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        if frame:
            glow = Image.new("RGBA", cell.size, (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse((px(0.2), px(0.2), px(9.8), px(9.8)), fill=RED + (105,))
            cell.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(1.3))))
        draw = ImageDraw.Draw(cell)
        draw.ellipse((px(2), px(2), px(8), px(8)), fill=(28, 9, 8, 255), outline=(5, 6, 6, 255), width=px(0.6))
        draw.ellipse((px(3), px(3), px(7), px(7)), fill=((244, 65, 52, 255) if frame else (85, 22, 19, 255)))
        if frame:
            draw.ellipse((px(3.6), px(3.4), px(5), px(4.8)), fill=(255, 218, 177, 225))
        strip.alpha_composite(cell, (0, frame * side))
    return strip


def standard_wheel(kind):
    """Load the stock Reason wheel used by the SDK's SimpleInstrument."""
    source = STANDARD_GUI2D / f"Reason_GUI_front_root_Wheel_{kind}.png"
    image = Image.open(source).convert("RGBA")
    expected = (px(WHEEL_SIZE[0]), px(WHEEL_SIZE[1]) * 64)
    assert image.size == expected, f"{source.name}: expected {expected}, got {image.size}"
    return image


def standard_asset(name):
    """Load required Reason furniture from the SDK's instrument example."""
    source = STANDARD_GUI2D / name
    assert source.is_file(), f"missing stock Reason asset: {source}"
    return Image.open(source).convert("RGBA")


def copy_frame(strip, frames, frame):
    frame_h = strip.height // frames
    return strip.crop((0, frame * frame_h, strip.width, (frame + 1) * frame_h))


def composite_front(panel, assets):
    """A stand-in render of the assembled face, for Reason's preview images."""
    image = panel.convert("RGBA")
    art = {"fader": ("Fader", 32, 16), "toggle": ("Toggle", 2, 0),
           "knob": ("Knob", 63, 22)}
    for node, kind, name, x, y in widgets():
        if kind == "wheel":
            path = "PitchWheel" if name == "pitchBend" else "ModWheel"
            frames, frame = 64, 32 if name == "pitchBend" else 0
        else:
            path, frames, frame = art[kind]
            frame = PREVIEW_NODE_FRAME.get(node, PREVIEW_FRAME.get(name, frame))
        image.alpha_composite(copy_frame(assets[path], frames, frame), px((x, y)))
    image.alpha_composite(copy_frame(assets["Lamp"], 2, 0), px(HEADER_NODES["S_note_on"]))
    image.alpha_composite(Image.open(OUT / "PatchBrowseGroup.png").convert("RGBA"),
                          px(HEADER_NODES["S_patch_browse_group"]))
    image.alpha_composite(assets["TapeHorz"], px(HEADER_NODES["S_device_name"]))
    preview_draw = ImageDraw.Draw(image)
    label(preview_draw, (432, 29), PREVIEW_PATCH_NAME, 11.0, ICE)
    status_width, status_height = ENGINE_STATUS_SIZE
    for item in ENGINE_STATUS:
        label(
            preview_draw,
            (item["x"] + status_width / 2,
             ENGINE_STATUS_Y + status_height / 2),
            item["preview"], 11.0, ICE,
        )
    label(preview_draw, (650, 29.5), "YOUKNOW", 5.5, PANEL_DARK)
    return image


def composite_back(panel, assets):
    image = panel.convert("RGBA")
    image.alpha_composite(assets["Placeholder"], px(PLACEHOLDER_POS))
    for _, _, x, y in REAR_CV_INPUTS:
        image.alpha_composite(copy_frame(assets["CVJack"], 3, 0), px((x, y)))
    for x, y in ((485, 230), (575, 230)):
        image.alpha_composite(copy_frame(assets["AudioJack"], 3, 0), px((x, y)))
    for node, kind, name, x, y in rear_widgets():
        if kind == "fader":
            image.alpha_composite(
                copy_frame(assets["Fader"], 32, PREVIEW_FRAME[name]), px((x, y)))
        else:
            image.alpha_composite(
                copy_frame(assets["Toggle"], 2, PREVIEW_NODE_FRAME.get(node, 0)),
                px((x, y)))
    image.alpha_composite(assets["TapeVert"], px((20, 150)))
    name = Image.new("RGBA", px((80, 13)), (0, 0, 0, 0))
    label(ImageDraw.Draw(name), (40, 6.5), "YOUKNOW", 5.5, PANEL_DARK)
    image.alpha_composite(name.transpose(Image.Transpose.ROTATE_90), px((20, 150)))
    return image


def composite_folded(panel, assets, front=True):
    image = panel.convert("RGBA")
    image.alpha_composite(assets["TapeHorz"], px((600, 8)))
    if front:
        image.alpha_composite(Image.open(OUT / "PatchBrowseGroup.png").convert("RGBA"), px((510, 4)))
        image.alpha_composite(copy_frame(assets["Lamp"], 2, 0), px((690, 10)))
        label(ImageDraw.Draw(image), (402, 15), PREVIEW_PATCH_NAME, 7.0, ICE)
    label(ImageDraw.Draw(image), (640, 14.5), "YOUKNOW", 7.0, PANEL_DARK)
    return image


def contained(image, size):
    """Aspect-preserving fit into one of Reason's fixed preview canvases."""
    width, height = size
    scale = min(width / image.width, height / image.height)
    fitted_size = (max(1, round(image.width * scale)),
                   max(1, round(image.height * scale)))
    fitted_image = image.convert("RGBA").resize(fitted_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(fitted_image,
                           ((width - fitted_size[0]) // 2,
                            (height - fitted_size[1]) // 2))
    return canvas


def compact_face(size, front=True):
    """A clean silhouette for slots too small to carry full panel legends."""
    width, height = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    panel_h = min(height, max(1, round(width * HEIGHT / WIDTH)))
    top = (height - panel_h) // 2
    right, bottom = width - 1, top + panel_h - 1
    draw = ImageDraw.Draw(image)
    radius = max(1, round(panel_h * 0.045))
    draw.rounded_rectangle((0, top, right, bottom), radius=radius,
                           fill=PANEL_DARK, outline=EDGE_HIGHLIGHT)
    header_h = max(2, round(panel_h * 0.16))
    if width >= 30:
        face = ImageFont.truetype(str(DISPLAY_FONT), max(6, round(panel_h * 0.2)))
        draw.text((max(2, round(width * 0.05)), top + header_h / 2), "YOUKNOW",
                  fill=INK, font=face, anchor="lm")
    bay_top = top + header_h + max(2, round(panel_h * 0.08))
    bay_bottom = bottom - max(1, round(panel_h * 0.08))
    gap = max(1, round(width * 0.025))
    margin = max(2, round(width * 0.04))
    bay_width = (width - 2 * margin - 2 * gap) / 3
    for index in range(3):
        left = round(margin + index * (bay_width + gap))
        bay_right = round(left + bay_width)
        draw.rounded_rectangle((left, bay_top, bay_right, bay_bottom),
                               radius=max(1, radius // 2), fill=PANEL)
    return image


def render_previews(front, back, folded_front, folded_back):
    # Fixed Rack-unit preview sizes from the SDK examples, scaled to this 8RU
    # device. Preserving the raw panel aspect ratio here leaves the browser
    # images a few pixels short and makes the device look undersized.
    thumbs = [("Reason_Icon128x128", 128, 96, 6), ("Reason_Navigator", 126, 92, 5),
              ("Reason_Palette", 130, 96, 6), ("Reason_TrackListIcon", 54, 40, 3)]
    for prefix, width, height, folded_height in thumbs:
        for face, image in (("front", front), ("back", back)):
            preview = (compact_face((width, height), face == "front")
                       if prefix == "Reason_TrackListIcon"
                       else contained(image, (width, height)))
            preview.save(OUT / f"{prefix}_{face}_root_Panel.png", optimize=True)
        for face, image in (("front", folded_front), ("back", folded_back)):
            contained(image, (width, folded_height)).save(
                OUT / f"{prefix}_{face}_folded_root_Panel.png", optimize=True)

    contained(front, (650, 480)).save(HD / "DevicePaletteImage.png", optimize=True)
    contained(front, (630, 460)).save(HD / "DeviceNavigator.png", optimize=True)
    contained(folded_front, (630, 25)).save(HD / "DeviceNavigatorFolded.png", optimize=True)
    contained(front, (270, 200)).save(HD / "DeviceTrackListThumbnail.png", optimize=True)
    atlas = Image.new("RGBA", (779, 518), (0, 0, 0, 0))
    # DeviceIcon uses fixed slot centres shared by all device heights. These
    # 8RU rectangles keep each rendition centred in its SDK atlas slot.
    for x, y, width, height in ((185, 4, 16, 16), (141, 7, 24, 18), (88, 7, 32, 26),
                                (3, 8, 48, 40), (3, 64, 64, 50), (3, 141, 128, 98),
                                (264, 67, 512, 384), (3, 290, 256, 194)):
        cell = (compact_face((width, height)) if width <= 64
                else contained(front, (width, height)))
        atlas.alpha_composite(cell, (x, y))
    atlas.save(HD / "DeviceIcon.png", optimize=True)


def check_layout():
    """The silkscreen and both panel definitions must agree on every node.

    `device_2D.lua` names its nodes, so it is checked node by node. `gui.lua`
    is the format-4.0 mirror and carries bare transforms, so it is checked as
    a set of occupied coordinates.
    """
    project = OUT.parent
    device = (project / "GUI2D" / "device_2D.lua").read_text()
    gui = (project / "GUI" / "Output" / "gui.lua").read_text()

    expected = {node: (float(x), float(y)) for node, _, _, x, y in all_widgets()}
    expected["S_placeholder"] = tuple(map(float, PLACEHOLDER_POS))
    expected.update({f"S_cv_input_{name}": (float(x), float(y))
                     for name, _, x, y in REAR_CV_INPUTS})
    expected.update({
        f'S_status_{item["name"]}': (float(item["x"]), float(ENGINE_STATUS_Y))
        for item in ENGINE_STATUS
    })
    key_mode_x = next(
        item["x"] for row in LAYOUT for _, _, _, controls in row["sections"]
        for item in controls if item["name"] == "keyMode")
    expected.update({
        f"S_momentary_keyMode_{index}": (float(key_mode_x), float(radio_top(
            body_top(LAYOUT[2])) + index * RADIO_PITCH))
        for index in range(3)
    })
    placed = {node: (float(x), float(y)) for node, x, y in re.findall(
        r"(S_[A-Za-z0-9_]+)\s*=\s*\w+\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)", device)}
    for node, position in expected.items():
        assert node in placed, f"device_2D.lua: {node} is not placed"
        assert placed[node] == position, (
            f"device_2D.lua: {node} at {placed[node]}, "
            f"silkscreen drawn at {position}")

    mirrored = {(float(x), float(y)) for x, y in re.findall(
        r"transform\s*=\s*\{\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\}", gui)}
    mirrored |= {(float(x), float(y)) for x, y in re.findall(
        r"\b(?:fader|toggle|radio|status)\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,", gui)}
    missing = sorted(set(expected.values()) - mirrored)
    assert not missing, f"gui.lua: no widget at {missing}"

    # Coordinates alone are not enough: two sliders could trade properties
    # and the old set-based check would still pass. Match every helper call to
    # the property it is meant to control.
    expected_faders = {(name, float(x), float(y))
                       for node, kind, name, x, y in all_widgets()
                       if kind == "fader"}
    actual_faders = {(name, float(x), float(y)) for x, y, name in re.findall(
        r'\bfader\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*"([^"]+)"'
        r'(?:\s*,\s*(?:true|false))?(?:\s*,\s*(?:true|false))?\s*\)', gui)}
    assert actual_faders == expected_faders, "gui.lua: fader property/position drift"

    expected_toggles = {(name, float(x), float(y))
                        for node, _, name, x, y in widgets()
                        if node.startswith("S_toggle_")}
    actual_toggles = {(name, float(x), float(y)) for x, y, name in re.findall(
        r'\btoggle\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*"([^"]+)"\s*\)', gui)}
    assert actual_toggles == expected_toggles, "gui.lua: toggle property/position drift"

    expected_radios = {(name, int(node.rsplit("_", 1)[1]), float(x), float(y))
                       for node, _, name, x, y in all_widgets()
                       if node.startswith("S_radio_")}
    actual_radios = {(name, int(index), float(x), float(y))
                     for x, y, name, index in re.findall(
        r'\bradio\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*"([^"]+)"\s*,\s*(\d+)'
        r'(?:\s*,\s*(?:true|false))?(?:\s*,\s*(?:true|false))?\s*\)', gui)}
    assert actual_radios == expected_radios, "gui.lua: radio property/position drift"
    for index, y in enumerate(radio_top(body_top(LAYOUT[2]))
                              + index * RADIO_PITCH
                              for index in range(3)):
        assert f'active_reassert({key_mode_x}, {y}, {index})' in gui, (
            f"gui.lua: active Key Mode {index} overlay drift")

    hdgui = (project / "GUI2D" / "hdgui_2D.lua").read_text()
    gui_front = gui[gui.index("front = jbox.panel"):gui.index("folded_front = jbox.panel")]
    hdgui_front = hdgui[
        hdgui.index("front = jbox.panel"):hdgui.index("folded_front = jbox.panel")
    ]
    for definition in (gui, hdgui):
        status_helper = definition[definition.index("local function status"):
                                   definition.index("front = jbox.panel")]
        assert "read_only = true" in status_helper
        assert "show_automation_rect = true" in status_helper
    status_helper = gui[gui.index("local function status"):gui.index("front = jbox.panel")]
    assert f"width = {ENGINE_STATUS_SIZE[0]}" in status_helper
    assert f"height = {ENGINE_STATUS_SIZE[1]}" in status_helper
    for item in ENGINE_STATUS:
        name = item["name"]
        node = f'S_status_{name}'
        assert f'status({item["x"]}, {ENGINE_STATUS_Y}, "{name}")' in gui_front
        assert f'status("{node}", "{name}")' in hdgui_front
    device_back = device[device.index("back = {"):device.index("folded_back = {")]
    gui_back = gui[gui.index("back = jbox.panel"):gui.index("folded_back = jbox.panel")]
    hdgui_back = hdgui[hdgui.index("back = jbox.panel"):hdgui.index("folded_back = jbox.panel")]
    motherboard = (project / "motherboard_def.lua").read_text()
    expected_cv_paths = {f"/cv_inputs/{name}_cv" for name, _, _, _ in REAR_CV_INPUTS}
    for definition in (gui, hdgui):
        cv_paths = re.findall(r'socket\s*=\s*"(/cv_inputs/[^\"]+)"', definition)
        assert set(cv_paths) == expected_cv_paths and len(cv_paths) == len(expected_cv_paths), (
            "CV socket inventory differs from the rear panel")
    for name, _, x, y in REAR_CV_INPUTS:
        node, socket = f"S_cv_input_{name}", f"/cv_inputs/{name}_cv"
        assert f'{node} = widget({x}, {y}, "CVJack", 3)' in device_back
        assert (f'graphics = {{ node = "{node}" }},\n\t\t\tsocket = "{socket}",') in hdgui_back
        assert (f'transform = {{ {x}, {y} }},\n\t\t\tsocket = "{socket}",') in gui_back
        assert re.search(rf'\b{name}_cv\s*=\s*jbox\.cv_input\s*\{{', motherboard), (
            f"{socket}: missing motherboard input")
    for item in REAR_CONTROLS:
        automation_suffix = "" if item["automation"] else (
            ", true, false" if item["remote"] else ", false, false")
        if item["kind"] == "fader":
            node = f'S_fader_{item["name"]}'
            assert f'{node} = fader({item["x"]}, {item["top"]})' in device_back
            assert (f'fader({item["x"]}, {item["top"]}, "{item["name"]}", '
                    f'{str(item["automation"]).lower()}, {str(item["remote"]).lower()})') in gui_back
            assert (f'fader("{node}", "{item["name"]}", {str(item["automation"]).lower()}, '
                    f'{str(item["remote"]).lower()})') in hdgui_back
        else:
            for index in range(len(item["labels"])):
                y = item["top"] + index * RADIO_PITCH
                node = f'S_radio_{item["name"]}_{index}'
                assert f'{node} = toggle({item["x"]}, {y})' in device_back
                assert (f'radio({item["x"]}, {y}, "{item["name"]}", '
                        f'{index}{automation_suffix})') in gui_back
                assert (f'radio("{node}", "{item["name"]}", '
                        f'{index}{automation_suffix})') in hdgui_back
        remote_mapping = f'remote("{item["name"]}"'
        if item["remote"]:
            assert remote_mapping in motherboard
        else:
            assert remote_mapping not in motherboard
    assert re.search(r'fader\([^\n]+"chorusNoise"\)', gui_front)
    assert 'fader("S_fader_chorusNoise", "chorusNoise")' in hdgui_front
    for item in REAR_CONTROLS:
        name = re.escape(item["name"])
        assert not re.search(rf'(?:fader|radio)\([^\n]*"{name}"', gui_front), (
            f"{item['name']}: rear setting has an editable front widget")
        assert not re.search(rf'(?:fader|radio)\([^\n]*"{name}"', hdgui_front), (
            f"{item['name']}: rear setting has an editable GUI2D front widget")
    assert f"handle_size = {px(FADER_HANDLE)}" in hdgui, "hdgui handle_size drift"
    assert f"inset1 = {px(FADER_MARGIN)}" in hdgui, "hdgui inset1 drift"
    assert f"inset2 = {px(FADER_MARGIN)}" in hdgui, "hdgui inset2 drift"
    assert f"handle_size = {FADER_HANDLE}" in gui, "gui.lua handle_size drift"
    assert f"inset1 = {FADER_MARGIN}" in gui, "gui.lua inset1 drift"
    assert f"inset2 = {FADER_MARGIN}" in gui, "gui.lua inset2 drift"
    assert 'orientation = "vertical"' in gui, "gui.lua fader orientation drift"
    assert "inverted = false" in gui, "gui.lua fader inversion drift"

    assert RADIO_PITCH > TOGGLE_SIZE + 2 * RADIO_HIT_MARGIN, (
        "adjacent Key Mode hit areas overlap")
    assert "top = Q, right = Q * 2, bottom = Q" in hdgui, (
        "hdgui radio/reassert vertical hit margins drift")
    assert "margins = { left = 2, top = 1, right = 2, bottom = 1 }" in gui, (
        "gui.lua radio/reassert vertical hit margins drift")


def control_width(item):
    return SIZES["toggle" if item["kind"] == "radio3" else item["kind"]][0]


def caption_centre(item):
    return item["x"] + (32 if item["kind"] == "radio3"
                        else control_width(item) / 2)


def section_rooms(x0, x1, controls):
    """Room a caption and a scale caption have, per control, in logical units.

    Shared by the renderer and the checker so the size drawn is the size
    verified.
    """
    centres = [caption_centre(item) for item in controls]
    last = len(controls) - 1
    rooms = []
    for index, item in enumerate(controls):
        left = x0 + GROUP_PADDING if index == 0 else (centres[index - 1] + centres[index]) / 2
        right = x1 - GROUP_PADDING if index == last else (centres[index] + centres[index + 1]) / 2
        before = x0 + GROUP_PADDING if index == 0 else (
            controls[index - 1]["x"] + control_width(controls[index - 1]) + 1)
        rooms.append((2 * min(centres[index] - left, right - centres[index]),
                      centres[index] - 10.4 - before))
    return rooms


def text_ink_width(value, size, strong=False):
    left, _, right, _ = font(size, strong=strong).getbbox(value, anchor="mm")
    return (right - left) / Q


def check_label_row(labels, strong=False):
    """Keep independent labels apart by their visible glyph bounds."""
    previous = None
    for centre, text, size in sorted(labels):
        if not text:
            continue
        half_width = text_ink_width(text, size, strong) / 2
        if previous:
            gap = centre - half_width - previous[1]
            assert gap >= LABEL_GAP, (
                f"{previous[0]!r} / {text!r}: {gap:.1f}px between labels, "
                f"need {LABEL_GAP}px")
        previous = (text, centre + half_width)


def check_spacing():
    """Nothing may overlap, and no caption may outgrow the room it has.

    Legibility is the whole point of the three-row layout, so it is asserted
    rather than eyeballed: a caption that no longer fits its slot fails the
    render instead of quietly colliding with its neighbour.
    """
    # Small functional legends use the brighter secondary ink. Keep them at
    # normal-text contrast even if the palette is adjusted later.
    assert contrast_ratio(MUTED, PANEL) >= 4.5
    assert abs(TITLE_H / 2 + TITLE_OPTICAL_OFFSET
               - (1 + TITLE_H) / 2) < 0.01, (
        "section-title target must be centred in the dark header")
    assert LAYOUT[0]["y"] - FRONT_HEADER_BOTTOM == BOX_GAP
    assert HEIGHT - (LAYOUT[-1]["y"] + LAYOUT[-1]["h"]) == BOX_GAP
    for previous, current in zip(LAYOUT, LAYOUT[1:]):
        assert current["y"] - (previous["y"] + previous["h"]) == BOX_GAP
    for row in LAYOUT:
        assert row["sections"][0][1] >= BOX_GAP
        assert WIDTH - row["sections"][-1][2] >= BOX_GAP
        for left, right in zip(row["sections"], row["sections"][1:]):
            assert right[1] - left[2] >= BOX_GAP
    rear_top_boxes = (REAR_INPUT_BOX, REAR_OUTPUT_BOX)
    assert rear_top_boxes[0][0] >= BOX_GAP
    assert WIDTH - rear_top_boxes[-1][2] >= BOX_GAP
    assert rear_top_boxes[1][0] - rear_top_boxes[0][2] >= BOX_GAP
    assert rear_top_boxes[0][1] - 66 >= BOX_GAP
    assert REAR_ENGINE_BOX[0] == REAR_INPUT_BOX[0]
    assert REAR_UNIT_BOX[2] == REAR_OUTPUT_BOX[2]
    assert REAR_UNIT_BOX[0] - REAR_ENGINE_BOX[2] == BOX_GAP
    assert REAR_ENGINE_BOX[1] - rear_top_boxes[0][3] >= BOX_GAP
    assert HEIGHT - REAR_ENGINE_BOX[3] >= BOX_GAP
    x0, y0, x1, y1 = REAR_INPUT_BOX
    for _, caption, x, y in REAR_CV_INPUTS:
        centre = x + CV_JACK_SIZE[0] / 2
        half_caption = text_ink_width(caption, CV_CAPTION_SIZE, True) / 2
        assert x >= x0 + GROUP_PADDING and x + CV_JACK_SIZE[0] <= x1 - GROUP_PADDING
        assert centre - half_caption >= x0 + GROUP_PADDING
        assert centre + half_caption <= x1 - GROUP_PADDING
        assert y - CV_CAPTION_OFFSET - CV_CAPTION_SIZE / 2 >= y0 + TITLE_H + GROUP_PADDING
        assert y + CV_JACK_SIZE[1] <= y1 - GROUP_PADDING
    for top in sorted({y for _, _, _, y in REAR_CV_INPUTS}):
        check_label_row([(x + CV_JACK_SIZE[0] / 2, caption, CV_CAPTION_SIZE)
                         for _, caption, x, y in REAR_CV_INPUTS if y == top], strong=True)

    # The fixed header and folded furniture must retain breathing room around
    # Reason's native patch/name widgets.
    assert 20 + text_width("YOUKNOW", 28.0, True) + 24 <= 160
    assert 20 + font(14, strong=True).getlength("PROTOCODUS") / Q < 300
    assert 17 + text_width("YOUKNOW", 18.0, True) + 16 <= 98
    assert 98 + font(12, strong=True).getlength("PROTOCODUS") / Q + 12 <= 202
    status_width, status_height = ENGINE_STATUS_SIZE
    previous_end = ENGINE_STATUS[0]["x"]
    for item in ENGINE_STATUS:
        assert item["x"] >= previous_end
        assert item["x"] + status_width <= 690
        assert ENGINE_STATUS_Y + status_height <= FRONT_HEADER_BOTTOM
        assert text_width(item["caption"], 8.0) <= status_width
        assert text_width(item["preview"], 11.0) <= status_width
        previous_end = item["x"] + status_width
    assert previous_end + BOX_GAP <= HEADER_NODES["S_note_on"][0]

    for row in LAYOUT:
        check_label_row([
            (caption_centre(item), item["caption"], CAPTION_SIZE)
            for _, _, _, controls in row["sections"] for item in controls
        ])
    check_label_row([
        (item["center"], item["caption"], 10.0) for item in REAR_CONTROLS
    ])
    check_label_row([
        (item["x"] + status_width / 2, item["caption"], 8.0)
        for item in ENGINE_STATUS
    ])
    # Check the widest status for every choice, not only the preview defaults.
    statuses = []
    for item, rear in zip(ENGINE_STATUS, REAR_CONTROLS):
        assert item["name"] == rear["name"]
        choices = rear.get("labels") or tuple(
            text if text.endswith("%") else text + "%" for _, text in rear["scale"])
        widest = max(choices, key=lambda text: text_ink_width(text, 11.0))
        assert text_ink_width(widest, 11.0) <= status_width
        statuses.append((item["x"] + status_width / 2, widest, 11.0))
    check_label_row(statuses)

    # Key-mode names and transpose numbers share the same three baselines.
    keyboard = LAYOUT[2]["sections"][1][3]
    key_mode = next(item for item in keyboard if item["name"] == "keyMode")
    transpose = next(item for item in keyboard if item["name"] == "transpose")
    key_end = key_mode["x"] + TOGGLE_SIZE + 4 + max(
        text_ink_width(text, RADIO_SIZE) for text in KEY_MODE_LABELS)
    transpose_left = transpose["x"] + FADER_SIZE[0] / 2 - 10.4 - max(
        text_ink_width(text, SCALE_SIZE) for _, text in transpose["scale"])
    assert transpose_left - key_end >= LABEL_GAP, (
        "Key Mode names and Shift values need more separation")

    for row in LAYOUT:
        for title, x0, x1, controls in row["sections"]:
            edge = x0 + GROUP_PADDING
            for item in controls:
                assert item["x"] >= edge, (
                    f"{title}: {item['name']} starts at {item['x']}, "
                    f"previous control ends at {edge}")
                edge = item["x"] + control_width(item)
            assert edge <= x1 - GROUP_PADDING, f"{title}: controls overflow the section"

            for item, (caption_room, scale_room) in zip(
                    controls, section_rooms(x0, x1, controls)):
                width = text_width(item["caption"], CAPTION_SIZE)
                assert width <= caption_room, (
                    f"{title}: caption {item['caption']!r} needs {width:.1f} "
                    f"at the {CAPTION_SIZE} size but has "
                    f"{caption_room:.1f} -- shorten it or spread the row")

                # Scale captions hang off the left of the fader, so they have
                # to clear whatever control sits before them.
                if not item["scale"]:
                    continue
                widest = max(text_width(text, SCALE_FLOOR)
                             for _, text in item["scale"])
                assert widest <= scale_room, (
                    f"{title}: {item['name']} scale caption needs "
                    f"{widest:.1f} even at the {SCALE_FLOOR} floor but has "
                    f"{scale_room:.1f}")

    for index, item in enumerate(REAR_CONTROLS):
        x0, y0, x1, y1 = (REAR_UNIT_BOX if item["kind"] == "fader"
                          else REAR_ENGINE_BOX)
        assert x0 + 2 <= item["x"]
        width = FADER_SIZE[0] if item["kind"] == "fader" else TOGGLE_SIZE
        assert item["x"] + width <= x1 - 2
        assert y0 + TITLE_H <= item["top"]
        if item["kind"] == "fader":
            assert item["top"] + FADER_SIZE[1] <= y1 - 2
        else:
            assert (item["top"] + (len(item["labels"]) - 1) * RADIO_PITCH
                    + TOGGLE_SIZE <= y1 - 2)
        assert text_width(item["caption"], CAPTION_FLOOR) <= 100
        if item["kind"] == "radio" and index + 1 < len(REAR_CONTROLS):
            label_end = (item["x"] + TOGGLE_SIZE + 4
                         + max(text_width(text, RADIO_SIZE)
                               for text in item["labels"]))
            assert label_end < REAR_CONTROLS[index + 1]["x"] - 8

    centres = [fader_centre_y(frame) for frame in range(32)]
    assert centres == sorted(centres, reverse=True), "fader frames are not monotonic"
    assert centres[0] == px(FADER_SIZE[1] - FADER_MARGIN - FADER_HANDLE / 2)
    assert centres[-1] == px(FADER_MARGIN + FADER_HANDLE / 2)


def validate():
    assert 'default_patch = "/Public/Init.repatch"' in (PROJECT / "info.lua").read_text()
    for _, kind, name, _, _ in widgets():
        if kind == "wheel":
            continue
        frames = {"fader": 32, "toggle": 2, "knob": 63}[kind]
        if name != "keyMode":
            assert 0 <= PREVIEW_FRAME[name] < frames, f"{name}: invalid preview frame"
    fader_h = px(FADER_SIZE[1]) * 32
    expected = {
        "Reason_GUI_front_root_Panel.png": (3770, 2760), "Reason_GUI_back_root_Panel.png": (3770, 2760),
        "Reason_GUI_folded_front_root_Panel.png": (3770, 150), "Reason_GUI_folded_back_root_Panel.png": (3770, 150),
        "Fader.png": (px(FADER_SIZE[0]), fader_h),
        "Knob.png": (px(KNOB_SIZE), px(KNOB_SIZE) * 63),
        "Toggle.png": (px(TOGGLE_SIZE), px(TOGGLE_SIZE) * 2),
        "MomentaryOverlay.png": (px(TOGGLE_SIZE), px(TOGGLE_SIZE) * 2),
        "EngineDisplay.png": px(ENGINE_STATUS_SIZE),
        "Lamp.png": (50, 100),
        "PitchWheel.png": (95, 32640), "ModWheel.png": (95, 32640),
        "AudioJack.png": (95, 315), "CVJack.png": (75, 255),
        "TapeHorz.png": (400, 65), "TapeVert.png": (65, 400),
        "Placeholder.png": (300, 100),
    }
    for name, size in expected.items():
        actual = Image.open(OUT / name).size
        assert actual == size, f"{name}: expected {size}, got {actual}"
    for name, frames in (("Fader.png", 32), ("Knob.png", 63), ("Toggle.png", 2),
                         ("MomentaryOverlay.png", 2),
                         ("Lamp.png", 2), ("PitchWheel.png", 64), ("ModWheel.png", 64),
                         ("AudioJack.png", 3), ("CVJack.png", 3)):
        assert Image.open(OUT / name).height % frames == 0, f"{name}: bad frame strip"
    for name, frames in (("Fader.png", 32), ("Knob.png", 63), ("Toggle.png", 2),
                         ("Lamp.png", 2), ("PitchWheel.png", 64), ("ModWheel.png", 64),
                         ("AudioJack.png", 3), ("CVJack.png", 3)):
        strip = Image.open(OUT / name).convert("RGBA")
        frame_h = strip.height // frames
        first = strip.crop((0, 0, strip.width, frame_h))
        last = strip.crop((0, strip.height - frame_h, strip.width, strip.height))
        assert first.getbbox() and last.getbbox(), f"{name}: blank visible frame"
        assert ImageChops.difference(first, last).convert("RGB").getbbox(), (
            f"{name}: states do not differ")
    for kind, name in (("Pitch", "PitchWheel.png"), ("Mod", "ModWheel.png")):
        source = Image.open(STANDARD_GUI2D / f"Reason_GUI_front_root_Wheel_{kind}.png").convert("RGBA")
        generated = Image.open(OUT / name).convert("RGBA")
        assert ImageChops.difference(source, generated).getbbox() is None, (
            f"{name}: pixels drifted from the standard Reason wheel")
    for source_name, generated_name in (
            ("SharedAudioJack.png", "AudioJack.png"),
            ("SharedCVJack.png", "CVJack.png"),
            ("TapeHorz.png", "TapeHorz.png"),
            ("TapeVert.png", "TapeVert.png"),
            ("Placeholder.png", "Placeholder.png")):
        source = Image.open(STANDARD_GUI2D / source_name).convert("RGBA")
        generated = Image.open(OUT / generated_name).convert("RGBA")
        assert ImageChops.difference(source, generated).getbbox() is None, (
            f"{generated_name}: pixels drifted from the stock Reason asset")
    previews = {"Reason_Icon128x128": (128, 96, 6), "Reason_Navigator": (126, 92, 5),
                "Reason_Palette": (130, 96, 6), "Reason_TrackListIcon": (54, 40, 3)}
    for prefix, (width, height, folded_height) in previews.items():
        for side in ("front", "back"):
            assert Image.open(OUT / f"{prefix}_{side}_root_Panel.png").size == (width, height)
            assert Image.open(OUT / f"{prefix}_{side}_folded_root_Panel.png").size == (width, folded_height)
    for name, size in (("DeviceIcon.png", (779, 518)), ("DevicePaletteImage.png", (650, 480)),
                       ("DeviceNavigator.png", (630, 460)), ("DeviceNavigatorFolded.png", (630, 25)),
                       ("DeviceTrackListThumbnail.png", (270, 200))):
        assert Image.open(HD / name).size == size, f"{name}: wrong Reason preview size"

    for name in PANEL_FILES:
        assert Image.open(OUT / name).mode == "RGBA", f"GUI2D/{name}: expected RGBA"
        assert Image.open(HD / name).mode == "RGB", f"HD/{name}: expected RGB"
    preview_names = {
        *(f"{prefix}_{side}{folded}_root_Panel.png"
          for prefix in previews for side in ("front", "back")
          for folded in ("", "_folded")),
    }
    for name in preview_names:
        assert Image.open(OUT / name).mode == "RGBA", f"GUI2D/{name}: expected RGBA"
    for name in ("DeviceIcon.png", "DevicePaletteImage.png", "DeviceNavigator.png",
                 "DeviceNavigatorFolded.png", "DeviceTrackListThumbnail.png"):
        assert Image.open(HD / name).mode == "RGBA", f"HD/{name}: expected RGBA"

    project = OUT.parent
    device = (project / "GUI2D" / "device_2D.lua").read_text()
    hdgui = (project / "GUI2D" / "hdgui_2D.lua").read_text()
    declared = set(re.findall(r"\b(S_[A-Za-z0-9_]+)\s*=", device))
    used = set(re.findall(r'"(S_[A-Za-z0-9_]+)"', hdgui))
    assert used == declared, "device_2D and hdgui_2D node sets differ"
    for lua, assets in ((project / "GUI2D" / "device_2D.lua", OUT),
                        (project / "GUI" / "Output" / "gui.lua", HD)):
        paths = set(re.findall(r'path\s*=\s*"([^"]+)"', lua.read_text()))
        missing = sorted(path for path in paths if not (assets / f"{path}.png").exists())
        assert not missing, f"{lua.name}: missing assets {missing}"
    check_layout()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    HD.mkdir(parents=True, exist_ok=True)
    # Development cache-buster twins are useful while iterating, but they are
    # redundant release payload. Keep only the canonical SDK panel names.
    for directory in (OUT, HD):
        for path in directory.glob("Reason_GUI_*_v[0-9]*_root_Panel.png"):
            path.unlink()
    (OUT / "QualityDisplay.png").unlink(missing_ok=True)
    check_spacing()
    assets = {
        "Fader": fader_strip(), "Knob": knob_strip(), "Toggle": toggle_strip(),
        "MomentaryOverlay": momentary_overlay_strip(),
        "EngineDisplay": Image.new("RGBA", px(ENGINE_STATUS_SIZE), (0, 0, 0, 0)),
        "Lamp": lamp_strip(), "PitchWheel": standard_wheel("Pitch"),
        "ModWheel": standard_wheel("Mod"),
        "AudioJack": standard_asset("SharedAudioJack.png"),
        "CVJack": standard_asset("SharedCVJack.png"),
        "TapeHorz": standard_asset("TapeHorz.png"),
        "TapeVert": standard_asset("TapeVert.png"),
        "Placeholder": standard_asset("Placeholder.png"),
    }
    for name, image in assets.items():
        image.save(OUT / f"{name}.png", optimize=True)

    panel_front = render_front()
    panel_back = render_back()
    panel_folded_front = render_folded(True)
    panel_folded_back = render_folded(False)
    preview_front = composite_front(panel_front, assets)
    preview_back = composite_back(panel_back, assets)
    preview_folded_front = composite_folded(panel_folded_front, assets, True)
    preview_folded_back = composite_folded(panel_folded_back, assets, False)
    render_previews(preview_front, preview_back, preview_folded_front, preview_folded_back)

    for name in PANEL_FILES:
        Image.open(OUT / name).convert("RGB").save(HD / name, optimize=True)
    for name in ("Fader.png", "Knob.png", "Toggle.png", "MomentaryOverlay.png",
                 "Lamp.png", "PitchWheel.png", "ModWheel.png"):
        shutil.copy2(OUT / name, HD / name)
    validate()
    print(f"YouKnow GUI: {WIDTH}x{HEIGHT} logical / {px(WIDTH)}x{px(HEIGHT)} HD; "
          f"{sum(1 for _ in widgets())} front controls in {len(LAYOUT)} rows, "
          f"{sum(1 for _ in rear_widgets())} rear controls; validated")


if __name__ == "__main__":
    main()
