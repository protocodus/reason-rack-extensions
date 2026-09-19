#!/usr/bin/env python3
"""Static verification of the Maremba Rack Extension declarations.

The Lua files are evaluated for real with the SDK's Lua 5.1 interpreter and a
recording jbox mock, then cross-checked: motherboard properties, display ranges,
texts.lua, Remote / MIDI charts, ui_groups, the Maremba.h parameter tables, CV
sockets against the wrapper functions that read them and realtime_controller.lua,
the GUI (hdgui_2D nodes against device_2D, widget coverage and bindings,
GUI/Output/gui.lua sync), and a static scan of DSP/ and the wrapper for heap
allocation outside the constructor-time allowlist.

validate_patches.py imports the loader from this file.
"""

import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("JUKEBOX_SDK_DIR", os.path.join(PROJECT, "..", ".."))
))
PRODUCT_ID = "cz.protocodus.Maremba"

# The final document_owner property set in declaration order (steps for stepped
# properties, None for continuous). Renaming, removing or re-stepping any of them
# after release breaks saved songs and patches (Tools/Build/motherboard_diff.lua).
EXPECTED_PROPERTIES = [
    ("model", 4), ("malletType", 4), ("malletHardness", None), ("strikePosition", None),
    ("strikeJitter", None), ("resonatorTune", None), ("resonatorCoupling", None),
    ("decay", None), ("buzzAmount", None), ("artifacts", None), ("sympathetic", None),
    ("pitchGlide", None), ("bodyBloom", None), ("closeLevel", None), ("farLevel", None),
    ("piezoLevel", None), ("stereoWidth", None), ("preampDrive", None), ("warmth", None),
    ("compAmount", None), ("compAttack", None), ("compRelease", None), ("volume", None),
    ("oversampling", 3), ("velocityCurve", 4), ("polyphony", 3), ("masterTune", None),
    ("detune", None),
]
EXPECTED_PERFORMANCE = ["modWheel", "pitchBend"]
# Reason's performance controllers declare no Lua default; these are the SDK rest positions.
PERFORMANCE_DEFAULTS = {"modWheel": 0.0, "pitchBend": 0.5}

# Socket names and order are part of saved cable routing.
EXPECTED_CV_INPUTS = ["note_cv", "gate_cv", "mallet_cv", "position_cv",
                      "coupling_cv", "volume_cv", "sympathetic_cv"]
EXPECTED_AUDIO_OUTPUTS = ["left", "right", "close_left", "close_right",
                          "far_left", "far_right", "piezo"]

# midi_cc_chart ids that belonged to removed properties and must never be reused.
RETIRED_MIDI_IDS = {258}

# The displayed range must describe the wrapper's 0..1 -> physical mapping
# (Maremba.cpp): (min, max, unit template key). Unlisted continuous properties
# are plain 0.00..1.00 amounts.
DISPLAY_RANGES = {
    "strikeJitter": (0.0, 100.0, "percent template"),
    "resonatorTune": (-50.0, 50.0, "cents template"),
    "decay": (0.10, 8.0, "multiplier template"),
    "stereoWidth": (0.0, 2.0, None),
    "warmth": (-1.0, 1.0, None),
    "compAttack": (1.0, 50.0, "ms template"),
    "compRelease": (20.0, 500.0, "ms template"),
    "masterTune": (-100.0, 100.0, "cents template"),
    "detune": (0.0, 100.0, "detune cents template"),
}

PANELS = ["front", "folded_front", "back", "folded_back"]

# ---------------------------------------------------------------------------
# Lua evaluation
# ---------------------------------------------------------------------------

# Runs one Lua file in its own environment with a jbox mock that records every
# call as { __jbox = name, __seq = call order, args = ... } and prints the
# file's globals as JSON. __seq gives declaration order, which Lua tables lose.
LUA_DRIVER = r"""
local path = arg[1]
local seq = 0
local jbox = setmetatable({}, { __index = function(_, name)
    return function(args)
        seq = seq + 1
        return { __jbox = name, __seq = seq, args = args }
    end
end })
-- Top-level jbox.add_* / set_* routing calls return nothing to assign, so
-- they are collected in __calls.
local calls = {}
local recording = setmetatable({}, { __index = function(_, name)
    local f = jbox[name]
    if name:find("^add_") or name:find("^set_") then
        return function(args)
            local rec = f(args)
            calls[#calls + 1] = rec
            return rec
        end
    end
    return f
end })
local env = setmetatable({ jbox = recording }, { __index = _G })

local chunk, err
if setfenv then
    chunk, err = loadfile(path)
    if chunk then setfenv(chunk, env) end
else
    chunk, err = loadfile(path, "t", env)
end
if not chunk then
    io.stderr:write(tostring(err) .. "\n")
    os.exit(2)
end
local ok, runerr = pcall(chunk)
if not ok then
    io.stderr:write(tostring(runerr) .. "\n")
    os.exit(3)
end

local out = {}
local function emit(s) out[#out + 1] = s end
local function encode_string(s)
    s = s:gsub('[%c"\\]', function(c)
        if c == '"' then return '\\"' end
        if c == "\\" then return "\\\\" end
        return string.format("\\u%04x", c:byte())
    end)
    return '"' .. s .. '"'
end
local function encode(v, depth)
    if depth > 64 then error("table nesting too deep") end
    local t = type(v)
    if t == "table" then
        local count, n = 0, #v
        for _ in pairs(v) do count = count + 1 end
        if n > 0 and count == n then
            emit("[")
            for i = 1, n do
                if i > 1 then emit(",") end
                encode(v[i], depth + 1)
            end
            emit("]")
        else
            emit("{")
            local first = true
            for k, item in pairs(v) do
                if not first then emit(",") end
                first = false
                emit(encode_string(tostring(k)))
                emit(":")
                encode(item, depth + 1)
            end
            emit("}")
        end
    elseif t == "string" then
        emit(encode_string(v))
    elseif t == "number" then
        if v ~= v then emit("NaN")
        elseif v == math.huge then emit("Infinity")
        elseif v == -math.huge then emit("-Infinity")
        else emit(string.format("%.17g", v)) end
    elseif t == "boolean" then
        emit(tostring(v))
    else
        emit(encode_string("<" .. t .. ">"))
    end
end

local globals = {}
for k, v in pairs(env) do
    if k ~= "jbox" then globals[k] = v end
end
globals.__calls = calls
encode(globals, 0)
io.write(table.concat(out))
"""


class ValidationError(Exception):
    pass


def find_lua():
    """The SDK's bundled Lua 5.1, falling back to a Lua on PATH."""
    system = platform.system()
    candidates = []
    if system == "Darwin":
        candidates.append(os.path.join(SDK_DIR, "Tools", "Build", "Lua", "Mac", "lua"))
    elif system == "Windows":
        candidates.append(os.path.join(SDK_DIR, "Tools", "Build", "Lua", "Win", "lua.exe"))
    for name in ("lua5.1", "lua"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise ValidationError(
        "no Lua interpreter found (expected the SDK's Tools/Build/Lua; set JUKEBOX_SDK_DIR)"
    )


_LUA_CACHE = {}


def load_lua(relative_path):
    """Evaluate a project Lua file and return its globals as Python data."""
    if relative_path in _LUA_CACHE:
        return _LUA_CACHE[relative_path]
    path = os.path.join(PROJECT, relative_path)
    if not os.path.exists(path):
        raise ValidationError(f"{relative_path} does not exist")
    result = subprocess.run(
        [find_lua(), "-", path], input=LUA_DRIVER, capture_output=True,
        text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        raise ValidationError(f"{relative_path} failed to evaluate: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    _LUA_CACHE[relative_path] = data
    return data


def is_call(value, name=None):
    return isinstance(value, dict) and "__jbox" in value and (
        name is None or value["__jbox"] == name
    )


def iter_calls(value):
    """Every recorded jbox call anywhere inside value."""
    if isinstance(value, dict):
        if "__jbox" in value:
            yield value
        for item in value.values():
            yield from iter_calls(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_calls(item)


def ui_text_keys(value):
    return {call["args"] for call in iter_calls(value) if call["__jbox"] == "ui_text"}


def text_key(value):
    """The key of a jbox.ui_text(...) value, or None."""
    return value["args"] if is_call(value, "ui_text") else None


def as_list(value):
    """A Lua array; the driver encodes an empty table as {}."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and not value:
        return []
    if isinstance(value, dict) and "__jbox" not in value:
        return [value[k] for k in sorted(value, key=lambda k: int(k)) if k.isdigit()]
    return [value]


def by_declaration_order(table):
    """Names of a Lua table of jbox declarations, in source order."""
    return [name for name, _ in sorted(table.items(), key=lambda item: item[1]["__seq"])]


class Motherboard:
    """motherboard_def.lua, evaluated."""

    def __init__(self):
        g = load_lua("motherboard_def.lua")
        self.globals = g
        property_set = g.get("custom_properties")
        if not is_call(property_set, "property_set"):
            raise ValidationError("motherboard_def.lua: custom_properties is not a jbox.property_set")
        owners = property_set["args"]
        # name -> {owner, kind, args, seq}
        self.properties = {}
        for owner, block in owners.items():
            for name, decl in (block.get("properties") or {}).items():
                if not is_call(decl):
                    raise ValidationError(f"motherboard_def.lua: {owner}.{name} is not a jbox declaration")
                if name in self.properties:
                    raise ValidationError(f"motherboard_def.lua: property {name} declared twice")
                self.properties[name] = {
                    "owner": owner, "kind": decl["__jbox"],
                    "args": decl["args"] if isinstance(decl["args"], dict) else {},
                    "seq": decl["__seq"],
                }
        document = [n for n, p in self.properties.items() if p["owner"] == "document_owner"]
        document.sort(key=lambda n: self.properties[n]["seq"])
        self.document = document
        self.performance = [n for n in document if self.properties[n]["kind"].startswith("performance_")]
        self.sound = [n for n in document if n not in self.performance]
        # document_owner properties default to patch persistence.
        self.patch_persisted = [
            n for n in self.sound
            if self.properties[n]["args"].get("persistence", "patch") == "patch"
        ]
        self.midi = {
            int(k): v for k, v in
            ((g.get("midi_implementation_chart") or {}).get("midi_cc_chart") or {}).items()
        }
        self.remote = g.get("remote_implementation_chart") or {}
        self.ui_groups = as_list(g.get("ui_groups") or [])
        self.cv_inputs = by_declaration_order(g.get("cv_inputs") or {})
        self.cv_outputs = by_declaration_order(g.get("cv_outputs") or {})
        self.audio_inputs = by_declaration_order(g.get("audio_inputs") or {})
        self.audio_outputs = by_declaration_order(g.get("audio_outputs") or {})
        self.routing_calls = g.get("__calls") or []

    def steps(self, name):
        return self.properties[name]["args"].get("steps")

    def default(self, name):
        if name in PERFORMANCE_DEFAULTS:
            return PERFORMANCE_DEFAULTS[name]
        value = self.properties[name]["args"].get("default")
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        return float(value)

    def property_path_exists(self, path):
        prefix = "/custom_properties/"
        return path.startswith(prefix) and path[len(prefix):] in self.properties


def load_texts():
    texts = load_lua(os.path.join("Resources", "English", "texts.lua")).get("texts")
    if not isinstance(texts, dict):
        raise ValidationError("texts.lua defines no texts table")
    return texts


def info_value(name):
    return load_lua("info.lua").get(name)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

FAILURES = []


def check(cond, msg):
    if not cond:
        FAILURES.append(msg)
        print(f"  FAIL: {msg}")
    return cond


def read(relative_path):
    with open(os.path.join(PROJECT, relative_path), "r", encoding="utf-8") as f:
        return f.read()


def gui_output_exists():
    return os.path.exists(os.path.join(PROJECT, "GUI", "Output", "gui.lua"))


def test_sdk_declarations():
    info = load_lua("info.lua")
    versions = {
        "info.lua": (info, "2.0"),
        "motherboard_def.lua": (load_lua("motherboard_def.lua"), "4.0"),
        "realtime_controller.lua": (load_lua("realtime_controller.lua"), "1.0"),
        "GUI2D/device_2D.lua": (load_lua(os.path.join("GUI2D", "device_2D.lua")), "2.0"),
        "GUI2D/hdgui_2D.lua": (load_lua(os.path.join("GUI2D", "hdgui_2D.lua")), "2.0"),
        "texts.lua": (load_lua(os.path.join("Resources", "English", "texts.lua")), "1.0"),
    }
    if gui_output_exists():
        versions["GUI/Output/gui.lua"] = (load_lua(os.path.join("GUI", "Output", "gui.lua")), "4.0")
    for name, (globals_, expected) in versions.items():
        check(globals_.get("format_version") == expected,
              f"{name} must use format_version {expected}, has {globals_.get('format_version')}")

    check(info.get("product_id") == PRODUCT_ID, f"info.lua product_id must be {PRODUCT_ID}")
    for field, limit in (("long_name", 40), ("medium_name", 20), ("short_name", 10)):
        value = info.get(field)
        check(isinstance(value, str) and 0 < len(value) <= limit,
              f"info.lua {field} must be 1..{limit} characters")
    check(info.get("supports_patches") is True, "supports_patches must be true")
    check(info.get("supports_performance_automation") is True,
          "supports_performance_automation must be true")
    check(re.fullmatch(r"\d+\.\d+\.\d+[bdf]\d+", str(info.get("version_number"))),
          f"invalid version_number {info.get('version_number')}")
    default_patch = str(info.get("default_patch", "")).lstrip("/")
    check(default_patch and os.path.exists(os.path.join(PROJECT, "Resources", default_patch)),
          f"default_patch not found: {default_patch}")
    return "format versions, identity, names, version and default patch"


def test_properties_and_display(mb):
    expected_names = [name for name, _ in EXPECTED_PROPERTIES]
    check(mb.sound == expected_names,
          f"document_owner sound properties differ from the contract set/order: "
          f"missing {sorted(set(expected_names) - set(mb.sound))}, "
          f"unexpected {sorted(set(mb.sound) - set(expected_names))}")
    check(mb.performance == EXPECTED_PERFORMANCE,
          f"performance properties must be {EXPECTED_PERFORMANCE}, found {mb.performance}")
    check(mb.document == expected_names + EXPECTED_PERFORMANCE,
          "performance controllers must be declared after the sound properties")

    for name, steps in EXPECTED_PROPERTIES:
        if name not in mb.properties:
            continue
        prop = mb.properties[name]
        args = prop["args"]
        check(prop["kind"] == "number", f"{name} must be a jbox.number")
        check(args.get("steps") == steps, f"{name}: steps {args.get('steps')} != {steps}")
        check(args.get("persistence", "patch") == "patch", f"{name} must be patch-persisted")
        check(text_key(args.get("ui_name")) is not None, f"{name} has no jbox.ui_text ui_name")
        default = args.get("default")
        ui_type = args.get("ui_type")
        if steps:
            check(isinstance(default, (int, float)) and float(default).is_integer()
                  and 0 <= default < steps, f"{name}: default {default} is not a step index")
            items = as_list(ui_type["args"]) if is_call(ui_type, "ui_selector") else None
            check(items is not None and len(items) == steps,
                  f"{name}: ui_selector must list exactly {steps} texts")
            continue
        check(isinstance(default, (int, float)) and 0.0 <= default <= 1.0,
              f"{name}: default {default} outside 0..1")
        if not check(is_call(ui_type, "ui_linear"), f"{name}: expected a ui_linear display"):
            continue
        lo, hi, template = DISPLAY_RANGES.get(name, (0.0, 1.0, None))
        linear = ui_type["args"]
        check(abs(float(linear.get("min", 0)) - lo) < 1e-9 and abs(float(linear.get("max", 1)) - hi) < 1e-9,
              f"{name}: displayed range {linear.get('min')}..{linear.get('max')} does not match the "
              f"wrapper mapping {lo}..{hi}")
        units = as_list(linear.get("units") or [])
        templates = [text_key((u.get("unit") or {}).get("template")) for u in units if isinstance(u, dict)]
        check((templates == [template]) if template else all(t is None for t in templates),
              f"{name}: unit template {templates} should be {template}")
    return (f"{len(mb.sound)} sound properties + {len(mb.performance)} performance controllers, "
            "steps, defaults and displayed ranges")


def gui_sources():
    """(label, globals) of every GUI Lua file that can reference texts."""
    sources = [("GUI2D/hdgui_2D.lua", load_lua(os.path.join("GUI2D", "hdgui_2D.lua")))]
    if gui_output_exists():
        sources.append(("GUI/Output/gui.lua", load_lua(os.path.join("GUI", "Output", "gui.lua"))))
    return sources


def test_texts(mb):
    texts = load_texts()
    source = read(os.path.join("Resources", "English", "texts.lua"))
    keys_in_source = re.findall(r'^\s*\["([^"]+)"\]\s*=', source, re.MULTILINE)
    duplicates = sorted({k for k in keys_in_source if keys_in_source.count(k) > 1})
    check(not duplicates, f"texts.lua defines keys twice: {duplicates}")

    used = {"motherboard_def.lua": ui_text_keys(mb.globals)}
    for label, globals_ in gui_sources():
        used[label] = ui_text_keys(globals_)
    all_used = set().union(*used.values())
    for label, keys in used.items():
        missing = sorted(keys - set(texts))
        check(not missing, f"{label} uses texts missing from texts.lua: {missing}")
    unused = sorted(set(texts) - all_used)
    check(not unused, f"texts.lua keys used nowhere (dead): {unused}")

    templates = {
        text_key((unit.get("unit") or {}).get("template"))
        for call in iter_calls(mb.globals) if call["__jbox"] in ("ui_linear", "ui_nonlinear")
        for unit in as_list(call["args"].get("units") or []) if isinstance(unit, dict)
    }
    templates.discard(None)
    templates |= {key for key in texts if key.endswith("template")}
    for key in sorted(templates):
        check("^0" in str(texts.get(key, "")), f"template '{key}' must contain ^0")
    for key, value in texts.items():
        check(isinstance(value, str) and value.strip(), f"texts.lua '{key}' is empty")
    return f"{len(all_used)} text keys used and defined, none dead, {len(templates)} templates contain ^0"


def test_remote_and_midi(mb):
    texts = load_texts()
    source = read("motherboard_def.lua")
    automatable = set(mb.sound)

    remote_props = set()
    internal_names = []
    for path, entry in mb.remote.items():
        name = path[len("/custom_properties/"):] if path.startswith("/custom_properties/") else path
        check(mb.property_path_exists(path) and name in automatable,
              f"remote chart references {path}, which is not a document_owner sound property")
        remote_props.add(name)
        internal = entry.get("internal_name")
        check(isinstance(internal, str) and 0 < len(internal) <= 64, f"{path}: bad internal_name")
        internal_names.append(internal)
        for field, limit in (("short_ui_name", 8), ("shortest_ui_name", 4)):
            key = text_key(entry.get(field))
            value = texts.get(key, "")
            check(key is not None and 0 < len(value) <= limit,
                  f"{path}: {field} '{value}' must be 1..{limit} characters")
    check(len(internal_names) == len(set(internal_names)), "remote internal_names must be unique")
    check(remote_props == automatable,
          f"remote chart must cover every sound property: missing {sorted(automatable - remote_props)}")

    # Lua silently keeps the last of duplicated keys, so scan the source too.
    ids_in_source = [int(x) for x in re.findall(r'\[(\d+)\]\s*=\s*"/custom_properties/', source)]
    check(len(ids_in_source) == len(set(ids_in_source)), "duplicate midi_cc_chart ids in motherboard_def.lua")
    check(not (set(mb.midi) & RETIRED_MIDI_IDS),
          f"retired midi_cc_chart ids reused: {sorted(set(mb.midi) & RETIRED_MIDI_IDS)}")
    midi_props = []
    for cc, path in mb.midi.items():
        check(mb.property_path_exists(path) and path.rsplit("/", 1)[-1] in automatable,
              f"midi_cc_chart[{cc}] references {path}, which is not a document_owner sound property")
        midi_props.append(path.rsplit("/", 1)[-1])
    check(len(midi_props) == len(set(midi_props)), "a property has more than one midi_cc_chart id")
    check(set(midi_props) == remote_props,
          f"midi_cc_chart and remote chart disagree: {sorted(set(midi_props) ^ remote_props)}")
    return f"{len(mb.remote)} Remote entries and {len(mb.midi)} automation ids reference real properties"


def test_ui_groups(mb):
    texts = load_texts()
    automatable = [n for n in mb.sound if f"/custom_properties/{n}" in mb.remote]
    if not check(mb.ui_groups, "motherboard_def.lua declares no ui_groups"):
        return
    seen = {}
    for index, group in enumerate(mb.ui_groups):
        key = text_key(group.get("ui_name"))
        check(key in texts, f"ui_groups[{index + 1}] ui_name must be a defined jbox.ui_text")
        members = as_list(group.get("properties") or [])
        check(2 <= len(members) <= 20,
              f"ui_group '{texts.get(key, key)}' has {len(members)} entries (2..20 allowed)")
        for path in members:
            check(mb.property_path_exists(path), f"ui_group '{texts.get(key, key)}' lists unknown {path}")
            name = path.rsplit("/", 1)[-1]
            check(name in automatable or name in mb.performance,
                  f"ui_group lists {path}, which is not automatable")
            check(name not in seen, f"{path} is in more than one ui_group")
            seen[name] = key
    ungrouped = [n for n in automatable if n not in seen]
    check(not ungrouped, f"automatable properties outside every ui_group: {ungrouped}")
    root_items = len(mb.ui_groups) + len([n for n in mb.performance if n not in seen])
    check(root_items <= 20, f"automation menu root has {root_items} items (max 20)")
    return (f"{len(mb.ui_groups)} ui_groups cover all {len(automatable)} automatable properties "
            f"({root_items} root menu items)")


def cpp_array(header, name):
    match = re.search(rf"{name}\s*\{{(.*?)\}};", header, re.DOTALL)
    check(match, f"Maremba.h has no {name} table")
    return match.group(1) if match else ""


def test_cpp_parameter_table(mb):
    header = read("Maremba.h")
    enum = re.search(r"enum EParameter\s*\{(.*?)kParameterCount", header, re.DOTALL)
    if not check(enum, "Maremba.h has no EParameter enum"):
        return
    enumerators = re.findall(r"\bk(\w+)\s*,", re.sub(r"//[^\n]*", "", enum.group(1)))
    names = re.findall(r'"([^"]+)"', re.sub(r"//[^\n]*", "", cpp_array(header, "kParameterNames")))
    rows = []
    for line in cpp_array(header, "kParameterDefaults").splitlines():
        m = re.match(r"\s*([-+0-9.eE]+)\s*,?\s*//\s*(\w+)", line)
        if m:
            rows.append((float(m.group(1)), m.group(2)))
        elif line.strip() and not line.strip().startswith("//"):
            check(False, f"kParameterDefaults row not in '<value>, // <name>' form: {line.strip()}")

    first_difference = next((i for i, pair in enumerate(zip(names, mb.document)) if pair[0] != pair[1]),
                            min(len(names), len(mb.document)))
    check(names == mb.document,
          f"kParameterNames must list the document_owner properties in motherboard order: "
          f"missing {[n for n in mb.document if n not in names]}, extra {[n for n in names if n not in mb.document]}, "
          f"first difference at index {first_difference}")
    check(len(enumerators) == len(names) == len(rows),
          f"EParameter ({len(enumerators)}), kParameterNames ({len(names)}) and "
          f"kParameterDefaults ({len(rows)}) must have the same length")
    for enumerator, name, (value, label) in zip(enumerators, names, rows):
        check(enumerator.lower() == name.lower(), f"EParameter k{enumerator} does not match name '{name}'")
        check(label == name, f"kParameterDefaults row '{label}' is not in kParameterNames order ('{name}')")
        if name in mb.properties:
            check(abs(value - mb.default(name)) < 1e-9,
                  f"{name}: C++ default {value} != motherboard default {mb.default(name)}")
    return f"Maremba.h parameter tables ({len(names)} entries) match motherboard names, order and defaults"


# ---------------------------------------------------------------------------
# C++ source scanning (comments, strings and preprocessor lines blanked out,
# offsets and line numbers preserved)
# ---------------------------------------------------------------------------

def strip_cpp(source):
    """source with comments, string/char literal contents and # lines replaced by spaces."""
    out = list(source)
    i, n = 0, len(source)

    def blank(start, end):
        for k in range(start, end):
            if out[k] != "\n":
                out[k] = " "

    at_line_start = True
    while i < n:
        c = source[i]
        if at_line_start and c == "#":
            end = i
            while end < n and not (source[end] == "\n" and source[end - 1] != "\\"):
                end += 1
            blank(i, end)
            i = end
            continue
        if c == "\n":
            at_line_start = True
            i += 1
            continue
        if not c.isspace():
            at_line_start = False
        if source.startswith("//", i):
            end = source.find("\n", i)
            end = n if end < 0 else end
            blank(i, end)
            i = end
        elif source.startswith("/*", i):
            end = source.find("*/", i + 2)
            end = n if end < 0 else end + 2
            blank(i, end)
            i = end
        elif c == '"' or (c == "'" and not (i > 0 and source[i - 1].isalnum())):  # not a digit separator
            end = i + 1
            while end < n and source[end] != c:
                end += 2 if source[end] == "\\" else 1
            blank(i + 1, min(end, n))
            i = end + 1
        else:
            i += 1
    return "".join(out)


CONTROL_WORDS = {"if", "for", "while", "switch", "catch", "constexpr", "return", "sizeof",
                 "alignas", "alignof", "decltype", "static_assert", "noexcept"}
FUNCTION_TAIL = re.compile(
    r"\s*(?:const\s*)?(?:noexcept\s*(?:\([^)]*\))?\s*)?(?:override\s*)?(?:final\s*)?"
    r"(?:->\s*[\w:<>,\s*&]+)?(?::.*)?$", re.DOTALL)


def classify_block(header):
    """('class', name) or ('function', name) for the text before a '{', else None."""
    m = re.search(r"\b(?:class|struct|union)\s+(?:alignas\s*\([^)]*\)\s*)?(\w+)[^(){};]*$", header)
    if m:
        return "class", m.group(1)
    m = re.search(r"(~?[A-Za-z_]\w*(?:\s*::\s*~?[A-Za-z_]\w*)*)\s*\(", header)
    if not m or m.group(1).split("::")[-1].strip() in CONTROL_WORDS:
        return None
    if re.search(r"[=\[(,]|\breturn\b", header[:m.start()]):
        return None  # an initializer, lambda or call argument, not a definition
    depth = 0
    for k in range(m.end() - 1, len(header)):
        depth += {"(": 1, ")": -1}.get(header[k], 0)
        if depth == 0:
            return ("function", re.sub(r"\s+", "", m.group(1))) if FUNCTION_TAIL.match(header[k + 1:]) else None
    return None


def cpp_blocks(code):
    """[(kind, name, open, close)] for every class and function body of stripped code."""
    blocks, stack = [], []
    for i, ch in enumerate(code):
        if ch == "{":
            start = max(code.rfind(";", 0, i), code.rfind("{", 0, i), code.rfind("}", 0, i)) + 1
            stack.append((classify_block(code[start:i]), i))
        elif ch == "}" and stack:
            kind_name, open_ = stack.pop()
            if kind_name:
                blocks.append((kind_name[0], kind_name[1], open_, i))
    return blocks


def qualify(blocks, block):
    """'Class::function' of a function block (its class from the name or the enclosing class)."""
    _, name, open_, _ = block
    if "::" in name:
        return name
    classes = [b for b in blocks if b[0] == "class" and b[2] < open_ < b[3]]
    return f"{max(classes, key=lambda b: b[2])[1]}::{name}" if classes else name


def enclosing_function(blocks, pos):
    """Qualified name of the innermost function whose body contains pos, else None."""
    functions = [b for b in blocks if b[0] == "function" and b[2] < pos <= b[3]]
    return qualify(blocks, max(functions, key=lambda b: b[2])) if functions else None


def is_constructor(qualified):
    parts = qualified.split("::") if qualified else []
    return len(parts) >= 2 and parts[-1] == parts[-2]


def function_body(code, blocks, qualified):
    """Stripped body text of the function whose qualified name is given, or None."""
    for block in blocks:
        if block[0] == "function" and qualify(blocks, block) == qualified:
            return code[block[2]:block[3] + 1]
    return None


# The wrapper functions that turn a CV input into sound: the modulation CVs are
# summed into their knob in LoadEngineParameters, Note and Gate drive the CV
# keyboard. A socket whose ECVInput enumerator appears only in the enum and the
# kCVPaths table is declared but dead (the removed roll_cv defect).
CV_READERS = ("CMaremba::LoadEngineParameters", "CMaremba::HandleCV", "CMaremba::CurrentCVNote")


def test_cv_and_rtc(mb):
    check(mb.cv_inputs == EXPECTED_CV_INPUTS,
          f"cv_inputs must be {EXPECTED_CV_INPUTS} in this order, found {mb.cv_inputs}")
    check(mb.audio_outputs == EXPECTED_AUDIO_OUTPUTS,
          f"audio_outputs must be {EXPECTED_AUDIO_OUTPUTS} in this order, found {mb.audio_outputs}")

    header, source = read("Maremba.h"), read("Maremba.cpp")
    cpp = source + header
    # kCVPaths (indexed by ECVInput) must list the declared sockets in order, so
    # each enumerator names exactly one socket.
    table = re.search(r"kCVPaths\[\]\s*\{(.*?)\};", source, re.DOTALL)
    cv_paths = re.findall(r'"/cv_inputs/(\w+)"', table.group(1)) if table else []
    check(cv_paths == mb.cv_inputs,
          f"Maremba.cpp kCVPaths must list the declared cv_inputs in order: {cv_paths} != {mb.cv_inputs}")
    enum = re.search(r"enum ECVInput\s*\{(.*?)\bkCVCount\b", strip_cpp(header), re.DOTALL)
    enumerators = re.findall(r"\b(k\w+)\b", enum.group(1)) if enum else []
    check(len(enumerators) == len(mb.cv_inputs),
          f"Maremba.h enum ECVInput has {len(enumerators)} inputs, motherboard declares {len(mb.cv_inputs)}")

    code = strip_cpp(source)
    blocks = cpp_blocks(code)
    readers = {name: function_body(code, blocks, name) for name in CV_READERS}
    for name, body in readers.items():
        check(body is not None, f"Maremba.cpp defines no {name} (update CV_READERS if it was renamed)")
    reader_code = "".join(body for body in readers.values() if body)
    for enumerator, socket in zip(enumerators, mb.cv_inputs):
        check(enumerator.lower() == "k" + socket.replace("_", "").lower(),
              f"ECVInput {enumerator} does not name the socket at its position, {socket}")
        check(re.search(rf"\b{enumerator}\b", reader_code),
              f"CV input {socket} ({enumerator}) is declared but never read by "
              f"{', '.join(n.split('::')[-1] for n in CV_READERS)}")
    audio_used = set(re.findall(r'"/audio_outputs/(\w+)', cpp))
    check(audio_used <= set(mb.audio_outputs),
          f"Maremba.cpp uses undeclared audio outputs {sorted(audio_used - set(mb.audio_outputs))}")

    rtc = load_lua("realtime_controller.lua")
    notify = as_list((rtc.get("rt_input_setup") or {}).get("notify") or [])
    for cv in mb.cv_inputs:
        for field in ("value", "connected"):
            check(f"/cv_inputs/{cv}/{field}" in notify, f"rt_input_setup.notify lacks /cv_inputs/{cv}/{field}")
    for path in notify:
        m = re.match(r"/cv_inputs/(\w+)/", path)
        if m:
            check(m.group(1) in mb.cv_inputs, f"rt_input_setup.notify references undeclared {path}")
        m = re.match(r"/custom_properties/(\w+)$", path)
        if m:
            check(m.group(1) in mb.properties, f"rt_input_setup.notify references undeclared {path}")
    rtc_source = read("realtime_controller.lua")
    for out in mb.audio_outputs:
        check(f'"/audio_outputs/{out}/dsp_latency"' in rtc_source, f"realtime_controller sets no dsp_latency for {out}")

    sockets = {f"/cv_inputs/{n}" for n in mb.cv_inputs} | {f"/audio_outputs/{n}" for n in mb.audio_outputs}
    for call in mb.routing_calls:
        for key, path in call["args"].items():
            if isinstance(path, str) and path.startswith("/"):
                check(path in sockets, f"jbox.{call['__jbox']} {key} references undeclared {path}")
    return (f"{len(mb.cv_inputs)} CV inputs declared, each read by the wrapper "
            f"({', '.join(n.split('::')[-1] for n in CV_READERS)}) and notified; "
            f"{len(mb.audio_outputs)} audio outputs")


# The audio thread must never allocate. DSP/ and the wrapper are scanned;
# JukeboxExports.cpp is not, since CreateNativeObject is where Reason expects the
# instance to be allocated.
RT_SOURCES = ("DSP/*.h", "DSP/*.cpp", "Maremba.h", "Maremba.cpp")
RT_ALLOCATIONS = (
    (r"\b(?:malloc|calloc|realloc|aligned_alloc|posix_memalign)\s*\(", "C heap allocation"),
    (r"\bnew\b(?!\s*\((?!\s*(?:std\s*::\s*)?nothrow\b))", "new expression"),  # placement new is fine
    (r"(?:\.|->)\s*(?:assign|resize|reserve|push_back|emplace_back|push_front|emplace_front|insert|emplace)\s*\(",
     "container growth"),
    (r"\bstd\s*::\s*(?:make_unique|make_shared|allocate_shared)\b", "smart-pointer allocation"),
)
# A standard container or std::function object inside a function body allocates
# when it is built or grows (declaring a member is fine; growing it is caught above).
RT_CONTAINER = (r"\bstd\s*::\s*(?:vector|basic_string|string|deque|forward_list|list|multimap|map|multiset|set|"
                r"unordered_map|unordered_set|function)\b")
# The only functions allowed to allocate (qualified name -> file), each with its
# reason. They may be called only from a constructor or from another entry here,
# never from code the audio thread runs.
RT_ALLOCATION_ALLOWLIST = {
    # Sizes the room's delay lines once, for the highest internal rate
    # (8x the host rate); SetSampleRate only changes their active length.
    "AcousticRoom::Allocate": "DSP/AcousticRoom.h",
    # Forwards to AcousticRoom::Allocate from MarembaEngine's constructor.
    "MicMixer::Allocate": "DSP/MicMixer.h",
}


def test_realtime_allocation():
    files = sorted({os.path.relpath(p, PROJECT) for pattern in RT_SOURCES
                    for p in glob.glob(os.path.join(PROJECT, pattern))})
    scanned = {}
    for path in files:
        code = strip_cpp(read(path))
        scanned[path] = (code, cpp_blocks(code))

    def line(code, pos):
        return code.count("\n", 0, pos) + 1

    allowed_sites = 0
    for path, (code, blocks) in scanned.items():
        hits = [(m.start(), label) for pattern, label in RT_ALLOCATIONS for m in re.finditer(pattern, code)]
        hits += [(m.start(), "std container object") for m in re.finditer(RT_CONTAINER, code)
                 if enclosing_function(blocks, m.start())]
        for pos, label in sorted(hits):
            function = enclosing_function(blocks, pos)
            if RT_ALLOCATION_ALLOWLIST.get(function) == path:
                allowed_sites += 1
                continue
            check(False, f"{path}:{line(code, pos)}: {label} in {function or 'file scope'} "
                         "(the audio thread must not allocate; see RT_ALLOCATION_ALLOWLIST)")

    for allowed, path in RT_ALLOCATION_ALLOWLIST.items():
        code, blocks = scanned.get(path, ("", []))
        check(function_body(code, blocks, allowed) is not None,
              f"RT_ALLOCATION_ALLOWLIST names {allowed} in {path}, which no longer exists")
    for name in sorted({allowed.split("::")[-1] for allowed in RT_ALLOCATION_ALLOWLIST}):
        for caller_path, (code, blocks) in scanned.items():
            for m in re.finditer(rf"(?:\.|->)\s*{name}\s*\(", code):
                caller = enclosing_function(blocks, m.start())
                check(is_constructor(caller) or caller in RT_ALLOCATION_ALLOWLIST,
                      f"{caller_path}:{line(code, m.start())}: {caller or 'file scope'} calls {name}(), "
                      "which allocates; only a constructor may")
    return (f"no heap allocation in {len(files)} DSP/wrapper sources outside the "
            f"{len(RT_ALLOCATION_ALLOWLIST)} constructor-time allowlist entries ({allowed_sites} sites)")


def device_nodes(table):
    """Every node name inside a device_2D panel table (recursively)."""
    names = set()

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, (dict, list)) and not key.isdigit() and key not in ("offset", "size", "transform"):
                    names.add(key)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(table)
    return names


def panel_widgets(panel):
    return [w for w in as_list(panel["args"].get("widgets") or []) if is_call(w)]


def widget_node(widget):
    return (widget["args"].get("graphics") or {}).get("node")


def binding_paths(widget):
    args = widget["args"]
    paths = []
    if isinstance(args.get("value"), str):
        paths.append(args["value"])
    paths += [v for v in as_list(args.get("values") or []) if isinstance(v, str)]
    return paths


def test_gui_nodes():
    hdgui = load_lua(os.path.join("GUI2D", "hdgui_2D.lua"))
    device = load_lua(os.path.join("GUI2D", "device_2D.lua"))
    resolved = 0
    for panel_name in PANELS:
        panel = hdgui.get(panel_name)
        table = device.get(panel_name)
        if not check(is_call(panel, "panel"), f"hdgui_2D.lua: {panel_name} is not a jbox.panel"):
            continue
        if not check(isinstance(table, dict), f"device_2D.lua: no {panel_name} panel"):
            continue
        nodes = device_nodes(table)
        backdrop = (panel["args"].get("graphics") or {}).get("node")
        check(backdrop == "S_backdrop", f"{panel_name}: panel graphics.node must be S_backdrop, is {backdrop}")
        check("S_backdrop" in table, f"device_2D.lua {panel_name} has no top-level S_backdrop")
        origin = (panel["args"].get("cable_origin") or {}).get("node")
        if origin is not None:
            check(origin in nodes, f"{panel_name}: cable_origin node {origin} not in device_2D.{panel_name}")
        for widget in panel_widgets(panel):
            node = widget_node(widget)
            if check(node in nodes, f"{panel_name}: {widget['__jbox']} node {node} not in device_2D.{panel_name}"):
                resolved += 1
    return f"all 4 panels use S_backdrop and {resolved} widget nodes resolve in device_2D.lua"


def gui_bindings(globals_):
    """{(panel, kind, target, index)} for every value/socket binding of a GUI file."""
    bindings = set()
    for panel_name in PANELS:
        panel = globals_.get(panel_name)
        if not is_call(panel, "panel"):
            continue
        for widget in panel_widgets(panel):
            for path in binding_paths(widget):
                bindings.add((panel_name, widget["__jbox"], path, widget["args"].get("index")))
            socket = widget["args"].get("socket")
            if isinstance(socket, str):
                bindings.add((panel_name, widget["__jbox"], socket, None))
    return bindings


SOCKET_WIDGETS = {
    "cv_input_socket": "/cv_inputs/", "cv_output_socket": "/cv_outputs/",
    "audio_input_socket": "/audio_inputs/", "audio_output_socket": "/audio_outputs/",
}


def test_gui_bindings(mb):
    hdgui = load_lua(os.path.join("GUI2D", "hdgui_2D.lua"))
    declared_sockets = (
        {f"/cv_inputs/{n}" for n in mb.cv_inputs} | {f"/cv_outputs/{n}" for n in mb.cv_outputs}
        | {f"/audio_inputs/{n}" for n in mb.audio_inputs} | {f"/audio_outputs/{n}" for n in mb.audio_outputs}
    )
    bound = set()
    socket_count = {}
    for panel_name in PANELS:
        panel = hdgui.get(panel_name)
        if not is_call(panel, "panel"):
            continue
        radio = {}
        for widget in panel_widgets(panel):
            kind = widget["__jbox"]
            for path in binding_paths(widget):
                if not check(mb.property_path_exists(path), f"{panel_name}: {kind} binds unknown property {path}"):
                    continue
                name = path.rsplit("/", 1)[-1]
                bound.add(name)
                if kind == "radio_button":
                    steps = mb.steps(name)
                    index = widget["args"].get("index")
                    if check(steps, f"{panel_name}: radio_button on continuous property {name}"):
                        check(isinstance(index, (int, float)) and float(index).is_integer() and 0 <= index < steps,
                              f"{panel_name}: radio_button index {index} invalid for {name} (steps {steps})")
                        radio.setdefault(name, []).append(index)
            socket = widget["args"].get("socket")
            if kind in SOCKET_WIDGETS:
                check(isinstance(socket, str) and socket.startswith(SOCKET_WIDGETS[kind]) and socket in declared_sockets,
                      f"{panel_name}: {kind} references undeclared socket {socket}")
                check(panel_name == "back", f"{kind} {socket} must sit on the back panel")
                socket_count[socket] = socket_count.get(socket, 0) + 1
        for name, indices in radio.items():
            check(sorted(indices) == list(range(mb.steps(name))),
                  f"{panel_name}: radio buttons for {name} have indices {sorted(indices)}, "
                  f"expected one per step 0..{mb.steps(name) - 1}")
    missing = [n for n in mb.sound if n not in bound]
    check(not missing, f"sound properties without a widget in hdgui_2D.lua: {missing}")
    for socket in sorted(declared_sockets):
        check(socket_count.get(socket) == 1,
              f"{socket} needs exactly one socket widget, has {socket_count.get(socket, 0)}")

    if gui_output_exists():
        gui = load_lua(os.path.join("GUI", "Output", "gui.lua"))
        hd, local = gui_bindings(hdgui), gui_bindings(gui)
        check(hd == local,
              "GUI/Output/gui.lua bindings differ from hdgui_2D.lua: "
              f"hdgui-only {sorted(hd - local, key=str)}, gui.lua-only {sorted(local - hd, key=str)}")
    return (f"every sound property has a widget, {len(declared_sockets)} sockets bound once, "
            "radio indices valid")


def main():
    tests = [
        ("1. SDK declarations", lambda mb: test_sdk_declarations()),
        ("2. Properties & displayed ranges", test_properties_and_display),
        ("3. Localization texts", test_texts),
        ("4. Remote & automation charts", test_remote_and_midi),
        ("5. Automation groups (ui_groups)", test_ui_groups),
        ("6. Maremba.h parameter tables", test_cpp_parameter_table),
        ("7. CV inputs & realtime notifications", test_cv_and_rtc),
        ("8. hdgui_2D nodes vs device_2D", lambda mb: test_gui_nodes()),
        ("9. GUI widget bindings", test_gui_bindings),
        ("10. Realtime allocation (static)", lambda mb: test_realtime_allocation()),
    ]
    try:
        mb = Motherboard()
    except ValidationError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    for title, test in tests:
        print(f"--- {title} ---")
        before = len(FAILURES)
        try:
            summary = test(mb)
        except Exception as e:  # a malformed file must not hide the remaining checks
            check(False, f"check crashed: {type(e).__name__}: {e}")
            summary = None
        if len(FAILURES) == before:
            print(f"  PASS: {summary}")
    if FAILURES:
        sys.stdout.flush()
        print(f"\nFAILED: {len(FAILURES)} extension check(s) failed", file=sys.stderr)
        return 1
    print("\n>>> ALL MAREMBA EXTENSION STRUCTURAL CHECKS PASSED SUCCESSFULLY! <<<\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
