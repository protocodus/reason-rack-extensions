#!/usr/bin/env python3
"""Validation script for Maremba Rack Extension patches, declarations, and metadata."""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT_ID = "cz.protocodus.Maremba"

STEPPED_MAX = {
    "model": 3,
    "malletType": 3,
    "oversampling": 2,
    "velocityCurve": 3,
    "polyphony": 2,
}

FORBIDDEN_PROPERTIES = {
    "modWheel",
    "pitchBend",
    "sustainPedal",
    "noteon",
    "instance",
}

def get_info_version():
    with open(os.path.join(PROJECT_DIR, "info.lua"), "r", encoding="utf-8") as f:
        match = re.search(r'version_number\s*=\s*"([^"]+)"', f.read())
        assert match, "info.lua has no version_number"
        return match.group(1)

def validate_all_patches():
    version = get_info_version()
    patches = sorted(glob.glob(os.path.join(PROJECT_DIR, "Resources", "Public", "*.repatch")))
    assert patches, "No patches found in Resources/Public!"

    for p in patches:
        basename = os.path.basename(p)
        tree = ET.parse(p)
        root = tree.getroot()
        assert root.tag == "JukeboxPatch" and root.get("version") == "1.0", (
            f"{basename}: root element must be <JukeboxPatch version=\"1.0\">"
        )
        assert root.findtext("DeviceNameInEnglish") == "Maremba", (
            f"{basename}: DeviceNameInEnglish must be 'Maremba'"
        )
        props = root.find("Properties")
        assert props is not None, f"{basename}: missing <Properties>"
        assert props.get("deviceProductID") == PRODUCT_ID, (
            f"{basename}: deviceProductID must be {PRODUCT_ID}"
        )
        assert props.get("deviceVersion") == version, (
            f"{basename}: deviceVersion {props.get('deviceVersion')} does not match info.lua {version}"
        )

        obj = props.find("Object")
        assert obj is not None and obj.get("name") == "custom_properties", (
            f"{basename}: missing <Object name=\"custom_properties\">"
        )

        for val in obj.findall("Value"):
            name = val.attrib.get("property")
            kind = val.attrib.get("type")
            text = (val.text or "").strip()

            assert name not in FORBIDDEN_PROPERTIES, (
                f"{basename}: property '{name}' is a performance controller or unpersisted property and must never be saved in a patch!"
            )

            if kind == "boolean":
                assert text in {"true", "false"}, f"{basename}: invalid boolean for {name}"
            elif kind == "number":
                parsed = float(text)
                if name in STEPPED_MAX:
                    max_allowed = STEPPED_MAX[name]
                    assert 0 <= parsed <= max_allowed and parsed.is_integer(), (
                        f"{basename}: stepped property '{name}'={parsed} must be integer in [0, {max_allowed}]"
                    )
                else:
                    assert 0.0 <= parsed <= 1.0, (
                        f"{basename}: continuous property '{name}'={parsed} out of range [0.0, 1.0]!"
                    )
            else:
                raise ValueError(f"{basename}: unknown type '{kind}' for property '{name}'")

    print(f"PASS: All {len(patches)} patches validated successfully against Reason Jukebox constraints.")

if __name__ == "__main__":
    validate_all_patches()
