#!/usr/bin/env python3
"""
Render authentic traditional African art, wood, stone, and dirt/terracotta patina GUI
for Maremba Rack Extension.
cz.protocodus.Maremba (Protocodus)

Aesthetics:
- Traditional African Art as primary design foundation:
  - Authentic carved African Hardwoods: Gabon Ebony, African Wenge, Honduran Rosewood, Iroko.
  - Ancient volcanic Basalt & weathered Slate stone chassis with organic tactile micro-texture.
  - Earthy Terracotta, clay, and dry yellow ochre dirt/patina settling into hand-chiseled crevices.
  - Bold 3D-chiseled Kuba cloth geometric chevron & diamond relief friezes (carved with light & shadow).
  - Sacred West African Adinkra medallions (Adinkrahene, Gye Nyame, Dwennimmen, Sankofa).
  - Carved African ceremonial tribal mask emblem on the brand header.
- Absolute Interface Readability:
  - Clean, deep matte obsidian slate / ebony recessed control bays for zero-clutter readability.
  - Crisp, high-contrast ivory-bone white and radiant warm gold typography with drop shadows.
  - Calibrated laser-etched dial ticks with generous spacing and zero overlapping labels.
  - Mathematically refined, pixel-perfect alignment across all 27 knobs and model cards.

Reason HD Divisibility Rule:
- All assets loaded by Reason must strictly satisfy (w % 5 == 0) and (h % 5 == 0).

Outputs:
- GUI2D/: the 5x (HD) art the universal45 package is rendered from (3770 px wide
  panels, 260 px knob frames, 1200x480 model frames) plus the small Reason_*
  browser previews. Nothing else is written there (the u45 must carry no unused file).
- GUI/Output/HD/: the same art for the local gui.lua build, plus Reason's local
  Device* images.
- docs/: composited front and rear previews.
validate() then checks every painted position against GUI2D/device_2D.lua, the
caption spacing, and runs Tests/validate_panel_geometry.py.
"""

import os
import math
import re
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter

Q = 5  # Reason HD 5x scale factor
WIDTH, HEIGHT = 754, 414  # 6U rack unit dimensions (6 * 69 px = 414 px)
FOLDED_HEIGHT = 30        # 1U folded height

HD_WIDTH = WIDTH * Q       # 3770
HD_HEIGHT = HEIGHT * Q     # 2070
HD_FOLDED_H = FOLDED_HEIGHT * Q  # 150

PROJECT = Path(__file__).resolve().parent.parent
GUI2D = PROJECT / "GUI2D"
HD = PROJECT / "GUI" / "Output" / "HD"

# -------------------------------------------------------------------------
# Layout (logical units), shared by the painted captions, the preview
# composites and validate(), which checks it against GUI2D/device_2D.lua.
# -------------------------------------------------------------------------

FRONT_HEADER = {
    "S_patch_name": (235, 14),
    "S_patch_browse_group": (435, 14),
    "S_device_name": (505, 18),
    "S_note_on": (595, 20),
    "S_model_art": (28, 84),
}
MODEL_RADIO_Y = 190
MODEL_RADIOS = (  # node, x, painted label
    ("S_radio_model_0", 32, "ROSEWOOD"),
    ("S_radio_model_1", 92, "PADAUK"),
    ("S_radio_model_2", 152, "BALAFON"),
    ("S_radio_model_3", 212, "KALIMBA"),
)
# The model display (S_model_art, one ModelArt.png frame per model step) ends in
# a nameplate: the model's selector name from texts.lua over its wood and
# resonator from DSP/MarimbaModel.h. validate() checks both lines.
MODEL_PLATES = (  # title, subtitle
    ("IMPERIAL ROSEWOOD 5.0", "HONDURAN ROSEWOOD & BRASS RESONATORS"),
    ("MAYAN PADAUK 4.3", "MEXICAN PADAUK & CEDAR SOUNDBOXES"),
    ("BALAFON ANCESTRAL", "KENE IRONWOOD & CALABASH MIRLITONS"),
    ("KALIMBA ARTISAN 17-KEY", "ACACIA SOUNDBOX & SPRING-STEEL TINES"),
)
PLATE_INSET = 15     # logical inset of the plate from the frame's sides
PLATE_TOP = 26       # logical height of the plate's top above the frame's bottom
PLATE_BOTTOM = 4     # logical gap below the plate
FRONT_KNOBS = {  # node: (x, y, property)
    "S_knob_sympathetic": (39, 228, "sympathetic"),
    "S_knob_bodyBloom": (122, 228, "bodyBloom"),
    "S_knob_pitchGlide": (205, 228, "pitchGlide"),
    "S_knob_buzz": (80, 310, "buzzAmount"),
    "S_knob_artifacts": (164, 310, "artifacts"),
    "S_knob_malletType": (286, 86, "malletType"),
    "S_knob_malletHardness": (338, 86, "malletHardness"),
    "S_knob_strikePosition": (390, 86, "strikePosition"),
    "S_knob_strikeJitter": (442, 86, "strikeJitter"),
    "S_knob_resonatorTune": (292, 194, "resonatorTune"),
    "S_knob_resonatorCoupling": (356, 194, "resonatorCoupling"),
    "S_knob_decay": (428, 194, "decay"),
    "S_knob_polyphony": (292, 298, "polyphony"),
    "S_knob_oversampling": (356, 298, "oversampling"),
    "S_knob_velocityCurve": (428, 298, "velocityCurve"),
    "S_knob_closeLevel": (515, 86, "closeLevel"),
    "S_knob_farLevel": (567, 86, "farLevel"),
    "S_knob_piezoLevel": (619, 86, "piezoLevel"),
    "S_knob_stereoWidth": (671, 86, "stereoWidth"),
    "S_knob_preampDrive": (515, 194, "preampDrive"),
    "S_knob_compAmount": (567, 194, "compAmount"),
    "S_knob_compAttack": (619, 194, "compAttack"),
    "S_knob_compRelease": (671, 194, "compRelease"),
    "S_knob_warmth": (515, 298, "warmth"),
    "S_knob_detune": (567, 298, "detune"),
    "S_knob_masterTune": (619, 298, "masterTune"),
    "S_knob_volume": (671, 298, "volume"),
}
KNOB_SIZE = 52       # logical frame (260 HD px)
KNOB_BODY_R = 19     # logical radius of the painted knob body in Knob.png
# Stepped selectors on the continuous 63-frame knob: Reason shows step i of n at
# frame round(i * 62 / (n - 1)), i.e. -135/0/+135 deg for 3 steps and
# -135/-45/+45/+135 deg for 4. The painted legends name those positions.
STEP_LEGENDS = {
    "S_knob_malletType": ("1", "2", "3", "4"),
    "S_knob_polyphony": ("8", "16", "24"),
    "S_knob_oversampling": ("2x", "4x", "8x"),
    "S_knob_velocityCurve": ("SOFT", "LINEAR", "HARD", "EXPR"),
}
FOLDED_FRONT = {
    "S_patch_name": (235, 6),
    "S_patch_browse_group": (435, 4),
    "S_device_name": (505, 8),
    "S_note_on": (595, 9),
}
FOLDED_BACK = {"S_device_name": (605, 8), "S_cable_origin": (377, 15)}

REAR_PLACEHOLDER = ("S_placeholder", 55, 245)
REAR_TAPE = ("S_device_name", 20, 150)
REAR_AUDIO = (  # node, x, y, caption, sub-caption
    ("S_out_left", 58, 150, "MAIN L", "MASTER L"),
    ("S_out_right", 114, 150, "MAIN R", "MASTER R"),
    ("S_out_close_l", 180, 150, "CLOSE L", "DIRECT L"),
    ("S_out_close_r", 236, 150, "CLOSE R", "DIRECT R"),
    ("S_out_far_l", 300, 150, "FAR L", "DIFFUSE L"),
    ("S_out_far_r", 352, 150, "FAR R", "DIFFUSE R"),
    ("S_out_piezo", 382, 250, "PIEZO", "CONTACT"),
)
REAR_CV = (  # node, x, y, caption, sub-caption (Reason note CV is note/127, not V/oct)
    ("S_cv_note", 460, 150, "NOTE CV", "PITCH"),
    ("S_cv_gate", 512, 150, "GATE CV", "TRIGGER"),
    ("S_cv_mallet", 564, 150, "MALLET", "HARDNESS"),
    ("S_cv_pos", 616, 150, "POSITION", "STRIKE"),
    ("S_cv_coup", 668, 150, "COUPLING", "RESONATOR"),
    ("S_cv_symp", 512, 250, "SYMPATHETIC", "HALO"),
    ("S_cv_vol", 616, 250, "VOLUME CV", "AMPLITUDE"),
)
# Reason Studios' stock routing symbols (RE2D_Stock_Graphics_1_1, Decorations/),
# committed byte for byte in GUI2D and GUI/Output/HD and never re-encoded here;
# docs/ASSET_PROVENANCE.md pins their hashes. The voice bus is mono: it leaves
# as stereo on the three pairs (02, mono in / stereo out) and as mono on the
# piezo jack (01, mono in / mono out). Each icon sits under its group caption.
REAR_ROUTING = (  # node, stock file, x, y, group caption, caption rule half-width
    ("S_routing_main", "Routing_Icon_White_02_1frames", 89, 127, "STEREO MIX", 28),
    ("S_routing_close", "Routing_Icon_White_02_1frames", 211, 127, "STEREO PAIR", 28),
    ("S_routing_far", "Routing_Icon_White_02_1frames", 329, 127, "STEREO PAIR", 26),
    ("S_routing_piezo", "Routing_Icon_White_01_1frames", 385, 227, "MONO", 14),
)
ROUTING_ICON_SIZE = (13, 17)

# The default patch sets the knob frames the previews show.
DEFAULT_PATCH = PROJECT / "Resources" / "Public" / "Concert Grand Rosewood.repatch"
PREVIEW_PATCH_NAME = "Concert Grand Rosewood"

# Functional text must stay readable in Reason (GUI design guidelines: 43 HD px,
# 8.6 logical, is safe) and captions keep at least this gap between them.
MIN_TEXT_SIZE = 8.6
CAPTION_GAP = 1.0
CAPTIONS = {"front": [], "back": [], "folded_front": [], "folded_back": []}
PLATE_TEXT = []      # (model, text, size, box, plate interior), ModelArt.png HD px

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
if not FONT_DIR.exists():
    FONT_DIR = Path("/System/Library/Fonts")

FONT_DIN_COND = FONT_DIR / "DIN Condensed Bold.ttf"
FONT_DIN_ALT = FONT_DIR / "DIN Alternate Bold.ttf"
FONT_ARIAL = FONT_DIR / "Arial Bold.ttf"
FONT_HELVETICA = Path("/System/Library/Fonts/Helvetica.ttc")

def get_font(font_path, size_pts):
    try:
        return ImageFont.truetype(str(font_path), int(size_pts * Q))
    except Exception:
        return ImageFont.load_default()


def caption(draw, panel, xy, text, font_path, size_pts, fill, anchor="mm"):
    """Draw functional text and record its box (HD px) for validate()."""
    font = get_font(font_path, size_pts)
    draw.text(xy, text, fill=fill, font=font, anchor=anchor)
    CAPTIONS[panel].append((text, size_pts, draw.textbbox(xy, text, font=font, anchor=anchor)))

# -------------------------------------------------------------------------
# Procedural African Wood, Stone & Dirt/Terracotta Textures
# -------------------------------------------------------------------------

def create_african_wood_texture(w, h, seed=42, tone="wenge"):
    """
    Procedural deep African Hardwood texture (Wenge / Ebony / Rosewood / Iroko).
    Multiscale growth rings, longitudinal organic fibers, and natural chatoyancy.
    """
    np.random.seed(seed)
    y, x = np.mgrid[0:h, 0:w]
    norm_x = x / float(w)
    norm_y = y / float(h)
    
    # Layered organic grain waviness
    waviness = np.sin(norm_x * 9.0) * 16.0 + np.sin(norm_x * 28.0) * 4.0
    rings = np.sin((norm_y * h * 0.05 + waviness) * 0.35)
    
    fibers = np.random.normal(0, 1.0, (h, w))
    fibers = gaussian_filter(fibers, sigma=(1.0, 10.0))
    
    grain = rings * 0.45 + fibers * 0.55
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    
    edge_vignette = 1.0 - 0.28 * (np.sin(norm_x * np.pi) ** 6)
    
    if tone == "wenge":
        # Deep rich dark African Wenge: espresso with warm caramel streaks
        r = (32 + grain * 58) * edge_vignette
        g = (20 + grain * 36) * edge_vignette
        b = (14 + grain * 22) * edge_vignette
    elif tone == "rosewood":
        r = (48 + grain * 70) * edge_vignette
        g = (22 + grain * 34) * edge_vignette
        b = (16 + grain * 24) * edge_vignette
    elif tone == "padauk":
        r = (78 + grain * 95) * edge_vignette
        g = (30 + grain * 44) * edge_vignette
        b = (16 + grain * 22) * edge_vignette
    else:
        r = (22 + grain * 30) * edge_vignette
        g = (22 + grain * 30) * edge_vignette
        b = (24 + grain * 32) * edge_vignette

    r = np.clip(r, 0, 255).astype(np.uint8)
    g = np.clip(g, 0, 255).astype(np.uint8)
    b = np.clip(b, 0, 255).astype(np.uint8)
    
    rgb = np.stack([r, g, b, np.full((h, w), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(rgb, "RGBA")


def create_stone_slate_texture(w, h, seed=101):
    """
    Procedural ancient volcanic basalt and weathered slate stone faceplate.
    Multiscale organic noise with subtle mineral flecks and tactile chiseling.
    """
    np.random.seed(seed)
    n_macro = gaussian_filter(np.random.normal(0, 1.0, (h, w)), sigma=40.0)
    n_meso  = gaussian_filter(np.random.normal(0, 1.0, (h, w)), sigma=12.0)
    n_micro = gaussian_filter(np.random.normal(0, 1.0, (h, w)), sigma=2.2)
    
    stone = n_macro * 0.45 + n_meso * 0.35 + n_micro * 0.20
    stone = (stone - stone.min()) / (stone.max() - stone.min())
    
    # Tactile basalt stone: deep charcoal to weathered slate with warm mineral flecks
    r = (24 + stone * 28).astype(np.uint8)
    g = (25 + stone * 29).astype(np.uint8)
    b = (27 + stone * 31).astype(np.uint8)
    
    rgb = np.stack([r, g, b, np.full((h, w), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(rgb, "RGBA")


def create_rear_stone_steel_texture(w, h, seed=303):
    """Procedural weathered dark steel & volcanic stone chassis for the rear panel."""
    np.random.seed(seed)
    brush = np.random.normal(0, 2.2, (h, 1))
    brush = np.repeat(brush, w, axis=1)
    micro = gaussian_filter(np.random.normal(0, 1.5, (h, w)), sigma=1.8)
    
    y_grad = np.linspace(28, 20, h)[:, None]
    base = np.clip(y_grad + brush + micro, 0, 255).astype(np.uint8)
    
    r = base
    g = np.clip(base + 1, 0, 255).astype(np.uint8)
    b = np.clip(base + 2, 0, 255).astype(np.uint8)
    
    rgb = np.stack([r, g, b, np.full((h, w), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(rgb, "RGBA")

# -------------------------------------------------------------------------
# Traditional African Art Drawing Primitives
# -------------------------------------------------------------------------

def draw_bold_kuba_chevron_border(draw, x0, y0, length, height):
    """
    Bold, authentic 3D-chiseled Kuba Cloth chevron frieze:
    Alternating bold triangular facets with light-and-shadow relief,
    inlaid with terracotta clay and diamond studs.
    """
    gold_hi = (242, 208, 110)
    shadow = (14, 10, 8)
    terracotta = (155, 68, 32)
    dark_wood = (28, 18, 12)
    
    # Background rail
    draw.rectangle([x0, y0, x0 + length, y0 + height], fill=dark_wood, outline=shadow, width=1)
    draw.line([(x0, y0), (x0 + length, y0)], fill=gold_hi, width=1)
    draw.line([(x0, y0 + height), (x0 + length, y0 + height)], fill=shadow, width=2)
    
    unit_w = int(height * 1.8)
    num = int(length / unit_w) + 1
    
    for i in range(num):
        cx0 = x0 + i * unit_w
        cx_mid = cx0 + unit_w / 2.0
        cx1 = cx0 + unit_w
        cy_top = y0 + 2
        cy_bot = y0 + height - 2
        
        if cx0 >= x0 + length:
            continue
            
        tri_up = [(cx0, cy_bot), (cx_mid, cy_top), (cx1, cy_bot)]
        draw.polygon(tri_up, fill=terracotta)
        draw.line([(cx0, cy_bot), (cx_mid, cy_top)], fill=gold_hi, width=2)
        draw.line([(cx_mid, cy_top), (cx1, cy_bot)], fill=shadow, width=2)
        
        dm_w = unit_w * 0.22
        dm_h = (cy_bot - cy_top) * 0.45
        dm_cy = cy_top + dm_h
        dm_pts = [(cx_mid, dm_cy - dm_h * 0.5), (cx_mid + dm_w * 0.5, dm_cy),
                  (cx_mid, dm_cy + dm_h * 0.5), (cx_mid - dm_w * 0.5, dm_cy)]
        draw.polygon(dm_pts, fill=dark_wood, outline=gold_hi, width=1)
        draw.ellipse([cx_mid - 2 * Q, dm_cy - 2 * Q, cx_mid + 2 * Q, dm_cy + 2 * Q], fill=gold_hi)


def draw_vertical_kuba_ear_carving(draw, x0, y0, width, height, point_right=True):
    """Vertical carved African totem pillar on the wood rack ears."""
    gold_hi = (242, 208, 110)
    shadow = (14, 10, 8)
    terracotta = (155, 68, 32)
    dark_wood = (22, 14, 10)
    
    draw.rectangle([x0, y0, x0 + width, y0 + height], fill=dark_wood, outline=shadow, width=1)
    
    unit_h = int(width * 1.6)
    num = int(height / unit_h) + 1
    
    for i in range(num):
        cy0 = y0 + i * unit_h
        cy_mid = cy0 + unit_h / 2.0
        cy1 = cy0 + unit_h
        
        if cy1 > y0 + height:
            continue
            
        if point_right:
            cx_base = x0 + 2
            cx_tip = x0 + width - 2
            tri = [(cx_base, cy0), (cx_tip, cy_mid), (cx_base, cy1)]
            draw.polygon(tri, fill=terracotta)
            draw.line([(cx_base, cy0), (cx_tip, cy_mid)], fill=gold_hi, width=2)
            draw.line([(cx_tip, cy_mid), (cx_base, cy1)], fill=shadow, width=2)
            
            dm_w = (cx_tip - cx_base) * 0.45
            dm_h = unit_h * 0.22
            dm_cx = cx_base + dm_w
            dm_pts = [(dm_cx - dm_w * 0.5, cy_mid), (dm_cx, cy_mid - dm_h * 0.5),
                      (dm_cx + dm_w * 0.5, cy_mid), (dm_cx, cy_mid + dm_h * 0.5)]
            draw.polygon(dm_pts, fill=dark_wood, outline=gold_hi, width=1)
            draw.ellipse([dm_cx - 2 * Q, cy_mid - 2 * Q, dm_cx + 2 * Q, cy_mid + 2 * Q], fill=gold_hi)
        else:
            cx_base = x0 + width - 2
            cx_tip = x0 + 2
            tri = [(cx_base, cy0), (cx_tip, cy_mid), (cx_base, cy1)]
            draw.polygon(tri, fill=terracotta)
            draw.line([(cx_base, cy0), (cx_tip, cy_mid)], fill=gold_hi, width=2)
            draw.line([(cx_tip, cy_mid), (cx_base, cy1)], fill=shadow, width=2)
            
            dm_w = (cx_base - cx_tip) * 0.45
            dm_h = unit_h * 0.22
            dm_cx = cx_base - dm_w
            dm_pts = [(dm_cx + dm_w * 0.5, cy_mid), (dm_cx, cy_mid - dm_h * 0.5),
                      (dm_cx - dm_w * 0.5, cy_mid), (dm_cx, cy_mid + dm_h * 0.5)]
            draw.polygon(dm_pts, fill=dark_wood, outline=gold_hi, width=1)
            draw.ellipse([dm_cx - 2 * Q, cy_mid - 2 * Q, dm_cx + 2 * Q, cy_mid + 2 * Q], fill=gold_hi)


def draw_carved_african_mask_crest(draw, cx, cy, radius, gold=(235, 195, 75), terracotta=(150, 68, 32)):
    """Authentic carved African Ceremonial Mask & Royal Sunburst Medallion."""
    draw.ellipse([cx - radius - 3, cy - radius - 3, cx + radius + 3, cy + radius + 3], fill=(10, 8, 6))
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(22, 16, 12), outline=gold, width=2)
    
    r_mid = max(3, int(radius * 0.76))
    draw.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], fill=terracotta, outline=gold, width=1)
    
    for i in range(8):
        ang = i * 45.0
        rad = math.radians(ang)
        p_tip = (cx + math.cos(rad) * radius * 0.95, cy + math.sin(rad) * radius * 0.95)
        p_b1  = (cx + math.cos(rad + 0.15) * r_mid, cy + math.sin(rad + 0.15) * r_mid)
        p_b2  = (cx + math.cos(rad - 0.15) * r_mid, cy + math.sin(rad - 0.15) * r_mid)
        draw.polygon([p_tip, p_b1, p_b2], fill=gold)
        
    fw = radius * 0.46
    fh = radius * 0.62
    face_pts = [
        (cx, cy - fh),
        (cx + fw, cy - fh * 0.3),
        (cx + fw * 0.65, cy + fh),
        (cx, cy + fh * 0.85),
        (cx - fw * 0.65, cy + fh),
        (cx - fw, cy - fh * 0.3)
    ]
    draw.polygon(face_pts, fill=(38, 22, 14), outline=gold, width=2)
    
    crown_pts = [(cx, cy - fh), (cx + fw * 0.6, cy - fh * 0.4), (cx, cy - fh * 0.25), (cx - fw * 0.6, cy - fh * 0.4)]
    draw.polygon(crown_pts, fill=terracotta, outline=gold, width=1)
    draw.ellipse([cx - 2 * Q, cy - fh * 0.5 - 2 * Q, cx + 2 * Q, cy - fh * 0.5 + 2 * Q], fill=gold)
    
    eye_y = cy - fh * 0.05
    eye_dx = fw * 0.42
    eye_w = fw * 0.32
    draw.line([(cx - eye_dx - eye_w, eye_y), (cx - eye_dx + eye_w, eye_y)], fill=gold, width=2)
    draw.line([(cx + eye_dx - eye_w, eye_y), (cx + eye_dx + eye_w, eye_y)], fill=gold, width=2)
    
    draw.line([(cx, cy - fh * 0.15), (cx, cy + fh * 0.35)], fill=gold, width=2)
    draw.line([(cx - 3 * Q, cy + fh * 0.35), (cx + 3 * Q, cy + fh * 0.35)], fill=gold, width=2)
    draw.rectangle([cx - 3 * Q, cy + fh * 0.55 - 1 * Q, cx + 3 * Q, cy + fh * 0.55 + 1 * Q], fill=(15, 10, 6), outline=gold, width=1)


def draw_carved_corner_bracket(draw, bx, by, size, sx, sy, gold=(235, 195, 75), shadow=(18, 12, 8)):
    """Hand-carved stepped right-angle bracket with brass rivet."""
    draw.line([(bx, by), (bx + sx * size, by)], fill=gold, width=2)
    draw.line([(bx, by), (bx, by + sy * size)], fill=gold, width=2)
    
    for off in [4 * Q, 9 * Q, 14 * Q]:
        if off < size:
            draw.line([(bx + sx * off, by + sy * 2 * Q), (bx + sx * 2 * Q, by + sy * off)], fill=gold, width=1)
            
    rx = bx + sx * 4 * Q
    ry = by + sy * 4 * Q
    draw.ellipse([rx - 2 * Q, ry - 2 * Q, rx + 2 * Q, ry + 2 * Q], fill=(10, 8, 6))
    draw.ellipse([rx - 2 * Q + 1, ry - 2 * Q + 1, rx + 2 * Q - 1, ry + 2 * Q - 1], fill=gold)


def draw_brass_wood_screw(draw, cx, cy, radius, angle_deg=40):
    """Heavy antiqued brass countersunk machine bolt on wood chassis."""
    draw.ellipse([cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2], fill=(10, 8, 6))
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(175, 135, 45), outline=(95, 70, 20), width=2)
    
    r_in = radius - 3
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(140, 105, 35))
    
    rad = math.radians(angle_deg)
    dx = math.cos(rad) * (r_in - 2)
    dy = math.sin(rad) * (r_in - 2)
    draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=(20, 15, 8), width=int(radius * 0.35))
    draw.arc([cx - r_in, cy - r_in, cx + r_in, cy + r_in], -135, -45, fill=(245, 215, 115), width=2)


def draw_recessed_control_bay(draw, x0, y0, w, h, gold_rim=(215, 175, 65), shadow=(18, 12, 8)):
    """Deep matte obsidian slate recessed mounting bay."""
    draw.rectangle([x0 - 3, y0 - 3, x0 + w + 3, y0 + h + 3], fill=shadow)
    draw.rectangle([x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1], outline=(55, 45, 35), width=1)
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(18, 19, 21), outline=(42, 45, 48), width=2)
    draw.line([(x0 + 1, y0 + 1), (x0 + w - 1, y0 + 1)], fill=gold_rim, width=2)
    draw.line([(x0 + 1, y0 + h - 1), (x0 + w - 1, y0 + h - 1)], fill=(75, 60, 42), width=1)


def draw_dial_ticks(draw, cx, cy, radius=132, start_angle_deg=225, sweep_deg=270, num_ticks=11,
                    active_color=(235, 195, 75), dim_color=(140, 135, 125), all_major=False):
    recess_r = radius - 15
    draw.ellipse([cx - recess_r, cy - recess_r, cx + recess_r, cy + recess_r], outline=(14, 15, 16), width=2)
    draw.arc([cx - recess_r, cy - recess_r, cx + recess_r, cy + recess_r], 45, 225, fill=(45, 48, 52), width=1)
    
    step = sweep_deg / (num_ticks - 1)
    for i in range(num_ticks):
        angle = start_angle_deg - i * step
        rad = math.radians(angle)
        is_major = all_major or (i == 0 or i == num_ticks - 1 or i == (num_ticks - 1) // 2)
        r1 = radius
        r2 = radius + (18 if is_major else 10)
        
        x1 = cx + math.cos(rad) * r1
        y1 = cy - math.sin(rad) * r1
        x2 = cx + math.cos(rad) * r2
        y2 = cy - math.sin(rad) * r2
        
        color = active_color if (i == 0 or i == num_ticks - 1) else dim_color
        tick_w = 3 if is_major else 2
        draw.line([(x1, y1), (x2, y2)], fill=color, width=tick_w)
        if is_major:
            draw.ellipse([x2 - 3, y2 - 3, x2 + 3, y2 + 3], fill=active_color)


def step_angles(steps):
    """Dial angles (deg, counter-clockwise from 3 o'clock) of each step position."""
    return [225.0 - i * 270.0 / (steps - 1) for i in range(steps)]


def draw_step_legend(draw, node, labels, color, radius=132):
    """Name each position of a stepped knob beside its tick.

    Side labels grow away from the knob, so the caption under it stays clear;
    the top position (3-step knobs) is labelled above its tick.
    """
    kx, ky, _ = FRONT_KNOBS[node]
    cx = (kx + KNOB_SIZE / 2) * Q
    cy = (ky + KNOB_SIZE / 2) * Q
    reach = radius + 18 + 4          # major tick end plus a small gap (HD px)
    draw_dial_ticks(draw, cx, cy, radius=radius, num_ticks=len(labels),
                    active_color=color, dim_color=color, all_major=True)
    for angle, text in zip(step_angles(len(labels)), labels):
        rad = math.radians(angle)
        if abs(math.cos(rad)) < 0.2:
            caption(draw, "front", (cx, cy - reach - 1 * Q), text, FONT_DIN_COND, 9.5, color, "mb")
            continue
        x = cx + math.cos(rad) * reach
        # Lower labels ride slightly above their tick so the caption keeps its gap.
        y = cy - math.sin(rad) * reach + (-1 * Q if math.sin(rad) < 0 else 0)
        caption(draw, "front", (x, y), text, FONT_DIN_COND, 9.5, color,
                "lm" if math.cos(rad) > 0 else "rm")


def draw_socket_collar(draw, cx, cy, is_audio=True):
    r_outer = 48 if is_audio else 42
    r_inner = 32 if is_audio else 26
    r_hole = 20 if is_audio else 16
    
    draw.ellipse([cx - r_outer - 3, cy - r_outer - 3, cx + r_outer + 3, cy + r_outer + 3], fill=(8, 8, 8))
    border_color = (225, 185, 70) if is_audio else (160, 165, 170)
    fill_ring = (48, 50, 54)
    draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=fill_ring, outline=border_color, width=3)
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=(20, 22, 24), outline=(36, 38, 42), width=2)
    draw.ellipse([cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole], fill=(5, 5, 6))
    draw.arc([cx - r_hole + 4, cy - r_hole + 4, cx + r_hole - 4, cy + r_hole - 4], 30, 120, fill=(240, 195, 70), width=3)

# -------------------------------------------------------------------------
# Native Art Model Badges (Filmstrip: 4 Frames of 1200x480 at 5x HD)
# -------------------------------------------------------------------------

def plate_top(y0, h):
    return y0 + h - PLATE_TOP * Q


def draw_model_plate(draw, model, x0, y0, w, h, fill):
    """Nameplate of a model frame; records both lines (HD px) for validate()."""
    gold = (235, 195, 70)
    plate = (x0 + PLATE_INSET * Q, plate_top(y0, h), x0 + w - PLATE_INSET * Q, y0 + h - PLATE_BOTTOM * Q)
    draw.rectangle(plate, fill=fill, outline=gold, width=2)
    interior = (plate[0] + 2, plate[1] + 2, plate[2] - 2, plate[3] - 2)
    title, subtitle = MODEL_PLATES[model]
    for text, dy, font_path, size, color in ((title, 9, FONT_DIN_COND, 13, gold),
                                             (subtitle, 17, FONT_DIN_ALT, 9, (235, 225, 210))):
        xy = (x0 + w // 2, plate[1] + dy * Q)
        font = get_font(font_path, size)
        draw.text(xy, text, fill=color, font=font, anchor="mm")
        PLATE_TEXT.append((model, text, size, draw.textbbox(xy, text, font=font, anchor="mm"), interior))


def draw_art_frame_rosewood(draw, x0, y0, w, h):
    gold = (235, 195, 70)
    shadow = (25, 16, 10)
    terracotta = (140, 68, 32)
    
    for i in range(h):
        r = int(26 + 18 * (i / float(h)))
        g = int(14 + 10 * (i / float(h)))
        b = int(10 + 8 * (i / float(h)))
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    bs = 35 * Q
    draw_carved_corner_bracket(draw, x0 + 4 * Q, y0 + 4 * Q, bs, 1, 1, gold, shadow)
    draw_carved_corner_bracket(draw, x0 + w - 4 * Q, y0 + 4 * Q, bs, -1, 1, gold, shadow)
    draw_carved_corner_bracket(draw, x0 + 4 * Q, y0 + h - 26 * Q, bs, 1, -1, gold, shadow)
    draw_carved_corner_bracket(draw, x0 + w - 4 * Q, y0 + h - 26 * Q, bs, -1, -1, gold, shadow)
    
    draw_bold_kuba_chevron_border(draw, x0 + 45 * Q, y0 + 3 * Q, w - 90 * Q, 9 * Q)
    
    bar_count = 11
    pad_x = 24 * Q
    avail_w = w - 2 * pad_x
    bar_step = avail_w / float(bar_count)
    center_y = y0 + int(h * 0.46)
    pl_y = plate_top(y0, h)

    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step + bar_step * 0.15)
        bw = int(bar_step * 0.70)
        pipe_len = int((h * 0.38) * (1.0 - 0.55 * (i / float(bar_count))))
        top_py = center_y + 12 * Q
        bot_py = min(top_py + pipe_len, pl_y)  # tubes run on behind the nameplate
        for col in range(bw):
            shine = math.sin((col / float(bw)) * math.pi)
            pr = int(185 + 65 * shine)
            pg = int(145 + 55 * shine)
            pb = int(45 + 35 * shine)
            draw.line([(bx + col, top_py), (bx + col, bot_py)], fill=(pr, pg, pb))
        if bot_py + 6 * Q <= pl_y:
            draw.arc([bx, bot_py - 6 * Q, bx + bw, bot_py + 6 * Q], 0, 180, fill=(105, 80, 25), width=2)

    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step)
        bw = int(bar_step * 0.88)
        bar_len = int((h * 0.44) * (1.0 - 0.42 * (i / float(bar_count))))
        top_by = center_y - bar_len // 2
        bot_by = center_y + bar_len // 2
        draw.rectangle([bx + 4 * Q, top_by + 4 * Q, bx + bw + 4 * Q, bot_by + 4 * Q], fill=(12, 8, 6))
        for col in range(bw):
            shine = math.sin((col / float(bw)) * math.pi)
            br = int(75 + 40 * shine)
            bg = int(32 + 20 * shine)
            bb = int(18 + 12 * shine)
            draw.line([(bx + col, top_by), (bx + col, bot_by)], fill=(br, bg, bb))
        draw.rectangle([bx, top_by, bx + bw, bot_by], outline=(45, 18, 10), width=2)
        arch_cy = bot_by - 4 * Q
        draw.arc([bx + 3 * Q, arch_cy - 12 * Q, bx + bw - 3 * Q, arch_cy + 12 * Q], 180, 360, fill=(30, 10, 6), width=2)
        n1 = top_by + int(bar_len * 0.224)
        n2 = bot_by - int(bar_len * 0.224)
        for ny in [n1, n2]:
            draw.ellipse([bx + bw // 2 - 3 * Q, ny - 3 * Q, bx + bw // 2 + 3 * Q, ny + 3 * Q], fill=gold)
            
    draw.line([(x0 + pad_x, center_y - 28 * Q), (x0 + w - pad_x, center_y - 12 * Q)], fill=(245, 220, 140), width=2)
    draw.line([(x0 + pad_x, center_y + 28 * Q), (x0 + w - pad_x, center_y + 12 * Q)], fill=(245, 220, 140), width=2)
    
    draw_model_plate(draw, 0, x0, y0, w, h, fill=(26, 16, 10))


def draw_art_frame_padauk(draw, x0, y0, w, h):
    shadow = (25, 16, 10)
    terracotta = (165, 72, 32)
    
    for i in range(h):
        r = int(48 + 26 * (i / float(h)))
        g = int(20 + 12 * (i / float(h)))
        b = int(12 + 8 * (i / float(h)))
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    draw_bold_kuba_chevron_border(draw, x0 + 45 * Q, y0 + 3 * Q, w - 90 * Q, 9 * Q)
    
    bar_count = 11
    pad_x = 24 * Q
    avail_w = w - 2 * pad_x
    bar_step = avail_w / float(bar_count)
    center_y = y0 + int(h * 0.46)
    
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step + bar_step * 0.12)
        bw = int(bar_step * 0.74)
        box_h = int((h * 0.35) * (1.0 - 0.50 * (i / float(bar_count))))
        top_py = center_y + 10 * Q
        draw.rectangle([bx, top_py, bx + bw, top_py + box_h], fill=(70, 36, 18), outline=(42, 20, 10), width=2)
        draw.rectangle([bx + 3 * Q, top_py + 4 * Q, bx + bw - 3 * Q, top_py + 10 * Q], fill=(22, 12, 8))
        
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step)
        bw = int(bar_step * 0.88)
        bar_len = int((h * 0.44) * (1.0 - 0.42 * (i / float(bar_count))))
        top_by = center_y - bar_len // 2
        bot_by = center_y + bar_len // 2
        draw.rectangle([bx + 4 * Q, top_by + 4 * Q, bx + bw + 4 * Q, bot_by + 4 * Q], fill=(16, 8, 5))
        for col in range(bw):
            shine = math.sin((col / float(bw)) * math.pi)
            br = int(145 + 55 * shine)
            bg = int(50 + 26 * shine)
            bb = int(22 + 14 * shine)
            draw.line([(bx + col, top_by), (bx + col, bot_by)], fill=(br, bg, bb))
        draw.rectangle([bx, top_by, bx + bw, bot_by], outline=(75, 24, 10), width=2)
        
    draw_model_plate(draw, 1, x0, y0, w, h, fill=(32, 18, 12))


def draw_art_frame_balafon(draw, x0, y0, w, h):
    shadow = (25, 16, 10)
    terracotta = (140, 75, 36)
    
    for i in range(h):
        r = int(32 + 18 * (i / float(h)))
        g = int(24 + 14 * (i / float(h)))
        b = int(16 + 10 * (i / float(h)))
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    draw_bold_kuba_chevron_border(draw, x0 + 45 * Q, y0 + 3 * Q, w - 90 * Q, 9 * Q)
    
    bar_count = 11
    pad_x = 24 * Q
    avail_w = w - 2 * pad_x
    bar_step = avail_w / float(bar_count)
    center_y = y0 + int(h * 0.46)
    
    for i in range(bar_count):
        gx = int(x0 + pad_x + i * bar_step + bar_step * 0.44)
        gourd_r = int((26 * Q) * (1.0 - 0.40 * (i / float(bar_count))))
        gy = center_y + int(18 * Q + gourd_r * 0.8)
        draw.ellipse([gx - gourd_r, gy - gourd_r, gx + gourd_r, gy + gourd_r],
                     fill=(145, 95, 42), outline=(68, 40, 16), width=2)
        mr = max(2 * Q, int(gourd_r * 0.28))
        draw.ellipse([gx - mr, gy - mr, gx + mr, gy + mr], fill=(240, 235, 215), outline=(90, 55, 25), width=2)
        
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step)
        bw = int(bar_step * 0.86)
        bar_len = int((h * 0.42) * (1.0 - 0.40 * (i / float(bar_count))))
        top_by = center_y - bar_len // 2
        bot_by = center_y + bar_len // 2
        draw.rectangle([bx + 4 * Q, top_by + 4 * Q, bx + bw + 4 * Q, bot_by + 4 * Q], fill=(12, 10, 8))
        for col in range(bw):
            shine = math.sin((col / float(bw)) * math.pi)
            br = int(45 + 24 * shine)
            bg = int(32 + 18 * shine)
            bb = int(22 + 12 * shine)
            draw.line([(bx + col, top_by), (bx + col, bot_by)], fill=(br, bg, bb))
        draw.rectangle([bx, top_by, bx + bw, bot_by], outline=(22, 16, 10), width=2)
        
    draw_model_plate(draw, 2, x0, y0, w, h, fill=(24, 18, 12))


def draw_art_frame_kalimba(draw, x0, y0, w, h):
    pyro = (195, 120, 40)
    
    for i in range(h):
        r = int(52 + 25 * (i / float(h)))
        g = int(30 + 15 * (i / float(h)))
        b = int(16 + 10 * (i / float(h)))
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    hole_cx = x0 + w // 2
    hole_cy = y0 + int(h * 0.58)
    rosette_r1 = 38 * Q
    rosette_r2 = 28 * Q
    soundhole_r = 18 * Q
    
    draw.ellipse([hole_cx - rosette_r1, hole_cy - rosette_r1, hole_cx + rosette_r1, hole_cy + rosette_r1],
                 outline=(165, 95, 35), width=2)
    draw.ellipse([hole_cx - rosette_r2, hole_cy - rosette_r2, hole_cx + rosette_r2, hole_cy + rosette_r2],
                 outline=(195, 120, 45), width=2)
    for ang in range(0, 360, 15):
        rad = math.radians(ang)
        x1 = hole_cx + int(rosette_r2 * math.cos(rad))
        y1 = hole_cy + int(rosette_r2 * math.sin(rad))
        x2 = hole_cx + int(rosette_r1 * math.cos(rad))
        y2 = hole_cy + int(rosette_r1 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=pyro, width=2)
        
    draw.ellipse([hole_cx - soundhole_r, hole_cy - soundhole_r, hole_cx + soundhole_r, hole_cy + soundhole_r],
                 fill=(14, 8, 5), outline=(75, 36, 16), width=3)
                 
    bridge_y = y0 + 14 * Q
    bridge_w = w - 40 * Q
    bridge_x = x0 + 20 * Q
    draw.rectangle([bridge_x, bridge_y, bridge_x + bridge_w, bridge_y + 16 * Q],
                   fill=(45, 24, 12), outline=(24, 12, 6), width=2)
    bar_y = bridge_y + 4 * Q
    draw.rectangle([bridge_x + 4 * Q, bar_y, bridge_x + bridge_w - 4 * Q, bar_y + 7 * Q],
                   fill=(145, 150, 160), outline=(80, 85, 95), width=2)
                   
    num_tines = 17
    center_idx = 8
    pad_tines_x = 28 * Q
    avail_tines_w = w - 2 * pad_tines_x
    tine_step = avail_tines_w / float(num_tines)
    
    for i in range(num_tines):
        tx = int(x0 + pad_tines_x + i * tine_step + tine_step * 0.10)
        tw = int(tine_step * 0.80)
        dist = abs(i - center_idx)
        tine_len = int((h * 0.58) - dist * (4.2 * Q))
        tine_top = bridge_y - 4 * Q
        tine_bot = tine_top + tine_len
        
        draw.rectangle([tx + 2 * Q, tine_top + 4 * Q, tx + tw + 2 * Q, tine_bot + 2 * Q], fill=(22, 12, 8))
        for col in range(tw):
            shine = math.sin((col / float(tw)) * math.pi)
            sr = int(175 + 75 * shine)
            sg = int(180 + 75 * shine)
            sb = int(190 + 65 * shine)
            draw.line([(tx + col, tine_top), (tx + col, tine_bot)], fill=(sr, sg, sb))
        draw.rectangle([tx, tine_top, tx + tw, tine_bot], outline=(95, 100, 110), width=1)
        draw.rounded_rectangle([tx, tine_bot - 4 * Q, tx + tw, tine_bot + 3 * Q],
                               radius=2 * Q, fill=(230, 235, 245), outline=(105, 110, 120), width=1)
                               
    draw_model_plate(draw, 3, x0, y0, w, h, fill=(28, 16, 10))


def render_model_art():
    fw = 240 * Q
    fh = 96 * Q
    total_h = fh * 4

    art_img = Image.new("RGBA", (fw, total_h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(art_img)

    draw_art_frame_rosewood(draw, 0, 0, fw, fh)
    draw_art_frame_padauk(draw, 0, fh, fw, fh)
    draw_art_frame_balafon(draw, 0, fh * 2, fw, fh)
    draw_art_frame_kalimba(draw, 0, fh * 3, fw, fh)

    # GUI2D carries the same 5x strip (device_2D places 240x96 logical frames).
    art_img.save(HD / "ModelArt.png")
    art_img.save(GUI2D / "ModelArt.png")
    print("Rendered ModelArt.png successfully (4 authentic African instrument frames)!")

# -------------------------------------------------------------------------
# Front Panel Technical Diagram & Components
# -------------------------------------------------------------------------

def draw_acoustic_bar_schematic(draw, x_u, y_u, w_u, h_u):
    x = x_u * Q
    y = y_u * Q
    w = w_u * Q
    h = h_u * Q
    gold = (235, 195, 75)
    dim_gold = (175, 145, 75)
    
    draw.rectangle([x, y, x + w, y + h], fill=(16, 17, 19), outline=(42, 46, 50), width=1)
    font_tiny = get_font(FONT_DIN_ALT, 6.5)
    
    # Text placed cleanly at top left and top right
    draw.text((x + 6 * Q, y + 4 * Q), "NODAL SUSPENSION (0.224 L)", fill=dim_gold, font=font_tiny, anchor="lt")
    draw.text((x + w - 6 * Q, y + 4 * Q), "1/4 WAVE RESONATOR", fill=dim_gold, font=font_tiny, anchor="rt")
    
    bar_y = y + int(h * 0.52)
    bar_w = int(w * 0.68)
    bx0 = x + (w - bar_w) // 2
    bx1 = bx0 + bar_w
    bar_h = 4 * Q
    
    draw.rectangle([bx0, bar_y - bar_h, bx1, bar_y], fill=(62, 34, 20), outline=gold, width=1)
    arch_cx = bx0 + bar_w // 2
    arch_rx = int(bar_w * 0.28)
    draw.arc([arch_cx - arch_rx, bar_y - 3 * Q, arch_cx + arch_rx, bar_y + 3 * Q], 0, 180, fill=(16, 17, 19), width=2)
    
    node1_x = int(bx0 + bar_w * 0.224)
    node2_x = int(bx1 - bar_w * 0.224)
    for nx in [node1_x, node2_x]:
        draw.ellipse([nx - 2 * Q, bar_y - bar_h // 2 - 2 * Q, nx + 2 * Q, bar_y - bar_h // 2 + 2 * Q], fill=gold)
        draw.line([(nx, bar_y - bar_h - 2 * Q), (nx, bar_y + 2 * Q)], fill=(215, 170, 50), width=1)
        
    pipe_w = int(bar_w * 0.32)
    px0 = arch_cx - pipe_w // 2
    px1 = arch_cx + pipe_w // 2
    py0 = bar_y + 2 * Q
    py1 = y + h - 3 * Q
    draw.line([(px0, py0), (px0, py1)], fill=gold, width=2)
    draw.line([(px1, py0), (px1, py1)], fill=gold, width=2)
    draw.arc([px0, py1 - 3 * Q, px1, py1 + 3 * Q], 0, 180, fill=gold, width=2)


# -------------------------------------------------------------------------
# Front Panel Main Renderer
# -------------------------------------------------------------------------

def render_front_panel():
    """Render the 6U front panel at 3770x2070 (5x), saved identically to GUI2D and HD."""
    panel = create_stone_slate_texture(HD_WIDTH, HD_HEIGHT, seed=101)
    
    ear_w = 24 * Q  # 120 px
    wenge_l = create_african_wood_texture(ear_w, HD_HEIGHT, seed=42, tone="wenge")
    wenge_r = create_african_wood_texture(ear_w, HD_HEIGHT, seed=84, tone="wenge")
    panel.paste(wenge_l, (0, 0))
    panel.paste(wenge_r, (HD_WIDTH - ear_w, 0))
    
    draw = ImageDraw.Draw(panel)
    gold = (235, 195, 75)
    shadow = (18, 12, 8)
    terracotta = (148, 65, 32)
    white_ink = (244, 242, 236)
    dim_ink = (165, 160, 150)
    
    # Vertical carved African totem pillars on wood ears
    draw_vertical_kuba_ear_carving(draw, 5 * Q, 25 * Q, 14 * Q, HD_HEIGHT - 50 * Q, point_right=True)
    draw_vertical_kuba_ear_carving(draw, HD_WIDTH - ear_w + 5 * Q, 25 * Q, 14 * Q, HD_HEIGHT - 50 * Q, point_right=False)
                            
    # Wood-to-Stone chiseled seam
    draw.line([(ear_w - 2, 0), (ear_w - 2, HD_HEIGHT)], fill=shadow, width=3)
    draw.line([(ear_w + 1, 0), (ear_w + 1, HD_HEIGHT)], fill=gold, width=2)
    draw.line([(HD_WIDTH - ear_w - 2, 0), (HD_WIDTH - ear_w - 2, HD_HEIGHT)], fill=gold, width=2)
    draw.line([(HD_WIDTH - ear_w, 0), (HD_WIDTH - ear_w, HD_HEIGHT)], fill=shadow, width=3)
    
    # Antiqued brass rack bolts
    screw_ys = [18 * Q, 90 * Q, 162 * Q, 252 * Q, 324 * Q, 396 * Q]
    for sy in screw_ys:
        draw_brass_wood_screw(draw, ear_w // 2, sy, 8 * Q, angle_deg=35)
        draw_brass_wood_screw(draw, HD_WIDTH - ear_w // 2, sy, 8 * Q, angle_deg=70)
        
    # Top and bottom bold Kuba chevron borders (11*Q height)
    frieze_h = 11 * Q
    frieze_x0 = ear_w + 4 * Q
    frieze_w = HD_WIDTH - 2 * ear_w - 8 * Q
    draw_bold_kuba_chevron_border(draw, frieze_x0, 2 * Q, frieze_w, frieze_h)
    draw_bold_kuba_chevron_border(draw, frieze_x0, HD_HEIGHT - 13 * Q, frieze_w, frieze_h)
    
    # ---------------------------------------------------------------------
    # Header Area (y = 13 to 52 in 1x / 65 to 260 in HD)
    # ---------------------------------------------------------------------
    header_x0 = ear_w + 4 * Q
    header_y0 = 13 * Q
    header_w = HD_WIDTH - 2 * ear_w - 8 * Q
    header_h = 40 * Q
    
    draw.rectangle([header_x0, header_y0, header_x0 + header_w, header_y0 + header_h],
                   fill=(22, 24, 27), outline=(45, 48, 52), width=2)
    draw.line([(header_x0, header_y0 + header_h), (header_x0 + header_w, header_y0 + header_h)], fill=gold, width=2)
    
    # Brand Plate: Left section of header (x: 28 to 223 in 1x)
    bp_x = 28 * Q
    bp_y = header_y0 + 3 * Q
    bp_w = 195 * Q
    bp_h = header_h - 6 * Q
    
    draw.rectangle([bp_x, bp_y, bp_x + bp_w, bp_y + bp_h], fill=(32, 20, 14), outline=gold, width=2)
    draw.rectangle([bp_x + 2 * Q, bp_y + 2 * Q, bp_x + bp_w - 2 * Q, bp_y + bp_h - 2 * Q], outline=terracotta, width=1)
    
    draw_carved_african_mask_crest(draw, bp_x + 18 * Q, bp_y + bp_h // 2, 13 * Q, gold=gold, terracotta=terracotta)
    
    font_logo = get_font(FONT_DIN_COND, 26)
    font_sub = get_font(FONT_DIN_ALT, 7.5)
    
    draw.text((bp_x + 38 * Q + 2, bp_y + 11 * Q + 2), "MAREMBA", fill=(10, 8, 6), font=font_logo, anchor="lm")
    draw.text((bp_x + 38 * Q, bp_y + 11 * Q), "MAREMBA", fill=gold, font=font_logo, anchor="lm")
    draw.text((bp_x + 38 * Q, bp_y + 24 * Q), "PROTOCODUS ACOUSTICS  |  MODAL SYNTHESIS", fill=white_ink, font=font_sub, anchor="lm")
    
    # Patch Name LCD Frame at transform = { 235, 14 }, size = { 190, 22 }
    px = FRONT_HEADER["S_patch_name"][0] * Q
    py = FRONT_HEADER["S_patch_name"][1] * Q
    pw = 190 * Q
    ph = 22 * Q
    draw.rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], fill=(12, 10, 8), outline=gold, width=2)
    draw.rectangle([px, py, px + pw, py + ph], fill=(8, 9, 10))
    for cx, cy in [(px - 2, py - 2), (px + pw + 2, py - 2), (px - 2, py + ph + 2), (px + pw + 2, py + ph + 2)]:
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=gold)
        
    # Note On Lamp Ring at { 595, 20 }
    lamp_x, lamp_y = FRONT_HEADER["S_note_on"]
    lx = lamp_x * Q + 25
    ly = lamp_y * Q + 25
    draw.ellipse([lx - 24, ly - 24, lx + 24, ly + 24], fill=(36, 28, 18), outline=gold, width=2)
    caption(draw, "front", ((lamp_x + 14) * Q, ly), "NOTE", FONT_DIN_ALT, 9, dim_ink, "lm")
    
    # Right decorative Adinkra medallion at { 665, 25 }
    draw_carved_african_mask_crest(draw, 665 * Q, 25 * Q, 13 * Q, gold=gold, terracotta=terracotta)
    
    # ---------------------------------------------------------------------
    # 3 Main Synthesis & Capture Control Sections
    # ---------------------------------------------------------------------
    def draw_section(x_u, y_u, w_u, h_u, title_text, accent_color=gold):
        x = x_u * Q
        y = y_u * Q
        w = w_u * Q
        h = h_u * Q
        draw_recessed_control_bay(draw, x, y, w, h, gold_rim=accent_color, shadow=shadow)
        
        header_banner_h = 22 * Q
        draw.rectangle([x, y, x + w, y + header_banner_h], fill=(28, 30, 34), outline=(48, 52, 56), width=1)
        draw.line([(x + 2, y + 1), (x + w - 2, y + 1)], fill=accent_color, width=2)
        
        font_sec = get_font(FONT_DIN_COND, 14)
        draw.text((x + w // 2 + 1, y + 11 * Q + 1), title_text, fill=(10, 10, 10), font=font_sec, anchor="mm")
        draw.text((x + w // 2, y + 11 * Q), title_text, fill=accent_color, font=font_sec, anchor="mm")
        
        bs = 18 * Q
        draw_carved_corner_bracket(draw, x + 2 * Q, y + 2 * Q, bs, 1, 1, accent_color, shadow)
        draw_carved_corner_bracket(draw, x + w - 2 * Q, y + 2 * Q, bs, -1, 1, accent_color, shadow)
        draw_carved_corner_bracket(draw, x + 2 * Q, y + h - 2 * Q, bs, 1, -1, accent_color, shadow)
        draw_carved_corner_bracket(draw, x + w - 2 * Q, y + h - 2 * Q, bs, -1, -1, accent_color, shadow)

    draw_section(24, 56, 248, 346, "ACOUSTIC MODEL & SYMPATHETIC MASS", gold)
    draw_section(278, 56, 224, 346, "EXCITER & RESONATOR CORE", (245, 175, 55))
    draw_section(508, 56, 222, 346, "STUDIO CAPTURE & MASTER DYNAMICS", (95, 205, 235))

    def knob_centre(node):
        kx, ky, _ = FRONT_KNOBS[node]
        return (kx + KNOB_SIZE // 2) * Q, (ky + KNOB_SIZE // 2) * Q

    def knob_row(nodes_and_names, radius, active_color, caption_color, num_ticks=11, dim_color=(140, 135, 125)):
        for node, name in nodes_and_names:
            cx, cy = knob_centre(node)
            draw_dial_ticks(draw, cx, cy, radius=radius, num_ticks=num_ticks,
                            active_color=active_color, dim_color=dim_color)
            knob_caption(node, name, caption_color)

    def knob_caption(node, name, color):
        cx, _ = knob_centre(node)
        ky = FRONT_KNOBS[node][1]
        caption(draw, "front", (cx, (ky + 56) * Q), name, FONT_DIN_ALT, 10.5, color)

    def group_plate(x0_u, x1_u, y_u, title, color):
        """Engraved group title over a run of knobs (replaces the old static meters)."""
        draw.rectangle([x0_u * Q, y_u * Q, x1_u * Q, (y_u + 14) * Q], fill=(16, 17, 19), outline=color, width=1)
        caption(draw, "front", ((x0_u + x1_u) / 2 * Q, (y_u + 8.4) * Q), title, FONT_DIN_COND, 10.5, color)
    
    # ---------------------------------------------------------------------
    # SECTION 1 CONTROLS
    # ---------------------------------------------------------------------
    art_x, art_y = FRONT_HEADER["S_model_art"]
    art_x *= Q
    art_y *= Q
    art_w = 240 * Q
    art_h = 96 * Q
    draw.rectangle([art_x - 4, art_y - 4, art_x + art_w + 4, art_y + art_h + 4], fill=(30, 20, 14), outline=gold, width=2)
    draw.rectangle([art_x - 1, art_y - 1, art_x + art_w + 1, art_y + art_h + 1], outline=(15, 16, 17), width=2)
    for bx, by in [(art_x - 2, art_y - 2), (art_x + art_w + 2, art_y - 2),
                   (art_x - 2, art_y + art_h + 2), (art_x + art_w + 2, art_y + art_h + 2)]:
        draw.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=gold)
        
    # Model radio bays: a recess exactly around each 20x20 toggle, its label to
    # the right, clear of the next toggle. The toggle's own lit frame shows the
    # selection, so no LED is painted.
    model_fills = [(48, 22, 16), (54, 24, 14), (26, 36, 20), (52, 36, 16)]
    for (node, rx, label), btn_fill in zip(MODEL_RADIOS, model_fills):
        rpx = rx * Q
        rpy = MODEL_RADIO_Y * Q
        draw.rounded_rectangle([rpx - 2 * Q, rpy - 2 * Q, rpx + 22 * Q, rpy + 22 * Q],
                               radius=2 * Q, fill=btn_fill, outline=(55, 58, 62), width=1)
        caption(draw, "front", (rpx + 24 * Q, rpy + 11.3 * Q), label, FONT_DIN_COND, 9.5, white_ink, "lm")
        
    draw_recessed_control_bay(draw, 28 * Q, 220 * Q, 240 * Q, 164 * Q, gold_rim=(185, 145, 50), shadow=shadow)
    
    knob_row([("S_knob_sympathetic", "SYMPATHETIC"), ("S_knob_bodyBloom", "BODY BLOOM"),
              ("S_knob_pitchGlide", "PITCH GLIDE")], 132, gold, gold)
    knob_row([("S_knob_buzz", "MIRLITON BUZZ"), ("S_knob_artifacts", "ARTIFACTS")],
             132, white_ink, white_ink)
        
    pl_x = 30 * Q
    pl_y = 388 * Q
    pl_w = 236 * Q
    pl_h = 11 * Q
    draw.rectangle([pl_x, pl_y, pl_x + pl_w, pl_y + pl_h], fill=(28, 20, 14), outline=gold, width=1)
    draw.text((pl_x + pl_w // 2, pl_y + pl_h // 2), "PROTOCODUS ACOUSTICS - 8 MODES PER BAR & SYMPATHETIC COUPLING",
              fill=gold, font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")

    # ---------------------------------------------------------------------
    # SECTION 2 CONTROLS (EXCITER & RESONATOR CORE)
    # ---------------------------------------------------------------------
    draw_step_legend(draw, "S_knob_malletType", STEP_LEGENDS["S_knob_malletType"], gold, radius=126)
    knob_caption("S_knob_malletType", "MALLET", gold)
    knob_row([("S_knob_malletHardness", "HARDNESS"), ("S_knob_strikePosition", "POSITION"),
              ("S_knob_strikeJitter", "VARIANCE")], 126, gold, white_ink)

    draw_acoustic_bar_schematic(draw, 284, 158, 212, 26)

    knob_row([("S_knob_resonatorTune", "RESONATOR"), ("S_knob_resonatorCoupling", "COUPLING"),
              ("S_knob_decay", "DECAY")], 132, gold, white_ink)

    # Mallet position legend (names match the Striker / Mallet Type texts)
    draw.rectangle([284 * Q, 267 * Q, 496 * Q, 283 * Q], fill=(16, 17, 19), outline=gold, width=1)
    caption(draw, "front", (390 * Q, 276.2 * Q), "1 SOFT YARN  |  2 MEDIUM CORD  |  3 HARD RUBBER  |  4 WOOD BATON",
            FONT_DIN_COND, 9, (205, 210, 215))

    for node, name in [("S_knob_polyphony", "POLYPHONY"), ("S_knob_oversampling", "OVERSAMPLE"),
                       ("S_knob_velocityCurve", "VELOCITY")]:
        draw_step_legend(draw, node, STEP_LEGENDS[node], white_ink)
        knob_caption(node, name, white_ink)
        
    draw.text((390 * Q, 390 * Q), "QUARTER-WAVE RESONATOR COUPLING - ASYMMETRIC HERTZIAN CONTACT",
              fill=(145, 140, 135), font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")

    # ---------------------------------------------------------------------
    # SECTION 3 CONTROLS (STUDIO CAPTURE & MASTER DYNAMICS)
    # ---------------------------------------------------------------------
    blue = (95, 205, 235)
    amber = (245, 165, 55)
    knob_row([("S_knob_closeLevel", "CLOSE"), ("S_knob_farLevel", "ROOM"),
              ("S_knob_piezoLevel", "PIEZO"), ("S_knob_stereoWidth", "WIDTH")],
             125, blue, (195, 230, 245))

    # Group titles where the static GR / VU meters used to be: the preamp drive,
    # the compressor (amount, attack, release), then tone and the master controls.
    group_plate(517, 565, 162, "PREAMP", amber)
    group_plate(569, 721, 162, "COMPRESSOR", amber)
    knob_row([("S_knob_preampDrive", "DRIVE"), ("S_knob_compAmount", "COMPRESS"),
              ("S_knob_compAttack", "ATTACK"), ("S_knob_compRelease", "RELEASE")],
             125, amber, (250, 220, 185))

    group_plate(517, 565, 268, "TONE", gold)
    group_plate(569, 721, 268, "MASTER", gold)
    knob_row([("S_knob_warmth", "WARMTH"), ("S_knob_detune", "DETUNE"),
              ("S_knob_masterTune", "TUNE"), ("S_knob_volume", "VOLUME")],
             125, gold, gold, dim_color=(135, 130, 125))
    
    draw.text((618 * Q, 390 * Q), "FLOATING-POINT ENGINE - 2x / 4x / 8x OVERSAMPLING",
              fill=(145, 140, 135), font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")
    
    save_panel(panel, "Reason_GUI_front_root_Panel.png")
    print("Rendered Reason_GUI_front_root_Panel.png (3770x2070, GUI2D and HD) successfully!")

# -------------------------------------------------------------------------
# Back Panel Main Renderer
# -------------------------------------------------------------------------

def render_back_panel():
    panel = create_rear_stone_steel_texture(HD_WIDTH, HD_HEIGHT, seed=303)
    
    ear_w = 24 * Q
    wenge_l = create_african_wood_texture(ear_w, HD_HEIGHT, seed=42, tone="wenge")
    wenge_r = create_african_wood_texture(ear_w, HD_HEIGHT, seed=84, tone="wenge")
    panel.paste(wenge_l, (0, 0))
    panel.paste(wenge_r, (HD_WIDTH - ear_w, 0))
    
    draw = ImageDraw.Draw(panel)
    gold = (235, 195, 75)
    shadow = (18, 12, 8)
    terracotta = (148, 65, 32)
    white = (245, 245, 245)
    
    screw_ys = [18 * Q, 90 * Q, 162 * Q, 252 * Q, 324 * Q, 396 * Q]
    for sy in screw_ys:
        draw_brass_wood_screw(draw, ear_w // 2, sy, 8 * Q, angle_deg=45)
        draw_brass_wood_screw(draw, HD_WIDTH - ear_w // 2, sy, 8 * Q, angle_deg=75)
        
    draw_vertical_kuba_ear_carving(draw, 5 * Q, 25 * Q, 14 * Q, HD_HEIGHT - 50 * Q, point_right=True)
    draw_vertical_kuba_ear_carving(draw, HD_WIDTH - ear_w + 5 * Q, 25 * Q, 14 * Q, HD_HEIGHT - 50 * Q, point_right=False)
    
    frieze_h = 11 * Q
    frieze_x0 = ear_w + 4 * Q
    frieze_w = HD_WIDTH - 2 * ear_w - 8 * Q
    draw_bold_kuba_chevron_border(draw, frieze_x0, 2 * Q, frieze_w, frieze_h)
    draw_bold_kuba_chevron_border(draw, frieze_x0, HD_HEIGHT - 13 * Q, frieze_w, frieze_h)
    
    draw_brass_wood_screw(draw, ear_w + 20 * Q, 32 * Q, 10 * Q, angle_deg=60)
    draw.text((ear_w + 35 * Q, 32 * Q), "CHASSIS GROUND", fill=(140, 145, 150), font=get_font(FONT_DIN_ALT, 8.5), anchor="lm")
    
    draw.text((HD_WIDTH // 2, 32 * Q), "PROTOCODUS - MAREMBA PHYSICAL MODELING REAR INTERFACE",
              fill=gold, font=get_font(FONT_DIN_COND, 22), anchor="mm")
    
    draw_recessed_control_bay(draw, 28 * Q, 60 * Q, 402 * Q, 335 * Q, gold_rim=gold, shadow=shadow)
    draw.rectangle([28 * Q, 60 * Q, 430 * Q, 88 * Q], fill=(28, 31, 34), outline=(48, 52, 56), width=1)
    draw.text((229 * Q, 74 * Q), "MULTI-CHANNEL AUDIO OUTPUTS", fill=gold, font=get_font(FONT_DIN_COND, 14), anchor="mm")
    
    draw_recessed_control_bay(draw, 438 * Q, 60 * Q, 288 * Q, 335 * Q, gold_rim=gold, shadow=shadow)
    draw.rectangle([438 * Q, 60 * Q, 726 * Q, 88 * Q], fill=(28, 31, 34), outline=(48, 52, 56), width=1)
    draw.text((582 * Q, 74 * Q), "CONTROL VOLTAGE (CV) MODULATION INPUTS", fill=gold, font=get_font(FONT_DIN_COND, 14), anchor="mm")
    
    for _, sx, sy, name, desc in REAR_AUDIO:
        cx = sx * Q + 48
        cy = sy * Q + 52
        draw_socket_collar(draw, cx, cy, is_audio=True)
        caption(draw, "back", (cx, (sy + 28) * Q), name, FONT_DIN_ALT, 11, white)
        caption(draw, "back", (cx, (sy + 37.5) * Q), desc, FONT_DIN_ALT, 9, (145, 150, 155))
        
    # Group caption, rule and stock routing symbol above each output group
    for _, _, ix, iy, title, half in REAR_ROUTING:
        cx = (ix + ROUTING_ICON_SIZE[0] / 2) * Q
        color = gold if title == "STEREO MIX" else (160, 165, 170)
        draw.line([(cx - half * Q, (iy - 7) * Q), (cx + half * Q, (iy - 7) * Q)], fill=color, width=2)
        caption(draw, "back", (cx, (iy - 15) * Q), title, FONT_DIN_ALT, 9, color)
    
    for _, sx, sy, name, desc in REAR_CV:
        cx = sx * Q + 38
        cy = sy * Q + 42
        draw_socket_collar(draw, cx, cy, is_audio=False)
        caption(draw, "back", (cx, (sy + 26) * Q), name, FONT_DIN_ALT, 10.5, (240, 220, 140))
        caption(draw, "back", (cx, (sy + 35.5) * Q), desc, FONT_DIN_ALT, 9, (145, 150, 155))
        
    # Plain recess for Reason's placeholder (300x100 HD px): nothing is painted
    # under the placeholder itself.
    _, ph_x, ph_y = REAR_PLACEHOLDER
    draw_recessed_control_bay(draw, (ph_x - 2) * Q, (ph_y - 2) * Q, 64 * Q, 24 * Q, gold_rim=gold, shadow=shadow)
    draw.rectangle([19 * Q, 149 * Q, 34 * Q, 231 * Q], fill=(14, 15, 17), outline=(42, 46, 50), width=1)

    # Maker badge: identity only, inside the CV bay (no origin or compliance claims)
    draw.rectangle([452 * Q, 315 * Q, 708 * Q, 375 * Q], fill=(12, 13, 14), outline=gold, width=1)
    draw_carved_african_mask_crest(draw, 474 * Q, 345 * Q, 15 * Q, gold=gold, terracotta=terracotta)
    caption(draw, "back", (500 * Q, 337 * Q), "MAREMBA  |  PHYSICAL MODELING SYNTHESIZER", FONT_DIN_ALT, 9,
            (230, 230, 235), "lm")
    caption(draw, "back", (500 * Q, 353 * Q), "PROTOCODUS  |  cz.protocodus.Maremba", FONT_DIN_ALT, 9,
            (160, 165, 170), "lm")
    
    save_panel(panel, "Reason_GUI_back_root_Panel.png")
    print("Rendered Reason_GUI_back_root_Panel.png (3770x2070, GUI2D and HD) successfully!")

# -------------------------------------------------------------------------
# Folded Panels (3770x150, GUI2D and HD)
# -------------------------------------------------------------------------

def render_folded_panels():
    gold = (235, 195, 75)
    
    panel_f = create_stone_slate_texture(HD_WIDTH, HD_FOLDED_H, seed=101)
    ear_w = 24 * Q
    wenge_l = create_african_wood_texture(ear_w, HD_FOLDED_H, seed=42, tone="wenge")
    wenge_r = create_african_wood_texture(ear_w, HD_FOLDED_H, seed=84, tone="wenge")
    panel_f.paste(wenge_l, (0, 0))
    panel_f.paste(wenge_r, (HD_WIDTH - ear_w, 0))
    
    draw_f = ImageDraw.Draw(panel_f)
    draw_f.rectangle([0, 0, HD_WIDTH - 1, HD_FOLDED_H - 1], outline=(55, 60, 65), width=2)
    draw_brass_wood_screw(draw_f, ear_w // 2, HD_FOLDED_H // 2, 7 * Q, angle_deg=30)
    draw_brass_wood_screw(draw_f, HD_WIDTH - ear_w // 2, HD_FOLDED_H // 2, 7 * Q, angle_deg=65)
    
    draw_bold_kuba_chevron_border(draw_f, ear_w + 6 * Q, 1 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 6 * Q)
    draw_bold_kuba_chevron_border(draw_f, ear_w + 6 * Q, HD_FOLDED_H - 7 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 6 * Q)
    
    draw_carved_african_mask_crest(draw_f, ear_w + 14 * Q, HD_FOLDED_H // 2, 9 * Q, gold=gold, terracotta=(148, 65, 32))
    draw_f.text((ear_w + 28 * Q, HD_FOLDED_H // 2), "PROTOCODUS - MAREMBA", fill=gold, font=get_font(FONT_DIN_COND, 16), anchor="lm")
    
    px = FOLDED_FRONT["S_patch_name"][0] * Q
    py = FOLDED_FRONT["S_patch_name"][1] * Q
    pw = 190 * Q
    ph = 18 * Q
    draw_f.rectangle([px - 2, py - 2, px + pw + 2, py + ph + 2], fill=(10, 11, 12), outline=gold, width=2)
    draw_f.rectangle([px, py, px + pw, py + ph], fill=(6, 7, 8))

    # Plain plate behind the patch browse group (58x22 logical), over the friezes
    bx = FOLDED_FRONT["S_patch_browse_group"][0] * Q
    by = FOLDED_FRONT["S_patch_browse_group"][1] * Q
    draw_f.rectangle([bx - 3, by - 3, bx + 58 * Q + 3, by + 22 * Q + 3], fill=(10, 11, 12), outline=(45, 50, 55), width=1)
    
    lamp_x, lamp_y = FOLDED_FRONT["S_note_on"]
    draw_f.ellipse([lamp_x * Q + 10, lamp_y * Q + 10, lamp_x * Q + 40, lamp_y * Q + 40], outline=gold, width=2)
    
    save_panel(panel_f, "Reason_GUI_folded_front_root_Panel.png")
    
    panel_b = create_rear_stone_steel_texture(HD_WIDTH, HD_FOLDED_H, seed=303)
    panel_b.paste(wenge_l, (0, 0))
    panel_b.paste(wenge_r, (HD_WIDTH - ear_w, 0))
    draw_b = ImageDraw.Draw(panel_b)
    draw_b.rectangle([0, 0, HD_WIDTH - 1, HD_FOLDED_H - 1], outline=(55, 60, 65), width=2)
    draw_brass_wood_screw(draw_b, ear_w // 2, HD_FOLDED_H // 2, 7 * Q, angle_deg=30)
    draw_brass_wood_screw(draw_b, HD_WIDTH - ear_w // 2, HD_FOLDED_H // 2, 7 * Q, angle_deg=65)
    
    draw_bold_kuba_chevron_border(draw_b, ear_w + 6 * Q, 1 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 6 * Q)
    draw_bold_kuba_chevron_border(draw_b, ear_w + 6 * Q, HD_FOLDED_H - 7 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 6 * Q)
    draw_carved_african_mask_crest(draw_b, ear_w + 14 * Q, HD_FOLDED_H // 2, 9 * Q, gold=gold, terracotta=(148, 65, 32))
    draw_b.text((ear_w + 28 * Q, HD_FOLDED_H // 2), "PROTOCODUS - MAREMBA PHYSICAL MODELING",
                fill=gold, font=get_font(FONT_DIN_COND, 16), anchor="lm")
    
    ox, oy = FOLDED_BACK["S_cable_origin"]
    draw_b.ellipse([ox * Q - 7, oy * Q - 7, ox * Q + 7, oy * Q + 7], fill=(14, 16, 18), outline=gold, width=2)
    tx, ty = FOLDED_BACK["S_device_name"]
    draw_b.rectangle([tx * Q - 2, ty * Q - 2, tx * Q + 400 + 2, ty * Q + 65 + 2], fill=(14, 15, 17), outline=(45, 50, 55), width=1)
    
    save_panel(panel_b, "Reason_GUI_folded_back_root_Panel.png")
    print("Rendered folded panels (3770x150, GUI2D and HD) successfully!")

# -------------------------------------------------------------------------
# Compositing & Previews
# -------------------------------------------------------------------------

def save_panel(image, name):
    """GUI2D and GUI/Output/HD carry the same 5x panel (RE2D renders from GUI2D)."""
    image.save(HD / name)
    image.save(GUI2D / name)


def copy_frame(strip, total_frames, frame_idx):
    w, h = strip.size
    frame_h = h // total_frames
    return strip.crop((0, frame_idx * frame_h, w, (frame_idx + 1) * frame_h))


def asset(name):
    """A shipped GUI2D image, so the previews show exactly what Reason renders."""
    return Image.open(GUI2D / f"{name}.png").convert("RGBA")


def preview_values():
    """Custom property values of the default patch (falls back to mid-scale)."""
    values = {}
    if DEFAULT_PATCH.is_file():
        text = DEFAULT_PATCH.read_text(encoding="utf-8")
        for name, value in re.findall(r'<Value property="(\w+)" type="number">([-0-9.eE+]+)</Value>', text):
            values[name] = float(value)
    return values


def knob_frame(node, values):
    """The Knob.png frame Reason shows for this knob's value in the default patch."""
    prop = FRONT_KNOBS[node][2]
    value = values.get(prop, 0.5)
    if node in STEP_LEGENDS:
        steps = len(STEP_LEGENDS[node])
        index = min(max(int(round(value)), 0), steps - 1)
        return int(round(index * 62 / (steps - 1)))
    return int(round(min(max(value, 0.0), 1.0) * 62))


def composite_front(panel=None):
    if panel is None:
        panel = Image.open(GUI2D / "Reason_GUI_front_root_Panel.png")
    image = panel.convert("RGBA")
    values = preview_values()
    model = min(max(int(round(values.get("model", 0))), 0), 3)
    
    # 1. Model Art Display (frame = selected model)
    image.alpha_composite(copy_frame(asset("ModelArt"), 4, model),
                          tuple(v * Q for v in FRONT_HEADER["S_model_art"]))
    
    # 2. Model Selection Toggles (lit frame on the selected model)
    toggle = asset("Toggle")
    for index, (_, rx, _) in enumerate(MODEL_RADIOS):
        image.alpha_composite(copy_frame(toggle, 2, 1 if index == model else 0), (rx * Q, MODEL_RADIO_Y * Q))
    
    # 3. Patch Browse Group
    image.alpha_composite(asset("PatchBrowseGroup"), tuple(v * Q for v in FRONT_HEADER["S_patch_browse_group"]))
    
    # 4. Device Name Tape
    tape_x, tape_y = FRONT_HEADER["S_device_name"]
    image.alpha_composite(asset("TapeHorz"), (tape_x * Q, tape_y * Q))
    draw = ImageDraw.Draw(image)
    font_tape = get_font(FONT_DIN_ALT, 8.5)
    draw.text((tape_x * Q + 200, tape_y * Q + 32), "Maremba", fill=(32, 34, 38), font=font_tape, anchor="mm")
    
    # 5. Note On Lamp
    image.alpha_composite(copy_frame(asset("Lamp"), 2, 0), tuple(v * Q for v in FRONT_HEADER["S_note_on"]))
    
    # 6. Patch Display Text
    font_patch = get_font(FONT_ARIAL, 11)
    patch_x, patch_y = FRONT_HEADER["S_patch_name"]
    draw.text((patch_x * Q + 475, patch_y * Q + 55), PREVIEW_PATCH_NAME, fill=(245, 235, 215), font=font_patch, anchor="mm")
    
    # 7. Knobs at the default patch's values
    knob = asset("Knob")
    for node, (kx, ky, _) in FRONT_KNOBS.items():
        image.alpha_composite(copy_frame(knob, 63, knob_frame(node, values)), (kx * Q, ky * Q))
        
    return image


def composite_back(panel=None):
    if panel is None:
        panel = Image.open(GUI2D / "Reason_GUI_back_root_Panel.png")
    image = panel.convert("RGBA")
    
    # Reason draws its own placeholder; the stock stand-in shows its footprint.
    _, ph_x, ph_y = REAR_PLACEHOLDER
    image.alpha_composite(asset("Placeholder"), (ph_x * Q, ph_y * Q))
    
    _, tape_x, tape_y = REAR_TAPE
    image.alpha_composite(asset("TapeVert"), (tape_x * Q, tape_y * Q))
    tape_txt = Image.new("RGBA", (400, 65), (0, 0, 0, 0))
    d_tv = ImageDraw.Draw(tape_txt)
    d_tv.text((200, 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    tape_rot = tape_txt.transpose(Image.Transpose.ROTATE_270)
    image.alpha_composite(tape_rot, (tape_x * Q, tape_y * Q))
    
    audio_jack = asset("AudioJack")
    for _, sx, sy, _, _ in REAR_AUDIO:
        image.alpha_composite(copy_frame(audio_jack, 3, 0), (sx * Q, sy * Q))
        
    cv_jack = asset("CVJack")
    for _, sx, sy, _, _ in REAR_CV:
        image.alpha_composite(copy_frame(cv_jack, 3, 0), (sx * Q, sy * Q))

    for _, path, ix, iy, _, _ in REAR_ROUTING:
        image.alpha_composite(asset(path), (ix * Q, iy * Q))
        
    return image


def composite_folded_front(panel=None):
    if panel is None:
        panel = Image.open(GUI2D / "Reason_GUI_folded_front_root_Panel.png")
    image = panel.convert("RGBA")
    draw = ImageDraw.Draw(image)
    
    patch_x, patch_y = FOLDED_FRONT["S_patch_name"]
    draw.text((patch_x * Q + 475, patch_y * Q + 45), PREVIEW_PATCH_NAME, fill=(245, 235, 215),
              font=get_font(FONT_ARIAL, 9.5), anchor="mm")
    
    image.alpha_composite(asset("PatchBrowseGroup"), tuple(v * Q for v in FOLDED_FRONT["S_patch_browse_group"]))

    tape_x, tape_y = FOLDED_FRONT["S_device_name"]
    image.alpha_composite(asset("TapeHorz"), (tape_x * Q, tape_y * Q))
    draw.text((tape_x * Q + 200, tape_y * Q + 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    
    image.alpha_composite(copy_frame(asset("Lamp"), 2, 0), tuple(v * Q for v in FOLDED_FRONT["S_note_on"]))
    return image


def composite_folded_back(panel=None):
    if panel is None:
        panel = Image.open(GUI2D / "Reason_GUI_folded_back_root_Panel.png")
    image = panel.convert("RGBA")
    tape_x, tape_y = FOLDED_BACK["S_device_name"]
    image.alpha_composite(asset("TapeHorz"), (tape_x * Q, tape_y * Q))
    draw = ImageDraw.Draw(image)
    draw.text((tape_x * Q + 200, tape_y * Q + 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    return image


def contained(image, size):
    """Aspect-preserving fit into a fixed preview canvas (transparent margins)."""
    width, height = size
    scale = min(width / image.width, height / image.height)
    fitted_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    fitted = image.convert("RGBA").resize(fitted_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(fitted, ((width - fitted_size[0]) // 2, (height - fitted_size[1]) // 2))
    return canvas


def generate_docs_previews(preview_front=None, preview_back=None):
    docs_dir = PROJECT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    if preview_front is None:
        preview_front = composite_front()
    if preview_back is None:
        preview_back = composite_back()
        
    preview_front.save(docs_dir / "front_hd.png")
    preview_back.save(docs_dir / "rear_hd.png")
    
    front_2x = preview_front.resize((WIDTH * 2, HEIGHT * 2), Image.Resampling.LANCZOS)
    rear_2x = preview_back.resize((WIDTH * 2, HEIGHT * 2), Image.Resampling.LANCZOS)
    front_2x.save(docs_dir / "front.png")
    rear_2x.save(docs_dir / "rear.png")
    
    front_1x = preview_front.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    rear_1x = preview_back.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    front_1x.save(docs_dir / "front_preview.png")
    rear_1x.save(docs_dir / "rear_preview.png")
    
    print("Generated all docs previews successfully!")


def render_device_icons(preview_front=None, preview_back=None, preview_ff=None, preview_fb=None):
    """Reason's local-build Device* images (GUI/Output/HD only) and the GUI2D Reason_* previews."""
    base_icon = create_stone_slate_texture(512, 384, seed=505)
    draw = ImageDraw.Draw(base_icon)
    gold = (235, 195, 75)
    shadow = (18, 12, 8)
    terracotta = (148, 65, 32)
    
    draw.rectangle([4, 4, 507, 379], outline=gold, width=3)
    draw.rectangle([8, 8, 503, 375], outline=(55, 45, 35), width=2)
    
    draw_bold_kuba_chevron_border(draw, 12, 10, 488, 16)
    draw_bold_kuba_chevron_border(draw, 12, 357, 488, 16)
    
    draw_carved_african_mask_crest(draw, 256, 70, 28, gold=gold, terracotta=terracotta)
    draw.text((256, 114), "PROTOCODUS ACOUSTICS", fill=gold, font=get_font(FONT_DIN_COND, 12), anchor="mm")
    
    bar_count = 7
    bar_w = 38
    spacing = 54
    start_x = 76
    cy = 210
    
    for i in range(bar_count):
        bx = start_x + i * spacing
        pipe_h = int(120 * (1.0 - 0.42 * (i / float(bar_count))))
        py0 = cy + 15
        py1 = py0 + pipe_h
        draw.rectangle([bx + 7, py0, bx + bar_w - 7, py1], fill=(185, 145, 45), outline=(100, 75, 20), width=2)
        draw.line([(bx + 11, py0 + 2), (bx + 11, py1 - 2)], fill=(245, 215, 115), width=2)
        draw.arc([bx + 7, py1 - 8, bx + bar_w - 7, py1 + 8], 0, 180, fill=(100, 75, 20), width=2)
        
    for i in range(bar_count):
        bx = start_x + i * spacing
        bar_len = int(136 * (1.0 - 0.36 * (i / float(bar_count))))
        top_y = cy - bar_len // 2
        bot_y = cy + bar_len // 2
        
        draw.rectangle([bx + 4, top_y + 4, bx + bar_w + 4, bot_y + 4], fill=(10, 8, 6))
        is_padauk = (i % 2 == 1)
        bar_fill = (165, 52, 22) if is_padauk else (88, 32, 20)
        bar_hi = (205, 75, 34) if is_padauk else (125, 48, 28)
        
        draw.rectangle([bx, top_y, bx + bar_w, bot_y], fill=bar_fill, outline=(55, 18, 10), width=2)
        draw.rectangle([bx + 2, top_y + 3, bx + bar_w - 2, bot_y - 3], fill=bar_hi)
        
        arch_cy = bot_y - 3
        draw.arc([bx + 4, arch_cy - 12, bx + bar_w - 4, arch_cy + 12], 180, 360, fill=(35, 10, 6), width=2)
        
        node1 = top_y + int(bar_len * 0.224)
        node2 = bot_y - int(bar_len * 0.224)
        for ny in [node1, node2]:
            draw.ellipse([bx + bar_w // 2 - 3, ny - 3, bx + bar_w // 2 + 3, ny + 3], fill=gold, outline=(30, 15, 8), width=1)
            
    draw.line([(start_x, cy - 36), (start_x + (bar_count - 1) * spacing + bar_w, cy - 20)], fill=(245, 225, 140), width=1)
    draw.line([(start_x, cy + 36), (start_x + (bar_count - 1) * spacing + bar_w, cy + 20)], fill=(245, 225, 140), width=1)
    
    pl_y0 = 300
    pl_y1 = 345
    draw.rectangle([40, pl_y0, 472, pl_y1], fill=(22, 16, 12), outline=gold, width=2)
    draw.text((256, pl_y0 + 15), "MAREMBA", fill=gold, font=get_font(FONT_DIN_COND, 22), anchor="mm")
    draw.text((256, pl_y0 + 32), "ACOUSTIC MODAL SYNTHESIZER", fill=(225, 225, 230), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    
    atlas = Image.new("RGBA", (779, 518), (0, 0, 0, 0))
    slots = [
        (185, 4, 16, 16),
        (141, 7, 24, 18),
        (88, 7, 32, 26),
        (3, 8, 48, 40),
        (3, 64, 64, 50),
        (3, 141, 128, 98),
        (264, 67, 512, 384),
        (3, 290, 256, 194),
    ]
    for sx, sy, sw, sh in slots:
        cell = base_icon.resize((sw, sh), Image.Resampling.LANCZOS)
        atlas.paste(cell, (sx, sy))
    atlas.save(HD / "DeviceIcon.png")
    
    if preview_front is None:
        preview_front = composite_front()
    if preview_back is None:
        preview_back = composite_back()
    if preview_ff is None:
        preview_ff = composite_folded_front()
    if preview_fb is None:
        preview_fb = composite_folded_back()

    # The palette image is a snapshot of the device, with no extra text.
    contained(preview_front, (650, 360)).save(HD / "DevicePaletteImage.png")
        
    nav_hd = preview_front.resize((630, 345), Image.Resampling.LANCZOS)
    nav_hd.save(HD / "DeviceNavigator.png")
    nav_f_hd = preview_ff.resize((630, 25), Image.Resampling.LANCZOS)
    nav_f_hd.save(HD / "DeviceNavigatorFolded.png")
    
    track_thumb_hd = preview_front.resize((270, 150), Image.Resampling.LANCZOS)
    track_thumb_hd.save(HD / "DeviceTrackListThumbnail.png")
    
    previews = [
        ("Reason_Icon128x128", 128, 72, 6),
        ("Reason_Navigator", 126, 69, 5),
        ("Reason_Palette", 130, 72, 6),
        ("Reason_TrackListIcon", 54, 30, 3),
    ]
    for prefix, pw, ph, pfh in previews:
        preview_front.resize((pw, ph), Image.Resampling.LANCZOS).save(GUI2D / f"{prefix}_front_root_Panel.png")
        preview_ff.resize((pw, pfh), Image.Resampling.LANCZOS).save(GUI2D / f"{prefix}_front_folded_root_Panel.png")
        preview_back.resize((pw, ph), Image.Resampling.LANCZOS).save(GUI2D / f"{prefix}_back_root_Panel.png")
        preview_fb.resize((pw, pfh), Image.Resampling.LANCZOS).save(GUI2D / f"{prefix}_back_folded_root_Panel.png")
        
    print("Rendered all Reason device icons, thumbnails, and preview assets successfully!")

# -------------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------------

def check_layout(nodes, failures):
    """Every painted position matches its node in GUI2D/device_2D.lua."""
    expected = {
        "front": {**FRONT_HEADER, **{node: (x, y) for node, (x, y, _) in FRONT_KNOBS.items()},
                  **{node: (x, MODEL_RADIO_Y) for node, x, _ in MODEL_RADIOS}},
        "folded_front": dict(FOLDED_FRONT),
        "back": {**{node: (x, y) for node, x, y, _, _ in REAR_AUDIO + REAR_CV},
                 **{node: (x, y) for node, _, x, y, _, _ in REAR_ROUTING},
                 REAR_PLACEHOLDER[0]: REAR_PLACEHOLDER[1:], REAR_TAPE[0]: REAR_TAPE[1:]},
        "folded_back": dict(FOLDED_BACK),
    }
    for panel, positions in expected.items():
        declared = {name for name in nodes[panel] if name != "S_backdrop"}
        for name in sorted(declared - set(positions)):
            failures.append(f"{panel}/{name}: declared in device_2D.lua but not painted/composited here")
        for name, (x, y) in positions.items():
            node = nodes[panel].get(name)
            if node is None:
                failures.append(f"{panel}/{name}: painted here but missing from device_2D.lua")
            elif (node.x, node.y) != (x, y):
                failures.append(f"{panel}/{name}: device_2D.lua has ({node.x:g}, {node.y:g}), art has ({x}, {y})")
    for node, path, *_ in REAR_ROUTING:
        declared = nodes["back"].get(node)
        if declared is not None and declared.path != path:
            failures.append(f"back/{node}: device_2D.lua uses {declared.path}, art expects {path}")


def check_captions(nodes, failures):
    """Functional text is readable, and clear of other text and of opaque widgets."""
    gap = CAPTION_GAP * Q
    for panel, items in CAPTIONS.items():
        height = (HEIGHT if panel in ("front", "back") else FOLDED_HEIGHT) * Q
        blockers = []
        for name, node in nodes[panel].items():
            rect = node.rect()
            if rect is None or name == "S_backdrop":
                continue
            if node.path == "Knob":
                # Only the knob body is opaque; legends sit in the frame's corners.
                cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
                rect = (cx - KNOB_BODY_R, cy - KNOB_BODY_R, cx + KNOB_BODY_R, cy + KNOB_BODY_R)
            blockers.append((name, tuple(v * Q for v in rect)))
        for index, (text, size, box) in enumerate(items):
            if size < MIN_TEXT_SIZE:
                failures.append(f"{panel}: '{text}' is {size} logical px, below the {MIN_TEXT_SIZE} readable minimum")
            if box[0] < 25 or box[2] > WIDTH * Q - 25 or box[1] < 0 or box[3] > height:
                failures.append(f"{panel}: '{text}' leaves the panel or enters its side margin")
            for other_text, _, other in items[index + 1:]:
                if (box[0] < other[2] + gap and other[0] < box[2] + gap and
                        box[1] < other[3] + gap and other[1] < box[3] + gap):
                    failures.append(f"{panel}: '{text}' and '{other_text}' are closer than {CAPTION_GAP} unit")
            for name, rect in blockers:
                if box[0] < rect[2] and rect[0] < box[2] and box[1] < rect[3] and rect[1] < box[3]:
                    failures.append(f"{panel}: '{text}' is covered by {name}")


def check_model_plates(geometry, failures):
    """Each ModelArt frame's plate names its model step as texts.lua does, readably and inside the plate."""
    motherboard = geometry.load_lua(PROJECT / "motherboard_def.lua")
    texts = geometry.load_lua(PROJECT / "Resources" / "English" / "texts.lua")["texts"]
    selector = motherboard["custom_properties"]["args"]["document_owner"]["properties"]["model"]["args"]["ui_type"]
    names = [texts.get(item["args"], item["args"]).upper() for _, item in geometry.entries(selector["args"])]
    if [title for title, _ in MODEL_PLATES] != names:
        failures.append(f"ModelArt plate titles {[title for title, _ in MODEL_PLATES]} are not the model names {names}")
    if sorted({model for model, *_ in PLATE_TEXT}) != list(range(len(MODEL_PLATES))):
        failures.append("ModelArt: not every model frame drew its nameplate")
    gap = CAPTION_GAP * Q
    for index, (model, text, size, box, interior) in enumerate(PLATE_TEXT):
        if size < MIN_TEXT_SIZE:
            failures.append(f"ModelArt {model}: '{text}' is {size} logical px, below the {MIN_TEXT_SIZE} readable minimum")
        if box[0] < interior[0] or box[1] < interior[1] or box[2] > interior[2] or box[3] > interior[3]:
            failures.append(f"ModelArt {model}: '{text}' {box} runs outside its plate {interior}")
        for other_model, other_text, _, other, _ in PLATE_TEXT[index + 1:]:
            if (other_model == model and box[0] < other[2] + gap and other[0] < box[2] + gap and
                    box[1] < other[3] + gap and other[1] < box[3] + gap):
                failures.append(f"ModelArt {model}: '{text}' and '{other_text}' are closer than {CAPTION_GAP} unit")


def validate():
    tests = PROJECT / "Tests"
    sys.path.insert(0, str(tests))
    try:
        import validate_panel_geometry as geometry
    finally:
        sys.path.remove(str(tests))
    failures = []
    nodes = geometry.load_device()
    check_layout(nodes, failures)
    check_captions(nodes, failures)
    check_model_plates(geometry, failures)
    for failure in failures:
        print(f"FAIL: {failure}")
    if geometry.main() != 0 or failures:
        raise SystemExit("panel validation failed")
    print(f"Validated painted layout and {sum(len(v) for v in CAPTIONS.values())} captions against device_2D.lua, "
          f"and {len(PLATE_TEXT)} model nameplate lines")

# -------------------------------------------------------------------------
# Main Execution Entry Point
# -------------------------------------------------------------------------

# Files older versions of this script wrote into GUI2D, which the u45 must not carry.
STALE_GUI2D_FILES = ("DeviceIcon.png", "DevicePaletteImage.png", "DeviceNavigator.png",
                     "DeviceNavigatorFolded.png", "DeviceTrackListThumbnail.png", "PatchName.png")

if __name__ == "__main__":
    os.makedirs(HD, exist_ok=True)
    os.makedirs(GUI2D, exist_ok=True)
    for stale in STALE_GUI2D_FILES:
        (GUI2D / stale).unlink(missing_ok=True)
    
    print(">>> Rendering Maremba Traditional African Art, Wood, Stone & Clay GUI <<<")
    render_model_art()
    render_front_panel()
    render_back_panel()
    render_folded_panels()
    
    preview_front = composite_front()
    preview_back = composite_back()
    preview_ff = composite_folded_front()
    preview_fb = composite_folded_back()
    
    render_device_icons(preview_front, preview_back, preview_ff, preview_fb)
    generate_docs_previews(preview_front, preview_back)
    validate()
    print(">>> All GUI Assets & Documentation Previews Successfully Rendered! <<<")
