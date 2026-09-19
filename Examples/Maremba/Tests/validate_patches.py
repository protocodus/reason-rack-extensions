#!/usr/bin/env python3
"""Validation of the Maremba factory patches against the evaluated motherboard_def.lua.

Every patch must store exactly the patch-persisted document_owner properties
(no performance controllers, rt/rtc properties or removed properties), stepped
values must be step indices, continuous values must lie in 0..1, and the patch
header must match info.lua.
"""

import glob
import os
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_extension import PRODUCT_ID, PROJECT, Motherboard, ValidationError, info_value  # noqa: E402

PUBLIC_DIR = os.path.join(PROJECT, "Resources", "Public")


def validate_patch(path, mb, version, device_name):
    """Return the patch's {property: value}; raise AssertionError on the first defect."""
    basename = os.path.basename(path)
    root = ET.parse(path).getroot()
    assert root.tag == "JukeboxPatch" and root.get("version") == "1.0", (
        f"{basename}: root element must be <JukeboxPatch version=\"1.0\">"
    )
    assert root.findtext("DeviceNameInEnglish") == device_name, (
        f"{basename}: DeviceNameInEnglish must be '{device_name}' (info.lua long_name)"
    )
    props = root.find("Properties")
    assert props is not None, f"{basename}: missing <Properties>"
    assert props.get("deviceProductID") == PRODUCT_ID, f"{basename}: deviceProductID must be {PRODUCT_ID}"
    assert props.get("deviceVersion") == version, (
        f"{basename}: deviceVersion {props.get('deviceVersion')} does not match info.lua {version}"
    )
    objects = props.findall("Object")
    assert len(objects) == 1 and objects[0].get("name") == "custom_properties", (
        f"{basename}: expected exactly one <Object name=\"custom_properties\">"
    )

    values = {}
    for val in objects[0].findall("Value"):
        name = val.get("property")
        kind = val.get("type")
        text = (val.text or "").strip()
        assert name not in values, f"{basename}: property '{name}' stored twice"
        assert name in mb.patch_persisted, (
            f"{basename}: '{name}' is not a patch-persisted document_owner property "
            "(unknown, removed, performance controller or non-persisted)"
        )
        declared = mb.properties[name]["kind"]
        if declared == "boolean":
            assert kind == "boolean" and text in {"true", "false"}, f"{basename}: invalid boolean for {name}"
            values[name] = text == "true"
            continue
        assert kind == "number", f"{basename}: '{name}' must be stored as type=\"number\", not {kind}"
        parsed = float(text)
        steps = mb.steps(name)
        if steps:
            assert parsed.is_integer() and 0 <= parsed < steps, (
                f"{basename}: stepped property '{name}'={text} must be an integer in [0, {steps - 1}]"
            )
        else:
            assert 0.0 <= parsed <= 1.0, f"{basename}: continuous property '{name}'={text} out of range [0, 1]"
        values[name] = parsed

    missing = [n for n in mb.patch_persisted if n not in values]
    assert not missing, f"{basename}: missing properties {missing} (loading it would keep the previous values)"
    return values


def validate_all_patches():
    mb = Motherboard()
    version = info_value("version_number")
    device_name = info_value("long_name")
    patches = sorted(glob.glob(os.path.join(PUBLIC_DIR, "*.repatch")))
    assert 5 <= len(patches) <= 20, (
        f"Resources/Public should contain 5..20 featured patches, found {len(patches)}"
    )
    default_patch = os.path.join(PROJECT, "Resources", str(info_value("default_patch")).lstrip("/"))
    assert os.path.abspath(default_patch) in map(os.path.abspath, patches), (
        f"default_patch {info_value('default_patch')} is not a factory patch"
    )

    signatures = {}
    models = set()
    for path in patches:
        values = validate_patch(path, mb, version, device_name)
        signature = tuple(values[n] for n in mb.patch_persisted)
        assert signature not in signatures, (
            f"{os.path.basename(path)} duplicates {signatures[signature]}"
        )
        signatures[signature] = os.path.basename(path)
        models.add(int(values["model"]))
    unused_models = sorted(set(range(mb.steps("model"))) - models)
    assert not unused_models, f"no factory patch uses model(s) {unused_models}"

    print(f"PASS: All {len(patches)} patches store exactly the {len(mb.patch_persisted)} patch-persisted "
          f"properties with valid values; every model has a factory patch.")


if __name__ == "__main__":
    try:
        validate_all_patches()
    except (AssertionError, ValidationError) as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
