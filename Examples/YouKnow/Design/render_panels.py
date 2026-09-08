#!/usr/bin/env python3
"""Build the complete deterministic YouKnow Reason GUI asset set.

The rack face is rendered directly at Reason's 5x authoring resolution. All
panel geometry, furniture, labels, and branding are drawn by this renderer.
The front's material uses the original YouKnow charcoal-plastic texture.

`LAYOUT`, `REAR_CONTROLS`, and `REAR_CV_INPUTS` below define control geometry.
The silkscreen is drawn from them and `validate()` asserts that GUI2D and
GUI/Output place their widget nodes on the same panel coordinates, so a caption
can never drift away from the control it names.
"""

from pathlib import Path
from functools import lru_cache
import math
import os
import random
import re
import shutil
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


Q = 5
WIDTH, HEIGHT = 754, 552
FOLDED_HEIGHT = 30
PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "GUI2D"
HD = PROJECT / "GUI" / "Output" / "HD"
SDK_ROOT = Path(os.environ.get("JUKEBOX_SDK_DIR", PROJECT.parents[1])).expanduser().resolve()
STANDARD_GUI2D = SDK_ROOT / "Examples" / "SimpleInstrument" / "GUI2D"
FRONT_MATERIAL = PROJECT / "Design" / "Assets" / "used-charcoal-plastic.png"

PANEL_FILES = {
    "Reason_GUI_front_root_Panel.png",
    "Reason_GUI_back_root_Panel.png",
    "Reason_GUI_folded_front_root_Panel.png",
    "Reason_GUI_folded_back_root_Panel.png",
}

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
# DIN is the industrial lettering standard actual instrument panels are
# silkscreened in, so the whole panel speaks one typographic language: the
# condensed cut carries the wordmark and section titles, the alternate cut
# carries every operational legend. Both stay legible at Reason's 1x rack view
# because DIN was drawn for small engraved plate lettering in the first place.
DISPLAY_FONT = FONT_DIR / "DIN Condensed Bold.ttf"
LABEL_FONT = FONT_DIR / "DIN Alternate Bold.ttf"
SECTION_FONT = FONT_DIR / "DIN Condensed Bold.ttf"

# A satin graphite chassis with white silkscreen. The neutral-warm grey reads
# as finely textured moulded plastic, and leaves
# the accent hues below as the only saturated colour on the panel.
INK = (240, 242, 240)
MUTED = (176, 182, 180)
DIM = (119, 125, 122)
RED = (216, 96, 66)
ICE = (126, 198, 214)
PANEL = (54, 56, 56)
FRONT_RECESS = (43, 44, 45)
PANEL_DARK = (28, 30, 31)
EDGE_HIGHLIGHT = (94, 97, 96)
CAPTION = (238, 240, 238)
SCALE_INK = (198, 202, 200)
TICK_INK = (139, 144, 142)

# --- Signal-flow accent system ----------------------------------------------
# Real panels colour-code by function, not by section, so four restrained
# families carry the whole layout: what makes tone, what shapes it, what
# sweetens it, and what the player touches. Section rules, fader caps and
# switch caps all draw from the same family, so a glance at a cap colour says
# which stage of the instrument a control belongs to.
FAMILY = {
    "source":  {"rule": (206, 150, 68),  "cap": (198, 142, 62),  "capTop": (233, 186, 112)},
    "shape":   {"rule": (86, 143, 190),  "cap": (78, 132, 178),  "capTop": (132, 180, 218)},
    "effect":  {"rule": (104, 164, 120), "cap": (94, 152, 110),  "capTop": (146, 196, 158)},
    "play":    {"rule": (168, 172, 172), "cap": (176, 180, 179), "capTop": (222, 226, 224)},
}
SECTION_FAMILY = {
    "LFO": "source", "DCO": "source", "MIXER": "source", "HPF": "source",
    "VCF": "shape", "VCA": "shape", "ENV": "shape",
    "CHORUS": "effect",
    "PERFORMANCE": "play", "KEYBOARD": "play",
}
# Which accent a control's cap wears, resolved from the section it sits in.
CONTROL_FAMILY = {}


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
GROUP_PADDING = 13
TITLE_PADDING = 8
# Reserve caption-to-frame clearance independently of the row's height.
# Wheels include a little more transparent padding above their visible edge.
CAPTION_FRAME_GAP = {"fader": 12, "wheel": 11}
LABEL_GAP = 17
# Minimum clear space between two neighbouring controls' reserved slots. The
# auto-layout below never packs tighter than this, so no caption, tick ladder
# or scale legend can end up shoulder to shoulder with its neighbour.
CONTROL_GAP = 17
MAX_CONTROL_EXTRA = 15
ROUNDING_GUARD = 0.75
FRONT_HEADER_BOTTOM = 70
REAR_HEADER_BOTTOM = 70
# The maker mark and wordmark sit at exactly these coordinates on both faces,
# so a flipped rack shows the same nameplate in the same place.
# Keep the nameplate beyond Reason's collapse-button overlay on either face.
HEADER_LEFT_INSET = 40
WORDMARK_X = HEADER_LEFT_INSET
FOLDED_WORDMARK_X = HEADER_LEFT_INSET
FOLDED_MAKER_X = FOLDED_WORDMARK_X + 81
# Actual glyph ink spans y=6..38 in the 44px nameplate: six pixels of
# plastic above and below the two-line logo, with the same spacing on both faces.
MAKER_Y = 10.2
MAKER_SIZE = 11.5
WORDMARK_Y = 29.2
WORDMARK_SIZE = 24.0
VERSION_Y = 51          # rear only: the build the panel was made for
VERSION_SIZE = 9.5

# --- Header readout strip ---------------------------------------------------
# The six engine readouts used to stack a caption over its value in the sliver
# between the patch window and the bottom of the header, six abreast. Setting
# each caption beside its own value instead puts the whole strip on one line,
# lets it use the full width of the panel, and gives every field the room its
# own caption needs. Positions are derived, exactly like the control rows.
STATUS_STRIP_TOP = 44
STATUS_RIGHT_MARGIN = 20
STATUS_CAPTION_GAP = 5
STATUS_CENTRE_Y = 56

# Type sizes are logical (1x) pixels. Control captions stay at a uniform size;
# spacing checks reject crowded text instead of shrinking labels. Section
# titles and small scale legends retain bounded fitting for their own slots.
TITLE_SIZE = 14.0     # section title
CAPTION_SIZE = 12.5   # the word above a control
SCALE_SIZE = 10.5     # numbers and switch positions beside a fader
RADIO_SIZE = 11.5     # the word beside a radio button
STATUS_SIZE = 10.0    # engine readout captions in the header
CAPTION_FLOOR = 11.5
SCALE_FLOOR = 9.5

SIZES = {
    "fader": FADER_SIZE,
    "wheel": WHEEL_SIZE,
    "knob": (KNOB_SIZE, KNOB_SIZE),
    "toggle": (TOGGLE_SIZE, TOGGLE_SIZE),
    "wave_stack": (62, 52),
}

# Offsets the silkscreen prints at, named so the placement engine reserves
# exactly the room the drawing routines go on to use.
SCALE_OFFSET = 10.4          # scale legend's right edge, left of a fader centre
SCALE_TICK_X = 8.7           # tick ladder's left end, left of a fader centre
RADIO_CAPTION_OFFSET = 32    # Key Mode caption centre, right of the button
RADIO_LABEL_GAP = 4          # button to its word
WAVE_LABEL_GAP = 5           # waveform button to its word
KEY_MODE_LABELS = ("POLY 1", "POLY 2", "UNISON")
RADIO_PITCH = 31
RADIO_HIT_MARGIN = 1


def px(value):
    if isinstance(value, tuple):
        return tuple(int(round(item * Q)) for item in value)
    return int(round(value * Q))


def font(size, display=False, strong=False):
    return ImageFont.truetype(str(DISPLAY_FONT if display else SECTION_FONT if strong else LABEL_FONT),
                              px(size))


# Silkscreened panel legends are letterspaced; set solid they read as software
# text. Tracking is in logical units per gap and is included in every width
# measurement, so the spacing checks below police the real drawn extent.
TRACK_TITLE = 1.15
TRACK_CAPTION = 0.55
TRACK_SCALE = 0.3


def tracked_width(value, face, track):
    """Advance width in device pixels, including inter-letter tracking."""
    if not value:
        return 0.0
    return (sum(face.getlength(char) for char in value)
            + px(track) * (len(value) - 1))


def label(draw, xy, value, size, colour=INK, *, display=False, strong=False,
          anchor="mm", track=0.0):
    face = font(size, display, strong)
    target_x, target_y = px(xy)
    bounds = draw.textbbox((0, 0), value, font=face, anchor=anchor)
    # Pillow's middle anchor follows font metrics rather than the visible ink.
    # Recenter the actual glyph bounds so legends from all three faces share a
    # true visual middle inside their headers and control slots.
    ink_x = (bounds[0] + bounds[2]) / 2
    ink_y = (bounds[1] + bounds[3]) / 2
    draw_y = target_y - ink_y if anchor[1] == "m" else target_y
    if not track:
        draw_x = target_x - ink_x if anchor[0] == "m" else target_x
        draw.text((draw_x, draw_y), value, fill=colour, font=face, anchor=anchor)
        return
    # Tracked runs are set glyph by glyph, so the left edge has to be resolved
    # from the tracked width rather than from Pillow's own anchor handling.
    width = tracked_width(value, face, track)
    if anchor[0] == "m":
        pen = target_x - width / 2
    elif anchor[0] == "r":
        pen = target_x - width
    else:
        pen = target_x
    for char in value:
        draw.text((pen, draw_y), char, fill=colour, font=face, anchor="l" + anchor[1])
        pen += face.getlength(char) + px(track)


def text_width(value, size, display=False, strong=False, track=0.0):
    """Rendered width in logical units, tracking included."""
    return tracked_width(value, font(size, display, strong), track) / Q


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


def control(kind, name, caption, scale=None, ticks=5):
    return {"kind": kind, "name": name, "x": None, "caption": caption,
            "scale": scale, "ticks": ticks}


def fader(name, caption, scale=TEN, ticks=9):
    return control("fader", name, caption, scale, ticks)


def selector(name, caption, *labels, min_scale_width=0.0):
    item = control("fader", name, caption, detents(*labels), len(labels))
    item["min_scale_width"] = min_scale_width
    return item


def wave_stack():
    return {
        "kind": "wave_stack", "name": "waveforms", "x": None,
        "caption": "", "scale": None, "ticks": 0,
        "properties": ("pulse", "saw"), "labels": ("PULSE", "SAW"),
    }


def fitted(text, room, ceiling, floor, display=False, strong=False, track=0.0):
    """The largest size at or below `ceiling` that fits `room`."""
    size = ceiling
    while size > floor and text_width(text, size, display, strong, track) > room:
        size -= 0.25
    return size


# --- Automatic control placement --------------------------------------------
# Control positions are derived from what each control actually has to print,
# never hand-tuned. Every control reserves the room its own widest element
# needs -- body, caption, tick ladder and scale legend -- and the row's spare
# width is then shared out equally, so density is uniform across the panel
# instead of cramped in one section and empty in the next. Change a caption or
# a type size and the layout re-flows to keep the same clearances.


def control_width(item):
    return SIZES["toggle" if item["kind"] == "radio3" else item["kind"]][0]


def caption_offset(item):
    """Distance from a control's origin to the point its caption centres on."""
    return (RADIO_CAPTION_OFFSET if item["kind"] == "radio3"
            else control_width(item) / 2)


def caption_centre(item):
    return item["x"] + caption_offset(item)


def scale_legend_width(item):
    """Width of the widest scale word printed to the left of a fader."""
    if item["kind"] != "fader" or not item["scale"] or item["scale"] == TEN:
        return 0.0
    return max(item.get("min_scale_width", 0.0),
               *(text_width(text, SCALE_SIZE, track=TRACK_SCALE)
                 for _, text in item["scale"]))


def radio_label_width():
    return max(text_width(text, RADIO_SIZE, track=TRACK_SCALE)
               for text in KEY_MODE_LABELS)


def wave_label_width():
    return max(text_width(text, SCALE_SIZE, track=TRACK_SCALE)
               for text in ("PULSE", "SAW"))


def reach(item):
    """How far a control's ink extends either side of its caption centre.

    Measured in logical units from the point the caption is centred on, which
    is what `caption_centre` returns and what the spacing checker polices.
    """
    caption_half = (text_width(item["caption"], CAPTION_SIZE, track=TRACK_CAPTION) / 2
                    if item["caption"] else 0.0)
    kind = item["kind"]
    if kind == "radio3":
        left = float(RADIO_CAPTION_OFFSET)
        right = (TOGGLE_SIZE + RADIO_LABEL_GAP - RADIO_CAPTION_OFFSET
                 + radio_label_width())
    elif kind == "wave_stack":
        left = SIZES["wave_stack"][0] / 2
        right = TOGGLE_SIZE + WAVE_LABEL_GAP - left + wave_label_width()
    else:
        width = control_width(item)
        legend = scale_legend_width(item)
        left = (SCALE_OFFSET + legend) if legend else width / 2
        right = width / 2
    # Positions are placed as floats but emitted as whole logical units, so
    # reserve the rounding error rather than letting it eat a clearance the
    # spacing checker is about to measure.
    return max(left, caption_half) + ROUNDING_GUARD, max(right, caption_half) + ROUNDING_GUARD


def place_row(sections, width=WIDTH):
    """Assign every control an x, then return (title, x0, x1, controls) boxes.

    Sections are sized to their contents; the row's leftover width is then
    divided between the gaps that exist, so the sections carrying the most
    controls receive the most relief and the whole row ends up at one density.
    """
    reaches = {id(item): reach(item)
               for _, controls in sections for item in controls}

    def section_span(controls, padding):
        return (2 * GROUP_PADDING + sum(sum(reaches[id(i)]) for i in controls)
                + (len(controls) - 1) * (CONTROL_GAP + padding))

    gaps = sum(len(controls) - 1 for _, controls in sections)
    base = sum(section_span(controls, 0.0) for _, controls in sections)
    spare = width - 2 * BOX_GAP - (len(sections) - 1) * BOX_GAP - base
    # A sparse row must not sprawl just because it can: past this cap the
    # surplus goes into the section boxes instead, so control pitch stays
    # comparable from the top row to the bottom one.
    padding = min(max(0.0, spare / gaps), MAX_CONTROL_EXTRA) if gaps else 0.0
    slack = (spare - padding * gaps) / len(sections)

    boxes = []
    x0 = float(BOX_GAP)
    for title, controls in sections:
        span = section_span(controls, padding) + slack
        cursor = x0 + GROUP_PADDING + slack / 2
        for item in controls:
            left, right = reaches[id(item)]
            item["x"] = int(round(cursor + left - caption_offset(item)))
            cursor += left + right + CONTROL_GAP + padding
        boxes.append((title, int(round(x0)), int(round(x0 + span)), controls))
        x0 += span + BOX_GAP
    return boxes


def build_layout(spec):
    rows = []
    for row in spec:
        for title, controls in row["sections"]:
            for item in controls:
                item["family"] = SECTION_FAMILY[title]
                item["caption_y"] = row["y"] + HEAD_DY
        rows.append({"y": row["y"], "h": row["h"],
                     "sections": place_row(row["sections"])})
    return rows


def fader_asset(family):
    return "Fader" + family.capitalize()


FADER_ASSETS = tuple(fader_asset(name) for name in FAMILY)


# --- Front panel layout -----------------------------------------------------
# Three generous rows: the tone-generating front half, filter/amplifier, and
# performance/setup controls. The 8RU height gives the controls their natural
# scale instead of asking every control to behave like a miniature annotation.
# Sections carry the names a hardware panel would be silkscreened with: the
# oscillator is a DCO, the filter and amplifier are the VCF and VCA, and the
# wheels are the bender. They are shorter than prose names, and they are what
# a synthesist reads for anyway. Master level is its own OUTPUT group rather
# than being filed under the bender it has nothing to do with.
LAYOUT_SPEC = [
    {
        "y": 80, "h": 144,
        "sections": [
            ("LFO", [
                fader("lfoRate", "RATE"),
                fader("lfoDelay", "DELAY"),
            ]),
            ("DCO", [
                selector("range", "RANGE", "16'", "8'", "4'"),
                fader("dcoLfo", "LFO"),
                fader("pwm", "PWM"),
                selector("pwmMode", "SOURCE", "LFO", "MAN"),
            ]),
            ("MIXER", [
                wave_stack(),
                fader("sub", "SUB"),
                fader("noise", "NOISE"),
            ]),
            ("HPF", [
                # Retain the existing section width as its zero legend shrinks.
                selector("highPass", "CUT", "0", "1", "2", "3",
                         min_scale_width=18.4),
            ]),
        ],
    },
    {
        "y": 234, "h": 144,
        "sections": [
            ("VCF", [
                fader("cutoff", "FREQ"),
                fader("resonance", "RES"),
                selector("envPolarity", "POL", "+", "−"),
                fader("vcfEnv", "ENV"),
                fader("vcfLfo", "LFO"),
                fader("keyFollow", "KYBD"),
            ]),
            ("VCA", [
                selector("vcaMode", "MODE", "ENV", "GATE"),
                fader("vcaLevel", "LEVEL"),
            ]),
            ("ENV", [
                fader("attack", "A"),
                fader("decay", "D"),
                fader("sustain", "S"),
                fader("release", "R"),
            ]),
            # Chorus sits at the end of the shaping row because that is where
            # it sits in the signal: after the amplifier, before the output.
            ("CHORUS", [
                selector("chorus", "MODE", "OFF", "I", "II", "I+II"),
                fader("chorusNoise", "NOISE"),
            ]),
        ],
    },
    {
        "y": 388, "h": 154,
        "sections": [
            ("PERFORMANCE", [
                control("wheel", "pitchBend", "BEND"),
                control("wheel", "modWheel", "MOD"),
                fader("benderDco", "DCO"),
                fader("benderVcf", "VCF"),
                fader("benderLfo", "LFO"),
                fader("volume", "VOLUME"),
            ]),
            ("KEYBOARD", [
                control("knob", "portamento", "GLIDE"),
                control("radio3", "keyMode", "MODE"),
                fader("transpose", "SHIFT", span("−12", "0", "+12"), 5),
                fader("masterTune", "TUNE", span("−50", "0", "+50")),
                fader("velocity", "VEL"),
                fader("polyphony", "VOICES",
                      ((1.0, "1"), (7 / 15, "8"), (0.0, "16")), 3),
            ]),
        ],
    },
]

LAYOUT = build_layout(LAYOUT_SPEC)
# Align the quality strip with the first control caption, below the collapse
# overlay. The two-line nameplate retains its separate protected left inset.
FIRST_CONTROL = LAYOUT[0]["sections"][0][3][0]
STATUS_LEFT_MARGIN = round(caption_centre(FIRST_CONTROL) - text_width(
    FIRST_CONTROL["caption"], CAPTION_SIZE, track=TRACK_CAPTION) / 2)


def family_by_node():
    """Which accent each placed front widget wears. Rear controls stay neutral."""
    mapping = {}
    for row in LAYOUT:
        body = body_top(row)
        for _, _, _, controls in row["sections"]:
            for item in controls:
                for node, *_ in row_controls([item], body):
                    mapping[node] = item["family"]
    return mapping

# Settings sit above all connections, leaving downward cable runs clear.
REAR_ENGINE_BOX = (60, 84, 500, 286)
REAR_UNIT_BOX = (510, 84, 694, 286)
REAR_INPUT_BOX = (60, 316, 360, 532)
REAR_OUTPUT_BOX = (394, 316, 694, 532)
REAR_CONTROL_CAPTION_Y = REAR_ENGINE_BOX[1] + 44
REAR_PERSISTENCE_Y = REAR_ENGINE_BOX[1] + 177
# Stock jack top-lefts; captions share the jack's horizontal centre.
REAR_CV_INPUTS = (
    ("note", "NOTE", 95, 387),
    ("gate", "GATE", 167, 387),
    ("cutoff", "CUTOFF", 239, 387),
    ("resonance", "RES", 311, 387),
    ("volume", "VOLUME", 95, 477),
    ("vca_level", "AMP", 167, 477),
    ("sub", "SUB", 239, 477),
    ("noise", "NOISE", 311, 477),
)
REAR_AUDIO_OUTPUTS = (("left", "LEFT", 485, 462), ("right", "RIGHT", 575, 462))
AUDIO_JACK_SIZE = (19, 21)
CV_CAPTION_SIZE = 12.0
CV_CAPTION_OFFSET = 22
REAR_CONTROLS = (
    {"kind": "radio", "name": "quality", "x": 0, "caption": "OVERSAMPLE",
     "x": 80, "center": 122, "top": 146,
     "labels": ("1x", "2x", "4x"), "remote": True, "automation": True},
    {"kind": "radio", "name": "vcfTanhMode", "x": 0, "caption": "SATURATION",
     "x": 188, "center": 230, "top": 146,
     "labels": ("EXACT", "FAST", "POLY"), "remote": True, "automation": True},
    {"kind": "radio", "name": "vcfFastEarlyMode", "x": 0, "caption": "EARLY MODEL",
     "x": 296, "center": 338, "top": 161,
     "labels": ("HERMITE", "CUBIC"), "remote": True, "automation": True},
    {"kind": "radio", "name": "vcfSolverMode", "x": 0, "caption": "FILTER SOLVER",
     "x": 404, "center": 446, "top": 146,
     "labels": ("MAX", "HIGH", "NORMAL"), "remote": True, "automation": True},
    {"kind": "fader", "name": "calibration", "x": 0, "caption": "CHARACTER",
     "x": 544, "center": 554, "top": 146,
     "scale": span("0", "100", "200%"), "ticks": 5,
     "remote": True, "automation": True},
    {"kind": "fader", "name": "aging", "x": 0, "caption": "AGING",
     "x": 636, "center": 646, "top": 146,
     "scale": span("0", "50", "100%"), "ticks": 5,
     "remote": True, "automation": True},
)
ENGINE_STATUS_SIZE = (56, 16)
ENGINE_STATUS_Y = STATUS_CENTRE_Y - 8
# One shared baseline for every caption in the header's readout strip.
STATUS_CAPTION_Y = STATUS_CENTRE_Y
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


def place_status_strip():
    """Spread the readouts and the Note lamp across the header's full width.

    Each field is a right-aligned caption followed by its value window, so the
    strip reads as one line of instrument status rather than six stacked pairs
    crammed under the patch name. Whatever width is left over is divided evenly
    between the fields.
    """
    display_width = ENGINE_STATUS_SIZE[0]
    widths = []
    for item in ENGINE_STATUS:
        caption = text_width(item["caption"], STATUS_SIZE, track=TRACK_SCALE)
        widths.append(caption + STATUS_CAPTION_GAP + display_width)
    note_caption = text_width("NOTE", STATUS_SIZE, track=TRACK_SCALE)
    widths.append(note_caption + STATUS_CAPTION_GAP + LAMP_SIZE)

    available = WIDTH - STATUS_LEFT_MARGIN - STATUS_RIGHT_MARGIN
    spacing = (available - sum(widths)) / (len(widths) - 1)
    cursor = float(STATUS_LEFT_MARGIN)
    for item, width in zip(ENGINE_STATUS, widths):
        item["x"] = int(round(cursor + width - display_width))
        cursor += width + spacing
    return int(round(cursor + widths[-1] - LAMP_SIZE))


NOTE_LAMP_X = place_status_strip()
PLACEHOLDER_POS = (347, 15)

# Radio clusters are laid out vertically so each position gets a full word.

# Header widgets, which sit outside the three control rows.
# Band one carries identity and the patch; band two is the readout strip that
# place_status_strip() spreads across the full width beneath it.
PATCH_BOX = (296, 12, 507, 36)
HEADER_NODES = {
    "S_patch_name": (299, 16),
    "S_patch_browse_group": (517, 13),
    "S_device_name": (589, 17),
    "S_note_on": (NOTE_LAMP_X, STATUS_CENTRE_Y - LAMP_SIZE // 2),
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


def control_top(item, body):
    """Place a control below its caption without crowding the section footer."""
    top = centred_y(body, SIZES[item["kind"]][1])
    gap = CAPTION_FRAME_GAP.get(item["kind"])
    return max(top, item["caption_y"] + gap) if gap is not None else top


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
                   "wheel", name, x, control_top(item, body))
        else:
            yield (f"S_fader_{name}", "fader", name,
                   x, control_top(item, body))


FAMILY_BY_NODE = family_by_node()


def fader_path(node):
    return fader_asset(FAMILY_BY_NODE.get(node, "play"))


def vertical_gradient(size, top, bottom, mode="RGB"):
    image = Image.new(mode, size)
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        amount = y / max(1, size[1] - 1)
        colour = tuple(round(a + (b - a) * amount) for a, b in zip(top, bottom))
        draw.line((0, y, size[0], y), fill=colour)
    return image


def plastic_grain(size, seed):
    """Quiet, non-directional mould grain with irregular finish variation.

    Independent isotropic fields give the plastic fine pores and much softer
    changes in sheen. Fixed seeds keep regenerated artwork byte-reproducible;
    none of the fields repeats or stretches into horizontal brush marks.
    """
    rng = random.Random(seed)
    grain = Image.new("L", size, 128)
    for cell, amplitude in ((0.35, 6), (1.15, 4), (8, 2), (37, 3)):
        field_size = tuple(max(2, math.ceil(edge / (cell * Q))) for edge in size)
        field = Image.frombytes("L", field_size, rng.randbytes(math.prod(field_size)))
        field = field.resize(size, Image.Resampling.BICUBIC)
        field = field.point(lambda value: 128 + round((value - 127.5) * amplitude / 127.5))
        grain = ImageChops.add(grain, field, offset=-128)
    return grain


@lru_cache(maxsize=1)
def front_material():
    """One continuous, aspect-preserved piece of the original ABS material."""
    with Image.open(FRONT_MATERIAL) as source:
        material = ImageOps.fit(source.convert("L"), px((WIDTH, HEIGHT)),
                                method=Image.Resampling.BICUBIC)
    return material.filter(ImageFilter.GaussianBlur(px(0.2)))


def front_plastic(height, top, bottom, contrast=0.55):
    """Warm matte plastic, retaining only quiet pores and sparse satin wear."""
    size = px((WIDTH, height))
    surface = vertical_gradient(size, top, bottom)
    grain = front_material().crop((0, 0, *size))
    # The source's mean luminance is 58.87. Centering it before compositing
    # keeps the chosen warm tint independent of the source material tones.
    grain = grain.point(lambda value: 128 + round((value - 59) * contrast))
    return ImageChops.add(surface, Image.merge("RGB", (grain, grain, grain)), offset=-128)


def vignette(image, depth=26):
    """Darken the chassis toward its edges, the way a lit panel falls off."""
    falloff = Image.radial_gradient("L").resize(image.size, Image.BILINEAR)
    # radial_gradient is black at the centre; invert it into a light map and
    # keep the centre unattenuated so the silkscreen keeps its full contrast.
    shade = falloff.point(lambda v: 255 - int(depth * (v / 255) ** 2.1))
    return ImageChops.multiply(image, Image.merge("RGB", (shade, shade, shade)))


def base_panel(height=HEIGHT, rear=False):
    if rear:
        image = vertical_gradient((px(WIDTH), px(height)), (109, 110, 111), (93, 94, 95))
        grain = plastic_grain(image.size, seed=1709)
        image = ImageChops.add(image, Image.merge("RGB", (grain, grain, grain)), offset=-128)
        image = vignette(image)
    else:
        image = front_plastic(height, (83, 79, 74), (73, 70, 66))
        image = vignette(image, depth=12)
    draw = ImageDraw.Draw(image)
    # Chassis edge: a dark folded rim with a lit top lip, so the panel reads as
    # a physical plate seated in the rack rather than a flat rectangle.
    draw.rectangle((0, 0, image.width - 1, image.height - 1), outline=(11, 12, 13), width=Q)
    draw.line((Q, Q, image.width - Q, Q),
              fill=(126, 129, 128) if rear else (99, 98, 95), width=px(0.4))
    draw.line((Q, image.height - Q, image.width - Q, image.height - Q),
              fill=(20, 21, 22), width=px(0.4))
    return image, draw


def section_title(draw, box, title, title_size=TITLE_SIZE):
    """Rear titles share one neutral rule, with no surrounding recess."""
    x0, y0, _, y1 = box
    label(draw, (x0, y0 + TITLE_H / 2 + TITLE_OPTICAL_OFFSET), title, title_size,
          strong=True, anchor="lm", track=TRACK_TITLE)
    rule_x = x0 + text_width(title, title_size, strong=True, track=TRACK_TITLE) + 7
    rule_y = y0 + TITLE_H / 2 + TITLE_OPTICAL_OFFSET
    draw.line(px((rule_x, rule_y, box[2], rule_y)), fill=FAMILY["play"]["rule"],
              width=px(0.8))


def section(image, draw, surface, box, title, title_size=TITLE_SIZE, family="play"):
    """A shallow machined recess, titled and colour-coded by signal stage.

    The pocket is drawn as a real edge rather than a flat card: a dark lip
    along the top and left where the light does not reach, a lit lower-right
    edge, and an accent rule under the title carrying the stage colour that the
    section's fader caps also wear.
    """
    x0, y0, x1, y1 = box
    accent = FAMILY[family]["rule"]
    left, top, right, bottom = px(box)
    bounds = (left, top, right + 1, bottom + 1)
    mask = Image.new("L", (right - left + 1, bottom - top + 1))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, mask.width - 1, mask.height - 1),
                                          radius=px(2.5), fill=255)
    image.paste(surface.crop(bounds), (left, top), mask)
    # Recess edges. Top/left shadow first, then the catch-light underneath.
    draw.arc(px((x0, y0, x0 + 5, y0 + 5)), 180, 270, fill=(26, 27, 28), width=px(0.5))
    draw.line(px((x0 + 2.5, y0, x1 - 2.5, y0)), fill=(26, 27, 28), width=px(0.5))
    draw.line(px((x0, y0 + 2.5, x0, y1 - 2.5)), fill=(30, 31, 32), width=px(0.5))
    draw.line(px((x0 + 2.5, y1, x1 - 2.5, y1)), fill=(70, 71, 69), width=px(0.5))
    draw.line(px((x1, y0 + 2.5, x1, y1 - 2.5)), fill=(63, 65, 63), width=px(0.5))
    label(draw, (x0 + TITLE_PADDING, y0 + TITLE_H / 2 + TITLE_OPTICAL_OFFSET),
          title, title_size, strong=True, anchor="lm", track=TRACK_TITLE)
    # The accent rule runs from the title to the section's right edge, which
    # gives every box the same horizontal anchor line to read along.
    rule_x = (x0 + TITLE_PADDING
              + text_width(title, title_size, strong=True, track=TRACK_TITLE) + 7)
    rule_y = y0 + TITLE_H / 2 + TITLE_OPTICAL_OFFSET
    draw.line(px((rule_x, rule_y, x1 - GROUP_PADDING, rule_y)), fill=accent, width=px(0.8))


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
        length = 5.4 if major else 3.0
        colour = SCALE_INK if major else TICK_INK
        draw.line(px((centre - SCALE_TICK_X, yy, centre - SCALE_TICK_X + length, yy)),
                  fill=colour, width=px(1.0 if major else 0.7))

    size = min((fitted(text, room, SCALE_SIZE, SCALE_FLOOR, track=TRACK_SCALE)
                for _, text in values), default=SCALE_SIZE)
    for amount, text in values:
        label(draw, (centre - SCALE_OFFSET, top + amount * FADER_TRAVEL), text,
              size, SCALE_INK, anchor="rm", track=TRACK_SCALE)


def header_plate(image, draw, bottom=None, dark=False):
    """The nameplate strip: darker satin plastic with a shallow lower step."""
    bottom = FRONT_HEADER_BOTTOM if bottom is None else bottom
    band = px((0, 0, WIDTH, bottom))
    if dark:
        plate = vertical_gradient((band[2], band[3]), (99, 100, 101), (89, 90, 91))
        grain = plastic_grain(plate.size, seed=2909)
        plate = ImageChops.add(plate, Image.merge("RGB", (grain, grain, grain)), offset=-128)
    else:
        plate = front_plastic(bottom, (67, 64, 60), (61, 59, 56), contrast=0.45)
    image.paste(plate, (0, 0))
    draw.line(px((0, bottom, WIDTH, bottom)), fill=(22, 23, 24), width=px(0.7))
    draw.line(px((0, bottom + 0.7, WIDTH, bottom + 0.7)),
              fill=(96, 99, 98) if dark else (74, 74, 71), width=px(0.4))


def device_version():
    """The version_number info.lua declares, for the rear nameplate."""
    text = (PROJECT / "info.lua").read_text(encoding="utf-8")
    match = re.search(r'^version_number\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "info.lua has no version_number"
    return match.group(1)


def wordmark(draw, version=None):
    """The maker mark and instrument name, identically placed on both faces."""
    centre = WORDMARK_X + text_width(
        "YOUKNOW", WORDMARK_SIZE, display=True, track=TRACK_CAPTION) / 2
    label(draw, (centre, MAKER_Y), "PROTOCODUS", MAKER_SIZE, ICE,
          strong=True, track=TRACK_TITLE)
    label(draw, (centre, WORDMARK_Y), "YOUKNOW", WORDMARK_SIZE, INK,
          display=True, track=TRACK_CAPTION)
    if version:
        label(draw, (WORDMARK_X, VERSION_Y), f"VERSION {version}", VERSION_SIZE,
              MUTED, anchor="lm", track=TRACK_SCALE)


def status_plate(image, draw):
    """A subtly darker readout band, retaining the continuous plastic grain."""
    bounds = px((0, STATUS_STRIP_TOP, WIDTH, FRONT_HEADER_BOTTOM))
    strip = image.crop(bounds).point(lambda channel: round(channel * 0.84))
    image.paste(strip, (bounds[0], bounds[1]))
    draw.line(px((0, STATUS_STRIP_TOP, WIDTH, STATUS_STRIP_TOP)),
              fill=(95, 96, 92), width=px(0.4))


def render_front():
    image, draw = base_panel()
    recess_surface = front_plastic(HEIGHT, (46, 47, 48), (40, 41, 42), contrast=0.32)
    header_plate(image, draw)
    status_plate(image, draw)
    wordmark(draw)
    # Patch window: a recessed smoked panel, lit along its lower edge.
    x0, y0, x1, y1 = PATCH_BOX
    draw.rounded_rectangle(px(PATCH_BOX), radius=px(2),
                           fill=(19, 20, 21), outline=(16, 17, 18), width=px(0.7))
    draw.line(px((x0 + 1.5, y1, x1 - 1.5, y1)), fill=(92, 95, 94), width=px(0.35))
    # Every caption is set immediately left of the window it names, all on one
    # baseline, so the strip reads as a single line of status.
    for item in ENGINE_STATUS:
        label(draw, (item["x"] - STATUS_CAPTION_GAP, STATUS_CAPTION_Y),
              item["caption"], STATUS_SIZE, MUTED, anchor="rm", track=TRACK_SCALE)
    label(draw, (NOTE_LAMP_X - STATUS_CAPTION_GAP, STATUS_CAPTION_Y), "NOTE",
          STATUS_SIZE, MUTED, anchor="rm", track=TRACK_SCALE)

    for row in LAYOUT:
        y0, y1 = row["y"], row["y"] + row["h"]
        body = body_top(row)
        for title, x0, x1, controls in row["sections"]:
            section(image, draw, recess_surface, (x0, y0, x1, y1), title,
                    fitted(title, x1 - x0 - 2 * GROUP_PADDING - 10, TITLE_SIZE,
                           10.5, strong=True, track=TRACK_TITLE),
                    SECTION_FAMILY[title])
            for item, (caption_room, scale_room) in zip(
                    controls, section_rooms(x0, x1, controls)):
                draw_caption(draw, item, y0)
                if item["kind"] == "fader" and item["scale"]:
                    fader_scale(draw, item["x"], control_top(item, body), item["scale"],
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
          CAPTION_SIZE, CAPTION, track=TRACK_CAPTION)


def draw_wave_labels(draw, item, body):
    top = centred_y(body, SIZES["wave_stack"][1])
    for index, text in enumerate(item["labels"]):
        y = top + index * (TOGGLE_SIZE + 12) + TOGGLE_SIZE / 2
        label(draw, (item["x"] + TOGGLE_SIZE + WAVE_LABEL_GAP, y), text,
              SCALE_SIZE, CAPTION, anchor="lm", track=TRACK_SCALE)


def draw_radio_labels(draw, x, top):
    for index, text in enumerate(KEY_MODE_LABELS):
        label(draw, (x + TOGGLE_SIZE + RADIO_LABEL_GAP,
                     top + index * RADIO_PITCH + TOGGLE_SIZE / 2),
              text, RADIO_SIZE, MUTED, anchor="lm", track=TRACK_SCALE)


def render_back():
    image, draw = base_panel(rear=True)
    header_plate(image, draw, bottom=REAR_HEADER_BOTTOM, dark=True)
    wordmark(draw, device_version())
    # The rear is a wiring diagram, not a performance surface: its areas are
    # titled and ruled, but not boxed. Recessed groups belong to the controls
    # you reach for, and drawing them back here only fences off sockets.
    section_title(draw, REAR_INPUT_BOX, "CV INPUTS")
    section_title(draw, REAR_OUTPUT_BOX, "AUDIO OUTPUTS")
    section_title(draw, REAR_ENGINE_BOX, "PROCESSING QUALITY")
    section_title(draw, REAR_UNIT_BOX, "UNIT MODEL")
    for name, title, x, y in REAR_CV_INPUTS:
        centre = x + CV_JACK_SIZE[0] / 2
        label(draw, (centre, y - CV_CAPTION_OFFSET), title,
              CV_CAPTION_SIZE, CAPTION, strong=True)
        if name == "note":
            label(draw, (centre, y + 33), "1 V/OCT", 9.5, MUTED)
    for _, title, x, y in REAR_AUDIO_OUTPUTS:
        label(draw, (x + (AUDIO_JACK_SIZE[0] - 1) / 2, y - 26), title, 12, CAPTION, strong=True)
    for item in REAR_CONTROLS:
        label(draw, (item["center"], REAR_CONTROL_CAPTION_Y), item["caption"], 10.0, CAPTION)
        if item["kind"] == "fader":
            fader_scale(draw, item["x"], item["top"], item["scale"],
                        item["ticks"], 42)
            continue
        for index, text in enumerate(item["labels"]):
            label(draw, (item["x"] + TOGGLE_SIZE + 6,
                         item["top"] + index * RADIO_PITCH + TOGGLE_SIZE / 2),
                  text if text[0].isdigit() else text.title(), 10.0, CAPTION, anchor="lm")
    label(draw, (280, REAR_PERSISTENCE_Y), "SONG", 9.0, MUTED)
    label(draw, (554, REAR_PERSISTENCE_Y), "PATCH", 9.0, MUTED)
    label(draw, (646, REAR_PERSISTENCE_Y), "SONG", 9.0, MUTED)
    save_panel(image, "Reason_GUI_back_root_Panel.png")
    return image


def render_folded(front=True):
    image, draw = base_panel(FOLDED_HEIGHT, rear=not front)
    # The folded strip is the same name plate as the full face, cropped to a
    # single rack unit, so a folded YouKnow still reads as the same hardware.
    header_plate(image, draw, bottom=FOLDED_HEIGHT, dark=not front)
    label(draw, (FOLDED_WORDMARK_X, 15), "YOUKNOW", 18.0, INK, display=True, anchor="lm",
          track=TRACK_CAPTION)
    label(draw, (FOLDED_MAKER_X, 15), "PROTOCODUS", 11.0, ICE, strong=True, anchor="lm",
          track=TRACK_TITLE)
    if front:
        draw.rounded_rectangle(px((297, 7, 507, 23)), radius=px(1.8),
                               fill=(19, 20, 21), outline=(16, 17, 18), width=px(0.55))
        draw.line(px((298.5, 23, 505.5, 23)), fill=(92, 95, 94), width=px(0.3))
        label(draw, (719, 15), "NOTE", 9.5, MUTED, track=TRACK_SCALE)
    else:
        # Reason anchors folded cable bundles here. Make that anchor visible so
        # a connected folded device never appears to grow a cable from nowhere.
        cx, cy = 377, 15
        draw.ellipse(px((cx - 8, cy - 8, cx + 8, cy + 8)),
                     fill=(7, 9, 9), outline=(101, 105, 101), width=px(0.8))
        draw.ellipse(px((cx - 4.5, cy - 4.5, cx + 4.5, cy + 4.5)),
                     fill=(0, 1, 1), outline=(43, 47, 45), width=px(0.6))
    filename = "Reason_GUI_folded_front_root_Panel.png" if front else "Reason_GUI_folded_back_root_Panel.png"
    save_panel(image, filename)
    return image


def save_panel(image, canonical_name):
    gui2d = image.convert("RGBA")
    gui2d.save(OUT / canonical_name, optimize=True)


def fader_centre_y(frame, frames=32):
    return round(px(FADER_SIZE[1] - FADER_MARGIN - FADER_HANDLE / 2)
                 - frame / (frames - 1) * px(FADER_TRAVEL))


def fader_strip(family="play"):
    top_colour = FAMILY[family]["capTop"]
    body_colour = FAMILY[family]["cap"]
    index_colour = (250, 248, 240) if family != "play" else (196, 74, 48)
    frame_w, frame_h, frames = px(FADER_SIZE[0]), px(FADER_SIZE[1]), 32
    strip = Image.new("RGBA", (frame_w, frame_h * frames), (0, 0, 0, 0))
    for frame in range(frames):
        cell = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(cell)
        cx = frame_w // 2
        draw.rounded_rectangle((cx - px(2), px(2), cx + px(2), frame_h - px(2)),
                               radius=px(1.5), fill=(14, 15, 15, 255),
                               outline=(24, 25, 26, 255), width=px(0.7))
        # Lit lower-right lip of the routed channel, then the shadowed floor.
        draw.line((cx + px(2), px(3), cx + px(2), frame_h - px(3)),
                  fill=(104, 107, 106, 200), width=px(0.4))
        draw.line((cx, px(4), cx, frame_h - px(4)),
                  fill=(44, 46, 46, 255), width=px(0.9))
        centre_y = fader_centre_y(frame, frames)
        cap_y = centre_y - px(FADER_HANDLE) // 2
        draw.rounded_rectangle((px(0.6), cap_y + px(1), frame_w - px(0.2),
                                cap_y + px(FADER_HANDLE) + px(2)),
                               radius=px(1), fill=(2, 3, 3, 125))
        cap = vertical_gradient((px(FADER_SIZE[0] - 2), px(FADER_HANDLE)),
                                top_colour + (255,), body_colour + (255,), "RGBA")
        mask = Image.new("L", cap.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cap.width - 1, cap.height - 1), radius=px(0.8), fill=255)
        cell.paste(cap, (px(1), cap_y), mask)
        draw = ImageDraw.Draw(cell)
        draw.rounded_rectangle((px(1), cap_y, frame_w - px(1), cap_y + px(FADER_HANDLE)),
                               radius=px(0.8), outline=(35, 37, 35, 235), width=px(0.5))
        draw.line((px(2), centre_y, frame_w - px(2), centre_y),
                  fill=index_colour + (255,), width=px(0.9))
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
            if kind == "fader":
                path = fader_path(node)
            frame = PREVIEW_NODE_FRAME.get(node, PREVIEW_FRAME.get(name, frame))
        image.alpha_composite(copy_frame(assets[path], frames, frame), px((x, y)))
    image.alpha_composite(copy_frame(assets["Lamp"], 2, 0), px(HEADER_NODES["S_note_on"]))
    image.alpha_composite(Image.open(OUT / "PatchBrowseGroup.png").convert("RGBA"),
                          px(HEADER_NODES["S_patch_browse_group"]))
    image.alpha_composite(assets["TapeHorz"], px(HEADER_NODES["S_device_name"]))
    preview_draw = ImageDraw.Draw(image)
    label(preview_draw, ((PATCH_BOX[0] + PATCH_BOX[2]) / 2,
                         (PATCH_BOX[1] + PATCH_BOX[3]) / 2),
          PREVIEW_PATCH_NAME, 11.0, ICE)
    status_width, status_height = ENGINE_STATUS_SIZE
    for item in ENGINE_STATUS:
        label(
            preview_draw,
            (item["x"] + status_width / 2,
             ENGINE_STATUS_Y + status_height / 2),
            item["preview"], 11.0, ICE,
        )
    tape_x, tape_y = HEADER_NODES["S_device_name"]
    label(preview_draw, (tape_x + 40, tape_y + 6.5), "YOUKNOW", 5.5, PANEL_DARK)
    return image


def composite_back(panel, assets):
    image = panel.convert("RGBA")
    image.alpha_composite(assets["Placeholder"], px(PLACEHOLDER_POS))
    for _, _, x, y in REAR_CV_INPUTS:
        image.alpha_composite(copy_frame(assets["CVJack"], 3, 0), px((x, y)))
    for _, _, x, y in REAR_AUDIO_OUTPUTS:
        image.alpha_composite(copy_frame(assets["AudioJack"], 3, 0), px((x, y)))
    for node, kind, name, x, y in rear_widgets():
        if kind == "fader":
            image.alpha_composite(
                copy_frame(assets[fader_path(node)], 32, PREVIEW_FRAME[name]),
                px((x, y)))
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
    """Two instrument-color bars for slots too small to carry panel legends."""
    width, height = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    panel_h = min(height, max(1, round(width * HEIGHT / WIDTH)))
    top = (height - panel_h) // 2
    right, bottom = width - 1, top + panel_h - 1
    draw = ImageDraw.Draw(image)
    radius = max(1, round(panel_h * 0.045))
    draw.rounded_rectangle((0, top, right, bottom), radius=radius,
                           fill=FRONT_RECESS if front else PANEL_DARK,
                           outline=(77, 80, 80))
    bar_width = max(2, round(width * 0.20))
    gap = max(2, round(width * 0.12))
    left = (width - 2 * bar_width - gap) // 2
    bar_height = max(2, round(panel_h * 0.64))
    bar_top = top + (panel_h - bar_height) // 2
    for index, family in enumerate(("shape", "source")):
        bar_left = left + index * (bar_width + gap)
        draw.rounded_rectangle(
            (bar_left, bar_top, bar_left + bar_width - 1, bar_top + bar_height - 1),
            radius=max(0, round(bar_width * 0.10)), fill=FAMILY[family]["capTop"])
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
    compact_face((270, 200)).save(HD / "DeviceTrackListThumbnail.png", optimize=True)
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


PANEL_SIZES = {
    "front": (WIDTH, HEIGHT), "back": (WIDTH, HEIGHT),
    "folded_front": (WIDTH, FOLDED_HEIGHT), "folded_back": (WIDTH, FOLDED_HEIGHT),
}
# Frame counts the device_2D helpers bake in, so a widget's drawn height is its
# strip height divided by its frames.
HELPER_FRAMES = {"fader": 32, "toggle": 2, "knob": 63, "lamp": 2,
                 "momentary_overlay": 2, "wheel": 64}


def check_panel_bounds(device):
    """No widget may fall outside the panel that declares it.

    The folded panels are one rack unit tall and declare some of the same node
    names as the full front. A rewrite that is not panel-aware moves the folded
    copy to the front's coordinates, which puts it off its own panel -- valid
    Lua, passes a node-set check, and fails the cloud GUI build with nothing but
    "an internal error occurred". This is the check that catches it here.
    """
    for name, (width, height) in PANEL_SIZES.items():
        match = re.search(rf"^{name} = \{{", device, re.M)
        if not match:
            continue
        rest = device[match.end():]
        others = [re.search(rf"^{other} = \{{", rest, re.M)
                  for other in PANEL_SIZES if other != name]
        ends = [found.start() for found in others if found]
        body = rest[:min(ends)] if ends else rest

        for node, helper, args in re.findall(
                r"(S_[A-Za-z0-9_]+)\s*=\s*(\w+)\(([^)]*)\)", body):
            fields = [field.strip().strip('"') for field in args.split(",")]
            try:
                x, y = float(fields[0]), float(fields[1])
            except (ValueError, IndexError):
                continue
            if helper == "widget":
                path, frames = fields[2], int(fields[3])
            else:
                frames = HELPER_FRAMES.get(helper)
                path = {"toggle": "Toggle", "knob": "Knob", "lamp": "Lamp",
                        "momentary_overlay": "MomentaryOverlay"}.get(helper)
                if path is None and len(fields) > 2:
                    path = fields[2]
            if not path or frames is None:
                continue
            image = Image.open(OUT / f"{path}.png")
            assert image.height % frames == 0, (
                f"{name}/{node}: {path} height {image.height} is not {frames} frames")
            frame_w = image.width / Q
            frame_h = image.height / frames / Q
            assert 0 <= x and 0 <= y and x + frame_w <= width and y + frame_h <= height, (
                f"{name}/{node}: {path} at ({x}, {y}) sized {frame_w}x{frame_h} "
                f"falls outside the {width}x{height} {name} panel")


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
    # The header furniture is derived now too, so hold it to the same contract.
    expected.update({node: (float(x), float(y))
                     for node, (x, y) in HEADER_NODES.items()})
    expected.update({f"S_cv_input_{name}": (float(x), float(y))
                     for name, _, x, y in REAR_CV_INPUTS})
    expected.update({f"S_audio_output_{name}": (float(x), float(y))
                     for name, _, x, y in REAR_AUDIO_OUTPUTS})
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
    # Reason's own furniture is declared as a table with an offset rather than
    # through one of the helper calls, so it needs its own pattern -- and it
    # must be read from the front panel alone, because folded_front declares
    # the very same node names at its own coordinates.
    check_panel_bounds(device)
    front_only = device[device.index("front = "):device.index("folded_front")]
    # Nodes the folded panels re-declare must be read from the front, or the
    # folded copy wins by appearing later and the front goes unchecked. Both
    # declaration forms need this, not just the offset one.
    placed.update({node: (float(x), float(y)) for node, x, y in re.findall(
        r"(S_[A-Za-z0-9_]+)\s*=\s*\w+\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)", front_only)})
    placed.update({node: (float(x), float(y)) for node, x, y in re.findall(
        r"(S_[A-Za-z0-9_]+)\s*=\s*\{\s*\n\s*offset\s*=\s*"
        r"\{\s*(-?[\d.]+)\s*\*\s*Q\s*,\s*(-?[\d.]+)\s*\*\s*Q\s*\}", front_only)})
    for node, position in expected.items():
        assert node in placed, f"device_2D.lua: {node} is not placed"
        assert placed[node] == position, (
            f"device_2D.lua: {node} at {placed[node]}, "
            f"silkscreen drawn at {position}")

    mirrored = {(float(x), float(y)) for x, y in re.findall(
        r"transform\s*=\s*\{\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\}", gui)}
    mirrored |= {(float(x), float(y)) for x, y in re.findall(
        r"\b(?:fader|toggle|radio|status|patch_name)\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,", gui)}
    missing = sorted(set(expected.values()) - mirrored)
    assert not missing, f"gui.lua: no widget at {missing}"

    # Coordinates alone are not enough: two sliders could trade properties
    # and the old set-based check would still pass. Match every helper call to
    # the property it is meant to control.
    # The cap art is part of the contract: a fader carrying another stage's
    # colour would silently mis-group the panel, so match it too.
    expected_faders = {(name, float(x), float(y), fader_path(node))
                       for node, kind, name, x, y in all_widgets()
                       if kind == "fader"}
    actual_faders = {(name, float(x), float(y), path)
                     for x, y, name, path in re.findall(
        r'\bfader\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*"([^"]+)"'
        r'\s*,\s*"([^"]+)"'
        r'(?:\s*,\s*(?:true|false))?(?:\s*,\s*(?:true|false))?\s*\)', gui)}
    assert actual_faders == expected_faders, (
        "gui.lua: fader property/position/cap-art drift: "
        f"{sorted(actual_faders ^ expected_faders)[:4]}")

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
    for name, _, x, y in REAR_AUDIO_OUTPUTS:
        node, socket = f"S_audio_output_{name}", f"/audio_outputs/{name}"
        assert f'{node} = widget({x}, {y}, "AudioJack", 3)' in device_back
        assert (f'graphics = {{ node = "{node}" }},\n\t\t\tsocket = "{socket}",') in hdgui_back
        assert (f'transform = {{ {x}, {y} }},\n\t\t\tsocket = "{socket}",') in gui_back
    for item in REAR_CONTROLS:
        automation_suffix = "" if item["automation"] else (
            ", true, false" if item["remote"] else ", false, false")
        if item["kind"] == "fader":
            node = f'S_fader_{item["name"]}'
            path = fader_path(node)
            assert f'{node} = fader({item["x"]}, {item["top"]}, "{path}")' in device_back
            assert (f'fader({item["x"]}, {item["top"]}, "{item["name"]}", "{path}", '
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
    assert re.search(r'fader\([^\n]+"chorusNoise",[^\n]*\)', gui_front)
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


def text_ink_width(value, size, strong=False, track=0.0):
    left, _, right, _ = font(size, strong=strong).getbbox(value, anchor="mm")
    return ((right - left) + px(track) * max(0, len(value) - 1)) / Q


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
    assert contrast_ratio(MUTED, FRONT_RECESS) >= 4.5
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
    rear_top_boxes = (REAR_ENGINE_BOX, REAR_UNIT_BOX)
    assert rear_top_boxes[0][0] >= BOX_GAP
    assert WIDTH - rear_top_boxes[-1][2] >= BOX_GAP
    assert rear_top_boxes[1][0] - rear_top_boxes[0][2] >= BOX_GAP
    assert rear_top_boxes[0][1] - 66 >= BOX_GAP
    assert REAR_ENGINE_BOX[0] == REAR_INPUT_BOX[0]
    assert REAR_UNIT_BOX[2] == REAR_OUTPUT_BOX[2]
    assert REAR_UNIT_BOX[0] - REAR_ENGINE_BOX[2] == BOX_GAP
    assert REAR_INPUT_BOX[1] - rear_top_boxes[0][3] >= BOX_GAP
    assert HEIGHT - REAR_INPUT_BOX[3] >= BOX_GAP
    for _, _, x, y in REAR_AUDIO_OUTPUTS:
        assert y > REAR_PERSISTENCE_Y + LABEL_GAP, "audio cable run crosses settings"
        assert REAR_OUTPUT_BOX[0] <= x and x + AUDIO_JACK_SIZE[0] <= REAR_OUTPUT_BOX[2]
        assert y + AUDIO_JACK_SIZE[1] <= REAR_OUTPUT_BOX[3]
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
    # The nameplate is identical on both faces and must clear the patch window.
    wordmark_end = WORDMARK_X + max(
        text_width("YOUKNOW", WORDMARK_SIZE, True, track=TRACK_CAPTION),
        text_width("PROTOCODUS", MAKER_SIZE, strong=True, track=TRACK_TITLE))
    assert wordmark_end + BOX_GAP <= PATCH_BOX[0], "nameplate runs into the patch window"
    assert PATCH_BOX[3] < STATUS_CENTRE_Y - ENGINE_STATUS_SIZE[1] / 2, (
        "the patch window overlaps the readout strip")
    assert WORDMARK_X >= 40 and FOLDED_WORDMARK_X >= 40, "branding overlaps collapse-button area"
    first_caption_left = caption_centre(FIRST_CONTROL) - text_width(
        FIRST_CONTROL["caption"], CAPTION_SIZE, track=TRACK_CAPTION) / 2
    assert abs(STATUS_LEFT_MARGIN - first_caption_left) <= ROUNDING_GUARD, (
        "QUALITY and the first control caption must share the left inset")
    assert WORDMARK_Y + WORDMARK_SIZE / 2 <= STATUS_STRIP_TOP, (
        "the nameplate overlaps the readout separator")
    assert STATUS_STRIP_TOP < ENGINE_STATUS_Y, "readouts must sit below the separator"
    assert (FOLDED_WORDMARK_X + text_width("YOUKNOW", 18.0, True, track=TRACK_CAPTION)
            + 12 <= FOLDED_MAKER_X)
    assert (FOLDED_MAKER_X + text_width("PROTOCODUS", 11.0, strong=True, track=TRACK_TITLE)
            + 12 <= 297)

    # The readout strip is one line of caption/value pairs. Nothing in it may
    # touch its neighbour, and it has to sit inside the header band.
    status_width, status_height = ENGINE_STATUS_SIZE
    assert ENGINE_STATUS_Y >= PATCH_BOX[3]
    assert ENGINE_STATUS_Y + status_height <= FRONT_HEADER_BOTTOM
    # Display positions are placed as floats and emitted as whole units, so the
    # left margin absorbs that rounding exactly as the control rows do.
    previous_end = STATUS_LEFT_MARGIN - ROUNDING_GUARD
    for item in ENGINE_STATUS:
        caption_start = (item["x"] - STATUS_CAPTION_GAP
                         - text_width(item["caption"], STATUS_SIZE, track=TRACK_SCALE))
        assert caption_start >= previous_end, (
            f"{item['caption']}: readout caption collides with its neighbour")
        assert text_width(item["preview"], 11.0) <= status_width
        previous_end = item["x"] + status_width
    note_start = (NOTE_LAMP_X - STATUS_CAPTION_GAP
                  - text_width("NOTE", STATUS_SIZE, track=TRACK_SCALE))
    assert note_start >= previous_end, "NOTE collides with the last readout"
    assert NOTE_LAMP_X + LAMP_SIZE <= WIDTH - STATUS_RIGHT_MARGIN + ROUNDING_GUARD

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
    key_end = key_mode["x"] + TOGGLE_SIZE + RADIO_LABEL_GAP + max(
        text_ink_width(text, RADIO_SIZE, track=TRACK_SCALE) for text in KEY_MODE_LABELS)
    transpose_left = transpose["x"] + FADER_SIZE[0] / 2 - SCALE_OFFSET - max(
        text_ink_width(text, SCALE_SIZE, track=TRACK_SCALE) for _, text in transpose["scale"])
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
                width = text_width(item["caption"], CAPTION_SIZE, track=TRACK_CAPTION)
                assert width <= caption_room, (
                    f"{title}: caption {item['caption']!r} needs {width:.1f} "
                    f"at the {CAPTION_SIZE} size but has "
                    f"{caption_room:.1f} -- shorten it or spread the row")

                # Scale captions hang off the left of the fader, so they have
                # to clear whatever control sits before them.
                if not item["scale"] or item["scale"] == TEN:
                    continue
                widest = max(text_width(text, SCALE_FLOOR, track=TRACK_SCALE)
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


def check_caption_clearance():
    """Measure caption gaps against every visible fader/wheel animation frame."""
    bounds = {}
    for row in LAYOUT:
        for _, _, _, controls in row["sections"]:
            for item in controls:
                kind = item["kind"]
                if kind not in ("fader", "wheel"):
                    continue
                if kind == "fader":
                    asset, frames = fader_asset(item["family"]), 32
                else:
                    asset = "PitchWheel" if item["name"] == "pitchBend" else "ModWheel"
                    frames = 64
                if asset not in bounds:
                    strip = Image.open(OUT / f"{asset}.png").convert("RGBA")
                    boxes = [copy_frame(strip, frames, i).getchannel("A").getbbox()
                             for i in range(frames)]
                    bounds[asset] = (min(box[1] for box in boxes) / Q,
                                     max(box[3] for box in boxes) / Q)
                ink_top, ink_bottom = bounds[asset]
                caption_box = font(CAPTION_SIZE).getbbox(item["caption"])
                caption_bottom = (item["caption_y"]
                                  + (caption_box[3] - caption_box[1]) / (2 * Q))
                top = control_top(item, body_top(row))
                gap = top + ink_top - caption_bottom
                assert gap >= 9, f"{item['name']}: only {gap:.1f}px below caption"
                footer = row["y"] + row["h"] - top - ink_bottom
                assert footer >= 8, f"{item['name']}: only {footer:.1f}px above section edge"


def validate():
    check_caption_clearance()
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
        **{f"{asset}.png": (px(FADER_SIZE[0]), fader_h) for asset in FADER_ASSETS},
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
    for name, frames in (*((f"{asset}.png", 32) for asset in FADER_ASSETS),
                         ("Knob.png", 63), ("Toggle.png", 2),
                         ("MomentaryOverlay.png", 2),
                         ("Lamp.png", 2), ("PitchWheel.png", 64), ("ModWheel.png", 64),
                         ("AudioJack.png", 3), ("CVJack.png", 3)):
        assert Image.open(OUT / name).height % frames == 0, f"{name}: bad frame strip"
    for name, frames in (*((f"{asset}.png", 32) for asset in FADER_ASSETS),
                         ("Knob.png", 63), ("Toggle.png", 2),
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
        **{fader_asset(name): fader_strip(name) for name in FAMILY},
        "Knob": knob_strip(), "Toggle": toggle_strip(),
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
    for name in (*(f"{asset}.png" for asset in FADER_ASSETS),
                 "Knob.png", "Toggle.png", "MomentaryOverlay.png",
                 "Lamp.png", "PitchWheel.png", "ModWheel.png"):
        shutil.copy2(OUT / name, HD / name)
    validate()
    print(f"YouKnow GUI: {WIDTH}x{HEIGHT} logical / {px(WIDTH)}x{px(HEIGHT)} HD; "
          f"{sum(1 for _ in widgets())} front controls in {len(LAYOUT)} rows, "
          f"{sum(1 for _ in rear_widgets())} rear controls; validated")


if __name__ == "__main__":
    main()
