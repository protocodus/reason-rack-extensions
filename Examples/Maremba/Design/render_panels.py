#!/usr/bin/env python3
"""
Render high-resolution photorealistic GUI backdrops, native art, and icons for Maremba.
cz.protocodus.Maremba (Protocodus)

Theme: African Native Art as primary design principle with modern, expensive, luxurious touch.
- Authentic Kuba cloth geometric tessellations & chevron ribbons.
- Royal Ashanti/Adinkra gold crest medallions & etched brass inlays.
- African hard timbers: African Wenge, Gabon Ebony, Honduran Rosewood, African Padauk, Acacia.
- Hand-charred Kene ironwood & calabash gourds with spider-egg cocoon mirliton membranes.
- Hand-sculpted Acacia thumb piano (Kalimba) with pyrographic sacred geometry rosette.
- Swiss/German precision luxury audio equipment layout: laser-etched gold graduation ticks,
  brushed obsidian/black titanium plates, warm vacuum tube filament glow, and calibrated meters.

Generates:
- Reason_GUI_front_root_Panel.png (3770x1725 5x HD & 754x345 1x)
- Reason_GUI_back_root_Panel.png (3770x1725 5x HD & 754x345 1x)
- Reason_GUI_folded_front_root_Panel.png (3770x150 5x HD & 754x30 1x)
- Reason_GUI_folded_back_root_Panel.png (3770x150 5x HD & 754x30 1x)
- ModelArt.png (1200x1920 5x HD & 240x384 1x - 4 frames)
- DeviceIcon.png (779x518 Reason SDK Atlas & 128x128 1x)
- DevicePaletteImage.png (650x300 HD & 130x60 1x)
- DeviceNavigator.png (630x290 HD & 126x58 1x)
- DeviceNavigatorFolded.png (630x25 HD & 126x5 1x)
- DeviceTrackListThumbnail.png (270x125 HD & 54x25 1x)
- Complete Reason browser & rack preview suite
"""

import os
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

Q = 5  # Reason HD 5x scale factor
WIDTH, HEIGHT = 754, 345  # 5U rack unit dimensions
FOLDED_HEIGHT = 30        # 1U folded height

HD_WIDTH = WIDTH * Q       # 3770
HD_HEIGHT = HEIGHT * Q     # 1725
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
# Procedural Luxury & African Native Material Textures
# -------------------------------------------------------------------------

def create_african_wenge_texture(w, h):
    """
    Procedural deep African Wenge / Gabon Ebony wood texture.
    Deep dark espresso/obsidian grain with subtle warm amber-brown porous fibers.
    """
    y, x = np.mgrid[0:h, 0:w]
    norm_x = x / float(w)
    norm_y = y / float(h)
    
    grain = (
        np.sin(norm_y * 110.0 + np.sin(norm_x * 10.0) * 1.8) * 0.45 +
        np.sin(norm_y * 360.0 + np.cos(norm_x * 22.0) * 1.2) * 0.28 +
        np.sin(norm_y * 820.0) * 0.15 +
        np.random.normal(0, 0.07, (h, w))
    )
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    
    # Deep African Wenge: obsidian dark espresso (16, 12, 11) to warm rich amber-brown (52, 32, 22)
    r = (16 + grain * 36).astype(np.uint8)
    g = (12 + grain * 20).astype(np.uint8)
    b = (11 + grain * 13).astype(np.uint8)
    
    # Subtle longitudinal edge shadow
    edge_vignette = 1.0 - 0.22 * (np.sin(norm_x * np.pi) ** 8)
    r = np.clip(r * edge_vignette, 0, 255).astype(np.uint8)
    g = np.clip(g * edge_vignette, 0, 255).astype(np.uint8)
    b = np.clip(b * edge_vignette, 0, 255).astype(np.uint8)
    
    rgb = np.stack([r, g, b, np.full((h, w), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(rgb, "RGBA")


def create_luxury_obsidian_plate_texture(w, h):
    """
    Procedural brushed obsidian / black titanium anodized audio faceplate.
    Fine horizontal micro-brush lines, silky satin reflection gradient.
    """
    np.random.seed(42)
    brush = np.random.normal(0, 2.8, (1, w))
    brush = np.repeat(brush, h, axis=0)
    fine_noise = np.random.normal(0, 1.4, (h, w))
    texture = brush + fine_noise * 0.4
    
    # Subtle vertical lighting gradient
    y_grad = np.linspace(26, 18, h)[:, None]
    base = np.clip(y_grad + texture, 0, 255).astype(np.uint8)
    
    r = np.clip(base, 0, 255).astype(np.uint8)
    g = np.clip(base + 1, 0, 255).astype(np.uint8)
    b = np.clip(base + 2, 0, 255).astype(np.uint8)
    
    rgb = np.stack([r, g, b, np.full((h, w), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(rgb, "RGBA")


def create_steel_back_texture(w, h):
    """Procedural industrial dark steel rear chassis texture."""
    np.random.seed(101)
    noise = np.random.normal(0, 2.5, (h, 1))
    noise = np.repeat(noise, w, axis=1)
    y_grad = np.linspace(24, 17, h)[:, None]
    base = np.clip(y_grad + noise, 0, 255).astype(np.uint8)
    
    r = base
    g = np.clip(base + 1, 0, 255).astype(np.uint8)
    b = np.clip(base + 2, 0, 255).astype(np.uint8)
    
    rgb = np.stack([r, g, b, np.full((h, w), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(rgb, "RGBA")

# -------------------------------------------------------------------------
# African Native Art Drawing Primitives & Motifs
# -------------------------------------------------------------------------

def draw_kuba_band(draw, x0, y0, w, h, gold=(218, 175, 55), bronze=(145, 105, 40), vertical=False):
    """
    Authentic Kuba Cloth geometric frieze: interlocking diamonds, stepped chevrons,
    and diagonal hatch frets in gold and bronze.
    """
    if vertical:
        step = w
        num_units = int(h / step) + 1
        for u in range(num_units):
            cy = y0 + u * step + step / 2.0
            cx = x0 + w / 2.0
            d_half = w / 2.0 - 2 * Q
            if cy + d_half > y0 + h:
                continue
            # Outer diamond
            draw.polygon([(cx, cy - d_half), (cx + d_half, cy), (cx, cy + d_half), (cx - d_half, cy)],
                         outline=gold, width=2)
            # Inner diamond filled with rich bronze
            d_in = d_half * 0.52
            draw.polygon([(cx, cy - d_in), (cx + d_in, cy), (cx, cy + d_in), (cx - d_in, cy)],
                         fill=bronze, outline=gold, width=1)
            # Central micro-dot
            draw.ellipse([cx - 2 * Q, cy - 2 * Q, cx + 2 * Q, cy + 2 * Q], fill=gold)
            # Connecting chevron lines
            draw.line([(cx - d_half, cy), (cx, cy - d_half * 1.5)], fill=bronze, width=1)
            draw.line([(cx + d_half, cy), (cx, cy - d_half * 1.5)], fill=bronze, width=1)
    else:
        step = h
        num_units = int(w / step) + 1
        for u in range(num_units):
            cx = x0 + u * step + step / 2.0
            cy = y0 + h / 2.0
            d_half = h / 2.0 - 2 * Q
            if cx + d_half > x0 + w:
                continue
            # Outer diamond
            draw.polygon([(cx, cy - d_half), (cx + d_half, cy), (cx, cy + d_half), (cx - d_half, cy)],
                         outline=gold, width=2)
            # Inner diamond filled with rich bronze
            d_in = d_half * 0.52
            draw.polygon([(cx, cy - d_in), (cx + d_in, cy), (cx, cy + d_in), (cx - d_in, cy)],
                         fill=bronze, outline=gold, width=1)
            # Central micro-dot
            draw.ellipse([cx - 2 * Q, cy - 2 * Q, cx + 2 * Q, cy + 2 * Q], fill=gold)
            # Corner chevron frets
            draw.line([(cx - d_half, cy), (cx - d_half * 1.5, cy - d_half)], fill=bronze, width=1)
            draw.line([(cx - d_half, cy), (cx - d_half * 1.5, cy + d_half)], fill=bronze, width=1)


def draw_african_crest(draw, cx, cy, radius, gold=(225, 180, 65), dark_fill=(26, 20, 14)):
    """
    Royal Ashanti/Adinkra inspired gold medallion:
    Concentric rings, radiating geometric sunburst rays, and sacred diamond core.
    """
    draw.ellipse([cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2], fill=(10, 8, 6))
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=dark_fill, outline=gold, width=3)
    
    r_inner = radius - 6 * Q
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], outline=gold, width=1)
    
    # 16 Radiating geometric sunburst teeth / petals
    num_rays = 16
    for i in range(num_rays):
        ang = i * (360.0 / num_rays)
        rad = math.radians(ang)
        rad_w = math.radians(ang + 8.0)
        rad_w2 = math.radians(ang - 8.0)
        
        p0_x = cx + math.cos(rad) * (radius - 2 * Q)
        p0_y = cy + math.sin(rad) * (radius - 2 * Q)
        p1_x = cx + math.cos(rad_w) * (r_inner + 2 * Q)
        p1_y = cy + math.sin(rad_w) * (r_inner + 2 * Q)
        p2_x = cx + math.cos(rad_w2) * (r_inner + 2 * Q)
        p2_y = cy + math.sin(rad_w2) * (r_inner + 2 * Q)
        draw.polygon([(p0_x, p0_y), (p1_x, p1_y), (p2_x, p2_y)], fill=gold)
        
    # Central sacred geometric diamond
    r_core = radius * 0.44
    pts_diamond = [
        (cx, cy - r_core),
        (cx + r_core, cy),
        (cx, cy + r_core),
        (cx - r_core, cy)
    ]
    draw.polygon(pts_diamond, fill=(45, 32, 16), outline=gold, width=2)
    
    r_in = r_core * 0.50
    pts_in = [
        (cx, cy - r_in),
        (cx + r_in, cy),
        (cx, cy + r_in),
        (cx - r_in, cy)
    ]
    draw.polygon(pts_in, fill=gold)
    draw.ellipse([cx - 2 * Q, cy - 2 * Q, cx + 2 * Q, cy + 2 * Q], fill=dark_fill)


def draw_african_corner_bracket(draw, bx, by, size, sx, sy, gold=(218, 175, 55), bronze=(145, 105, 40)):
    """
    High-end African stepped geometric L-bracket with nested right-angle chevrons and gold studs.
    """
    draw.line([(bx, by), (bx + sx * size, by)], fill=gold, width=2)
    draw.line([(bx, by), (bx, by + sy * size)], fill=gold, width=2)
    
    for off in [4 * Q, 8 * Q, 12 * Q]:
        if off < size:
            draw.line([(bx + sx * off, by + sy * 2 * Q), (bx + sx * 2 * Q, by + sy * off)], fill=bronze, width=1)
            
    draw.ellipse([bx + sx * 3 * Q - 2 * Q, by + sy * 3 * Q - 2 * Q,
                  bx + sx * 3 * Q + 2 * Q, by + sy * 3 * Q + 2 * Q], fill=gold)


def draw_screw(draw, cx, cy, radius, angle_deg=35, is_brass=False):
    """Draw a recessed black-oxide or 24K gold-plated oval head screw with countersunk bevel."""
    draw.ellipse([cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2], fill=(10, 10, 10))
    outer_color = (195, 155, 50) if is_brass else (50, 52, 55)
    border_color = (235, 190, 70) if is_brass else (20, 21, 22)
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=outer_color, outline=border_color, width=2)
    
    r_in = radius - 3
    in_color = (130, 95, 30) if is_brass else (32, 34, 36)
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=in_color)
    
    rad = math.radians(angle_deg)
    dx = math.cos(rad) * (r_in - 2)
    dy = math.sin(rad) * (r_in - 2)
    draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=(12, 13, 14), width=int(radius * 0.35))
    
    highlight = (255, 230, 130) if is_brass else (90, 95, 100)
    draw.arc([cx - r_in, cy - r_in, cx + r_in, cy + r_in], -120, -30, fill=highlight, width=2)


def draw_recessed_bay(draw, x0, y0, w, h, fill_color=(19, 21, 23), outline_color=(45, 48, 52), bevel_width=3, gold_accent=False):
    """Draw a beveled recessed equipment bay with inner shadow and highlight rim."""
    draw.rectangle([x0 - bevel_width, y0 - bevel_width, x0 + w + bevel_width, y0 + h + bevel_width], fill=(50, 54, 58))
    draw.rectangle([x0 - bevel_width, y0 - bevel_width, x0 + w, y0 + h], fill=(12, 13, 14))
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=fill_color, outline=outline_color, width=2)
    if gold_accent:
        gold = (218, 175, 55)
        draw.line([(x0 + 2, y0 + 2), (x0 + w - 2, y0 + 2)], fill=gold, width=2)
        draw.line([(x0 + 2, y0 + h - 2), (x0 + w - 2, y0 + h - 2)], fill=gold, width=1)


def draw_knob_dial_ticks(draw, cx, cy, radius=132, start_angle_deg=225, sweep_deg=270, num_ticks=11,
                         active_color=(225, 180, 65), dim_color=(125, 130, 135)):
    """Laser-etched radial dial graduation ticks around a knob center with micro-dot accents."""
    recess_r = radius - 15
    draw.ellipse([cx - recess_r, cy - recess_r, cx + recess_r, cy + recess_r], outline=(15, 16, 17), width=2)
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
            dot_r = 3
            draw.ellipse([x2 - dot_r, y2 - dot_r, x2 + dot_r, y2 + dot_r], fill=active_color)


def draw_knob_ticks_labeled(draw, cx, cy, radius=132, start_angle_deg=225, sweep_deg=270, num_ticks=11,
                            active_color=(225, 180, 65), dim_color=(125, 130, 135),
                            min_lbl=None, mid_lbl=None, max_lbl=None):
    """Draw radial graduation ticks with calibrated labels."""
    draw_knob_dial_ticks(draw, cx, cy, radius, start_angle_deg, sweep_deg, num_ticks, active_color, dim_color)
    font_lbl = get_font(FONT_DIN_ALT, 5.5)
    
    if min_lbl:
        rad = math.radians(start_angle_deg)
        tx = cx + math.cos(rad) * (radius + 16)
        ty = cy - math.sin(rad) * (radius + 16)
        draw.text((tx, ty), min_lbl, fill=dim_color, font=font_lbl, anchor="mm")
        
    if mid_lbl:
        rad = math.radians(start_angle_deg - sweep_deg / 2)
        tx = cx + math.cos(rad) * (radius + 15)
        ty = cy - math.sin(rad) * (radius + 15)
        draw.text((tx, ty), mid_lbl, fill=dim_color, font=font_lbl, anchor="mm")
        
    if max_lbl:
        rad = math.radians(start_angle_deg - sweep_deg)
        tx = cx + math.cos(rad) * (radius + 16)
        ty = cy - math.sin(rad) * (radius + 16)
        draw.text((tx, ty), max_lbl, fill=dim_color, font=font_lbl, anchor="mm")


def draw_socket_bezel(draw, cx, cy, is_audio=True):
    """Photorealistic jack socket bezel with metallic grounding collar and drop shadow."""
    r_outer = 48 if is_audio else 42
    r_inner = 32 if is_audio else 26
    r_hole = 20 if is_audio else 16
    
    draw.ellipse([cx - r_outer - 2, cy - r_outer - 2, cx + r_outer + 2, cy + r_outer + 2], fill=(8, 9, 10))
    border_color = (218, 175, 55) if is_audio else (165, 170, 175)
    fill_ring = (52, 54, 58)
    draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=fill_ring, outline=border_color, width=3)
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=(22, 24, 26), outline=(36, 38, 42), width=2)
    draw.ellipse([cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole], fill=(5, 5, 6))
    draw.arc([cx - r_hole + 4, cy - r_hole + 4, cx + r_hole - 4, cy + r_hole - 4], 30, 120, fill=(235, 185, 55), width=3)

# -------------------------------------------------------------------------
# Native Art Model Artwork Filmstrip (4 Frames of 1200x480 at 5x HD)
# -------------------------------------------------------------------------

def draw_art_frame_rosewood(draw, x0, y0, w, h):
    """
    Frame 0: IMPERIAL ROSEWOOD 5.0
    Concert Honduras Palisander bars with parabolic undercut, gold suspension cord,
    polished 24K brass resonator pipes with engraved Kuba geometric bands.
    """
    gold = (218, 175, 55)
    bronze = (145, 105, 40)
    
    for i in range(h):
        ratio = i / float(h)
        r = int(22 + 16 * ratio)
        g = int(14 + 10 * ratio)
        b = int(12 + 8 * ratio)
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    bracket_s = 35 * Q
    draw_african_corner_bracket(draw, x0 + 4 * Q, y0 + 4 * Q, bracket_s, 1, 1, gold, bronze)
    draw_african_corner_bracket(draw, x0 + w - 4 * Q, y0 + 4 * Q, bracket_s, -1, 1, gold, bronze)
    draw_african_corner_bracket(draw, x0 + 4 * Q, y0 + h - 26 * Q, bracket_s, 1, -1, gold, bronze)
    draw_african_corner_bracket(draw, x0 + w - 4 * Q, y0 + h - 26 * Q, bracket_s, -1, -1, gold, bronze)
    
    draw_kuba_band(draw, x0 + 45 * Q, y0 + 3 * Q, w - 90 * Q, 8 * Q, gold, bronze)
    
    bar_count = 11
    pad_x = 24 * Q
    avail_w = w - 2 * pad_x
    bar_step = avail_w / float(bar_count)
    center_y = y0 + int(h * 0.46)
    
    # 1. 24K Polished Brass Resonator Pipes with Engraved Geometric Collars
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step + bar_step * 0.15)
        bw = int(bar_step * 0.70)
        pipe_len = int((h * 0.38) * (1.0 - 0.55 * (i / float(bar_count))))
        top_py = center_y + 12 * Q
        bot_py = top_py + pipe_len
        
        for col in range(bw):
            col_ratio = col / float(bw)
            shine = math.sin(col_ratio * math.pi)
            br = int(140 + 105 * shine)
            bg = int(110 + 85 * shine)
            bb = int(30 + 55 * shine)
            draw.line([(bx + col, top_py), (bx + col, bot_py)], fill=(br, bg, bb))
            
        draw.arc([bx, bot_py - 6 * Q, bx + bw, bot_py + 6 * Q], 0, 180, fill=gold, width=2)
        
        ring_y = top_py + 8 * Q
        draw.line([(bx, ring_y), (bx + bw, ring_y)], fill=gold, width=2)
        draw.line([(bx, ring_y + 4 * Q), (bx + bw, ring_y + 4 * Q)], fill=gold, width=1)
        for rx in range(bx + 2 * Q, bx + bw - 2 * Q, 4 * Q):
            draw.line([(rx, ring_y), (rx + 2 * Q, ring_y + 4 * Q)], fill=(80, 50, 15), width=1)
            
    # 2. Suspended Honduras Rosewood Tone Bars
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step)
        bw = int(bar_step * 0.88)
        bar_len = int((h * 0.32) * (1.0 - 0.40 * (i / float(bar_count))))
        top_by = center_y - bar_len // 2
        bot_by = center_y + bar_len // 2
        
        draw.rectangle([bx + 3 * Q, top_by + 3 * Q, bx + bw + 3 * Q, bot_by + 3 * Q], fill=(12, 6, 4))
        draw.rectangle([bx, top_by, bx + bw, bot_by], fill=(66, 26, 18), outline=(38, 14, 10), width=2)
        draw.rectangle([bx + 3, top_by + 4, bx + bw - 3, bot_by - 4], fill=(88, 36, 26))
        draw.line([(bx + 2, top_by + 2), (bx + bw - 2, top_by + 2)], fill=(175, 95, 75), width=2)
        
        arch_cy = bot_by - 2 * Q
        draw.arc([bx + 2 * Q, arch_cy - 8 * Q, bx + bw - 2 * Q, arch_cy + 8 * Q], 180, 360, fill=(35, 12, 8), width=2)
        
        hole_y1 = top_by + int(bar_len * 0.22)
        hole_y2 = bot_by - int(bar_len * 0.22)
        for hy in [hole_y1, hole_y2]:
            draw.ellipse([bx + bw // 2 - 4 * Q, hy - 4 * Q, bx + bw // 2 + 4 * Q, hy + 4 * Q],
                         fill=(20, 8, 5), outline=gold, width=1)
            draw.ellipse([bx + bw // 2 - 2 * Q, hy - 2 * Q, bx + bw // 2 + 2 * Q, hy + 2 * Q], fill=(10, 4, 2))
            
    draw.line([(x0 + pad_x, center_y - int(h * 0.08)), (x0 + w - pad_x, center_y - int(h * 0.04))],
              fill=(235, 205, 120), width=2)
    draw.line([(x0 + pad_x, center_y + int(h * 0.08)), (x0 + w - pad_x, center_y + int(h * 0.04))],
              fill=(235, 205, 120), width=2)
              
    plaque_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, plaque_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(28, 20, 14), outline=gold, width=2)
    draw.rectangle([x0 + 17 * Q, plaque_y + 2 * Q, x0 + w - 17 * Q, y0 + h - 6 * Q], outline=bronze, width=1)
    
    for px, py in [(x0 + 19 * Q, plaque_y + 4 * Q), (x0 + w - 19 * Q, plaque_y + 4 * Q),
                   (x0 + 19 * Q, y0 + h - 8 * Q), (x0 + w - 19 * Q, y0 + h - 8 * Q)]:
        draw.ellipse([px - 2 * Q, py - 2 * Q, px + 2 * Q, py + 2 * Q], fill=gold)
        
    font_p = get_font(FONT_DIN_COND, 11)
    font_sub = get_font(FONT_DIN_ALT, 6.0)
    draw.text((x0 + w // 2, plaque_y + 6 * Q), "IMPERIAL ROSEWOOD 5.0", fill=gold, font=font_p, anchor="mm")
    draw.text((x0 + w // 2, plaque_y + 13 * Q), "HONDURAS PALISANDER TONE BARS & ENGRAVED 24K BRASS RESONATORS",
              fill=(205, 185, 145), font=font_sub, anchor="mm")


def draw_art_frame_padauk(draw, x0, y0, w, h):
    """
    Frame 1: PADAUK VIRTUOSO 4.3
    Quarter-sawn African Padauk bars, stepped African cedar acoustic soundbox resonator,
    inlaid tribal sunburst and geometric brass corner braces.
    """
    gold = (225, 155, 45)
    bronze = (150, 90, 30)
    
    for i in range(h):
        ratio = i / float(h)
        r = int(42 + 22 * ratio)
        g = int(20 + 12 * ratio)
        b = int(12 + 6 * ratio)
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    step_size = 8 * Q
    for i in range(0, w - step_size, step_size * 2):
        draw.line([(x0 + i, y0 + step_size), (x0 + i + step_size, y0 + step_size),
                   (x0 + i + step_size, y0 + 3 * Q), (x0 + i + 2 * step_size, y0 + 3 * Q)], fill=gold, width=2)
        draw.line([(x0 + i, y0 + h - step_size - 20 * Q), (x0 + i + step_size, y0 + h - step_size - 20 * Q),
                   (x0 + i + step_size, y0 + h - 3 * Q - 20 * Q), (x0 + i + 2 * step_size, y0 + h - 3 * Q - 20 * Q)],
                  fill=gold, width=2)
                  
    cx = x0 + w // 2
    cy = y0 + int(h * 0.26)
    draw_african_crest(draw, cx, cy, 22 * Q, gold=gold, dark_fill=(38, 18, 10))
    
    bar_count = 10
    pad_x = 24 * Q
    avail_w = w - 2 * pad_x
    bar_step = avail_w / float(bar_count)
    center_y = y0 + int(h * 0.52)
    
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step + bar_step * 0.12)
        bw = int(bar_step * 0.76)
        box_len = int((h * 0.34) * (1.0 - 0.45 * (i / float(bar_count))))
        top_py = center_y + 10 * Q
        bot_py = top_py + box_len
        
        draw.rectangle([bx, top_py, bx + bw, bot_py], fill=(95, 48, 26), outline=(48, 22, 10), width=2)
        port_r = int(bw * 0.28)
        port_cy = bot_py - port_r - 4 * Q
        draw.ellipse([bx + bw // 2 - port_r, port_cy - port_r, bx + bw // 2 + port_r, port_cy + port_r],
                     fill=(25, 12, 6), outline=gold, width=1)
        draw.line([(bx, top_py), (bx + 4 * Q, top_py)], fill=gold, width=2)
        draw.line([(bx, top_py), (bx, top_py + 4 * Q)], fill=gold, width=2)
        draw.line([(bx + bw, top_py), (bx + bw - 4 * Q, top_py)], fill=gold, width=2)
        draw.line([(bx + bw, top_py), (bx + bw, top_py + 4 * Q)], fill=gold, width=2)
        
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step)
        bw = int(bar_step * 0.90)
        bar_len = int((h * 0.30) * (1.0 - 0.38 * (i / float(bar_count))))
        top_by = center_y - bar_len // 2
        bot_by = center_y + bar_len // 2
        
        draw.rectangle([bx + 3 * Q, top_by + 3 * Q, bx + bw + 3 * Q, bot_by + 3 * Q], fill=(18, 8, 4))
        draw.rectangle([bx, top_by, bx + bw, bot_by], fill=(195, 62, 22), outline=(95, 26, 10), width=2)
        draw.rectangle([bx + 3, top_by + 4, bx + bw - 3, bot_by - 4], fill=(225, 85, 34))
        draw.line([(bx + bw // 2, top_by + 3), (bx + bw // 2, bot_by - 3)], fill=(160, 48, 14), width=2)
        
    plaque_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, plaque_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(36, 18, 10), outline=gold, width=2)
    draw.rectangle([x0 + 17 * Q, plaque_y + 2 * Q, x0 + w - 17 * Q, y0 + h - 6 * Q], outline=bronze, width=1)
    font_p = get_font(FONT_DIN_COND, 11)
    font_sub = get_font(FONT_DIN_ALT, 6.0)
    draw.text((x0 + w // 2, plaque_y + 6 * Q), "PADAUK VIRTUOSO 4.3", fill=gold, font=font_p, anchor="mm")
    draw.text((x0 + w // 2, plaque_y + 13 * Q), "QUARTER-SAWN AFRICAN PADAUK & CEDAR ACOUSTIC SOUNDBOX",
              fill=(220, 195, 160), font=font_sub, anchor="mm")


def draw_art_frame_balafon(draw, x0, y0, w, h):
    """
    Frame 2: BALAFON ANCESTRAL
    Fire-charred African ironwood (Kene) keys, natural calabash gourds with spider-silk
    mirliton buzz membranes rimmed with dark wax rings, and twisted rawhide bindings.
    """
    cream = (215, 195, 165)
    cream_dim = (120, 105, 85)
    
    for i in range(h):
        ratio = i / float(h)
        r = int(26 + 14 * ratio)
        g = int(22 + 10 * ratio)
        b = int(18 + 8 * ratio)
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    step = 25 * Q
    for ix in range(x0 + 10 * Q, x0 + w - 10 * Q, step):
        draw.line([(ix, y0 + 10 * Q), (ix + 12 * Q, y0 + 22 * Q), (ix + 24 * Q, y0 + 10 * Q)], fill=cream_dim, width=2)
        draw.line([(ix, y0 + h - 26 * Q), (ix + 12 * Q, y0 + h - 38 * Q), (ix + 24 * Q, y0 + h - 26 * Q)], fill=cream_dim, width=2)
        
    bar_count = 9
    pad_x = 24 * Q
    avail_w = w - 2 * pad_x
    bar_step = avail_w / float(bar_count)
    center_y = y0 + int(h * 0.48)
    
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step + bar_step * 0.50)
        gourd_r = int((22 * Q + (8 - i) * 3 * Q))
        gy = center_y + gourd_r + 8 * Q
        
        draw.ellipse([bx - gourd_r, gy - gourd_r, bx + gourd_r, gy + gourd_r],
                     fill=(145, 98, 48), outline=(78, 50, 22), width=3)
        draw.ellipse([bx - gourd_r + 4, gy - gourd_r + 4, bx + gourd_r - 4, gy + gourd_r - 4],
                     fill=(172, 120, 62))
                     
        mem_r = int(gourd_r * 0.36)
        draw.ellipse([bx - mem_r - 3, gy - mem_r - 3, bx + mem_r + 3, gy + mem_r + 3], fill=(20, 14, 10))
        draw.ellipse([bx - mem_r, gy - mem_r, bx + mem_r, gy + mem_r],
                     fill=(35, 24, 18), outline=(235, 225, 200), width=2)
        draw.line([(bx - mem_r + 2, gy), (bx + mem_r - 2, gy)], fill=(245, 240, 225), width=2)
        draw.line([(bx, gy - mem_r + 2), (bx, gy + mem_r - 2)], fill=(245, 240, 225), width=2)
        
        draw.line([(bx - 3 * Q, gy - gourd_r), (bx - 3 * Q, center_y + 6 * Q)], fill=(120, 85, 45), width=2)
        draw.line([(bx + 3 * Q, gy - gourd_r), (bx + 3 * Q, center_y + 6 * Q)], fill=(120, 85, 45), width=2)
        
    for i in range(bar_count):
        bx = int(x0 + pad_x + i * bar_step)
        bw = int(bar_step * 0.88)
        bar_len = int((h * 0.32) * (1.0 - 0.35 * (i / float(bar_count))))
        top_by = center_y - bar_len // 2
        bot_by = center_y + bar_len // 2
        
        draw.rectangle([bx + 4 * Q, top_by + 4 * Q, bx + bw + 4 * Q, bot_by + 4 * Q], fill=(12, 8, 6))
        draw.rectangle([bx, top_by, bx + bw, bot_by], fill=(42, 30, 24), outline=(18, 12, 10), width=3)
        draw.rectangle([bx + 4, top_by + 5, bx + bw - 4, bot_by - 5], fill=(62, 44, 34))
        
        draw.line([(bx + 3, top_by + bar_len // 3), (bx + bw - 3, top_by + bar_len // 3)], fill=(25, 16, 12), width=2)
        draw.line([(bx + 3, bot_by - bar_len // 3), (bx + bw - 3, bot_by - bar_len // 3)], fill=(25, 16, 12), width=2)
        
        draw.rectangle([bx + 2, top_by + 8 * Q, bx + bw - 2, top_by + 12 * Q], fill=(170, 130, 80), outline=(80, 50, 25), width=1)
        draw.rectangle([bx + 2, bot_by - 12 * Q, bx + bw - 2, bot_by - 8 * Q], fill=(170, 130, 80), outline=(80, 50, 25), width=1)
        
    plaque_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, plaque_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(24, 18, 14), outline=cream, width=2)
    draw.rectangle([x0 + 17 * Q, plaque_y + 2 * Q, x0 + w - 17 * Q, y0 + h - 6 * Q], outline=cream_dim, width=1)
    font_p = get_font(FONT_DIN_COND, 11)
    font_sub = get_font(FONT_DIN_ALT, 6.0)
    draw.text((x0 + w // 2, plaque_y + 6 * Q), "BALAFON ANCESTRAL", fill=cream, font=font_p, anchor="mm")
    draw.text((x0 + w // 2, plaque_y + 13 * Q), "FIRE-CHARRED KENE IRONWOOD & NATURAL CALABASH MIRLITONS",
              fill=(200, 185, 160), font=font_sub, anchor="mm")


def draw_art_frame_kalimba(draw, x0, y0, w, h):
    """
    Frame 3: KALIMBA ARTISAN 17
    Hand-sculpted solid African Acacia / Wenge soundbox with curved ergonomic waist,
    pyrographic sacred geometric rosette, 17 spring-steel tines in alternating V-stagger,
    and solid machined brass bridge & pressure bar with knurled tension bolts.
    """
    gold = (225, 165, 55)
    pyro_color = (195, 125, 45)
    
    for i in range(h):
        ratio = i / float(h)
        r = int(56 + 28 * ratio)
        g = int(32 + 16 * ratio)
        b = int(14 + 10 * ratio)
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))
        
    draw.rounded_rectangle([x0 + 8 * Q, y0 + 6 * Q, x0 + w - 8 * Q, y0 + h - 6 * Q],
                           radius=10 * Q, outline=(135, 80, 34), width=3)
    draw.rounded_rectangle([x0 + 11 * Q, y0 + 9 * Q, x0 + w - 11 * Q, y0 + h - 9 * Q],
                           radius=8 * Q, outline=(42, 22, 10), width=2)
                           
    hole_cx = x0 + w // 2
    hole_cy = y0 + int(h * 0.58)
    
    rosette_r1 = 38 * Q
    rosette_r2 = 30 * Q
    rosette_r3 = 24 * Q
    soundhole_r = 18 * Q
    
    draw.ellipse([hole_cx - rosette_r1, hole_cy - rosette_r1, hole_cx + rosette_r1, hole_cy + rosette_r1],
                 outline=(165, 100, 38), width=2)
    draw.ellipse([hole_cx - rosette_r2, hole_cy - rosette_r2, hole_cx + rosette_r2, hole_cy + rosette_r2],
                 outline=(190, 120, 45), width=2)
    draw.ellipse([hole_cx - rosette_r3, hole_cy - rosette_r3, hole_cx + rosette_r3, hole_cy + rosette_r3],
                 outline=(145, 85, 30), width=2)
                 
    for ang in range(0, 360, 15):
        rad = math.radians(ang)
        x1 = hole_cx + int(rosette_r3 * math.cos(rad))
        y1 = hole_cy + int(rosette_r3 * math.sin(rad))
        x2 = hole_cx + int(rosette_r2 * math.cos(rad))
        y2 = hole_cy + int(rosette_r2 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=pyro_color, width=2)
        
    draw.ellipse([hole_cx - soundhole_r, hole_cy - soundhole_r, hole_cx + soundhole_r, hole_cy + soundhole_r],
                 fill=(16, 9, 6), outline=(75, 38, 16), width=3)
    draw.arc([hole_cx - soundhole_r + 2, hole_cy - soundhole_r + 2, hole_cx + soundhole_r - 2, hole_cy + soundhole_r - 2],
             45, 135, fill=(125, 70, 30), width=2)
             
    bridge_y = y0 + 14 * Q
    bridge_w = w - 40 * Q
    bridge_x = x0 + 20 * Q
    
    draw.rectangle([bridge_x, bridge_y, bridge_x + bridge_w, bridge_y + 16 * Q],
                   fill=(48, 24, 12), outline=(25, 12, 6), width=2)
                   
    bar_y = bridge_y + 4 * Q
    draw.rectangle([bridge_x + 4 * Q, bar_y, bridge_x + bridge_w - 4 * Q, bar_y + 7 * Q],
                   fill=(145, 150, 160), outline=(85, 90, 98), width=2)
    draw.line([(bridge_x + 5 * Q, bar_y + 2 * Q), (bridge_x + bridge_w - 5 * Q, bar_y + 2 * Q)],
              fill=(215, 220, 230), width=2)
              
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
        
        draw.rectangle([tx + 2 * Q, tine_top + 4 * Q, tx + tw + 2 * Q, tine_bot + 2 * Q], fill=(25, 14, 8))
        
        for col in range(tw):
            ratio = col / float(tw)
            shine = math.sin(ratio * math.pi)
            sr = int(172 + 76 * shine)
            sg = int(178 + 76 * shine)
            sb = int(188 + 66 * shine)
            draw.line([(tx + col, tine_top), (tx + col, tine_bot)], fill=(sr, sg, sb))
            
        draw.rectangle([tx, tine_top, tx + tw, tine_bot], outline=(100, 105, 115), width=1)
        draw.rounded_rectangle([tx, tine_bot - 4 * Q, tx + tw, tine_bot + 3 * Q],
                               radius=2 * Q, fill=(225, 230, 240), outline=(110, 115, 125), width=1)
                               
        if dist % 2 == 0:
            mark_y = tine_bot - 10 * Q
            draw.ellipse([tx + tw // 2 - 2 * Q, mark_y - 2 * Q, tx + tw // 2 + 2 * Q, mark_y + 2 * Q],
                         fill=(195, 145, 45), outline=(90, 60, 20), width=1)
                         
    draw.rectangle([bridge_x + 4 * Q, bar_y, bridge_x + bridge_w - 4 * Q, bar_y + 6 * Q],
                   fill=(135, 140, 150), outline=(65, 70, 78), width=2)
    draw.line([(bridge_x + 5 * Q, bar_y + 2 * Q), (bridge_x + bridge_w - 5 * Q, bar_y + 2 * Q)],
              fill=(208, 212, 222), width=2)
              
    bolt_count = 7
    bolt_step = (bridge_w - 16 * Q) / float(bolt_count - 1)
    for b in range(bolt_count):
        bx = int(bridge_x + 8 * Q + b * bolt_step)
        by = bar_y + int(3.0 * Q)
        draw.ellipse([bx - 3 * Q, by - 3 * Q, bx + 3 * Q, by + 3 * Q], fill=(215, 175, 65), outline=(75, 55, 15), width=1)
        draw.line([(bx - 2 * Q, by), (bx + 2 * Q, by)], fill=(40, 25, 10), width=1)
        
    plaque_y = y0 + h - 22 * Q
    draw.rectangle([x0 + 15 * Q, plaque_y, x0 + w - 15 * Q, y0 + h - 4 * Q], fill=(28, 16, 10), outline=gold, width=2)
    draw.rectangle([x0 + 17 * Q, plaque_y + 2 * Q, x0 + w - 17 * Q, y0 + h - 6 * Q], outline=pyro_color, width=1)
    font_p = get_font(FONT_DIN_COND, 11)
    font_sub = get_font(FONT_DIN_ALT, 6.0)
    draw.text((x0 + w // 2, plaque_y + 6 * Q), "KALIMBA ARTISAN 17", fill=gold, font=font_p, anchor="mm")
    draw.text((x0 + w // 2, plaque_y + 13 * Q), "SOLID SCULPTED ACACIA SOUNDBOX & POLISHED SPRING-STEEL TINES",
              fill=(230, 205, 165), font=font_sub, anchor="mm")


def render_model_art():
    """Render the 4-frame ModelArt filmstrip (1200x1920 in HD, 240x384 in 1x)."""
    fw = 240 * Q  # 1200 px
    fh = 96 * Q   # 480 px
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
    print("Rendered ModelArt.png successfully (4 luxury African native art frames)!")

# -------------------------------------------------------------------------
# Front Panel Components: Bar Schematic, Tube Grill, Meter Tower
# -------------------------------------------------------------------------

def draw_bar_schematic(draw, x_u, y_u, w_u, h_u):
    """
    Laser-etched technical diagram of acoustic tone bar physics:
    Hand-carved undercut parabolic arch, nodal suspension points at 0.224 L,
    Quarter-wave acoustic resonator tube with African geometric relief bands.
    """
    x = x_u * Q
    y = y_u * Q
    w = w_u * Q
    h = h_u * Q
    gold = (218, 175, 55)
    dim_gold = (140, 110, 45)
    
    draw.rectangle([x, y, x + w, y + h], fill=(16, 18, 20), outline=(42, 46, 50), width=1)
    font_tiny = get_font(FONT_DIN_ALT, 5.0)
    
    bar_y = y + int(h * 0.44)
    bar_w = int(w * 0.70)
    bx0 = x + (w - bar_w) // 2
    bx1 = bx0 + bar_w
    bar_h = 4 * Q
    
    draw.rectangle([bx0, bar_y - bar_h, bx1, bar_y], fill=(48, 30, 20), outline=gold, width=1)
    arch_cx = bx0 + bar_w // 2
    arch_rx = int(bar_w * 0.28)
    draw.arc([arch_cx - arch_rx, bar_y - 3 * Q, arch_cx + arch_rx, bar_y + 3 * Q], 0, 180, fill=(16, 18, 20), width=2)
    
    node1_x = int(bx0 + bar_w * 0.224)
    node2_x = int(bx1 - bar_w * 0.224)
    for nx in [node1_x, node2_x]:
        draw.ellipse([nx - 2 * Q, bar_y - bar_h // 2 - 2 * Q, nx + 2 * Q, bar_y - bar_h // 2 + 2 * Q], fill=(235, 190, 70))
        draw.line([(nx, bar_y - bar_h - 2 * Q), (nx, bar_y + 2 * Q)], fill=(215, 170, 50), width=1)
        
    draw.line([(arch_cx, bar_y - bar_h - 4 * Q), (arch_cx, bar_y - bar_h)], fill=(245, 225, 110), width=2)
    draw.polygon([(arch_cx - 2 * Q, bar_y - bar_h - 2 * Q),
                  (arch_cx + 2 * Q, bar_y - bar_h - 2 * Q),
                  (arch_cx, bar_y - bar_h)], fill=(245, 225, 110))
                  
    pipe_w = int(bar_w * 0.34)
    px0 = arch_cx - pipe_w // 2
    px1 = arch_cx + pipe_w // 2
    py0 = bar_y + 2 * Q
    py1 = y + h - 3 * Q
    draw.line([(px0, py0), (px0, py1)], fill=gold, width=2)
    draw.line([(px1, py0), (px1, py1)], fill=gold, width=2)
    draw.arc([px0, py1 - 3 * Q, px1, py1 + 3 * Q], 0, 180, fill=gold, width=2)
    
    ring_y = py0 + 4 * Q
    draw.line([(px0, ring_y), (px1, ring_y)], fill=dim_gold, width=1)
    
    draw.text((x + 6 * Q, y + h // 2), "NODAL SUSPENSION (0.224 L)", fill=dim_gold, font=font_tiny, anchor="lm")
    draw.text((x + w - 6 * Q, y + h // 2), "1/4 WAVE ACOUSTIC RESONATOR", fill=dim_gold, font=font_tiny, anchor="rm")


def draw_tube_grill(draw, x0, y0, w, h):
    """Warm vacuum tube ventilation grill with African geometric brass mesh & incandescent glow."""
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=3 * Q, fill=(14, 10, 8), outline=(55, 42, 32), width=1)
    cx = x0 + w // 2
    cy = y0 + h // 2
    
    for r in range(int(h * 0.6), 2, -int(3 * Q)):
        alpha_ratio = (1.0 - r / (h * 0.6))
        gr = int(245 * alpha_ratio)
        gg = int(130 * alpha_ratio)
        gb = int(25 * alpha_ratio)
        draw.ellipse([cx - r * 2, cy - r, cx + r * 2, cy + r], fill=(gr, gg, gb))
        
    draw.ellipse([cx - 4 * Q, cy - 2 * Q, cx + 4 * Q, cy + 2 * Q], fill=(255, 238, 180))
    draw.line([(cx - 6 * Q, cy), (cx + 6 * Q, cy)], fill=(255, 245, 210), width=2)
    
    mesh_step = 6 * Q
    for mx in range(x0 + 4 * Q, x0 + w - 4 * Q, mesh_step):
        draw.line([(mx, y0 + 2 * Q), (mx + 3 * Q, y0 + h - 2 * Q)], fill=(75, 55, 35), width=1)
        draw.line([(mx + 3 * Q, y0 + 2 * Q), (mx, y0 + h - 2 * Q)], fill=(75, 55, 35), width=1)


def draw_led_ladder(draw, x0, y0, w, h):
    """8-segment Gain Reduction LED ladder for dynamics compressor with gold bezel."""
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=2 * Q, fill=(12, 14, 16), outline=(218, 175, 55), width=1)
    font_micro = get_font(FONT_DIN_ALT, 5.0)
    draw.text((x0 + 4 * Q, y0 + h // 2), "GR", fill=(218, 175, 55), font=font_micro, anchor="lm")
    
    leds = [
        ("0", (40, 180, 70)),
        ("-1", (40, 180, 70)),
        ("-2", (40, 180, 70)),
        ("-4", (220, 160, 40)),
        ("-8", (220, 160, 40)),
        ("-12", (220, 60, 40)),
        ("-16", (220, 40, 40))
    ]
    num_leds = len(leds)
    led_w = 4 * Q
    led_h = h - 6 * Q
    avail_x = w - 24 * Q
    step = avail_x / float(num_leds)
    start_x = x0 + 16 * Q
    
    for i, (lbl, color) in enumerate(leds):
        lx = int(start_x + i * step)
        ly = y0 + 3 * Q
        draw.rectangle([lx, ly, lx + led_w, ly + led_h], fill=color, outline=(18, 20, 22), width=1)
        draw.line([(lx + 1, ly + 1), (lx + led_w - 1, ly + 1)], fill=(255, 255, 255), width=1)


def draw_stereo_meter_tower(draw, x0, y0, w, h):
    """Precision calibrated vertical Stereo Peak & RMS LED meter column with gold bezel."""
    gold = (218, 175, 55)
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=3 * Q, fill=(14, 15, 17), outline=gold, width=1)
    draw.rounded_rectangle([x0 + 2, y0 + 2, x0 + w - 2, y0 + h - 2], radius=2 * Q, outline=(20, 22, 25), width=1)
    
    font_meter = get_font(FONT_DIN_ALT, 5.0)
    font_title = get_font(FONT_DIN_COND, 7.0)
    
    draw.text((x0 + w // 2, y0 + 6 * Q), "STEREO VU", fill=gold, font=font_title, anchor="mm")
    
    clip_y = y0 + 12 * Q
    draw.ellipse([x0 + 6 * Q, clip_y - 2 * Q, x0 + 10 * Q, clip_y + 2 * Q], fill=(230, 40, 30), outline=(100, 20, 15), width=1)
    draw.ellipse([x0 + w - 10 * Q, clip_y - 2 * Q, x0 + w - 6 * Q, clip_y + 2 * Q], fill=(230, 40, 30), outline=(100, 20, 15), width=1)
    draw.text((x0 + w // 2, clip_y), "CLIP", fill=(220, 60, 50), font=get_font(FONT_DIN_ALT, 4.5), anchor="mm")
    
    segments = [
        ("+3", (230, 40, 30)),
        ("0",  (230, 70, 30)),
        ("-3", (230, 160, 40)),
        ("-6", (220, 180, 45)),
        ("-12", (45, 190, 75)),
        ("-18", (40, 170, 70)),
        ("-24", (35, 150, 65)),
        ("-36", (30, 120, 55)),
    ]
    num_segs = len(segments)
    top_seg_y = y0 + 17 * Q
    bot_seg_y = y0 + h - 14 * Q
    seg_step = (bot_seg_y - top_seg_y) / float(num_segs - 1)
    
    bar_w = 6 * Q
    bar_h = 3 * Q
    for i, (lbl, color) in enumerate(segments):
        sy = int(top_seg_y + i * seg_step)
        lx = x0 + 5 * Q
        draw.rectangle([lx, sy, lx + bar_w, sy + bar_h], fill=color, outline=(15, 16, 18), width=1)
        draw.line([(lx + 1, sy + 1), (lx + bar_w - 1, sy + 1)], fill=(255, 255, 255), width=1)
        
        rx = x0 + w - 5 * Q - bar_w
        draw.rectangle([rx, sy, rx + bar_w, sy + bar_h], fill=color, outline=(15, 16, 18), width=1)
        draw.line([(rx + 1, sy + 1), (rx + bar_w - 1, sy + 1)], fill=(255, 255, 255), width=1)
        
        draw.text((x0 + w // 2, sy + bar_h // 2), lbl, fill=(160, 165, 170), font=font_meter, anchor="mm")
        
    draw.text((x0 + 8 * Q, y0 + h - 5 * Q), "L", fill=gold, font=font_meter, anchor="mm")
    draw.text((x0 + w - 8 * Q, y0 + h - 5 * Q), "R", fill=gold, font=font_meter, anchor="mm")
    draw.text((x0 + w // 2, y0 + h - 5 * Q), "dB", fill=(130, 135, 140), font=font_meter, anchor="mm")

# -------------------------------------------------------------------------
# Front Panel Main Renderer
# -------------------------------------------------------------------------

def render_front_panel():
    """
    Render 5U Rack Extension Front Panel at 3770x1725 (5x HD) and 754x345 (1x GUI2D).
    Features:
    - African Wenge rack ear cheeks with vertical laser-inlaid gold Kuba diamond ribbons.
    - Continuous gold & bronze Kuba geometric frieze borders running across top and bottom.
    - Royal Ashanti/Adinkra gold crest medallion on brand plate.
    - Luxury typography with gold drop shadow and filigree framing.
    - African stepped corner brackets on all sub-chassis bays.
    """
    panel = create_luxury_obsidian_plate_texture(HD_WIDTH, HD_HEIGHT)
    
    ear_w = 22 * Q  # 110 px
    wenge_left = create_african_wenge_texture(ear_w, HD_HEIGHT)
    wenge_right = create_african_wenge_texture(ear_w, HD_HEIGHT)
    panel.paste(wenge_left, (0, 0))
    panel.paste(wenge_right, (HD_WIDTH - ear_w, 0))
    
    draw = ImageDraw.Draw(panel)
    gold = (218, 175, 55)
    gold_bright = (235, 190, 70)
    bronze = (145, 105, 40)
    white_ink = (245, 245, 245)
    dim_ink = (150, 155, 160)
    
    draw_kuba_band(draw, 4 * Q, 25 * Q, 14 * Q, HD_HEIGHT - 50 * Q, gold=gold, bronze=bronze, vertical=True)
    draw_kuba_band(draw, HD_WIDTH - ear_w + 4 * Q, 25 * Q, 14 * Q, HD_HEIGHT - 50 * Q, gold=gold, bronze=bronze, vertical=True)
    
    draw.line([(ear_w - 1, 0), (ear_w - 1, HD_HEIGHT)], fill=(12, 13, 14), width=3)
    draw.line([(ear_w + 1, 0), (ear_w + 1, HD_HEIGHT)], fill=gold, width=2)
    draw.line([(HD_WIDTH - ear_w - 2, 0), (HD_WIDTH - ear_w - 2, HD_HEIGHT)], fill=gold, width=2)
    draw.line([(HD_WIDTH - ear_w, 0), (HD_WIDTH - ear_w, HD_HEIGHT)], fill=(12, 13, 14), width=3)
    
    screw_ys = [18 * Q, 80 * Q, 172 * Q, 264 * Q, 326 * Q]
    for sy in screw_ys:
        draw_screw(draw, ear_w // 2, sy, 8 * Q, is_brass=True)
        draw_screw(draw, HD_WIDTH - ear_w // 2, sy, 8 * Q, is_brass=True)
        
    frieze_h = 6 * Q
    frieze_x0 = ear_w + 4
    frieze_w = HD_WIDTH - 2 * ear_w - 8
    draw_kuba_band(draw, frieze_x0, 2 * Q, frieze_w, frieze_h, gold=gold, bronze=bronze)
    draw_kuba_band(draw, frieze_x0, HD_HEIGHT - 8 * Q, frieze_w, frieze_h, gold=gold, bronze=bronze)
    
    draw.rectangle([ear_w + 3, 3, HD_WIDTH - ear_w - 4, HD_HEIGHT - 4], outline=(55, 60, 65), width=2)
    
    header_h = 46 * Q
    header_x0 = ear_w + 6
    header_w = HD_WIDTH - 2 * ear_w - 12
    draw.rectangle([header_x0, 8 * Q, header_x0 + header_w, header_h], fill=(22, 24, 26), outline=(42, 45, 48), width=2)
    draw.line([(header_x0, header_h), (header_x0 + header_w, header_h)], fill=gold, width=2)
    
    font_brand = get_font(FONT_DIN_COND, 13)
    font_logo = get_font(FONT_DIN_COND, 28)
    font_sub = get_font(FONT_DIN_ALT, 7.5)
    
    bp_x = header_x0 + 10 * Q
    bp_y = 13 * Q
    bp_w = 82 * Q
    bp_h = 24 * Q
    draw.rectangle([bp_x, bp_y, bp_x + bp_w, bp_y + bp_h], fill=(36, 28, 18), outline=gold, width=2)
    draw.rectangle([bp_x + 2 * Q, bp_y + 2 * Q, bp_x + bp_w - 2 * Q, bp_y + bp_h - 2 * Q], outline=bronze, width=1)
    
    draw_african_crest(draw, bp_x + 12 * Q, bp_y + bp_h // 2, 8 * Q, gold=gold_bright, dark_fill=(28, 20, 12))
    draw.text((bp_x + 48 * Q, bp_y + bp_h // 2), "PROTOCODUS", fill=gold_bright, font=font_brand, anchor="mm")
    
    draw.text((header_x0 + 104 * Q + 2, 25 * Q + 2), "MAREMBA", fill=(10, 11, 12), font=font_logo, anchor="lm")
    draw.text((header_x0 + 104 * Q, 25 * Q), "MAREMBA", fill=gold_bright, font=font_logo, anchor="lm")
    draw.text((header_x0 + 208 * Q, 25 * Q), "ACOUSTIC MODAL SYNTHESIS INSTRUMENT", fill=dim_ink, font=font_sub, anchor="lm")
    
    px = 380 * Q
    py = 14 * Q
    pw = 190 * Q
    ph = 18 * Q
    draw.rectangle([px - 4, py - 4, px + pw + 4, py + ph + 4], fill=(12, 13, 14), outline=gold, width=2)
    draw.rectangle([px, py, px + pw, py + ph], fill=(8, 9, 10))
    for cx, cy in [(px - 2, py - 2), (px + pw + 2, py - 2), (px - 2, py + ph + 2), (px + pw + 2, py + ph + 2)]:
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=gold)
        
    lx = 692 * Q + 25
    ly = 16 * Q + 25
    draw.ellipse([lx - 28, ly - 28, lx + 28, ly + 28], fill=(48, 40, 26), outline=gold, width=2)
    draw.text((680 * Q, 25 * Q), "NOTE", fill=dim_ink, font=font_sub, anchor="rm")
    
    def draw_section_bay(x_u, y_u, w_u, h_u, title_text, accent_color=gold):
        x = x_u * Q
        y = y_u * Q
        w = w_u * Q
        h = h_u * Q
        draw_recessed_bay(draw, x, y, w, h, fill_color=(18, 20, 22), outline_color=(45, 48, 52), bevel_width=3, gold_accent=True)
        draw.rectangle([x, y, x + w, y + 20 * Q], fill=(28, 30, 34), outline=(48, 52, 56), width=1)
        draw.line([(x + 2, y + 1), (x + w - 2, y + 1)], fill=accent_color, width=2)
        font_sec = get_font(FONT_DIN_COND, 11.5)
        draw.text((x + w // 2, y + 10 * Q), title_text, fill=accent_color, font=font_sec, anchor="mm")
        
        bs = 18 * Q
        draw_african_corner_bracket(draw, x + 2 * Q, y + 2 * Q, bs, 1, 1, accent_color, bronze)
        draw_african_corner_bracket(draw, x + w - 2 * Q, y + 2 * Q, bs, -1, 1, accent_color, bronze)
        draw_african_corner_bracket(draw, x + 2 * Q, y + h - 2 * Q, bs, 1, -1, accent_color, bronze)
        draw_african_corner_bracket(draw, x + w - 2 * Q, y + h - 2 * Q, bs, -1, -1, accent_color, bronze)
        
    draw_section_bay(24, 52, 252, 284, "ACOUSTIC MODEL & SYMPATHETIC MASS", gold)
    draw_section_bay(282, 52, 228, 284, "PHYSICAL RESONATOR CORE", (225, 160, 50))
    draw_section_bay(516, 52, 214, 284, "STUDIO CAPTURE & MASTER DYNAMICS", (80, 190, 220))
    
    # Section 1
    art_x = 30 * Q
    art_y = 76 * Q
    art_w = 240 * Q
    art_h = 96 * Q
    draw.rectangle([art_x - 4, art_y - 4, art_x + art_w + 4, art_y + art_h + 4], fill=(32, 24, 16), outline=gold, width=2)
    draw.rectangle([art_x - 1, art_y - 1, art_x + art_w + 1, art_y + art_h + 1], outline=(15, 16, 17), width=2)
    for bx, by in [(art_x - 2, art_y - 2), (art_x + art_w + 2, art_y - 2),
                   (art_x - 2, art_y + art_h + 2), (art_x + art_w + 2, art_y + art_h + 2)]:
        draw.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=gold)
        
    font_lbl = get_font(FONT_DIN_ALT, 8)
    font_lbl_sm = get_font(FONT_DIN_ALT, 6.5)
    
    models_info = [
        (34, "ROSEWOOD", (48, 22, 16), (245, 175, 45)),
        (94, "PADAUK", (54, 24, 14), (235, 75, 40)),
        (154, "BALAFON", (26, 36, 20), (65, 215, 85)),
        (214, "KALIMBA", (52, 36, 16), (255, 215, 65)),
    ]
    for rx, label, btn_fill, led_glow in models_info:
        rpx = rx * Q
        rpy = 178 * Q
        draw.rounded_rectangle([rpx - 2 * Q, rpy - 2 * Q, rpx + 16 * Q, rpy + 18 * Q], radius=2 * Q,
                               fill=btn_fill, outline=(55, 58, 62), width=1)
        draw.ellipse([rpx + 18 * Q, rpy + 4 * Q, rpx + 22 * Q, rpy + 8 * Q], fill=led_glow, outline=(15, 16, 18), width=1)
        draw.text((rpx + 25 * Q, rpy + 8 * Q), label, fill=white_ink, font=font_lbl_sm, anchor="lm")
        
    draw_recessed_bay(draw, 28 * Q, 196 * Q, 244 * Q, 124 * Q, fill_color=(17, 18, 20), outline_color=(40, 44, 48), bevel_width=2)
    
    s1_knobs = [
        (42, 200, "SYMPATHETIC", True, "0", "10"),
        (124, 200, "BODY BLOOM", True, "0", "10"),
        (206, 200, "PITCH GLIDE", True, "0", "50c"),
        (42, 262, "MALLET ROLL", True, "5Hz", "25Hz"),
        (124, 262, "MIRLITON BUZZ", False, "0%", "100%"),
        (206, 262, "ARTIFACTS", False, "CLEAN", "RAW"),
    ]
    for kx, ky, name, is_gold, mi, mx in s1_knobs:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_ticks_labeled(draw, cx, cy, radius=132, active_color=gold_bright if is_gold else white_ink,
                                min_lbl=mi, mid_lbl=None, max_lbl=mx)
        draw.text((cx, (ky + 54) * Q), name, fill=gold_bright if is_gold else white_ink, font=font_lbl, anchor="mm")
        
    pl_x = 30 * Q
    pl_y = 323 * Q
    pl_w = 240 * Q
    pl_h = 10 * Q
    draw.rectangle([pl_x, pl_y, pl_x + pl_w, pl_y + pl_h], fill=(28, 22, 16), outline=gold, width=1)
    draw.text((pl_x + pl_w // 2, pl_y + pl_h // 2), "PROTOCODUS ACOUSTICS - 8 PITCHED MODES & ANISOTROPIC SPLIT",
              fill=gold_bright, font=get_font(FONT_DIN_ALT, 5.5), anchor="mm")
              
    # Section 2
    draw_recessed_bay(draw, 286 * Q, 74 * Q, 220 * Q, 66 * Q, fill_color=(17, 18, 20), outline_color=(40, 44, 48), bevel_width=2)
    
    st_cx = (294 + 26) * Q
    st_cy = (80 + 26) * Q
    draw_knob_dial_ticks(draw, st_cx, st_cy, radius=126, start_angle_deg=225, sweep_deg=270, num_ticks=4,
                         active_color=gold_bright, dim_color=gold_bright)
    striker_steps = [
        (225, "1"),
        (135, "2"),
        (45, "3"),
        (-45, "4")
    ]
    font_step_num = get_font(FONT_DIN_COND, 8.5)
    for ang, num_str in striker_steps:
        rad = math.radians(ang)
        tx = st_cx + math.cos(rad) * 144
        ty = st_cy - math.sin(rad) * 144
        draw.text((tx, ty), num_str, fill=gold_bright, font=font_step_num, anchor="mm")
        
    draw.text((st_cx, (80 + 53) * Q), "STRIKER", fill=gold_bright, font=font_lbl, anchor="mm")
    draw.text((st_cx, (80 + 58) * Q), "MALLET (1-4)", fill=(200, 165, 85), font=get_font(FONT_DIN_ALT, 4.8), anchor="mm")

    s2_row1 = [
        (347, 80, "HARDNESS", "SOFT", "HARD"),
        (400, 80, "POSITION", "CTR", "EDGE"),
        (453, 80, "VARIANCE", "0%", "100%")
    ]
    for kx, ky, name, mi, mx in s2_row1:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_ticks_labeled(draw, cx, cy, radius=126, active_color=gold_bright, min_lbl=mi, mid_lbl=None, max_lbl=mx)
        draw.text((cx, (ky + 54) * Q), name, fill=white_ink, font=font_lbl, anchor="mm")

    draw_bar_schematic(draw, 288, 145, 216, 12)
    
    s2_row2 = [
        (298, 160, "RESONATOR", "-50c", "+50c"),
        (369, 160, "COUPLING", "0%", "100%"),
        (440, 160, "BAR DECAY", "0.1s", "5.0s")
    ]
    for kx, ky, name, mi, mx in s2_row2:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_ticks_labeled(draw, cx, cy, radius=132, active_color=gold_bright, min_lbl=mi, mid_lbl=None, max_lbl=mx)
        draw.text((cx, (ky + 54) * Q), name, fill=white_ink, font=font_lbl, anchor="mm")

    draw.rectangle([288 * Q, 222 * Q, 504 * Q, 240 * Q], fill=(16, 17, 19), outline=gold, width=1)
    draw.text((396 * Q, 231 * Q), "1: SOFT YARN/FLESH   |   2: MEDIUM CORD/THUMB   |   3: HARD RUBBER/NAIL   |   4: WOOD/PICK",
              fill=(190, 195, 200), font=get_font(FONT_DIN_ALT, 4.8), anchor="mm")

    s2_row3 = [
        (298, 246, "POLYPHONY", "8", "32"),
        (369, 246, "OVERSAMPLE", "2x", "8x"),
        (440, 246, "VELOCITY", "SOFT", "EXP")
    ]
    for kx, ky, name, mi, mx in s2_row3:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_ticks_labeled(draw, cx, cy, radius=132, active_color=white_ink, min_lbl=mi, mid_lbl=None, max_lbl=mx)
        draw.text((cx, (ky + 54) * Q), name, fill=white_ink, font=font_lbl, anchor="mm")
        
    draw.text((396 * Q, 323 * Q), "QUARTER-WAVE RESONATOR COUPLING - ASYMMETRIC HERTZIAN CONTACT",
              fill=(135, 140, 145), font=get_font(FONT_DIN_ALT, 5.5), anchor="mm")

    # Section 3
    s3_row1 = [
        (522, 80, "CLOSE"),
        (576, 80, "FAR ROOM"),
        (630, 80, "PIEZO"),
        (682, 80, "STEREO WIDTH")
    ]
    for kx, ky, name in s3_row1:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_dial_ticks(draw, cx, cy, radius=125, active_color=(90, 190, 220))
        draw.text((cx, (ky + 54) * Q), name, fill=(180, 220, 240), font=font_lbl_sm, anchor="mm")

    draw_tube_grill(draw, 524 * Q, 142 * Q, 58 * Q, 14 * Q)
    draw_led_ladder(draw, 626 * Q, 142 * Q, 96 * Q, 14 * Q)
    
    s3_row2 = [
        (522, 160, "DRIVE"),
        (576, 160, "WARMTH"),
        (630, 160, "COMPRESSOR"),
        (682, 160, "RELEASE")
    ]
    for kx, ky, name in s3_row2:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_dial_ticks(draw, cx, cy, radius=125, active_color=(235, 155, 50))
        draw.text((cx, (ky + 54) * Q), name, fill=(245, 215, 175), font=font_lbl_sm, anchor="mm")

    draw.rectangle([520 * Q, 222 * Q, 690 * Q, 238 * Q], fill=(16, 17, 19), outline=gold, width=1)
    draw.text((605 * Q, 230 * Q), "STEREO MASTER BUS - ANALOG SATURATION & VCA", fill=gold_bright,
              font=get_font(FONT_DIN_COND, 8.5), anchor="mm")

    s3_row3 = [
        (522, 246, "KEY DETUNE"),
        (576, 246, "MASTER TUNE")
    ]
    for kx, ky, name in s3_row3:
        cx = (kx + 26) * Q
        cy = (ky + 26) * Q
        draw_knob_dial_ticks(draw, cx, cy, radius=125, num_ticks=11, active_color=gold_bright, dim_color=(120, 125, 130))
        draw.text((cx, (ky + 54) * Q), name, fill=gold_bright, font=font_lbl_sm, anchor="mm")
        
    vcx = (642 + 26) * Q
    vcy = (246 + 26) * Q
    draw_knob_ticks_labeled(draw, vcx, vcy, radius=142, num_ticks=15, active_color=gold_bright,
                            min_lbl="-inf", mid_lbl=None, max_lbl="+6dB")
    font_vol = get_font(FONT_DIN_COND, 10.5)
    draw.text((vcx, (246 + 55) * Q), "MASTER LEVEL", fill=gold_bright, font=font_vol, anchor="mm")
    
    draw_stereo_meter_tower(draw, 696 * Q, 242 * Q, 30 * Q, 88 * Q)
    
    panel.save(HD / "Reason_GUI_front_root_Panel.png")
    panel_1x = panel.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    panel_1x.save(GUI2D / "Reason_GUI_front_root_Panel.png")
    print("Rendered Reason_GUI_front_root_Panel.png (3770x1725 & 754x345) successfully!")

# -------------------------------------------------------------------------
# Back Panel Main Renderer
# -------------------------------------------------------------------------

def render_back_panel():
    """
    Render 5U Rear Panel with dark steel texture, gold African geometric border,
    and gold-plated balanced output & CV modulation socket bezels.
    """
    panel = create_steel_back_texture(HD_WIDTH, HD_HEIGHT)
    draw = ImageDraw.Draw(panel)
    gold = (218, 175, 55)
    bronze = (145, 105, 40)
    white = (240, 240, 240)
    
    ear_w = 22 * Q
    screw_ys = [18 * Q, 80 * Q, 172 * Q, 264 * Q, 326 * Q]
    for sy in screw_ys:
        draw_screw(draw, ear_w // 2, sy, 8 * Q, is_brass=True)
        draw_screw(draw, HD_WIDTH - ear_w // 2, sy, 8 * Q, is_brass=True)
        
    draw_kuba_band(draw, ear_w + 4 * Q, 3 * Q, HD_WIDTH - 2 * ear_w - 8 * Q, 6 * Q, gold=gold, bronze=bronze)
    draw_kuba_band(draw, ear_w + 4 * Q, HD_HEIGHT - 9 * Q, HD_WIDTH - 2 * ear_w - 8 * Q, 6 * Q, gold=gold, bronze=bronze)
    
    draw_screw(draw, ear_w + 20 * Q, 32 * Q, 10 * Q, angle_deg=60, is_brass=True)
    draw.text((ear_w + 35 * Q, 32 * Q), "CHASSIS GROUND", fill=(130, 135, 140), font=get_font(FONT_DIN_ALT, 7), anchor="lm")
    
    font_title = get_font(FONT_DIN_COND, 20)
    font_lbl = get_font(FONT_DIN_ALT, 9)
    font_sm = get_font(FONT_DIN_ALT, 7.5)
    
    draw.text((HD_WIDTH // 2, 30 * Q), "PROTOCODUS - MAREMBA PHYSICAL MODELING REAR INTERFACE", fill=gold, font=font_title, anchor="mm")
    
    draw_recessed_bay(draw, 30 * Q, 60 * Q, 395 * Q, 270 * Q, fill_color=(16, 18, 20), outline_color=(50, 54, 58), bevel_width=3, gold_accent=True)
    draw.rectangle([30 * Q, 60 * Q, 425 * Q, 85 * Q], fill=(28, 31, 34), outline=(48, 52, 56), width=1)
    draw.text((227 * Q, 72 * Q), "MULTI-CHANNEL BALANCED AUDIO OUTPUTS", fill=gold, font=get_font(FONT_DIN_COND, 12), anchor="mm")
    
    draw_recessed_bay(draw, 435 * Q, 60 * Q, 289 * Q, 270 * Q, fill_color=(16, 18, 20), outline_color=(50, 54, 58), bevel_width=3, gold_accent=True)
    draw.rectangle([435 * Q, 60 * Q, 724 * Q, 85 * Q], fill=(28, 31, 34), outline=(48, 52, 56), width=1)
    draw.text((579 * Q, 72 * Q), "CONTROL VOLTAGE (CV) MODULATION INPUTS", fill=gold, font=get_font(FONT_DIN_COND, 12), anchor="mm")
    
    audio_sockets = [
        (60, 140, "MAIN L", "MASTER L"),
        (115, 140, "MAIN R", "MASTER R"),
        (185, 140, "CLOSE L", "DIRECT L"),
        (240, 140, "CLOSE R", "DIRECT R"),
        (305, 140, "FAR L", "DIFFUSE L"),
        (355, 140, "FAR R", "DIFFUSE R"),
        (385, 220, "PIEZO", "CONTACT"),
    ]
    for sx, sy, name, desc in audio_sockets:
        cx = sx * Q + 56
        cy = sy * Q + 60
        draw_socket_bezel(draw, cx, cy, is_audio=True)
        draw.text((cx, (sy + 26) * Q), name, fill=white, font=font_lbl, anchor="mm")
        draw.text((cx, (sy + 33) * Q), desc, fill=(130, 135, 140), font=font_sm, anchor="mm")
        
    draw.line([(60 * Q + 56, 115 * Q), (115 * Q + 56, 115 * Q)], fill=gold, width=2)
    draw.text(((60 + 115) // 2 * Q + 56, 108 * Q), "BALANCED STEREO", fill=gold, font=font_sm, anchor="mm")
    
    draw.line([(185 * Q + 56, 115 * Q), (240 * Q + 56, 115 * Q)], fill=(160, 165, 170), width=2)
    draw.text(((185 + 240) // 2 * Q + 56, 108 * Q), "STEREO PAIR", fill=(160, 165, 170), font=font_sm, anchor="mm")
    
    draw.line([(305 * Q + 56, 115 * Q), (355 * Q + 56, 115 * Q)], fill=(160, 165, 170), width=2)
    draw.text(((305 + 355) // 2 * Q + 56, 108 * Q), "STEREO PAIR", fill=(160, 165, 170), font=font_sm, anchor="mm")
    
    cv_sockets = [
        (465, 140, "NOTE CV", "1V / OCT"),
        (515, 140, "GATE CV", "TRIGGER"),
        (565, 140, "MALLET", "HARDNESS"),
        (615, 140, "POSITION", "STRIKE"),
        (665, 140, "COUPLING", "RESONATOR"),
        (465, 220, "SYMPATHETIC", "BODY MESH"),
        (565, 220, "ROLL CV", "TREMOLO"),
        (665, 220, "VOLUME CV", "AMPLITUDE"),
    ]
    for sx, sy, name, desc in cv_sockets:
        cx = sx * Q + 41
        cy = sy * Q + 47
        draw_socket_bezel(draw, cx, cy, is_audio=False)
        draw.text((cx, (sy + 24) * Q), name, fill=(225, 205, 120), font=font_lbl, anchor="mm")
        draw.text((cx, (sy + 31) * Q), desc, fill=(130, 135, 140), font=font_sm, anchor="mm")
        
    # Placeholder Bay: Clean recessed mounting bay at [55*Q, 225*Q, 355*Q, 325*Q]
    # Reason Acceptance Testing Guideline: ZERO text or graphics underneath placeholder widget!
    draw_recessed_bay(draw, 53 * Q, 223 * Q, 304 * Q, 104 * Q, fill_color=(14, 15, 17), outline_color=(40, 44, 48), bevel_width=2, gold_accent=False)

    # Vertical tape recess for device_name at [20*Q, 130*Q, 33*Q, 210*Q]
    draw.rectangle([19 * Q, 129 * Q, 34 * Q, 211 * Q], fill=(14, 15, 17), outline=(42, 46, 50), width=1)

    # Manufacturer & Certification Badge: Cleanly placed beneath CV modulation inputs
    draw.rectangle([452 * Q, 268 * Q, 708 * Q, 318 * Q], fill=(12, 13, 14), outline=gold, width=1)
    draw_african_crest(draw, 474 * Q, 293 * Q, 13 * Q, gold=gold, dark_fill=(20, 16, 12))
    draw.text((495 * Q, 279 * Q), "cz.protocodus.Maremba  |  PHYSICAL MODELING SYNTHESIZER", fill=(215, 215, 220), font=font_sm, anchor="lm")
    draw.text((495 * Q, 293 * Q), "MADE IN REASON STUDIOS RACK EXTENSION  |  PRO-AUDIO CLASS A", fill=(140, 145, 150), font=font_sm, anchor="lm")
    draw.text((495 * Q, 307 * Q), "CE / RoHS COMPLIANT - 100% REAL-TIME DSP SYNTHESIS ENGINE", fill=gold, font=font_sm, anchor="lm")
    
    panel.save(HD / "Reason_GUI_back_root_Panel.png")
    panel_1x = panel.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    panel_1x.save(GUI2D / "Reason_GUI_back_root_Panel.png")
    print("Rendered Reason_GUI_back_root_Panel.png (3770x1725 & 754x345) successfully!")

# -------------------------------------------------------------------------
# Folded Panels (3770x150 HD / 754x30 1x)
# -------------------------------------------------------------------------

def render_folded_panels():
    gold = (218, 175, 55)
    bronze = (145, 105, 40)
    
    panel_f = create_luxury_obsidian_plate_texture(HD_WIDTH, HD_FOLDED_H)
    ear_w = 22 * Q
    wenge_l = create_african_wenge_texture(ear_w, HD_FOLDED_H)
    wenge_r = create_african_wenge_texture(ear_w, HD_FOLDED_H)
    panel_f.paste(wenge_l, (0, 0))
    panel_f.paste(wenge_r, (HD_WIDTH - ear_w, 0))
    
    draw_f = ImageDraw.Draw(panel_f)
    draw_f.rectangle([0, 0, HD_WIDTH - 1, HD_FOLDED_H - 1], outline=(55, 60, 65), width=2)
    draw_screw(draw_f, ear_w // 2, HD_FOLDED_H // 2, 7 * Q, is_brass=True)
    draw_screw(draw_f, HD_WIDTH - ear_w // 2, HD_FOLDED_H // 2, 7 * Q, is_brass=True)
    
    draw_kuba_band(draw_f, ear_w + 6 * Q, 1 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 5 * Q, gold=gold, bronze=bronze)
    draw_kuba_band(draw_f, ear_w + 6 * Q, HD_FOLDED_H - 6 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 5 * Q, gold=gold, bronze=bronze)
    
    draw_african_crest(draw_f, ear_w + 14 * Q, HD_FOLDED_H // 2, 9 * Q, gold=gold, dark_fill=(28, 20, 12))
    font_logo = get_font(FONT_DIN_COND, 16)
    draw_f.text((ear_w + 28 * Q, HD_FOLDED_H // 2), "PROTOCODUS - MAREMBA", fill=gold, font=font_logo, anchor="lm")
    
    px = 380 * Q
    py = 6 * Q
    pw = 190 * Q
    ph = 18 * Q
    draw_f.rectangle([px - 2, py - 2, px + pw + 2, py + ph + 2], fill=(10, 11, 12), outline=gold, width=2)
    draw_f.rectangle([px, py, px + pw, py + ph], fill=(6, 7, 8))
    
    draw_f.ellipse([692 * Q + 10, 9 * Q + 10, 692 * Q + 40, 9 * Q + 40], outline=gold, width=2)
    
    panel_f.save(HD / "Reason_GUI_folded_front_root_Panel.png")
    panel_f_1x = panel_f.resize((WIDTH, FOLDED_HEIGHT), Image.Resampling.LANCZOS)
    panel_f_1x.save(GUI2D / "Reason_GUI_folded_front_root_Panel.png")
    
    panel_b = create_steel_back_texture(HD_WIDTH, HD_FOLDED_H)
    draw_b = ImageDraw.Draw(panel_b)
    draw_b.rectangle([0, 0, HD_WIDTH - 1, HD_FOLDED_H - 1], outline=(55, 60, 65), width=2)
    draw_screw(draw_b, ear_w // 2, HD_FOLDED_H // 2, 7 * Q, is_brass=True)
    draw_screw(draw_b, HD_WIDTH - ear_w // 2, HD_FOLDED_H // 2, 7 * Q, is_brass=True)
    
    draw_kuba_band(draw_b, ear_w + 6 * Q, 1 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 5 * Q, gold=gold, bronze=bronze)
    draw_kuba_band(draw_b, ear_w + 6 * Q, HD_FOLDED_H - 6 * Q, HD_WIDTH - 2 * ear_w - 12 * Q, 5 * Q, gold=gold, bronze=bronze)
    draw_african_crest(draw_b, ear_w + 14 * Q, HD_FOLDED_H // 2, 9 * Q, gold=gold, dark_fill=(28, 20, 12))
    draw_b.text((ear_w + 28 * Q, HD_FOLDED_H // 2), "PROTOCODUS - MAREMBA PHYSICAL MODELING", fill=gold, font=font_logo, anchor="lm")
    
    # Cable origin marker at (377*Q, 15*Q)
    draw_b.ellipse([377 * Q - 7, 15 * Q - 7, 377 * Q + 7, 15 * Q + 7], fill=(14, 16, 18), outline=gold, width=2)
    
    # Device name tape recess at (605*Q, 8*Q) (80x13 in 1x, 400x65 in HD)
    draw_b.rectangle([605 * Q - 2, 8 * Q - 2, 605 * Q + 400 + 2, 8 * Q + 65 + 2], fill=(14, 15, 17), outline=(45, 50, 55), width=1)
    
    panel_b.save(HD / "Reason_GUI_folded_back_root_Panel.png")
    panel_b_1x = panel_b.resize((WIDTH, FOLDED_HEIGHT), Image.Resampling.LANCZOS)
    panel_b_1x.save(GUI2D / "Reason_GUI_folded_back_root_Panel.png")
    print("Rendered folded panels (3770x150 & 754x30) successfully!")

# -------------------------------------------------------------------------
# GUI Assembly, Compositing & Previews
# -------------------------------------------------------------------------

def copy_frame(strip, total_frames, frame_idx):
    """Extract a single frame from a vertically stacked sprite strip."""
    w, h = strip.size
    frame_h = h // total_frames
    return strip.crop((0, frame_idx * frame_h, w, (frame_idx + 1) * frame_h))


def composite_front(panel=None):
    """
    Render a fully assembled, realistic front-panel preview with Model Art,
    knobs, toggles, patch LCD, and tape labels composited at HD authoring resolution.
    """
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_front_root_Panel.png")
    image = panel.convert("RGBA")
    
    # 1. Model Art Display (Frame 0: Concert Grand Rosewood Marimba)
    model_art = Image.open(HD / "ModelArt.png").convert("RGBA")
    image.alpha_composite(copy_frame(model_art, 4, 0), (30 * Q, 76 * Q))
    
    # 2. Model Selection Radio Toggles (Frame 1 on first, Frame 0 on others)
    toggle = Image.open(HD / "Toggle.png").convert("RGBA")
    image.alpha_composite(copy_frame(toggle, 2, 1), (34 * Q, 178 * Q))
    image.alpha_composite(copy_frame(toggle, 2, 0), (94 * Q, 178 * Q))
    image.alpha_composite(copy_frame(toggle, 2, 0), (154 * Q, 178 * Q))
    image.alpha_composite(copy_frame(toggle, 2, 0), (214 * Q, 178 * Q))
    
    # 3. Patch Browse Group
    pbg = Image.open(HD / "PatchBrowseGroup.png").convert("RGBA")
    image.alpha_composite(pbg, (580 * Q, 12 * Q))
    
    # 4. Device Name Tape
    tape_h = Image.open(HD / "TapeHorz.png").convert("RGBA")
    image.alpha_composite(tape_h, (605 * Q, 16 * Q))
    
    # Draw Tape Text "Maremba"
    draw = ImageDraw.Draw(image)
    font_tape = get_font(FONT_DIN_ALT, 8.5)
    draw.text((605 * Q + 200, 16 * Q + 32), "Maremba", fill=(32, 34, 38), font=font_tape, anchor="mm")
    
    # 5. Note On Lamp
    lamp = Image.open(HD / "Lamp.png").convert("RGBA")
    image.alpha_composite(copy_frame(lamp, 2, 0), (692 * Q, 16 * Q))
    
    # 6. Patch Display Text
    font_patch = get_font(FONT_ARIAL, 10.5)
    draw.text((380 * Q + 475, 14 * Q + 45), "Concert Grand Rosewood", fill=(245, 235, 215), font=font_patch, anchor="mm")
    
    # 7. Knobs: 26 knobs at exact coordinates with musical positions
    knob = Image.open(HD / "Knob.png").convert("RGBA")
    knob_settings = [
        # Section 1: Resonant Body & Character
        (42, 200, 32),   # sympathetic (50%)
        (124, 200, 26),  # bodyBloom (42%)
        (206, 200, 0),   # pitchGlide (0%)
        (42, 262, 22),   # rollSpeed (35%)
        (124, 262, 15),  # buzzAmount (24%)
        (206, 262, 18),  # artifacts (28%)
        # Section 2: Bar Excitation & Resonator Matrix
        (294, 80, 12),   # malletType (Hard Felt)
        (347, 80, 35),   # malletHardness (55%)
        (400, 80, 25),   # strikePosition (40%)
        (453, 80, 16),   # strikeJitter (25%)
        (298, 160, 31),  # resonatorTune (0 cents)
        (369, 160, 42),  # resonatorCoupling (67%)
        (440, 160, 38),  # decay (60%)
        (298, 246, 48),  # polyphony (16 voices)
        (369, 246, 20),  # oversampling (2x)
        (440, 246, 31),  # velocityCurve (Linear)
        # Section 3: Microphones, Studio Preamps & Dynamics
        (522, 80, 45),   # closeLevel (72%)
        (576, 80, 32),   # farLevel (50%)
        (630, 80, 20),   # piezoLevel (32%)
        (682, 80, 48),   # stereoWidth (76%)
        (522, 160, 18),  # preampDrive (28%)
        (576, 160, 36),  # warmth (58%)
        (630, 160, 25),  # compAmount (40%)
        (682, 160, 30),  # compRelease (48%)
        (522, 246, 14),  # detune (22%)
        (576, 246, 31),  # masterTune (440 Hz)
        (642, 246, 50),  # volume (80%)
    ]
    for kx, ky, frame in knob_settings:
        image.alpha_composite(copy_frame(knob, 63, frame), (kx * Q, ky * Q))
        
    return image


def composite_back(panel=None):
    """
    Render fully assembled, realistic rear-panel preview with Audio & CV jacks,
    Reason placeholder badge, and vertical tape label at HD authoring resolution.
    """
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_back_root_Panel.png")
    image = panel.convert("RGBA")
    
    # 1. Reason Studios Placeholder Badge
    # Official 300x100 1x / 1500x500 HD mounting area at [55*Q, 225*Q]
    ph_x, ph_y = 55 * Q, 225 * Q
    ph_w, ph_h = 1500, 500
    ph_card = Image.new("RGBA", (ph_w, ph_h), (18, 20, 23, 240))
    d_ph = ImageDraw.Draw(ph_card)
    d_ph.rectangle([0, 0, ph_w - 1, ph_h - 1], outline=(55, 60, 68), width=2)
    d_ph.rectangle([6, 6, ph_w - 7, ph_h - 7], outline=(36, 40, 45), width=1)
    
    gold = (218, 175, 55)
    draw_african_crest(d_ph, 140, ph_h // 2, 18 * Q, gold=gold, dark_fill=(26, 22, 16))
    d_ph.text((260, ph_h // 2 - 50), "REASON STUDIOS LICENSED RACK EXTENSION", fill=gold, font=get_font(FONT_DIN_COND, 13), anchor="lm")
    d_ph.text((260, ph_h // 2 - 5), "REGISTERED TO: PRO-AUDIO PRODUCTION WORKSTATION", fill=(220, 225, 230), font=get_font(FONT_DIN_ALT, 9.5), anchor="lm")
    d_ph.text((260, ph_h // 2 + 40), "DEVICE ID: cz.protocodus.Maremba  |  LICENSE: RS-RE-MAR-2026-7741", fill=(140, 145, 155), font=get_font(FONT_DIN_ALT, 8), anchor="lm")
    image.alpha_composite(ph_card, (ph_x, ph_y))
    
    # 2. Vertical Tape for Device Name at [20*Q, 130*Q]
    tape_v = Image.open(HD / "TapeVert.png").convert("RGBA")
    image.alpha_composite(tape_v, (20 * Q, 130 * Q))
    
    tape_txt = Image.new("RGBA", (400, 65), (0, 0, 0, 0))
    d_tv = ImageDraw.Draw(tape_txt)
    d_tv.text((200, 32), "Maremba", fill=(32, 34, 38), font=get_font(FONT_DIN_ALT, 8.5), anchor="mm")
    tape_rot = tape_txt.transpose(Image.Transpose.ROTATE_270)
    image.alpha_composite(tape_rot, (20 * Q, 130 * Q))
    
    # 3. Balanced Audio Output Sockets (Unplugged Frame 0)
    audio_jack = Image.open(HD / "AudioJack.png").convert("RGBA")
    audio_sockets = [
        (60, 140),
        (115, 140),
        (185, 140),
        (240, 140),
        (305, 140),
        (355, 140),
        (385, 220),
    ]
    for sx, sy in audio_sockets:
        image.alpha_composite(copy_frame(audio_jack, 3, 0), (sx * Q, sy * Q))
        
    # 4. CV Modulation Input Sockets (Unplugged Frame 0)
    cv_jack = Image.open(HD / "CVJack.png").convert("RGBA")
    cv_sockets = [
        (465, 140),
        (515, 140),
        (565, 140),
        (615, 140),
        (665, 140),
        (465, 220),
        (565, 220),
        (665, 220),
    ]
    for sx, sy in cv_sockets:
        image.alpha_composite(copy_frame(cv_jack, 3, 0), (sx * Q, sy * Q))
        
    return image


def composite_folded_front(panel=None):
    """Render assembled folded front preview."""
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_folded_front_root_Panel.png")
    image = panel.convert("RGBA")
    draw = ImageDraw.Draw(image)
    
    # Patch display text in folded LCD
    font_patch = get_font(FONT_ARIAL, 9.5)
    draw.text((380 * Q + 475, 6 * Q + 45), "Concert Grand Rosewood", fill=(245, 235, 215), font=font_patch, anchor="mm")
    
    # Tape on folded front
    tape_h = Image.open(HD / "TapeHorz.png").convert("RGBA")
    image.alpha_composite(tape_h, (605 * Q, 8 * Q))
    font_tape = get_font(FONT_DIN_ALT, 8.5)
    draw.text((605 * Q + 200, 8 * Q + 32), "Maremba", fill=(32, 34, 38), font=font_tape, anchor="mm")
    
    # Lamp
    lamp = Image.open(HD / "Lamp.png").convert("RGBA")
    image.alpha_composite(copy_frame(lamp, 2, 0), (692 * Q, 9 * Q))
    
    return image


def composite_folded_back(panel=None):
    """Render assembled folded rear preview."""
    if panel is None:
        panel = Image.open(HD / "Reason_GUI_folded_back_root_Panel.png")
    image = panel.convert("RGBA")
    
    # Tape on folded back
    tape_h = Image.open(HD / "TapeHorz.png").convert("RGBA")
    image.alpha_composite(tape_h, (605 * Q, 8 * Q))
    draw = ImageDraw.Draw(image)
    font_tape = get_font(FONT_DIN_ALT, 8.5)
    draw.text((605 * Q + 200, 8 * Q + 32), "Maremba", fill=(32, 34, 38), font=font_tape, anchor="mm")
    
    return image


def generate_docs_previews(preview_front=None, preview_back=None):
    """
    Generate front/rear presentation preview images and save them into the docs/ directory.
    Output:
    - docs/front.png (Crisp 2x 1508x690 Retina presentation image)
    - docs/rear.png (Crisp 2x 1508x690 Retina presentation image)
    - docs/front_preview.png (1x 754x345 native Reason rack size)
    - docs/rear_preview.png (1x 754x345 native Reason rack size)
    - docs/front_hd.png (5x 3770x1725 full HD authoring resolution)
    - docs/rear_hd.png (5x 3770x1725 full HD authoring resolution)
    """
    docs_dir = PROJECT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    if preview_front is None:
        preview_front = composite_front()
    if preview_back is None:
        preview_back = composite_back()
        
    # 5x HD images
    preview_front.save(docs_dir / "front_hd.png")
    preview_back.save(docs_dir / "rear_hd.png")
    
    # 2x Retina presentation images (front.png & rear.png)
    front_2x = preview_front.resize((WIDTH * 2, HEIGHT * 2), Image.Resampling.LANCZOS)
    rear_2x = preview_back.resize((WIDTH * 2, HEIGHT * 2), Image.Resampling.LANCZOS)
    front_2x.save(docs_dir / "front.png")
    rear_2x.save(docs_dir / "rear.png")
    
    # 1x native rack extension images
    front_1x = preview_front.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    rear_1x = preview_back.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    front_1x.save(docs_dir / "front_preview.png")
    rear_1x.save(docs_dir / "rear_preview.png")
    
    print("Generated all docs previews (front.png, rear.png, etc.) in docs/ successfully!")


def render_device_icons(preview_front=None, preview_back=None, preview_ff=None, preview_fb=None):
    """Render high-resolution African native art & luxury icons, palette, and navigators."""
    base_icon = Image.new("RGBA", (512, 384), (20, 22, 25, 255))
    draw = ImageDraw.Draw(base_icon)
    gold = (218, 175, 55)
    bronze = (145, 105, 40)
    
    draw.rectangle([4, 4, 507, 379], fill=(24, 26, 30), outline=gold, width=4)
    draw.rectangle([12, 12, 499, 371], outline=(45, 48, 52), width=2)
    
    draw_kuba_band(draw, 16, 16, 480, 20, gold=gold, bronze=bronze)
    draw_african_crest(draw, 256, 105, 34, gold=gold, dark_fill=(30, 22, 14))
    
    bar_w = 34
    cx, cy = 256, 240
    for i in range(7):
        bx = 75 + i * 52
        h_bar = int(120 - i * 10)
        top_y = cy - h_bar // 2
        bot_y = cy + h_bar // 2
        
        pipe_len = int(105 * (1.0 - 0.45 * (i / 7.0)))
        draw.rectangle([bx + 6, bot_y + 8, bx + bar_w - 6, bot_y + 8 + pipe_len], fill=(190, 150, 48), outline=gold, width=2)
        draw.arc([bx + 6, bot_y + 8 + pipe_len - 8, bx + bar_w - 6, bot_y + 8 + pipe_len + 8], 0, 180, fill=gold, width=2)
        
        draw.rectangle([bx, top_y, bx + bar_w, bot_y], fill=(185, 60, 22), outline=(80, 20, 10), width=2)
        draw.rectangle([bx + 3, top_y + 4, bx + bar_w - 3, bot_y - 4], fill=(215, 82, 32))
        draw.ellipse([bx + bar_w // 2 - 3, top_y + 12, bx + bar_w // 2 + 3, top_y + 18], fill=gold)
        draw.ellipse([bx + bar_w // 2 - 3, bot_y - 18, bx + bar_w // 2 + 3, bot_y - 12], fill=gold)
        
    draw.rectangle([50, 325, 462, 365], fill=(14, 15, 17), outline=gold, width=2)
    font_icon = get_font(FONT_DIN_COND, 13)
    draw.text((256, 345), "PROTOCODUS - MAREMBA", fill=gold, font=font_icon, anchor="mm")
    
    # 1. Reason HD Atlas (779x518)
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
    
    # GUI2D DeviceIcon (128x128)
    icon_128 = Image.new("RGBA", (128, 128), (20, 22, 25, 255))
    icon_128_draw = ImageDraw.Draw(icon_128)
    icon_128_draw.rectangle([2, 2, 125, 125], outline=gold, width=2)
    scaled_cell = base_icon.resize((120, 90), Image.Resampling.LANCZOS)
    icon_128.paste(scaled_cell, (4, 19))
    icon_128.save(GUI2D / "DeviceIcon.png")
    
    # 2. DevicePaletteImage.png (650x300 in HD, 130x60 in 1x)
    pal_hd = Image.new("RGBA", (650, 300), (22, 24, 26, 255))
    pal_draw = ImageDraw.Draw(pal_hd)
    pal_draw.rectangle([2, 2, 647, 297], outline=gold, width=2)
    draw_kuba_band(pal_draw, 10, 10, 630, 16, gold=gold, bronze=bronze)
    pal_draw.text((220, 130), "PROTOCODUS - MAREMBA", fill=gold, font=get_font(FONT_DIN_COND, 22), anchor="lm")
    pal_draw.text((220, 165), "PHYSICAL-MODELED MARIMBA & KALIMBA", fill=(180, 185, 190), font=get_font(FONT_DIN_ALT, 10), anchor="lm")
    pal_icon = base_icon.resize((180, 135), Image.Resampling.LANCZOS)
    pal_hd.paste(pal_icon, (25, 82))
    pal_hd.save(HD / "DevicePaletteImage.png")
    
    pal_2d = pal_hd.resize((130, 60), Image.Resampling.LANCZOS)
    pal_2d.save(GUI2D / "DevicePaletteImage.png")
    
    # 3. DeviceNavigator.png & Folded
    if preview_front is None:
        preview_front = composite_front()
    if preview_back is None:
        preview_back = composite_back()
    if preview_ff is None:
        preview_ff = composite_folded_front()
    if preview_fb is None:
        preview_fb = composite_folded_back()
        
    nav_hd = preview_front.resize((630, 290), Image.Resampling.LANCZOS)
    nav_hd.save(HD / "DeviceNavigator.png")
    
    nav_f_hd = preview_ff.resize((630, 25), Image.Resampling.LANCZOS)
    nav_f_hd.save(HD / "DeviceNavigatorFolded.png")
    
    nav_2d = preview_front.resize((126, 58), Image.Resampling.LANCZOS)
    nav_2d.save(GUI2D / "DeviceNavigator.png")
    
    nav_f_2d = preview_ff.resize((126, 5), Image.Resampling.LANCZOS)
    nav_f_2d.save(GUI2D / "DeviceNavigatorFolded.png")
    
    # 4. DeviceTrackListThumbnail.png (270x125 in HD, 54x25 in 2D)
    track_thumb_hd = preview_front.resize((270, 125), Image.Resampling.LANCZOS)
    track_thumb_hd.save(HD / "DeviceTrackListThumbnail.png")
    track_thumb_2d = preview_front.resize((54, 25), Image.Resampling.LANCZOS)
    track_thumb_2d.save(GUI2D / "DeviceTrackListThumbnail.png")
    
    # 5. Reason Browser & Rack Preview Suite
    previews = [
        ("Reason_Icon128x128", 128, 58, 6),
        ("Reason_Navigator", 126, 58, 5),
        ("Reason_Palette", 130, 59, 6),
        ("Reason_TrackListIcon", 54, 25, 3),
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
    
    print(">>> Rendering Maremba African Native Art Luxury GUI Assets <<<")
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
    print(">>> All GUI Assets Successfully Rendered! <<<")
