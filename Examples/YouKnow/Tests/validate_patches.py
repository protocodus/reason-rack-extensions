#!/usr/bin/env python3
"""Validate YouKnow SDK declarations, localization, and public patch bank."""

import json
from pathlib import Path
import re
import runpy
import xml.etree.ElementTree as ET


PROJECT = Path(__file__).resolve().parent.parent
PUBLIC = PROJECT / "Resources" / "Public"
LEVELS_PATH = PROJECT / "Design" / "preset_levels.json"
PRODUCT_ID = "cz.protocodus.YouKnow"
SUPPORT_URL = "https://protocodus.cz/product/youknow/"
TEXT_KEY = re.compile(
    r'"((?:(?:property|value|unit|group|cv|audio|remote4?|remote) )[^"\n]+)"'
)

STEPPED_MAX = {
    "keyMode": 2,
    "pwmMode": 1,
    "range": 2,
    "highPass": 3,
    "envPolarity": 1,
    "vcaMode": 1,
    "chorus": 3,
    "transpose": 24,
    "polyphony": 15,
}

CATEGORY_PAIRS = {
    ("Bass", "Synth"),
    ("Drum Sounds", "Bass Drums"),
    ("Drum Sounds", "Claps"),
    ("Drum Sounds", "Snare Drums"),
    ("Drum Sounds", "Toms"),
    ("FX", "Sound FX"),
    ("FX", "Synth FX"),
    ("FX", "Textures"),
    ("Guitar & Plucked", "Acoustic Guitar"),
    ("Guitar & Plucked", "Misc"),
    ("Keys", "Electric Piano"),
    ("Keys", "Misc"),
    ("Keys", "Organ"),
    ("Keys", "Piano"),
    ("Mallets", "Bells & Vibes"),
    ("Mallets", "Marimba & Xylo"),
    ("Mallets", "Misc"),
    ("Misc", "Templates"),
    ("Percussion", "Electronic"),
    ("Percussion", "Metal"),
    ("Percussion", "Shakers"),
    ("Percussion", "Skin"),
    ("Strings", "Ensemble"),
    ("Strings", "Solo"),
    ("Strings", "Synth"),
    ("Synth", "Leads"),
    ("Synth", "Pads"),
    ("Synth", "Plucks"),
    ("Synth", "Poly"),
    ("Synth", "Sequences & Loops"),
    ("Voice", "Choir"),
    ("Wind", "Brass"),
    ("Wind", "Woodwind"),
}

CONTENT_TAGS = {
    "Acoustic", "Airy", "Analog", "Arpeggio", "Atmospheric", "Atonal",
    "Bassy", "Boomy", "Breathy", "Bright", "Chord", "Clean", "Clicky",
    "Dark", "Deep", "Digital", "Dirty", "Distorted", "Dull", "Evolving",
    "Exclude", "FM", "Fast", "Fat", "Glassy", "Glide", "Glitchy", "Hard",
    "Hybrid", "Layered", "Lo-Fi", "Long", "Lush", "Mellow", "Metallic",
    "Modeled", "Monophonic", "Noisy", "Organic", "Percussive", "Portamento",
    "Processed", "Punchy", "Realistic", "Rhythmic", "Sampled", "Sequenced",
    "Short", "Slow", "Snappy", "Soft", "Spacious", "Split", "Staff Pick",
    "Sub", "Synthetic", "Thin", "Tight", "Vintage", "Warm", "Weird", "Wide",
}

ORIGINAL_CATEGORIES = {"Bass", "Leads", "Keys", "Brass", "Pads", "Strings", "Effects"}

AUTOMATION_MAP = {
    256: "volume",
    257: "benderDco",
    258: "benderVcf",
    259: "benderLfo",
    260: "portamento",
    261: "keyMode",
    262: "lfoRate",
    263: "lfoDelay",
    264: "dcoLfo",
    265: "pwm",
    266: "pwmMode",
    267: "range",
    268: "saw",
    269: "pulse",
    270: "sub",
    271: "noise",
    272: "highPass",
    273: "cutoff",
    274: "resonance",
    275: "envPolarity",
    276: "vcfEnv",
    277: "vcfLfo",
    278: "keyFollow",
    279: "vcaMode",
    280: "vcaLevel",
    281: "attack",
    282: "decay",
    283: "sustain",
    284: "release",
    285: "chorus",
    286: "transpose",
    287: "masterTune",
    288: "velocity",
    289: "polyphony",
    290: "chorusNoise",
    291: "calibration",
    292: "aging",
    293: "quality",
    294: "vcfTanhMode",
    295: "vcfFastEarlyMode",
    296: "vcfSolverMode",
}

REMOTE_ONLY_CONTROLS = {
    "keyModeReassertPress",
}


def info_value(name):
    match = re.search(
        rf'^{re.escape(name)}\s*=\s*"([^"]+)"',
        (PROJECT / "info.lua").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match, f"info.lua has no {name}"
    return match.group(1)


def validate_sdk5_declarations():
    info = (PROJECT / "info.lua").read_text(encoding="utf-8")
    motherboard = (PROJECT / "motherboard_def.lua").read_text(encoding="utf-8")
    device_2d = (PROJECT / "GUI2D" / "device_2D.lua").read_text(encoding="utf-8")
    assert info.startswith('format_version = "2.0"'), "info.lua must use SDK 5 format 2.0"
    assert motherboard.startswith('format_version = "4.0"'), (
        "motherboard_def.lua must use SDK 5 format 4.0"
    )
    assert device_2d.startswith('format_version = "2.0"'), (
        "device_2D.lua must use SDK 5 format 2.0"
    )
    assert "automation_highlight_color = { r = 60, g = 255, b = 2 }" in info, (
        "use the SDK acceptance color unless Reason Studios approves another"
    )
    assert "supports_performance_automation = true" in info
    aging = re.search(
        r'\baging = jbox.number\{\s*default = ([0-9.]+),(.*?)\n\s*\},',
        motherboard, re.DOTALL,
    )
    assert aging and float(aging.group(1)) == 0.50, "fresh Aging must start at 50%"
    assert 'persistence = "song"' in aging.group(2), "Aging must remain song-persistent"
    assert "jbox.ui_percent" in aging.group(2), "Aging uses normalized 0..1 percent travel"
    automation = {
        int(identifier): property_name
        for identifier, property_name in re.findall(
            r'\[(\d+)\]\s*=\s*"/custom_properties/([^"]+)"', motherboard
        )
    }
    assert automation == AUTOMATION_MAP, (
        "Reason automation IDs must preserve the complete permanent control map"
    )
    remote_properties = set(re.findall(r'^remote\("([^"]+)"', motherboard, re.MULTILINE))
    assert remote_properties == set(AUTOMATION_MAP.values()) | REMOTE_ONLY_CONTROLS, (
        "Reason Remote must cover every user-facing custom control"
    )
    cv_names = re.findall(r'^    (\w+) = jbox.cv_input\{', motherboard, re.MULTILINE)
    assert cv_names == ["note_cv", "gate_cv", "cutoff_cv", "resonance_cv",
                        "volume_cv", "vca_level_cv", "sub_cv", "noise_cv"], (
        "CV socket names/order must preserve saved cable routing"
    )
    rtc = (PROJECT / "realtime_controller.lua").read_text(encoding="utf-8")
    for name in cv_names:
        for field in ("value", "connected"):
            assert f'"/cv_inputs/{name}/{field}"' in rtc, (
                f"{name}/{field}: missing realtime notification"
            )
    assert info_value("product_id") == PRODUCT_ID
    assert PRODUCT_ID.rsplit(".", 1)[-1] == "YouKnow"
    assert len(info_value("long_name")) <= 40
    assert len(info_value("medium_name")) <= 20
    assert len(info_value("short_name")) <= 10
    assert re.fullmatch(r"\d+\.\d+\.\d+[bdf]\d+", info_value("version_number")), (
        "invalid beta/development/final candidate version"
    )


def validate_support_url():
    for relative in ("README.md", "PRIVACY.md", "Docs/SHOP_COPY.md",
                     "Docs/USER_GUIDE.md", "Docs/RELEASE_CHECKLIST.md"):
        text = (PROJECT / relative).read_text(encoding="utf-8")
        assert SUPPORT_URL in text, f"{relative}: support URL is stale or missing"
        assert "protocodus.cz/youknow/" not in text, (
            f"{relative}: legacy support URL remains"
        )


def validate_texts():
    motherboard = (PROJECT / "motherboard_def.lua").read_text(encoding="utf-8")
    texts = (PROJECT / "Resources" / "English" / "texts.lua").read_text(
        encoding="utf-8"
    )
    required = set(TEXT_KEY.findall(motherboard))
    entries = re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]*)"', texts)
    keys = [key for key, _ in entries]
    localized = dict(entries)
    assert len(keys) == len(set(keys)), "texts.lua contains duplicate keys"
    missing = sorted(required - set(keys))
    assert not missing, f"texts.lua missing keys: {', '.join(missing)}"
    for short_key, shortest_key in re.findall(
        r'remote\("[^"]+",\s*"[^"]+",\s*"([^"]+)",\s*"([^"]+)"\)',
        motherboard,
    ):
        assert len(localized[short_key]) <= 8, (
            f"{short_key}: Remote short_ui_name exceeds 8 characters"
        )
        assert len(localized[shortest_key]) <= 4, (
            f"{shortest_key}: Remote shortest_ui_name exceeds 4 characters"
        )
    return len(required)


def read_patch(path):
    root = ET.parse(path).getroot()
    assert root.tag == "JukeboxPatch" and root.get("version") == "1.0", (
        f"{path.name}: invalid JukeboxPatch root"
    )
    assert root.findtext("DeviceNameInEnglish") == info_value("long_name"), (
        f"{path.name}: wrong DeviceNameInEnglish"
    )
    properties = root.find("Properties")
    assert properties is not None, f"{path.name}: missing Properties"
    assert properties.get("deviceProductID") == PRODUCT_ID, (
        f"{path.name}: wrong product id"
    )
    assert properties.get("deviceVersion") == info_value("version_number"), (
        f"{path.name}: wrong device version"
    )
    objects = properties.findall("Object")
    assert len(objects) == 1 and objects[0].get("name") == "custom_properties", (
        f"{path.name}: expected one custom_properties object"
    )

    values = {}
    types = {}
    for value in objects[0].findall("Value"):
        name = value.get("property")
        assert name and name not in values, f"{path.name}: duplicate property {name}"
        kind = value.get("type")
        text = (value.text or "").strip()
        assert kind in {"number", "boolean"}, f"{path.name}: invalid type for {name}"
        if kind == "boolean":
            assert text in {"true", "false"}, f"{path.name}: invalid boolean {name}"
            parsed = text == "true"
        else:
            parsed = float(text)
            maximum = STEPPED_MAX.get(name, 1)
            assert 0 <= parsed <= maximum, f"{path.name}: {name} out of range"
            if name in STEPPED_MAX:
                assert parsed.is_integer(), f"{path.name}: {name} is not stepped"
        values[name] = parsed
        types[name] = kind
    return values, types


def validate_metadata(patches):
    metadata_path = PROJECT / "YouKnow.rsmeta"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    files = metadata.get("Files")
    assert isinstance(files, list), "YouKnow.rsmeta has no Files list"
    by_url = {}
    prefix = f"rackext:/{PRODUCT_ID}/Public/"
    for entry in files:
        assert isinstance(entry, dict), "YouKnow.rsmeta entry is not an object"
        url = entry.get("URL")
        assert isinstance(url, str) and url not in by_url, (
            f"YouKnow.rsmeta duplicate or invalid URL: {url!r}"
        )
        assert entry.get("Author") == "Protocodus", f"{url}: wrong author"
        assert entry.get("Excluded") is False, f"{url}: patch unexpectedly excluded"
        tags = entry.get("Tags")
        assert isinstance(tags, list) and len(tags) == len(set(tags)), (
            f"{url}: Tags must be a unique list"
        )
        assert all(isinstance(tag, str) and tag in CONTENT_TAGS for tag in tags), (
            f"{url}: invalid Reason content tag"
        )
        categories = entry.get("Categories")
        assert isinstance(categories, list) and len(categories) == 1, (
            f"{url}: expected one primary category"
        )
        category = categories[0]
        assert category.get("ContentType") == "instrument_patch" and (
            category.get("Primary"), category.get("Sub")
        ) in CATEGORY_PAIRS, (
            f"{url}: invalid instrument category"
        )
        by_url[url] = entry

    expected = {
        prefix + path.relative_to(PUBLIC).as_posix()
        for path in patches
    }
    assert set(by_url) == expected, "YouKnow.rsmeta and Resources/Public differ"
    return len(files)


def validate_preset_levels(patches):
    data = json.loads(LEVELS_PATH.read_text(encoding="utf-8"))
    assert data["format"] == 1
    assert data["target_peak"] == .18 and data["target_rms"] == .04
    trims = data["preset_gain"]
    measurements = data["measurements"]
    expected = {path.relative_to(PUBLIC).as_posix() for path in patches}
    assert set(trims) == set(measurements) == expected, (
        "preset level table differs from public bank"
    )
    for path in patches:
        relative = path.relative_to(PUBLIC).as_posix()
        values, _ = read_patch(path)
        assert abs(values["presetGain"] - float(trims[relative])) < 1e-9, (
            f"{relative}: preset level differs from calibration table"
        )
        assert 0.0 <= values["presetGain"] <= 1.0
    return len(trims)


def main():
    validate_sdk5_declarations()
    validate_support_url()
    text_count = validate_texts()
    root_patches = sorted(PUBLIC.glob("*.repatch"))
    assert 5 <= len(root_patches) <= 20, (
        f"public root should contain 5-20 featured patches, found {len(root_patches)}"
    )
    category_directories = {path.name for path in PUBLIC.iterdir() if path.is_dir()}
    assert category_directories == ORIGINAL_CATEGORIES, (
        f"categorized bank differs: {sorted(category_directories)}"
    )
    for category in sorted(ORIGINAL_CATEGORIES):
        count = len(list((PUBLIC / category).glob("*.repatch")))
        assert count >= 4, f"{category}: expected at least four categorized patches"
    patches = sorted(PUBLIC.rglob("*.repatch"))
    assert len(patches) == 100, f"expected 100 public patches, found {len(patches)}"
    original_paths = runpy.run_path(
        str(PROJECT / "Design" / "generate_presets.py")
    )["ORIGINAL_PATCH_PATHS"]
    assert {path.relative_to(PUBLIC).as_posix() for path in patches} == original_paths, (
        "public bank differs from the reviewed original patch catalog"
    )
    level_count = validate_preset_levels(patches)
    init_values, init_types = read_patch(PUBLIC / "Init.repatch")
    signatures = {}
    for path in patches:
        relative = path.relative_to(PUBLIC).as_posix()
        assert relative.isascii(), f"{relative}: patch path must be ASCII"
        values, types = read_patch(path)
        assert values.keys() == init_values.keys(), f"{path.name}: property set drift"
        assert types == init_types, f"{path.name}: property type drift"
        signature = tuple(
            values[name] for name in init_values if name != "presetGain"
        )
        assert signature not in signatures, (
            f"{path.name}: duplicates {signatures.get(signature)}"
        )
        signatures[signature] = relative
    metadata_count = validate_metadata(patches)
    print(
        f"YouKnow: {text_count} text keys valid; {len(patches)} unique patches, "
        f"{metadata_count} metadata entries; {level_count} deterministic level trims; "
        "SDK 5/schema/ranges/identity valid"
    )


if __name__ == "__main__":
    main()
