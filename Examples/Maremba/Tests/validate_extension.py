#!/usr/bin/env python3
"""Comprehensive static verification of Maremba Rack Extension declarations, defaults, Remote, and CV."""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fail(msg):
    print(f"FAILED: {msg}", file=sys.stderr)
    sys.exit(1)

def check(cond, msg):
    if not cond:
        fail(msg)

def test_sdk_declarations():
    print("--- 1. Validating SDK Declarations ---")
    info = open(os.path.join(PROJECT, "info.lua"), "r", encoding="utf-8").read()
    motherboard = open(os.path.join(PROJECT, "motherboard_def.lua"), "r", encoding="utf-8").read()
    rtc = open(os.path.join(PROJECT, "realtime_controller.lua"), "r", encoding="utf-8").read()
    device2d = open(os.path.join(PROJECT, "GUI2D", "device_2D.lua"), "r", encoding="utf-8").read()
    gui = open(os.path.join(PROJECT, "GUI", "Output", "gui.lua"), "r", encoding="utf-8").read()

    check('format_version = "2.0"' in info, "info.lua must use format_version 2.0")
    check('format_version = "4.0"' in motherboard, "motherboard_def.lua must use format_version 4.0")
    check('format_version = "1.0"' in rtc, "realtime_controller.lua must use format_version 1.0")
    check('format_version = "2.0"' in device2d, "device_2D.lua must use format_version 2.0")
    check('format_version = "4.0"' in gui, "gui.lua must use format_version 4.0")

    check('product_id = "cz.protocodus.Maremba"' in info, "Wrong product_id in info.lua")
    check('long_name = "Maremba"' in info, "Wrong long_name in info.lua")
    check('supports_patches = true' in info, "supports_patches must be true")
    check('supports_performance_automation = true' in info, "supports_performance_automation must be true")
    
    # Check default patch exists
    m = re.search(r'default_patch\s*=\s*"([^"]+)"', info)
    check(m, "info.lua must declare default_patch")
    default_patch_rel = m.group(1).lstrip("/")
    default_patch_path = os.path.join(PROJECT, "Resources", default_patch_rel)
    check(os.path.exists(default_patch_path), f"default_patch not found at {default_patch_path}")
    print(f"  PASS: SDK declarations verified. Default patch exists: {default_patch_rel}")

def test_texts_coverage():
    print("--- 2. Validating Localization Texts ---")
    motherboard = open(os.path.join(PROJECT, "motherboard_def.lua"), "r", encoding="utf-8").read()
    texts = open(os.path.join(PROJECT, "Resources", "English", "texts.lua"), "r", encoding="utf-8").read()

    keys_used = set(re.findall(r'jbox\.ui_text\("([^"]+)"\)', motherboard))
    keys_defined = dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]*)"', texts))

    missing = keys_used - set(keys_defined.keys())
    check(not missing, f"Missing keys in texts.lua: {missing}")
    print(f"  PASS: All {len(keys_used)} UI text keys referenced in motherboard_def.lua are defined in texts.lua")

def test_remote_and_midi():
    print("--- 3. Validating Reason Remote & Automation ---")
    motherboard = open(os.path.join(PROJECT, "motherboard_def.lua"), "r", encoding="utf-8").read()
    texts = open(os.path.join(PROJECT, "Resources", "English", "texts.lua"), "r", encoding="utf-8").read()
    keys_defined = dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]*)"', texts))

    remote_entries = re.findall(
        r'\["([^"]+)"\]\s*=\s*\{\s*internal_name\s*=\s*"([^"]+)",\s*short_ui_name\s*=\s*jbox\.ui_text\("([^"]+)"\),\s*shortest_ui_name\s*=\s*jbox\.ui_text\("([^"]+)"\)',
        motherboard
    )
    check(len(remote_entries) > 20, "Insufficient Remote entries")
    for target, internal, short_key, shortest_key in remote_entries:
        short_val = keys_defined.get(short_key, "")
        shortest_val = keys_defined.get(shortest_key, "")
        check(len(short_val) <= 8, f"{short_key} ({short_val}) exceeds 8 chars!")
        check(len(shortest_val) <= 4, f"{shortest_key} ({shortest_val}) exceeds 4 chars!")
        check(len(short_val) > 0, f"Empty short Remote name for {target}")
        check(len(shortest_val) > 0, f"Empty shortest Remote name for {target}")

    # Check midi_cc_chart IDs are contiguous or unique
    midi_ids = [int(x) for x in re.findall(r'\[(\d+)\]\s*=\s*"/custom_properties/', motherboard)]
    check(len(midi_ids) == len(set(midi_ids)), "Duplicate automation MIDI CC IDs in motherboard_def.lua")
    print(f"  PASS: {len(remote_entries)} Remote controls & {len(midi_ids)} Automation channels verified")

def test_cpp_defaults():
    print("--- 4. Validating C++ Defaults Matching Motherboard ---")
    motherboard = open(os.path.join(PROJECT, "motherboard_def.lua"), "r", encoding="utf-8").read()
    header = open(os.path.join(PROJECT, "Maremba.h"), "r", encoding="utf-8").read()

    table_match = re.search(r"kParameterDefaults\s*\{\s*(.*?)\s*\};", header, re.DOTALL)
    check(table_match, "No kParameterDefaults in Maremba.h")

    rows = []
    for line in table_match.group(1).split("\n"):
        line = line.strip()
        if not line or not "//" in line:
            continue
        val_part, comment_part = line.split("//", 1)
        val = float(val_part.strip().rstrip(","))
        name = comment_part.strip().split()[0]
        rows.append((name, val))

    perf_defaults = {"modWheel": 0.0, "pitchBend": 0.5, "sustainPedal": 0.0}

    for name, cpp_val in rows:
        if name in perf_defaults:
            expected = perf_defaults[name]
        else:
            m = re.search(rf"\b{name}\s*=\s*jbox\.number\{{[^}}]*?default\s*=\s*([0-9.]+)", motherboard)
            check(m, f"Property {name} default not found in motherboard_def.lua")
            expected = float(m.group(1))
        check(abs(cpp_val - expected) < 1e-5, f"{name}: C++ default {cpp_val} != motherboard default {expected}")

    print(f"  PASS: All {len(rows)} C++ parameter defaults strictly match motherboard_def.lua")

def test_cv_and_rtc():
    print("--- 5. Validating CV Inputs & Realtime Notifications ---")
    motherboard = open(os.path.join(PROJECT, "motherboard_def.lua"), "r", encoding="utf-8").read()
    rtc = open(os.path.join(PROJECT, "realtime_controller.lua"), "r", encoding="utf-8").read()

    cv_inputs = re.findall(r"(\w+)\s*=\s*jbox\.cv_input", motherboard)
    check(len(cv_inputs) == 8, f"Expected 8 CV inputs, found {len(cv_inputs)}")

    for cv in cv_inputs:
        for field in ["value", "connected"]:
            target = f'"/cv_inputs/{cv}/{field}"'
            check(target in rtc, f"Missing realtime notification for {target}")

    for out in ["left", "right", "close_left", "close_right", "far_left", "far_right", "piezo"]:
        target = f'"/audio_outputs/{out}/dsp_latency"'
        check(target in rtc, f"Missing dsp_latency for audio output {out}")

    print(f"  PASS: All {len(cv_inputs)} CV sockets & all 7 audio outputs registered in realtime controller")

if __name__ == "__main__":
    test_sdk_declarations()
    test_texts_coverage()
    test_remote_and_midi()
    test_cpp_defaults()
    test_cv_and_rtc()
    print("\n>>> ALL MAREMBA EXTENSION STRUCTURAL CHECKS PASSED SUCCESSFULLY! <<<\n")
