#!/usr/bin/env python3
"""
render_knob.py
Renders authentic primitive hand-carved African hardwood / volcanic stone analog knobs
for Maremba Rack Extension.

Output (the same 5x strip in both places; RE2D reads GUI2D at authoring resolution):
- GUI/Output/HD/Knob.png: 260 x 16380 (63 frames of 260x260, strictly divisible by 5)
- GUI2D/Knob.png: identical copy for the universal45 package
"""

import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
HD_DIR = os.path.join(PROJECT_DIR, "GUI", "Output", "HD")
GUI2D_DIR = os.path.join(PROJECT_DIR, "GUI2D")

TOTAL_FRAMES = 63
FRAME_SIZE_HD = 260


def render_primitive_knob_frame(frame_idx, total_frames=TOTAL_FRAMES, size=FRAME_SIZE_HD):
    """
    Renders one frame of a primitive hand-carved African wood/stone knob.
    Rotation angle spans 270 degrees (-135 deg at frame 0, +135 deg at frame 62).
    """
    angle_deg = -135.0 + (frame_idx / float(total_frames - 1)) * 270.0
    angle_rad = math.radians(angle_deg - 90.0) # 0 rad = 12 o'clock (top)

    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy = size / 2.0, size / 2.0

    # 1. Soft Realistic Drop Shadow (Fixed light source from top-left ~135 deg)
    shadow_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_im)
    s_draw.ellipse([cx - 96 + 4, cy - 96 + 7, cx + 96 + 4, cy + 96 + 7], fill=(6, 5, 4, 195))
    shadow_im = shadow_im.filter(ImageFilter.GaussianBlur(radius=5.5))
    im = Image.alpha_composite(im, shadow_im)

    # 2. Outer Primitive Cylindrical Rim (R = 95 down to R = 83)
    R_outer = 95
    R_inner = 83

    rim_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rim_draw = ImageDraw.Draw(rim_im)

    # Cylindrical body gradient with dark African ironwood / volcanic basalt tones
    for r in range(R_outer, R_inner - 1, -1):
        t = (r - R_inner) / float(R_outer - R_inner)
        cr = int(32 + 18 * t)
        cg = int(24 + 14 * t)
        cb = int(18 + 10 * t)
        rim_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(cr, cg, cb, 255))

    # Rim Lighting: Highlight on top-left (225 deg math), Shadow on bottom-right
    for deg in range(360):
        rad = math.radians(deg)
        light = math.cos(rad - math.radians(225))
        for dr in range(R_inner, R_outer):
            t = (dr - R_inner) / float(R_outer - R_inner)
            px = cx + dr * math.cos(rad)
            py = cy + dr * math.sin(rad)
            if light > 0:
                h = int(60 * light * (1.0 - t * 0.4))
                rim_draw.point((px, py), fill=(min(255, 45 + h + 15), min(255, 35 + h + 10), min(255, 25 + h), 255))
            else:
                s = int(18 * abs(light))
                rim_draw.point((px, py), fill=(max(10, 32 - s), max(8, 24 - s), max(6, 18 - s), 255))

    # 3. Primitive Hand-Carved Thumb Grip Notches (8 chiseled notches around perimeter)
    for i in range(8):
        notch_angle = angle_rad + i * (2.0 * math.pi / 8.0)
        nx = cx + (R_outer - 5) * math.cos(notch_angle)
        ny = cy + (R_outer - 5) * math.sin(notch_angle)
        rim_draw.ellipse([nx - 5, ny - 5, nx + 5, ny + 5], fill=(14, 11, 9, 210))
        # Sunward highlight on notch lip
        hx = nx + 2.0 * math.cos(math.radians(225))
        hy = ny + 2.0 * math.sin(math.radians(225))
        rim_draw.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(110, 95, 75, 140))

    im = Image.alpha_composite(im, rim_im)

    # 4. Top Face (R = 83) with Rotating Hand-Carved Wood/Stone Grain
    face_size = R_inner * 2 + 4
    face_arr = np.zeros((face_size, face_size, 4), dtype=np.uint8)

    fcx, fcy = face_size / 2.0, face_size / 2.0
    y, x = np.ogrid[:face_size, :face_size]
    r_map = np.sqrt((x - fcx)**2 + (y - fcy)**2)
    mask = r_map <= R_inner

    # Deterministic procedural grain aligned with rotating knob angle
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    x_rot = (x - fcx) * cos_a - (y - fcy) * sin_a
    y_rot = (x - fcx) * sin_a + (y - fcy) * cos_a

    # Organic wood growth rings + fibers
    rings = np.sin(x_rot * 0.16 + np.sin(y_rot * 0.05) * 2.0) * 12.0
    # Fine grain noise
    np.random.seed(int(abs(angle_deg) * 17) % 10000 + 42)
    fiber = np.random.normal(0, 4.5, (face_size, face_size))

    # Subtle convex dome shading
    dome = (1.0 - (r_map / float(R_inner))**2) * 8.0

    vr = np.clip(38 + rings + fiber + dome, 18, 75).astype(np.uint8)
    vg = np.clip(28 + rings * 0.8 + fiber * 0.8 + dome * 0.8, 14, 58).astype(np.uint8)
    vb = np.clip(20 + rings * 0.6 + fiber * 0.6 + dome * 0.6, 10, 45).astype(np.uint8)

    face_arr[mask, 0] = vr[mask]
    face_arr[mask, 1] = vg[mask]
    face_arr[mask, 2] = vb[mask]
    face_arr[mask, 3] = 255

    face_disk = Image.fromarray(face_arr)
    im.alpha_composite(face_disk, (int(cx - fcx), int(cy - fcy)))

    draw = ImageDraw.Draw(im)

    # Subtle concentric artisan scoring rings at r = 62 and r = 40
    for ring_r in [62, 40]:
        draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(18, 14, 11, 140), width=1)
        draw.arc([cx - ring_r + 1, cy - ring_r + 1, cx + ring_r + 1, cy + ring_r + 1], 180, 270, fill=(75, 60, 45, 100), width=1)

    # Top face ambient light sheen from top-left (fixed lighting)
    sheen = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_dr = ImageDraw.Draw(sheen)
    s_dr.ellipse([cx - R_inner + 8, cy - R_inner + 6, cx + R_inner - 14, cy + R_inner - 20], fill=(140, 120, 95, 42))
    sheen = sheen.filter(ImageFilter.GaussianBlur(radius=8))
    im = Image.alpha_composite(im, sheen)
    draw = ImageDraw.Draw(im)

    # 5. Hand-Carved Artisan Indicator Groove
    # A carved channel in the wood/stone filled with aged bone ivory & terracotta pigment
    r_start = 22
    r_end = 80

    # Deep carved shadow channel
    for w, a in [(7, 160), (5, 220), (3, 255)]:
        x1 = cx + r_start * math.cos(angle_rad)
        y1 = cy + r_start * math.sin(angle_rad)
        x2 = cx + r_end * math.cos(angle_rad)
        y2 = cy + r_end * math.sin(angle_rad)
        draw.line([(x1, y1), (x2, y2)], fill=(10, 8, 6, a), width=w)

    # Inlaid Aged Ivory / Bone Pigment with warm gold tone
    x1_inlay = cx + (r_start + 4) * math.cos(angle_rad)
    y1_inlay = cy + (r_start + 4) * math.sin(angle_rad)
    x2_inlay = cx + (r_end - 2) * math.cos(angle_rad)
    y2_inlay = cy + (r_end - 2) * math.sin(angle_rad)
    draw.line([(x1_inlay, y1_inlay), (x2_inlay, y2_inlay)], fill=(245, 230, 195, 255), width=3)
    # Bright center core
    draw.line([(x1_inlay, y1_inlay), (x2_inlay, y2_inlay)], fill=(255, 250, 235, 255), width=1)

    # Hand-carved diamond / pip indicator head at outer edge (r = 74)
    pip_x = cx + 74 * math.cos(angle_rad)
    pip_y = cy + 74 * math.sin(angle_rad)
    d_sz = 3.5
    draw.polygon([
        (pip_x + d_sz * math.cos(angle_rad), pip_y + d_sz * math.sin(angle_rad)),
        (pip_x - d_sz * math.sin(angle_rad), pip_y + d_sz * math.cos(angle_rad)),
        (pip_x - d_sz * math.cos(angle_rad), pip_y - d_sz * math.sin(angle_rad)),
        (pip_x + d_sz * math.sin(angle_rad), pip_y - d_sz * math.cos(angle_rad)),
    ], fill=(255, 245, 215, 255), outline=(20, 14, 10, 200))

    # 6. Central Carved Bushing / Rosette Core (R = 13)
    draw.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(20, 15, 12), outline=(60, 48, 36), width=1)
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(12, 9, 7), outline=(160, 125, 65), width=1)
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(215, 175, 85, 240))

    return im


def generate_knob_filmstrip():
    print(f">>> Rendering {TOTAL_FRAMES}-frame Primitive Wood/Stone Knob Filmstrip <<<")
    total_height_hd = FRAME_SIZE_HD * TOTAL_FRAMES
    filmstrip_hd = Image.new("RGBA", (FRAME_SIZE_HD, total_height_hd), (0, 0, 0, 0))

    for i in range(TOTAL_FRAMES):
        frame = render_primitive_knob_frame(i, TOTAL_FRAMES, FRAME_SIZE_HD)
        filmstrip_hd.paste(frame, (0, i * FRAME_SIZE_HD))
        if (i + 1) % 15 == 0 or (i + 1) == TOTAL_FRAMES:
            print(f"  Rendered {i + 1}/{TOTAL_FRAMES} frames...")

    # Save HD Knob filmstrip (260 x 16380)
    os.makedirs(HD_DIR, exist_ok=True)
    hd_path = os.path.join(HD_DIR, "Knob.png")
    filmstrip_hd.save(hd_path, "PNG", optimize=True)
    print(f"  Saved HD filmstrip: {hd_path} ({filmstrip_hd.size[0]}x{filmstrip_hd.size[1]})")

    # GUI2D carries the same 5x strip: device_2D places it at 52 logical units
    # (260 HD px) per frame, so a downscaled copy would render at 1/5 size.
    os.makedirs(GUI2D_DIR, exist_ok=True)
    gui2d_path = os.path.join(GUI2D_DIR, "Knob.png")
    filmstrip_hd.save(gui2d_path, "PNG", optimize=True)
    print(f"  Saved GUI2D filmstrip: {gui2d_path} ({filmstrip_hd.size[0]}x{filmstrip_hd.size[1]})")

    print(">>> Primitive Wood/Stone Knob Filmstrip Generation Complete! <<<")


if __name__ == "__main__":
    generate_knob_filmstrip()
