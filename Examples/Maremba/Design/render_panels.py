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
  - Mathematically refined, pixel-perfect alignment across all 26 knobs, model cards, and meters.

Reason HD Divisibility Rule:
- All assets loaded by Reason must strictly satisfy (w % 5 == 0) and (h % 5 == 0).
"""

import os
import math
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
                    active_color=(235, 195, 75), dim_color=(140, 135, 125)):
    recess_r = radius - 15
    draw.ellipse([cx - recess_r, cy - recess_r, cx + recess_r, cy + recess_r], outline=(14, 15, 16), width=2)
    draw.arc([cx - recess_r, cy - recess_r, cx + recess_r, cy + recess_r], 45, 225, fill=(45, 48, 52), width=1)
    
    step = sweep_deg / (num_ticks - 1)
    for i in range(num_ticks):
        angle = start_angle_deg - i * step
        rad = math.radians(angle)
        is_major = (i == 0 or i == num_ticks - 1 or i == (num_ticks - 1) // 2)
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
    
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step + bar_step * 0.15)
        bw = int(bar_step * 0.70)
        pipe_len = int((h * 0.38) * (1.0 - 0.55 * (i / float(bar_count))))
        top_py = center_y + 12 * Q
        bot_py = top_py + pipe_len
        for col in range(bw):
            shine = math.sin((col / float(bw)) * math.pi)
            pr = int(185 + 65 * shine)
            pg = int(145 + 55 * shine)
            pb = int(45 + 35 * shine)
            draw.line([(bx + col, top_py), (bx + col, bot_py)], fill=(pr, pg, pb))
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
    
    pl_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, pl_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(26, 16, 10), outline=gold, width=2)
    draw.text((x0 + w // 2, pl_y + 6 * Q), "IMPERIAL ROSEWOOD 5.0", fill=gold, font=get_font(FONT_DIN_COND, 13), anchor="mm")
    draw.text((x0 + w // 2, pl_y + 13 * Q), "HONDURAS PALISANDER - 4:10 PARABOLIC UNDERCUT ARCH",
              fill=(235, 225, 210), font=get_font(FONT_DIN_ALT, 7.5), anchor="mm")


def draw_art_frame_padauk(draw, x0, y0, w, h):
    gold = (235, 195, 70)
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
        
    pl_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, pl_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(32, 18, 12), outline=gold, width=2)
    draw.text((x0 + w // 2, pl_y + 6 * Q), "CHIAPAS PADAUK 4.3", fill=gold, font=get_font(FONT_DIN_COND, 13), anchor="mm")
    draw.text((x0 + w // 2, pl_y + 13 * Q), "AFRICAN PADAUK BARS & CEDAR RESONATOR BOXES",
              fill=(235, 225, 210), font=get_font(FONT_DIN_ALT, 7.5), anchor="mm")


def draw_art_frame_balafon(draw, x0, y0, w, h):
    gold = (235, 195, 70)
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
        
    pl_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, pl_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(24, 18, 12), outline=gold, width=2)
    draw.text((x0 + w // 2, pl_y + 6 * Q), "ANCESTRAL BALAFON 21", fill=gold, font=get_font(FONT_DIN_COND, 13), anchor="mm")
    draw.text((x0 + w // 2, pl_y + 13 * Q), "FIRE-CHARRED KENE IRONWOOD & NATURAL CALABASH MIRLITONS",
              fill=(235, 225, 210), font=get_font(FONT_DIN_ALT, 7.5), anchor="mm")


def draw_art_frame_kalimba(draw, x0, y0, w, h):
    gold = (235, 195, 70)
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
                               
    pl_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, pl_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(28, 16, 10), outline=gold, width=2)
    draw.text((x0 + w // 2, pl_y + 6 * Q), "KALIMBA ARTISAN 17", fill=gold, font=get_font(FONT_DIN_COND, 13), anchor="mm")
    draw.text((x0 + w // 2, pl_y + 13 * Q), "SOLID SCULPTED ACACIA SOUNDBOX & POLISHED SPRING-STEEL TINES",
              fill=(235, 225, 210), font=get_font(FONT_DIN_ALT, 7.5), anchor="mm")


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

    art_img.save(HD / "ModelArt.png")
    art_1x = art_img.resize((240, 96 * 4), Image.Resampling.LANCZOS)
    art_1x.save(GUI2D / "ModelArt.png")
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


def draw_tube_grill_accent(draw, x0, y0, w, h):
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=3 * Q, fill=(14, 10, 8), outline=(55, 42, 30), width=1)
    cx = x0 + w // 2
    cy = y0 + h // 2
    for r in range(int(h * 0.6), 2, -int(3 * Q)):
        ratio = (1.0 - r / (h * 0.6))
        draw.ellipse([cx - r * 2, cy - r, cx + r * 2, cy + r],
                     fill=(int(245 * ratio), int(125 * ratio), int(25 * ratio)))
        
    draw.ellipse([cx - 4 * Q, cy - 2 * Q, cx + 4 * Q, cy + 2 * Q], fill=(255, 238, 180))
    mesh_step = 6 * Q
    for mx in range(x0 + 4 * Q, x0 + w - 4 * Q, mesh_step):
        draw.line([(mx, y0 + 2 * Q), (mx + 3 * Q, y0 + h - 2 * Q)], fill=(85, 60, 35), width=1)
        draw.line([(mx + 3 * Q, y0 + 2 * Q), (mx, y0 + h - 2 * Q)], fill=(85, 60, 35), width=1)


def draw_gain_reduction_meter(draw, x0, y0, w, h):
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=2 * Q, fill=(12, 14, 16), outline=(215, 175, 65), width=1)
    draw.text((x0 + 4 * Q, y0 + h // 2), "GR", fill=(215, 175, 65), font=get_font(FONT_DIN_ALT, 5.0), anchor="lm")
    leds = [("0", (40, 180, 70)), ("-1", (40, 180, 70)), ("-2", (40, 180, 70)),
            ("-4", (220, 160, 40)), ("-8", (220, 160, 40)), ("-12", (220, 60, 40)), ("-16", (220, 40, 40))]
    led_w = 4 * Q
    led_h = h - 6 * Q
    step = (w - 24 * Q) / float(len(leds))
    start_x = x0 + 16 * Q
    for i, (lbl, col) in enumerate(leds):
        lx = int(start_x + i * step)
        ly = y0 + 3 * Q
        draw.rectangle([lx, ly, lx + led_w, ly + led_h], fill=col, outline=(18, 20, 22), width=1)
        draw.line([(lx + 1, ly + 1), (lx + led_w - 1, ly + 1)], fill=(255, 255, 255), width=1)


def draw_stereo_vu_column(draw, x0, y0, w, h):
    gold = (235, 195, 75)
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=3 * Q, fill=(14, 15, 17), outline=gold, width=1)
    draw.text((x0 + w // 2, y0 + 6 * Q), "STEREO VU", fill=gold, font=get_font(FONT_DIN_COND, 7.5), anchor="mm")
    
    clip_y = y0 + 12 * Q
    draw.ellipse([x0 + 6 * Q, clip_y - 2 * Q, x0 + 10 * Q, clip_y + 2 * Q], fill=(230, 40, 30))
    draw.ellipse([x0 + w - 10 * Q, clip_y - 2 * Q, x0 + w - 6 * Q, clip_y + 2 * Q], fill=(230, 40, 30))
    draw.text((x0 + w // 2, clip_y), "CLIP", fill=(220, 60, 50), font=get_font(FONT_DIN_ALT, 4.5), anchor="mm")
    
    segs = [("+3", (230, 40, 30)), ("0", (230, 70, 30)), ("-3", (230, 160, 40)),
            ("-6", (220, 180, 45)), ("-12", (45, 190, 75)), ("-18", (40, 170, 70)),
            ("-24", (35, 150, 65)), ("-36", (30, 120, 55))]
    top_sy = y0 + 17 * Q
    bot_sy = y0 + h - 14 * Q
    seg_step = (bot_sy - top_sy) / float(len(segs) - 1)
    bar_w = 6 * Q
    bar_h = 3 * Q
    
    font_meter = get_font(FONT_DIN_ALT, 5.0)
    for i, (lbl, col) in enumerate(segs):
        sy = int(top_sy + i * seg_step)
        lx = x0 + 5 * Q
        draw.rectangle([lx, sy, lx + bar_w, sy + bar_h], fill=col, outline=(15, 16, 18), width=1)
        rx = x0 + w - 5 * Q - bar_w
        draw.rectangle([rx, sy, rx + bar_w, sy + bar_h], fill=col, outline=(15, 16, 18), width=1)
        draw.text((x0 + w // 2, sy + bar_h // 2), lbl, fill=(160, 165, 170), font=font_meter, anchor="mm")
        
    draw.text((x0 + 8 * Q, y0 + h - 5 * Q), "L", fill=gold, font=font_meter, anchor="mm")
    draw.text((x0 + w - 8 * Q, y0 + h - 5 * Q), "R", fill=gold, font=font_meter, anchor="mm")
    draw.text((x0 + w // 2, y0 + h - 5 * Q), "dB", fill=(135, 140, 145), font=font_meter, anchor="mm")

# -------------------------------------------------------------------------
# Front Panel Main Renderer
# -------------------------------------------------------------------------

def render_front_panel():
    """Render 6U Rack Extension Front Panel at 3770x2070 (5x HD) and 754x414 (1x GUI2D)."""
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
    px = 235 * Q
    py = 14 * Q
    pw = 190 * Q
    ph = 22 * Q
    draw.rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], fill=(12, 10, 8), outline=gold, width=2)
    draw.rectangle([px, py, px + pw, py + ph], fill=(8, 9, 10))
    for cx, cy in [(px - 2, py - 2), (px + pw + 2, py - 2), (px - 2, py + ph + 2), (px + pw + 2, py + ph + 2)]:
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=gold)
        
    # Note On Lamp Ring at { 595, 20 }
    lx = 595 * Q + 25
    ly = 20 * Q + 25
    draw.ellipse([lx - 24, ly - 24, lx + 24, ly + 24], fill=(36, 28, 18), outline=gold, width=2)
    draw.text((585 * Q, 25 * Q), "NOTE", fill=dim_ink, font=font_sub, anchor="rm")
    
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
    
    # ---------------------------------------------------------------------
    # SECTION 1 CONTROLS
    # ---------------------------------------------------------------------
    art_x = 28 * Q
    art_y = 84 * Q
    art_w = 240 * Q
    art_h = 96 * Q
    draw.rectangle([art_x - 4, art_y - 4, art_x + art_w + 4, art_y + art_h + 4], fill=(30, 20, 14), outline=gold, width=2)
    draw.rectangle([art_x - 1, art_y - 1, art_x + art_w + 1, art_y + art_h + 1], outline=(15, 16, 17), width=2)
    for bx, by in [(art_x - 2, art_y - 2), (art_x + art_w + 2, art_y - 2),
                   (art_x - 2, art_y + art_h + 2), (art_x + art_w + 2, art_y + art_h + 2)]:
        draw.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=gold)
        
    font_lbl = get_font(FONT_DIN_ALT, 10.5)
    font_lbl_sm = get_font(FONT_DIN_ALT, 8.5)
    
    models_info = [
        (32, "ROSEWOOD", (48, 22, 16), (245, 175, 45)),
        (92, "PADAUK",   (54, 24, 14), (235, 75, 40)),
        (152, "BALAFON", (26, 36, 20), (65, 215, 85)),
        (212, "KALIMBA", (52, 36, 16), (255, 215, 65)),
    ]
    for rx, label, btn_fill, led_glow in models_info:
        rpx = rx * Q
        rpy = 190 * Q
        draw.rounded_rectangle([rpx - 2 * Q, rpy - 2 * Q, rpx + 16 * Q, rpy + 18 * Q],
                               radius=2 * Q, fill=btn_fill, outline=(55, 58, 62), width=1)
        draw.ellipse([rpx + 18 * Q, rpy + 4 * Q, rpx + 22 * Q, rpy + 8 * Q], fill=led_glow, outline=(15, 16, 18), width=1)
        draw.text((rpx + 25 * Q, rpy + 8 * Q), label, fill=white_ink, font=font_lbl_sm, anchor="lm")
        
    draw_recessed_control_bay(draw, 28 * Q, 220 * Q, 240 * Q, 164 * Q, gold_rim=(185, 145, 50), shadow=shadow)
    
    s1_knobs = [
        (39, 228, "SYMPATHETIC", True),
        (122, 228, "BODY BLOOM",  True),
        (205, 228, "PITCH GLIDE", True),
        (80, 310, "MIRLITON BUZZ", False),
        (164, 310, "ARTIFACTS",   False),
    ]
    for kx, ky, name, is_gold in s1_knobs:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=132, active_color=gold if is_gold else white_ink)
        draw.text((cx, (ky + 56) * Q), name, fill=gold if is_gold else white_ink, font=font_lbl, anchor="mm")
        
    pl_x = 30 * Q
    pl_y = 388 * Q
    pl_w = 236 * Q
    pl_h = 11 * Q
    draw.rectangle([pl_x, pl_y, pl_x + pl_w, pl_y + pl_h], fill=(28, 20, 14), outline=gold, width=1)
    draw.text((pl_x + pl_w // 2, pl_y + pl_h // 2), "PROTOCODUS ACOUSTICS - 8 MODAL BARS & ANISOTROPIC COUPLING",
              fill=gold, font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")

    # ---------------------------------------------------------------------
    # SECTION 2 CONTROLS (EXCITER & RESONATOR CORE)
    # ---------------------------------------------------------------------
    st_cx = (286 + 26) * Q
    st_cy = (86 + 26) * Q
    draw_dial_ticks(draw, st_cx, st_cy, radius=126, start_angle_deg=225, sweep_deg=270, num_ticks=4,
                    active_color=gold, dim_color=gold)
    for ang, num_str in [(225, "1"), (135, "2"), (45, "3"), (-45, "4")]:
        rad = math.radians(ang)
        tx = st_cx + math.cos(rad) * 144
        ty = st_cy - math.sin(rad) * 144
        draw.text((tx, ty), num_str, fill=gold, font=get_font(FONT_DIN_COND, 10.5), anchor="mm")
    draw.text((st_cx, (86 + 56) * Q), "MALLET", fill=gold, font=font_lbl, anchor="mm")

    s2_row1 = [
        (338, 86, "HARDNESS"),
        (390, 86, "POSITION"),
        (442, 86, "VARIANCE")
    ]
    for kx, ky, name in s2_row1:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=126, active_color=gold)
        draw.text((cx, (ky + 56) * Q), name, fill=white_ink, font=font_lbl, anchor="mm")

    draw_acoustic_bar_schematic(draw, 284, 158, 212, 26)

    s2_row2 = [
        (300, 194, "RESONATOR"),
        (364, 194, "COUPLING"),
        (428, 194, "DECAY")
    ]
    for kx, ky, name in s2_row2:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=132, active_color=gold)
        draw.text((cx, (ky + 56) * Q), name, fill=white_ink, font=font_lbl, anchor="mm")

    draw.rectangle([284 * Q, 268 * Q, 496 * Q, 282 * Q], fill=(16, 17, 19), outline=gold, width=1)
    draw.text((390 * Q, 275 * Q), "1: SOFT YARN   |   2: MEDIUM CORD   |   3: HARD RUBBER   |   4: BARK / BATON",
              fill=(205, 210, 215), font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")

    s2_row3 = [
        (300, 298, "POLYPHONY"),
        (364, 298, "OVERSAMPLE"),
        (428, 298, "VELOCITY")
    ]
    for kx, ky, name in s2_row3:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=132, active_color=white_ink)
        draw.text((cx, (ky + 56) * Q), name, fill=white_ink, font=font_lbl, anchor="mm")
        
    draw.text((390 * Q, 390 * Q), "QUARTER-WAVE RESONATOR COUPLING - ASYMMETRIC HERTZIAN CONTACT",
              fill=(145, 140, 135), font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")

    # ---------------------------------------------------------------------
    # SECTION 3 CONTROLS (STUDIO CAPTURE & MASTER DYNAMICS)
    # ---------------------------------------------------------------------
    s3_row1 = [
        (515, 86, "CLOSE"),
        (567, 86, "ROOM"),
        (619, 86, "PIEZO"),
        (671, 86, "WIDTH")
    ]
    for kx, ky, name in s3_row1:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=125, active_color=(95, 205, 235))
        draw.text((cx, (ky + 56) * Q), name, fill=(195, 230, 245), font=font_lbl, anchor="mm")

    draw_tube_grill_accent(draw, 515 * Q, 160 * Q, 58 * Q, 20 * Q)
    draw_gain_reduction_meter(draw, 615 * Q, 160 * Q, 108 * Q, 20 * Q)

    s3_row2 = [
        (515, 194, "DRIVE"),
        (567, 194, "WARMTH"),
        (619, 194, "COMPRESS"),
        (671, 194, "RELEASE")
    ]
    for kx, ky, name in s3_row2:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=125, active_color=(245, 165, 55))
        draw.text((cx, (ky + 56) * Q), name, fill=(250, 220, 185), font=font_lbl, anchor="mm")

    draw.rectangle([512 * Q, 268 * Q, 724 * Q, 282 * Q], fill=(16, 17, 19), outline=gold, width=1)
    draw.text((618 * Q, 275 * Q), "CLASS-A TUBE SATURATION & VCA DYNAMICS", fill=gold,
              font=get_font(FONT_DIN_COND, 10.5), anchor="mm")

    s3_row3 = [
        (515, 298, "DETUNE"),
        (567, 298, "TUNE")
    ]
    for kx, ky, name in s3_row3:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_dial_ticks(draw, cx, cy, radius=125, num_ticks=11, active_color=gold, dim_color=(135, 130, 125))
        draw.text((cx, (ky + 56) * Q), name, fill=gold, font=font_lbl, anchor="mm")
        
    vcx = (626 + 26) * Q
    vcy = (298 + 26) * Q
    draw_dial_ticks(draw, vcx, vcy, radius=140, num_ticks=15, active_color=gold, dim_color=(135, 130, 125))
    draw.text((vcx, (298 + 56) * Q), "VOLUME", fill=gold, font=font_lbl, anchor="mm")
    
    draw_stereo_vu_column(draw, 688 * Q, 294 * Q, 32 * Q, 96 * Q)
    
    draw.text((618 * Q, 390 * Q), "24-BIT / 192 kHz FLOATING POINT MASTER BUS",
              fill=(145, 140, 135), font=get_font(FONT_DIN_ALT, 6.5), anchor="mm")
    
    panel.save(HD / "Reason_GUI_front_root_Panel.png")
    panel_1x = panel.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    panel_1x.save(GUI2D / "Reason_GUI_front_root_Panel.png")
    print("Rendered Reason_GUI_front_root_Panel.png (3770x2070 & 754x414) successfully!")

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
    draw.text((229 * Q, 74 * Q), "MULTI-CHANNEL BALANCED AUDIO OUTPUTS", fill=gold, font=get_font(FONT_DIN_COND, 14), anchor="mm")
    
    draw_recessed_control_bay(draw, 438 * Q, 60 * Q, 288 * Q, 335 * Q, gold_rim=gold, shadow=shadow)
    draw.rectangle([438 * Q, 60 * Q, 726 * Q, 88 * Q], fill=(28, 31, 34), outline=(48, 52, 56), width=1)
    draw.text((582 * Q, 74 * Q), "CONTROL VOLTAGE (CV) MODULATION INPUTS", fill=gold, font=get_font(FONT_DIN_COND, 14), anchor="mm")
    
    font_lbl = get_font(FONT_DIN_ALT, 11)
    font_sm = get_font(FONT_DIN_ALT, 8.5)
    
    audio_sockets = [
        (58, 150, "MAIN L", "MASTER L"),
        (114, 150, "MAIN R", "MASTER R"),
        (180, 150, "CLOSE L", "DIRECT L"),
        (236, 150, "CLOSE R", "DIRECT R"),
        (300, 150, "FAR L", "DIFFUSE L"),
        (352, 150, "FAR R", "DIFFUSE R"),
        (382, 250, "PIEZO", "CONTACT"),
    ]
    for sx, sy, name, desc in audio_sockets:
        cx = sx * Q + 48
        cy = sy * Q + 52
        draw_socket_collar(draw, cx, cy, is_audio=True)
        draw.text((cx, (sy + 28) * Q), name, fill=white, font=font_lbl, anchor="mm")
        draw.text((cx, (sy + 36) * Q), desc, fill=(145, 150, 155), font=font_sm, anchor="mm")
        
    draw.line([(58 * Q + 48, 120 * Q), (114 * Q + 48, 120 * Q)], fill=gold, width=2)
    draw.text(((58 + 114) // 2 * Q + 48, 112 * Q), "BALANCED STEREO", fill=gold, font=font_sm, anchor="mm")
    
    draw.line([(180 * Q + 48, 120 * Q), (236 * Q + 48, 120 * Q)], fill=(160, 165, 170), width=2)
    draw.text(((180 + 236) // 2 * Q + 48, 112 * Q), "STEREO PAIR", fill=(160, 165, 170), font=font_sm, anchor="mm")
    
    draw.line([(300 * Q + 48, 120 * Q), (352 * Q + 48, 120 * Q)], fill=(160, 165, 170), width=2)
    draw.text(((300 + 352) // 2 * Q + 48, 112 * Q), "STEREO PAIR", fill=(160, 165, 170), font=font_sm, anchor="mm")
    
    cv_sockets = [
        (460, 150, "NOTE CV", "1V / OCT"),
        (512, 150, "GATE CV", "TRIGGER"),
        (564, 150, "MALLET", "HARDNESS"),
        (616, 150, "POSITION", "STRIKE"),
        (668, 150, "COUPLING", "RESONATOR"),
        (460, 250, "SYMPATHETIC", "BODY MESH"),
        (564, 250, "ROLL CV", "TREMOLO"),
        (668, 250, "VOLUME CV", "AMPLITUDE"),
    ]
    for sx, sy, name, desc in cv_sockets:
        cx = sx * Q + 38
        cy = sy * Q + 42
        draw_socket_collar(draw, cx, cy, is_audio=False)
        draw.text((cx, (sy + 26) * Q), name, fill=(240, 220, 140), font=font_lbl, anchor="mm")
        draw.text((cx, (sy + 34) * Q), desc, fill=(145, 150, 155), font=font_sm, anchor="mm")
        
    draw_recessed_control_bay(draw, 53 * Q, 243 * Q, 304 * Q, 104 * Q, gold_rim=gold, shadow=shadow)
    draw.rectangle([19 * Q, 149 * Q, 34 * Q, 231 * Q], fill=(14, 15, 17), outline=(42, 46, 50), width=1)

    draw.rectangle([452 * Q, 315 * Q, 708 * Q, 375 * Q], fill=(12, 13, 14), outline=gold, width=1)
    draw_carved_african_mask_crest(draw, 474 * Q, 345 * Q, 15 * Q, gold=gold, terracotta=terracotta)
    draw.text((500 * Q, 330 * Q), "cz.protocodus.Maremba  |  PHYSICAL MODELING SYNTHESIZER", fill=(230, 230, 235), font=font_sm, anchor="lm")
    draw.text((500 * Q, 345 * Q), "MADE IN REASON STUDIOS RACK EXTENSION  |  PRO-AUDIO CLASS A", fill=(160, 165, 170), font=font_sm, anchor="lm")
    draw.text((500 * Q, 360 * Q), "CE / RoHS COMPLIANT - 100% REAL-TIME DSP SYNTHESIS ENGINE", fill=gold, font=font_sm, anchor="lm")
    
    panel.save(HD / "Reason_GUI_back_root_Panel.png")
    panel_1x = panel.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    panel_1x.save(GUI2D / "Reason_GUI_back_root_Panel.png")
    print("Rendered Reason_GUI_back_root_Panel.png (3770x2070 & 754x414) successfully!")

# -------------------------------------------------------------------------
# Folded Panels (3770x150 HD / 754x30 1x)
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
    
    px = 235 * Q
    py = 6 * Q
    pw = 190 * Q
    ph = 18 * Q
    draw_f.rectangle([px - 2, py - 2, px + pw + 2, py + ph + 2], fill=(10, 11, 12), outline=gold, width=2)
    draw_f.rectangle([px, py, px + pw, py + ph], fill=(6, 7, 8))
    
    draw_f.ellipse([595 * Q + 10, 9 * Q + 10, 595 * Q + 40, 9 * Q + 40], outline=gold, width=2)
    
    panel_f.save(HD / "Reason_GUI_folded_front_root_Panel.png")
    panel_f_1x = panel_f.resize((WIDTH, FOLDED_HEIGHT), Image.Resampling.LANCZOS)
    panel_f_1x.save(GUI2D / "Reason_GUI_folded_front_root_Panel.png")
    
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
    
    draw_b.ellipse([377 * Q - 7, 15 * Q - 7, 377 * Q + 7, 15 * Q + 7], fill=(14, 16, 18), outline=gold, width=2)
    draw_b.rectangle([605 * Q - 2, 8 * Q - 2, 605 * Q + 400 + 2, 8 * Q + 65 + 2], fill=(14, 15, 17), outline=(45, 50, 55), width=1)
    
    panel_b.save(HD / "Reason_GUI_folded_back_root_Panel.png")
    panel_b_1x = panel_b.resize((WIDTH, FOLDED_HEIGHT), Image.Resampling.LANCZOS)
    panel_b_1x.save(GUI2D / "Reason_GUI_folded_back_root_Panel.png")
    print("Rendered folded panels (3770x150 & 754x30) successfully!")

# -------------------------------------------------------------------------
# Compositing & Previews
# -------------------------------------------------------------------------

def copy_frame(strip, total_frames, frame_idx):
    w, h = strip.size
    frame_h = h // total_frames
    return strip.crop((0, frame_idx * frame_h, w, (frame_idx + 1) * frame_h))


def composite_front(panel=None):
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_front_root_Panel.png")
    image = panel.convert("RGBA")
    
    # 1. Model Art Display (Frame 0: Concert Grand Rosewood)
    model_art = Image.open(HD / "ModelArt.png").convert("RGBA")
    image.alpha_composite(copy_frame(model_art, 4, 0), (28 * Q, 84 * Q))
    
    # 2. Model Selection Toggles (Frame 1 on first, Frame 0 on others)
    toggle = Image.open(HD / "Toggle.png").convert("RGBA")
    image.alpha_composite(copy_frame(toggle, 2, 1), (32 * Q, 190 * Q))
    image.alpha_composite(copy_frame(toggle, 2, 0), (92 * Q, 190 * Q))
    image.alpha_composite(copy_frame(toggle, 2, 0), (152 * Q, 190 * Q))
    image.alpha_composite(copy_frame(toggle, 2, 0), (212 * Q, 190 * Q))
    
    # 3. Patch Browse Group at { 435, 14 }
    pbg = Image.open(HD / "PatchBrowseGroup.png").convert("RGBA")
    image.alpha_composite(pbg, (435 * Q, 14 * Q))
    
    # 4. Device Name Tape at { 505, 18 }
    tape_h = Image.open(HD / "TapeHorz.png").convert("RGBA")
    image.alpha_composite(tape_h, (505 * Q, 18 * Q))
    draw = ImageDraw.Draw(image)
    font_tape = get_font(FONT_DIN_ALT, 8.5)
    draw.text((505 * Q + 200, 18 * Q + 32), "Maremba", fill=(32, 34, 38), font=font_tape, anchor="mm")
    
    # 5. Note On Lamp at { 595, 20 }
    lamp = Image.open(HD / "Lamp.png").convert("RGBA")
    image.alpha_composite(copy_frame(lamp, 2, 0), (595 * Q, 20 * Q))
    
    # 6. Patch Display Text at { 235, 14 }
    font_patch = get_font(FONT_ARIAL, 11)
    draw.text((235 * Q + 475, 14 * Q + 55), "Concert Grand Rosewood", fill=(245, 235, 215), font=font_patch, anchor="mm")
    
    # 7. Knobs: 26 knobs at exact coordinates
    knob = Image.open(HD / "Knob.png").convert("RGBA")
    knob_settings = [
        # Section 1
        (39, 228, 32),   # sympathetic
        (122, 228, 26),  # bodyBloom
        (205, 228, 0),   # pitchGlide
        (80, 310, 15),   # buzzAmount
        (164, 310, 18),  # artifacts
        # Section 2
        (286, 86, 12),   # malletType
        (338, 86, 35),   # malletHardness
        (390, 86, 25),   # strikePosition
        (442, 86, 16),   # strikeJitter
        (300, 194, 31),  # resonatorTune
        (364, 194, 42),  # resonatorCoupling
        (428, 194, 38),  # decay
        (300, 298, 48),  # polyphony
        (364, 298, 20),  # oversampling
        (428, 298, 31),  # velocityCurve
        # Section 3
        (515, 86, 45),   # closeLevel
        (567, 86, 32),   # farLevel
        (619, 86, 20),   # piezoLevel
        (671, 86, 48),   # stereoWidth
        (515, 194, 18),  # preampDrive
        (567, 194, 36),  # warmth
        (619, 194, 25),  # compAmount
        (671, 194, 30),  # compRelease
        (515, 298, 14),  # detune
        (567, 298, 31),  # masterTune
        (626, 298, 50),  # volume
    ]
    for kx, ky, frame in knob_settings:
        image.alpha_composite(copy_frame(knob, 63, frame), (kx * Q, ky * Q))
        
    return image


def composite_back(panel=None):
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_back_root_Panel.png")
    image = panel.convert("RGBA")
    
    ph_x, ph_y = 55 * Q, 245 * Q
    ph_w, ph_h = 1500, 500
    ph_card = Image.new("RGBA", (ph_w, ph_h), (18, 20, 23, 240))
    d_ph = ImageDraw.Draw(ph_card)
    d_ph.rectangle([0, 0, ph_w - 1, ph_h - 1], outline=(55, 60, 68), width=2)
    d_ph.rectangle([6, 6, ph_w - 7, ph_h - 7], outline=(36, 40, 45), width=1)
    
    gold = (235, 195, 75)
    draw_carved_african_mask_crest(d_ph, 140, ph_h // 2, 18 * Q, gold=gold, terracotta=(148, 65, 32))
    d_ph.text((260, ph_h // 2 - 50), "REASON STUDIOS LICENSED RACK EXTENSION", fill=gold, font=get_font(FONT_DIN_COND, 14), anchor="lm")
    d_ph.text((260, ph_h // 2 - 5), "REGISTERED TO: PRO-AUDIO PRODUCTION WORKSTATION", fill=(220, 225, 230), font=get_font(FONT_DIN_ALT, 10), anchor="lm")
    d_ph.text((260, ph_h // 2 + 40), "DEVICE ID: cz.protocodus.Maremba  |  LICENSE: RS-RE-MAR-2026-7741", fill=(140, 145, 155), font=get_font(FONT_DIN_ALT, 8.5), anchor="lm")
    image.alpha_composite(ph_card, (ph_x, ph_y))
    
    tape_v = Image.open(HD / "TapeVert.png").convert("RGBA")
    image.alpha_composite(tape_v, (20 * Q, 150 * Q))
    tape_txt = Image.new("RGBA", (400, 65), (0, 0, 0, 0))
    d_tv = ImageDraw.Draw(tape_txt)
    d_tv.text((200, 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    tape_rot = tape_txt.transpose(Image.Transpose.ROTATE_270)
    image.alpha_composite(tape_rot, (20 * Q, 150 * Q))
    
    audio_jack = Image.open(HD / "AudioJack.png").convert("RGBA")
    for sx, sy in [(58, 150), (114, 150), (180, 150), (236, 150), (300, 150), (352, 150), (382, 250)]:
        image.alpha_composite(copy_frame(audio_jack, 3, 0), (sx * Q, sy * Q))
        
    cv_jack = Image.open(HD / "CVJack.png").convert("RGBA")
    for sx, sy in [(460, 150), (512, 150), (564, 150), (616, 150), (668, 150), (460, 250), (564, 250), (668, 250)]:
        image.alpha_composite(copy_frame(cv_jack, 3, 0), (sx * Q, sy * Q))
        
    return image


def composite_folded_front(panel=None):
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_folded_front_root_Panel.png")
    image = panel.convert("RGBA")
    draw = ImageDraw.Draw(image)
    
    draw.text((235 * Q + 475, 6 * Q + 45), "Concert Grand Rosewood", fill=(245, 235, 215), font=get_font(FONT_ARIAL, 9.5), anchor="mm")
    
    tape_h = Image.open(HD / "TapeHorz.png").convert("RGBA")
    image.alpha_composite(tape_h, (505 * Q, 8 * Q))
    draw.text((505 * Q + 200, 8 * Q + 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    
    lamp = Image.open(HD / "Lamp.png").convert("RGBA")
    image.alpha_composite(copy_frame(lamp, 2, 0), (595 * Q, 9 * Q))
    return image


def composite_folded_back(panel=None):
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_folded_back_root_Panel.png")
    image = panel.convert("RGBA")
    tape_h = Image.open(HD / "TapeHorz.png").convert("RGBA")
    image.alpha_composite(tape_h, (605 * Q, 8 * Q))
    draw = ImageDraw.Draw(image)
    draw.text((605 * Q + 200, 8 * Q + 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    return image


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
    
    artifacts_dir = Path("/Users/vojta/.gemini/antigravity/brain/57115581-b1fd-4366-a6f4-3ecaf5a71e3a")
    if artifacts_dir.exists():
        front_1x.save(artifacts_dir / "front_preview.png")
        rear_1x.save(artifacts_dir / "rear_preview.png")
        front_2x.save(artifacts_dir / "front_2x.png")
        rear_2x.save(artifacts_dir / "rear_2x.png")
    
    print("Generated all docs previews successfully!")


def render_device_icons(preview_front=None, preview_back=None, preview_ff=None, preview_fb=None):
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
    
    icon_128 = Image.new("RGBA", (128, 128), (20, 22, 25, 255))
    icon_128_draw = ImageDraw.Draw(icon_128)
    icon_128_draw.rectangle([2, 2, 125, 125], outline=gold, width=2)
    scaled_cell = base_icon.resize((120, 90), Image.Resampling.LANCZOS)
    icon_128.paste(scaled_cell, (4, 19))
    icon_128.save(GUI2D / "DeviceIcon.png")
    
    pal_hd = create_stone_slate_texture(650, 360, seed=606)
    pal_draw = ImageDraw.Draw(pal_hd)
    pal_draw.rectangle([2, 2, 647, 357], outline=gold, width=2)
    draw_bold_kuba_chevron_border(pal_draw, 10, 10, 630, 16)
    pal_draw.text((220, 140), "PROTOCODUS - MAREMBA", fill=gold, font=get_font(FONT_DIN_COND, 26), anchor="lm")
    pal_draw.text((220, 180), "PHYSICAL-MODELED MARIMBA & KALIMBA", fill=(230, 230, 235), font=get_font(FONT_DIN_ALT, 11), anchor="lm")
    pal_draw.text((220, 215), "ACOUSTIC MODAL SYNTHESIS ENGINE", fill=gold, font=get_font(FONT_DIN_ALT, 9), anchor="lm")
    pal_icon = base_icon.resize((180, 135), Image.Resampling.LANCZOS)
    pal_hd.paste(pal_icon, (25, 100))
    pal_hd.save(HD / "DevicePaletteImage.png")
    pal_2d = pal_hd.resize((130, 72), Image.Resampling.LANCZOS)
    pal_2d.save(GUI2D / "DevicePaletteImage.png")
    
    if preview_front is None:
        preview_front = composite_front()
    if preview_back is None:
        preview_back = composite_back()
    if preview_ff is None:
        preview_ff = composite_folded_front()
    if preview_fb is None:
        preview_fb = composite_folded_back()
        
    nav_hd = preview_front.resize((630, 345), Image.Resampling.LANCZOS)
    nav_hd.save(HD / "DeviceNavigator.png")
    nav_f_hd = preview_ff.resize((630, 25), Image.Resampling.LANCZOS)
    nav_f_hd.save(HD / "DeviceNavigatorFolded.png")
    
    nav_2d = preview_front.resize((126, 69), Image.Resampling.LANCZOS)
    nav_2d.save(GUI2D / "DeviceNavigator.png")
    nav_f_2d = preview_ff.resize((126, 5), Image.Resampling.LANCZOS)
    nav_f_2d.save(GUI2D / "DeviceNavigatorFolded.png")
    
    track_thumb_hd = preview_front.resize((270, 150), Image.Resampling.LANCZOS)
    track_thumb_hd.save(HD / "DeviceTrackListThumbnail.png")
    track_thumb_2d = preview_front.resize((54, 30), Image.Resampling.LANCZOS)
    track_thumb_2d.save(GUI2D / "DeviceTrackListThumbnail.png")
    
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
# Main Execution Entry Point
# -------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(HD, exist_ok=True)
    os.makedirs(GUI2D, exist_ok=True)
    
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
    print(">>> All GUI Assets & Documentation Previews Successfully Rendered! <<<")
