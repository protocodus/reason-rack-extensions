format_version = "4.0"

local function percent(name, default)
    return jbox.number{
        default = default,
        ui_name = jbox.ui_text(name),
        ui_type = jbox.ui_percent{ decimals = 0 },
        persistence = "patch",
    }
end

-- Physical-value readouts mirror the source plug-in while the stored values
-- remain the original 0..1 panel positions consumed by the engine.
local control_scan_hz = 1000 / 4.2
local envelope_peak = 0x3fff

local function clamp01(value)
    return math.max(0, math.min(1, value))
end

local function rounded_byte(value, maximum)
    return math.floor(clamp01(value) * maximum + 0.5)
end

local function attack_increment_for_byte(byte)
    if byte == 0 then return 0x4000 end
    if byte <= 63 then
        local value = math.floor((8192 + math.floor(byte / 2)) / byte)
        if byte == 3 or byte == 20 or byte == 28 then value = value - 1 end
        return value
    end
    if byte <= 80 then
        return 127 - math.floor(11 * (byte - 64) / 4)
    end
    if byte <= 86 then
        return 83 - math.floor((17 * (byte - 80) + 1) / 6)
    end
    if byte <= 107 then
        return 64 - math.floor(3 * (byte - 87) / 2)
    end
    if byte <= 121 then
        local numerator = 429 - 6 * (byte - 108)
        return math.floor((2 * numerator + 13) / 26)
    end
    return 26 - (byte - 122)
end

local function decay_multiplier_for_byte(byte)
    local value = 0x1000 + math.min(byte, 4) * 0x2000
    if byte >= 5 then value = value + 0x1000 end
    value = value + math.min(math.max(byte - 5, 0), 10) * 0x0800
    value = value + math.min(math.max(byte - 15, 0), 28) * 0x0080
    value = value + math.min(math.max(byte - 43, 0), 22) * 0x000c
    value = value + math.min(math.max(byte - 65, 0), 58) * 0x0004
    value = value + math.max(byte - 123, 0)
    return value
end

local function truncated_decay_product(value, coefficient)
    local value_high = math.floor(value / 256)
    local value_low = value % 256
    local coefficient_high = math.floor(coefficient / 256)
    local coefficient_low = coefficient % 256
    return coefficient_high * value_high
        + math.floor(coefficient_low * value_high / 256)
        + math.floor(coefficient_high * value_low / 256)
end

local function envelope_attack_seconds(position)
    local increment = attack_increment_for_byte(rounded_byte(position, 127))
    return math.floor((envelope_peak + increment - 1) / increment) / control_scan_hz
end

local function envelope_decay_seconds(position)
    local multiplier = decay_multiplier_for_byte(rounded_byte(position, 127))
    local level = envelope_peak
    local threshold = math.floor(envelope_peak / 10)
    local passes = 0
    while level > threshold and passes < 100000 do
        level = truncated_decay_product(level, multiplier)
        passes = passes + 1
    end
    return passes / control_scan_hz
end

local function envelope_release_seconds(position)
    local multiplier = decay_multiplier_for_byte(rounded_byte(position, 127))
    local level = envelope_peak
    local passes = 0
    while level ~= 0 and passes < 100000 do
        level = truncated_decay_product(level, multiplier)
        passes = passes + 1
    end
    return passes / control_scan_hz
end

local function lfo_rate_increment_for_byte(byte)
    local value = 5 + math.min(byte, 2) * 10
    value = value + math.min(math.max(byte - 2, 0), 3) * 15
    value = value + math.min(math.max(byte - 5, 0), 58) * 10
    value = value + math.min(math.max(byte - 63, 0), 32) * 16
    value = value + math.min(math.max(byte - 95, 0), 7) * 52
    if byte >= 103 then value = value + 54 end
    value = value + math.min(math.max(byte - 103, 0), 2) * 70
    value = value + math.min(math.max(byte - 105, 0), 4) * 80
    value = value + math.min(math.max(byte - 109, 0), 10) * 100
    value = value + math.min(math.max(byte - 119, 0), 3) * 120
    value = value + math.min(math.max(byte - 122, 0), 4) * 150
    if byte >= 127 then value = value + 96 end
    return value
end

local function lfo_rate_hz(position)
    local coefficient = lfo_rate_increment_for_byte(rounded_byte(position, 127))
    local passes = math.floor((8192 + coefficient - 1) / coefficient)
    return control_scan_hz / (4 * passes)
end

local function lfo_delay_seconds(position)
    local byte = rounded_byte(position, 127)
    local hold_increment = attack_increment_for_byte(byte)
    local region = math.floor(byte / 16)
    local fade_increment = 256
    if region == 0 then fade_increment = 0xffff
    elseif region == 1 then fade_increment = 1049
    elseif region == 2 then fade_increment = 524
    elseif region == 3 then fade_increment = 350 end
    local hold_passes = math.floor((16384 + hold_increment - 1) / hold_increment)
    local fade_passes = math.floor((65536 + fade_increment - 1) / fade_increment)
    -- The hold-crossing scan also performs the first fade increment.
    return (hold_passes + fade_passes - 1) / control_scan_hz
end

local function portamento_increment(position)
    local raw = rounded_byte(position, 255)
    if raw == 0 then return 0 end
    local index = math.floor(raw / 2)
    if index == 0 then return 0 end
    if index <= 25 then return 263 - 8 * index end
    if index <= 47 then return 113 - 2 * index end
    if index == 48 then return 18 end
    if index == 49 then return 17 end
    if index <= 61 then return 29 - math.floor((index + 2) / 4) end
    return math.max(1, 26 - math.floor((index + 3) / 5))
end

local function portamento_seconds(position)
    local increment = portamento_increment(position)
    if increment == 0 then return 0 end
    return math.floor((3072 + increment - 1) / increment) / control_scan_hz
end

local function portamento_adc_fraction(travel)
    local x = clamp01(travel)
    return x * 47000 / (47000 + x * (1 - x) * 50000)
end

local function cutoff_hz(position)
    local counts = rounded_byte(position, 127) * 128
    return math.min(50000, math.max(1, 5.53 * math.pow(2, counts / 1143)))
end

-- The DSP deliberately reads hardware bytes, so its exact laws are staircases.
-- A Jukebox nonlinear UI must nevertheless round-trip every continuous panel
-- position. Add a sub-display-resolution slope to each staircase: the values
-- still render as the exact physical byte law at the declared precision, while
-- the inverse has one unambiguous data position for Reason to recover.
local time_epsilon_seconds = 0.001
local rate_epsilon_hz = 0.001
local cutoff_epsilon_hz = 0.1

local function injective_law(position, law, epsilon)
    local x = clamp01(position)
    return law(x) + epsilon * x
end

local function inverse_injective_law(target, law)
    if target <= law(0) then return 0 end
    if target >= law(1) then return 1 end
    local low = 0
    local high = 1
    for _ = 1, 64 do
        local middle = (low + high) / 2
        if law(middle) < target then low = middle
        else high = middle end
    end
    return (low + high) / 2
end

local function attack_gui(position)
    return injective_law(position, envelope_attack_seconds,
                         time_epsilon_seconds) * 1000
end

local function decay_gui(position)
    return injective_law(position, envelope_decay_seconds,
                         time_epsilon_seconds) * 1000
end

local function release_gui(position)
    return injective_law(position, envelope_release_seconds,
                         time_epsilon_seconds) * 1000
end

local function lfo_rate_gui(position)
    return injective_law(position, lfo_rate_hz, rate_epsilon_hz)
end

local function lfo_delay_gui(position)
    return injective_law(position, lfo_delay_seconds,
                         time_epsilon_seconds) * 1000
end

local function cutoff_gui(position)
    return injective_law(position, cutoff_hz, cutoff_epsilon_hz)
end

local function portamento_gui(position)
    local function seconds(travel)
        return portamento_seconds(portamento_adc_fraction(travel))
    end
    return injective_law(position, seconds, time_epsilon_seconds) * 1000
end

local function inverse_nonnegative(value, law)
    if value < 0 then return nil end
    return inverse_injective_law(value, law)
end

local function attack_data(milliseconds)
    return inverse_nonnegative(milliseconds, attack_gui)
end

local function decay_data(milliseconds)
    return inverse_nonnegative(milliseconds, decay_gui)
end

local function release_data(milliseconds)
    return inverse_nonnegative(milliseconds, release_gui)
end

local function lfo_rate_data(hertz)
    return inverse_nonnegative(hertz, lfo_rate_gui)
end

local function lfo_delay_data(milliseconds)
    return inverse_nonnegative(milliseconds, lfo_delay_gui)
end

local function cutoff_data(hertz)
    return inverse_nonnegative(hertz, cutoff_gui)
end

local function portamento_data(milliseconds)
    return inverse_nonnegative(milliseconds, portamento_gui)
end

local function milliseconds_units(per_octave)
    local milliseconds = per_octave and "unit milliseconds per octave"
                                      or "unit milliseconds"
    local seconds = per_octave and "unit seconds per octave" or "unit seconds"
    return {
        { min_value = 0, unit = { template = jbox.ui_text(milliseconds), base = 1,
                                  default = true }, decimals = 0 },
        { min_value = 1000, unit = { template = jbox.ui_text(seconds), base = 1000 },
          decimals = 2 },
        { min_value = 10000, unit = { template = jbox.ui_text(seconds), base = 1000 },
          decimals = 1 },
    }
end

local function physical_number(name, default, data_to_gui, gui_to_data, units)
    return jbox.number{
        default = default,
        ui_name = jbox.ui_text(name),
        ui_type = jbox.ui_nonlinear{
            data_to_gui = data_to_gui,
            gui_to_data = gui_to_data,
            units = units,
        },
        persistence = "patch",
    }
end

local function selector(name, default, labels, persistence)
    return jbox.number{
        steps = #labels,
        default = default,
        ui_name = jbox.ui_text(name),
        ui_type = jbox.ui_selector(labels),
        persistence = persistence or "patch",
    }
end

local function switch(name, default)
    return jbox.boolean{
        default = default,
        ui_name = jbox.ui_text(name),
        ui_type = jbox.ui_selector{
            jbox.ui_text("value off"),
            jbox.ui_text("value on"),
        },
        persistence = "patch",
    }
end

custom_properties = jbox.property_set{
    document_owner = {
        properties = {
            volume = percent("property volume", 0.80),
            -- Panel-less patch makeup trim. It stays outside Remote and the
            -- device GUI, but is grouped predictably in the host's parameter
            -- menus instead of falling into the unnamed default group. 0.5 is
            -- unity and the Rack wrapper maps the full travel to +/-18 dB.
            presetGain = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("property preset gain"),
                ui_type = jbox.ui_linear{
                    min = -18,
                    max = 18,
                    units = { { decimals = 1 } },
                },
                persistence = "patch",
            },
            benderDco = percent("property bender dco", 0.30),
            benderVcf = percent("property bender vcf", 0.00),
            benderLfo = percent("property bender lfo", 0.00),
            portamento = physical_number(
                "property portamento", 0.00,
                portamento_gui,
                portamento_data, milliseconds_units(true)),
            keyMode = selector("property key mode", 0, {
                jbox.ui_text("value poly 1"),
                jbox.ui_text("value poly 2"),
                jbox.ui_text("value unison"),
            }),

            lfoRate = physical_number(
                "property lfo rate", 0.42, lfo_rate_gui, lfo_rate_data, {
                    { min_value = 0,
                      unit = { template = jbox.ui_text("unit hertz"), base = 1,
                               default = true }, decimals = 2 },
                    { min_value = 10,
                      unit = { template = jbox.ui_text("unit hertz"), base = 1 },
                      decimals = 1 },
                }),
            lfoDelay = physical_number(
                "property lfo delay", 0.00, lfo_delay_gui,
                lfo_delay_data, milliseconds_units(false)),
            dcoLfo = percent("property dco lfo", 0.00),
            pwm = percent("property pwm", 0.30),
            pwmMode = selector("property pwm mode", 1, {
                jbox.ui_text("value lfo"),
                jbox.ui_text("value manual"),
            }),
            range = selector("property range", 1, {
                jbox.ui_text("value range 16"),
                jbox.ui_text("value range 8"),
                jbox.ui_text("value range 4"),
            }),
            saw = switch("property saw", true),
            pulse = switch("property pulse", false),
            sub = percent("property sub", 0.00),
            noise = percent("property noise", 0.00),

            highPass = selector("property high pass", 1, {
                jbox.ui_text("value hpf boost"),
                jbox.ui_text("value hpf 1"),
                jbox.ui_text("value hpf 2"),
                jbox.ui_text("value hpf 3"),
            }),
            cutoff = physical_number(
                "property cutoff", 0.62, cutoff_gui, cutoff_data, {
                    { min_value = 0,
                      unit = { template = jbox.ui_text("unit hertz"), base = 1,
                               default = true }, decimals = 1 },
                    { min_value = 100, decimals = 0 },
                    { min_value = 1000,
                      unit = { template = jbox.ui_text("unit kilohertz"), base = 1000 },
                      decimals = 2 },
                }),
            resonance = percent("property resonance", 0.10),
            envPolarity = selector("property env polarity", 0, {
                jbox.ui_text("value positive"),
                jbox.ui_text("value negative"),
            }),
            vcfEnv = percent("property vcf env", 0.35),
            vcfLfo = percent("property vcf lfo", 0.00),
            keyFollow = percent("property key follow", 0.50),

            vcaMode = selector("property vca mode", 0, {
                jbox.ui_text("value envelope"),
                jbox.ui_text("value gate"),
            }),
            vcaLevel = percent("property vca level", 0.80),
            attack = physical_number(
                "property attack", 0.00, attack_gui,
                attack_data, milliseconds_units(false)),
            decay = physical_number(
                "property decay", 0.45, decay_gui,
                decay_data, milliseconds_units(false)),
            sustain = percent("property sustain", 0.70),
            release = physical_number(
                "property release", 0.30, release_gui,
                release_data, milliseconds_units(false)),
            chorus = selector("property chorus", 0, {
                jbox.ui_text("value chorus off"),
                jbox.ui_text("value chorus one"),
                jbox.ui_text("value chorus two"),
                jbox.ui_text("value chorus one two"),
            }),

            transpose = jbox.number{
                steps = 25,
                default = 12,
                ui_name = jbox.ui_text("property transpose"),
                ui_type = jbox.ui_linear{ min = -12, max = 12, units = { { decimals = 0 } } },
                persistence = "patch",
            },
            masterTune = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("property master tune"),
                ui_type = jbox.ui_linear{
                    min = -50,
                    max = 50,
                    units = { {
                        min_value = 0,
                        unit = { template = jbox.ui_text("unit cents"), base = 1, default = true },
                        decimals = 1,
                    } },
                },
                persistence = "patch",
            },
            velocity = percent("property velocity", 0.00),
            calibration = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("property calibration"),
                ui_type = jbox.ui_linear{
                    min = 0,
                    max = 200,
                    units = { {
                        min_value = 0,
                        unit = { template = jbox.ui_text("unit percent"), base = 1, default = true },
                        decimals = 0,
                    } },
                },
                persistence = "patch",
            },
            aging = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("property aging"),
                ui_type = jbox.ui_percent{ decimals = 0 },
                persistence = "song",
            },
            chorusNoise = percent("property chorus noise", 0.29858038),
            polyphony = jbox.number{
                steps = 16,
                default = 5,
                ui_name = jbox.ui_text("property polyphony"),
                ui_type = jbox.ui_linear{ min = 1, max = 16, units = { { decimals = 0 } } },
                persistence = "patch",
            },
            -- Engine policy follows the VST's global, non-patch state.
            quality = selector("property quality", 0, {
                jbox.ui_text("value quality 1x"),
                jbox.ui_text("value quality 2x"),
                jbox.ui_text("value quality 4x"),
            }, "song"),
            vcfTanhMode = selector("property vcf tanh", 2, {
                jbox.ui_text("value vcf tanh exact"),
                jbox.ui_text("value vcf tanh fast"),
                jbox.ui_text("value vcf tanh poly"),
            }, "song"),
            vcfFastEarlyMode = selector("property vcf fast early", 1, {
                jbox.ui_text("value vcf fast early hermite"),
                jbox.ui_text("value vcf fast early cubic"),
            }, "song"),
            vcfSolverMode = selector("property vcf solver", 2, {
                jbox.ui_text("value vcf solver max"),
                jbox.ui_text("value vcf solver high"),
                jbox.ui_text("value vcf solver normal"),
            }, "song"),
            keyModeReassertPress = jbox.boolean{
                default = false,
                ui_name = jbox.ui_text("property reassign held keys"),
                ui_type = jbox.ui_selector{
                    jbox.ui_text("value off"),
                    jbox.ui_text("value on"),
                },
                persistence = "none",
            },
            modWheel = jbox.performance_modwheel{},
            pitchBend = jbox.performance_pitchbend{},
            sustainPedal = jbox.performance_sustainpedal{},
        },
    },
    rtc_owner = {
        properties = {
            instance = jbox.native_object{},
        },
    },
    rt_owner = {
        properties = {
            noteOn = jbox.boolean{
                default = false,
                ui_name = jbox.ui_text("property note on"),
                ui_type = jbox.ui_linear{ min = 0, max = 1, units = { { decimals = 0 } } },
            },
        },
    },
}

midi_implementation_chart = {
    -- IDs above the physical MIDI-CC range expose stable Reason automation
    -- lanes without claiming hardware CCs. Existing IDs are permanent;
    -- additional controls are appended so recorded songs keep their targets.
    midi_cc_chart = {
        [256] = "/custom_properties/volume",
        [257] = "/custom_properties/benderDco",
        [258] = "/custom_properties/benderVcf",
        [259] = "/custom_properties/benderLfo",
        [260] = "/custom_properties/portamento",
        [261] = "/custom_properties/keyMode",
        [262] = "/custom_properties/lfoRate",
        [263] = "/custom_properties/lfoDelay",
        [264] = "/custom_properties/dcoLfo",
        [265] = "/custom_properties/pwm",
        [266] = "/custom_properties/pwmMode",
        [267] = "/custom_properties/range",
        [268] = "/custom_properties/saw",
        [269] = "/custom_properties/pulse",
        [270] = "/custom_properties/sub",
        [271] = "/custom_properties/noise",
        [272] = "/custom_properties/highPass",
        [273] = "/custom_properties/cutoff",
        [274] = "/custom_properties/resonance",
        [275] = "/custom_properties/envPolarity",
        [276] = "/custom_properties/vcfEnv",
        [277] = "/custom_properties/vcfLfo",
        [278] = "/custom_properties/keyFollow",
        [279] = "/custom_properties/vcaMode",
        [280] = "/custom_properties/vcaLevel",
        [281] = "/custom_properties/attack",
        [282] = "/custom_properties/decay",
        [283] = "/custom_properties/sustain",
        [284] = "/custom_properties/release",
        [285] = "/custom_properties/chorus",
        [286] = "/custom_properties/transpose",
        [287] = "/custom_properties/masterTune",
        [288] = "/custom_properties/velocity",
        [289] = "/custom_properties/polyphony",
        [290] = "/custom_properties/chorusNoise",
        [291] = "/custom_properties/calibration",
        [292] = "/custom_properties/aging",
        [293] = "/custom_properties/quality",
        [294] = "/custom_properties/vcfTanhMode",
        [295] = "/custom_properties/vcfFastEarlyMode",
        [296] = "/custom_properties/vcfSolverMode",
    },
}

remote_implementation_chart = {}
local function remote(property, internal, short, shortest)
    remote_implementation_chart["/custom_properties/" .. property] = {
        internal_name = internal,
        short_ui_name = jbox.ui_text(short),
        shortest_ui_name = jbox.ui_text(shortest),
    }
end

remote("volume", "Volume", "remote volume", "remote4 volume")
remote("benderDco", "Bender DCO", "remote bender dco", "remote4 bender dco")
remote("benderVcf", "Bender VCF", "remote bender vcf", "remote4 bender vcf")
remote("benderLfo", "Bender LFO", "remote bender lfo", "remote4 bender lfo")
remote("portamento", "Portamento", "remote portamento", "remote4 portamento")
remote("keyMode", "Key Mode", "remote key mode", "remote4 key mode")
remote("lfoRate", "LFO Rate", "remote lfo rate", "remote4 lfo rate")
remote("lfoDelay", "LFO Delay", "remote lfo delay", "remote4 lfo delay")
remote("dcoLfo", "DCO LFO", "remote dco lfo", "remote4 dco lfo")
remote("pwm", "PWM", "remote pwm", "remote4 pwm")
remote("pwmMode", "PWM Mode", "remote pwm mode", "remote4 pwm mode")
remote("range", "DCO Range", "remote range", "remote4 range")
remote("saw", "Saw", "remote saw", "remote4 saw")
remote("pulse", "Pulse", "remote pulse", "remote4 pulse")
remote("sub", "Sub", "remote sub", "remote4 sub")
remote("noise", "Noise", "remote noise", "remote4 noise")
remote("highPass", "High Pass", "remote high pass", "remote4 high pass")
remote("cutoff", "VCF Cutoff", "remote cutoff", "remote4 cutoff")
remote("resonance", "VCF Resonance", "remote resonance", "remote4 resonance")
remote("envPolarity", "VCF Env Polarity", "remote env polarity", "remote4 env polarity")
remote("vcfEnv", "VCF Env", "remote vcf env", "remote4 vcf env")
remote("vcfLfo", "VCF LFO", "remote vcf lfo", "remote4 vcf lfo")
remote("keyFollow", "VCF Keyboard", "remote key follow", "remote4 key follow")
remote("vcaMode", "VCA Mode", "remote vca mode", "remote4 vca mode")
remote("vcaLevel", "VCA Level", "remote vca level", "remote4 vca level")
remote("attack", "Attack", "remote attack", "remote4 attack")
remote("decay", "Decay", "remote decay", "remote4 decay")
remote("sustain", "Sustain", "remote sustain", "remote4 sustain")
remote("release", "Release", "remote release", "remote4 release")
remote("chorus", "Chorus", "remote chorus", "remote4 chorus")
remote("transpose", "Transpose", "remote transpose", "remote4 transpose")
remote("masterTune", "Master Tune", "remote master tune", "remote4 master tune")
remote("velocity", "Velocity", "remote velocity", "remote4 velocity")
remote("calibration", "Unit Character", "remote calibration", "remote4 calibration")
remote("aging", "Aging", "remote aging", "remote4 aging")
remote("chorusNoise", "Chorus Noise", "remote chorus noise", "remote4 chorus noise")
remote("polyphony", "Polyphony", "remote polyphony", "remote4 polyphony")
remote("quality", "Processing Quality", "remote quality", "remote4 quality")
remote("vcfTanhMode", "VCF Tanh", "remote vcf tanh", "remote4 vcf tanh")
remote("vcfFastEarlyMode", "VCF Fast Early", "remote vcf fast early", "remote4 vcf fast early")
remote("vcfSolverMode", "VCF Solver", "remote vcf solver", "remote4 vcf solver")
remote("keyModeReassertPress", "Reassign Held Keys", "remote reassign held keys", "remote4 reassign held keys")

ui_groups = {
    {
        ui_name = jbox.ui_text("group performance"),
        properties = {
            "/custom_properties/volume", "/custom_properties/presetGain",
            "/custom_properties/benderDco",
            "/custom_properties/benderVcf", "/custom_properties/benderLfo",
            "/custom_properties/portamento", "/custom_properties/keyMode",
            "/custom_properties/transpose", "/custom_properties/masterTune",
            "/custom_properties/velocity", "/custom_properties/polyphony",
            "/custom_properties/keyModeReassertPress",
        },
    },
    {
        ui_name = jbox.ui_text("group oscillator"),
        properties = {
            "/custom_properties/lfoRate", "/custom_properties/lfoDelay",
            "/custom_properties/dcoLfo", "/custom_properties/pwm",
            "/custom_properties/pwmMode", "/custom_properties/range",
            "/custom_properties/saw", "/custom_properties/pulse",
            "/custom_properties/sub", "/custom_properties/noise",
        },
    },
    {
        ui_name = jbox.ui_text("group filter amp"),
        properties = {
            "/custom_properties/highPass", "/custom_properties/cutoff",
            "/custom_properties/resonance", "/custom_properties/envPolarity",
            "/custom_properties/vcfEnv", "/custom_properties/vcfLfo",
            "/custom_properties/keyFollow", "/custom_properties/vcaMode",
            "/custom_properties/vcaLevel",
        },
    },
    {
        ui_name = jbox.ui_text("group envelope character"),
        properties = {
            "/custom_properties/attack", "/custom_properties/decay",
            "/custom_properties/sustain", "/custom_properties/release",
            "/custom_properties/chorus", "/custom_properties/chorusNoise",
        },
    },
    {
        ui_name = jbox.ui_text("group engine quality"),
        properties = {
            "/custom_properties/quality", "/custom_properties/vcfTanhMode",
            "/custom_properties/vcfFastEarlyMode", "/custom_properties/vcfSolverMode",
            "/custom_properties/calibration", "/custom_properties/aging",
        },
    },
}

cv_inputs = {
    note_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv note") },
    gate_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv gate") },
    cutoff_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv cutoff") },
    resonance_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv resonance") },
    volume_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv volume") },
    vca_level_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv vca level") },
    sub_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv sub") },
    noise_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv noise") },
}

audio_outputs = {
    left = jbox.audio_output{ ui_name = jbox.ui_text("audio left") },
    right = jbox.audio_output{ ui_name = jbox.ui_text("audio right") },
}

jbox.add_stereo_audio_routing_pair{
    left = "/audio_outputs/left",
    right = "/audio_outputs/right",
}

jbox.add_stereo_instrument_routing_hint{
    left_output = "/audio_outputs/left",
    right_output = "/audio_outputs/right",
}

jbox.add_stereo_audio_routing_target{
    signal_type = "normal",
    left = "/audio_outputs/left",
    right = "/audio_outputs/right",
    auto_route_enable = true,
}

jbox.add_cv_routing_target{
    signal_type = "gate",
    path = "/cv_inputs/gate_cv",
    auto_route_enable = true,
}

jbox.add_cv_routing_target{
    signal_type = "pitch",
    path = "/cv_inputs/note_cv",
    auto_route_enable = true,
}
