format_version = "2.0"
Q = 5

local function property(name)
    return "/custom_properties/" .. name
end

local function knob(node, name)
    return jbox.analog_knob{
        graphics = {
            node = node,
            hit_boundaries = { left = Q * 2, top = Q * 2, right = Q * 2, bottom = Q * 2 },
        },
        value = property(name),
        show_remote_box = true,
        show_automation_rect = true,
    }
end

local function toggle(node, name)
    return jbox.toggle_button{
        graphics = {
            node = node,
            hit_boundaries = { left = Q * 2, top = Q * 2, right = Q * 2, bottom = Q * 2 },
        },
        value = property(name),
    }
end

local function radio(node, name, index)
    return jbox.radio_button{
        graphics = {
            node = node,
            hit_boundaries = { left = Q * 2, top = Q, right = Q * 2, bottom = Q },
        },
        value = property(name),
        index = index,
        show_remote_box = true,
        show_automation_rect = true,
    }
end

front = jbox.panel{
    graphics = { node = "S_backdrop" },
    widgets = {
        jbox.patch_name{
            graphics = { node = "S_patch_name" },
            center = true,
            text_style = "Arial medium font",
            fg_color = { 245, 235, 215 },
            loader_alt_color = { 200, 160, 90 },
        },
        jbox.patch_browse_group{
            graphics = { node = "S_patch_browse_group" },
        },
        jbox.device_name{
            graphics = { node = "S_device_name" },
        },
        jbox.sequence_meter{
            graphics = { node = "S_note_on" },
            value = property("noteon"),
        },

        jbox.sequence_meter{
            graphics = { node = "S_model_art" },
            value = property("model"),
        },
        radio("S_radio_model_0", "model", 0),
        radio("S_radio_model_1", "model", 1),
        radio("S_radio_model_2", "model", 2),
        radio("S_radio_model_3", "model", 3),

        knob("S_knob_sympathetic", "sympathetic"),
        knob("S_knob_bodyBloom", "bodyBloom"),
        knob("S_knob_pitchGlide", "pitchGlide"),

        knob("S_knob_buzz", "buzzAmount"),
        knob("S_knob_artifacts", "artifacts"),

        knob("S_knob_malletType", "malletType"),
        knob("S_knob_malletHardness", "malletHardness"),
        knob("S_knob_strikePosition", "strikePosition"),
        knob("S_knob_strikeJitter", "strikeJitter"),

        knob("S_knob_resonatorTune", "resonatorTune"),
        knob("S_knob_resonatorCoupling", "resonatorCoupling"),
        knob("S_knob_decay", "decay"),

        knob("S_knob_polyphony", "polyphony"),
        knob("S_knob_oversampling", "oversampling"),
        knob("S_knob_velocityCurve", "velocityCurve"),

        knob("S_knob_closeLevel", "closeLevel"),
        knob("S_knob_farLevel", "farLevel"),
        knob("S_knob_piezoLevel", "piezoLevel"),
        knob("S_knob_stereoWidth", "stereoWidth"),

        knob("S_knob_preampDrive", "preampDrive"),
        knob("S_knob_compAmount", "compAmount"),
        knob("S_knob_compAttack", "compAttack"),
        knob("S_knob_compRelease", "compRelease"),

        knob("S_knob_warmth", "warmth"),
        knob("S_knob_detune", "detune"),
        knob("S_knob_masterTune", "masterTune"),
        knob("S_knob_volume", "volume"),
    }
}

folded_front = jbox.panel{
    graphics = { node = "S_backdrop" },
    widgets = {
        jbox.patch_name{
            graphics = { node = "S_patch_name" },
            center = true,
            text_style = "Bold LCD font",
            fg_color = { 245, 235, 215 },
            loader_alt_color = { 200, 160, 90 },
        },
        jbox.patch_browse_group{
            graphics = { node = "S_patch_browse_group" },
        },
        jbox.device_name{
            graphics = { node = "S_device_name" },
        },
        jbox.sequence_meter{
            graphics = { node = "S_note_on" },
            value = property("noteon"),
        },
    }
}

back = jbox.panel{
    graphics = { node = "S_backdrop" },
    widgets = {
        jbox.placeholder{
            graphics = { node = "S_placeholder" },
        },
        jbox.device_name{
            graphics = { node = "S_device_name" },
        },

        jbox.audio_output_socket{ graphics = { node = "S_out_left" }, socket = "/audio_outputs/left" },
        jbox.audio_output_socket{ graphics = { node = "S_out_right" }, socket = "/audio_outputs/right" },
        jbox.audio_output_socket{ graphics = { node = "S_out_close_l" }, socket = "/audio_outputs/close_left" },
        jbox.audio_output_socket{ graphics = { node = "S_out_close_r" }, socket = "/audio_outputs/close_right" },
        jbox.audio_output_socket{ graphics = { node = "S_out_far_l" }, socket = "/audio_outputs/far_left" },
        jbox.audio_output_socket{ graphics = { node = "S_out_far_r" }, socket = "/audio_outputs/far_right" },
        jbox.audio_output_socket{ graphics = { node = "S_out_piezo" }, socket = "/audio_outputs/piezo" },

        jbox.cv_input_socket{ graphics = { node = "S_cv_note" }, socket = "/cv_inputs/note_cv" },
        jbox.cv_input_socket{ graphics = { node = "S_cv_gate" }, socket = "/cv_inputs/gate_cv" },
        jbox.cv_input_socket{ graphics = { node = "S_cv_mallet" }, socket = "/cv_inputs/mallet_cv" },
        jbox.cv_input_socket{ graphics = { node = "S_cv_pos" }, socket = "/cv_inputs/position_cv" },
        jbox.cv_input_socket{ graphics = { node = "S_cv_coup" }, socket = "/cv_inputs/coupling_cv" },
        jbox.cv_input_socket{ graphics = { node = "S_cv_symp" }, socket = "/cv_inputs/sympathetic_cv" },
        jbox.cv_input_socket{ graphics = { node = "S_cv_vol" }, socket = "/cv_inputs/volume_cv" },

        -- Stock routing symbols: stereo pairs (02) and the mono piezo jack (01)
        jbox.static_decoration{ graphics = { node = "S_routing_main" } },
        jbox.static_decoration{ graphics = { node = "S_routing_close" } },
        jbox.static_decoration{ graphics = { node = "S_routing_far" } },
        jbox.static_decoration{ graphics = { node = "S_routing_piezo" } },
    }
}

folded_back = jbox.panel{
    graphics = { node = "S_backdrop" },
    cable_origin = { node = "S_cable_origin" },
    widgets = {
        jbox.device_name{
            graphics = { node = "S_device_name" },
        },
    }
}
