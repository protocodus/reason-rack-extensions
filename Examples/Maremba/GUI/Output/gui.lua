format_version = "4.0"

local function property(name)
    return "/custom_properties/" .. name
end

local function knob(x, y, propName)
    return jbox.analog_knob{
        transform = { x, y },
        animation = jbox.image_sequence{ path = "Knob", frames = 63 },
        margins = { left = 2, top = 2, right = 2, bottom = 2 },
        value = property(propName),
        show_remote_box = true,
        show_automation_rect = true,
    }
end

local function radio(x, y, propName, index)
    return jbox.radio_button{
        transform = { x, y },
        background = jbox.image_sequence{ path = "Toggle", frames = 2 },
        margins = { left = 1, top = 1, right = 1, bottom = 1 },
        value = property(propName),
        index = index,
        show_remote_box = true,
        show_automation_rect = true,
    }
end

front = jbox.panel{
    backdrop = jbox.image{ path = "Reason_GUI_front_root_Panel" },
    widgets = {
        -- Header: Patch name and browsing
        jbox.patch_name{
            transform = { 235, 14 },
            width = 190,
            height = 22,
            center = true,
            text_style = "Arial medium font",
            fg_color = { 245, 235, 215 },
            loader_alt_color = { 200, 160, 90 },
        },
        jbox.patch_browse_group{
            transform = { 435, 14 },
        },
        jbox.device_name{
            transform = { 505, 18 },
        },
        -- Header: Note On Lamp
        jbox.sequence_meter{
            transform = { 595, 20 },
            animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
            value = property("noteon"),
        },

        -- Section 1: Model Art Display (4 frames representing the 4 models)
        jbox.sequence_meter{
            transform = { 28, 84 },
            animation = jbox.image_sequence{ path = "ModelArt", frames = 4 },
            value = property("model"),
        },
        -- Model Selection Radio Buttons
        radio(32, 190, "model", 0),
        radio(92, 190, "model", 1),
        radio(152, 190, "model", 2),
        radio(212, 190, "model", 3),

        -- Section 1 Row 1: Sympathetic, Body Bloom, Pitch Glide
        knob(39, 228, "sympathetic"),
        knob(122, 228, "bodyBloom"),
        knob(205, 228, "pitchGlide"),

        -- Section 1 Row 2: Mirliton Buzz, Artifacts
        knob(80, 310, "buzzAmount"),
        knob(164, 310, "artifacts"),

        -- Section 2: Exciter & Resonator Core
        -- Row 1: Striker, Hardness, Position, Variance
        knob(286, 86, "malletType"),
        knob(338, 86, "malletHardness"),
        knob(390, 86, "strikePosition"),
        knob(442, 86, "strikeJitter"),

        -- Row 2: Resonator Tune, Resonator Coupling, Bar Decay
        knob(300, 194, "resonatorTune"),
        knob(364, 194, "resonatorCoupling"),
        knob(428, 194, "decay"),

        -- Row 3: Polyphony, Oversampling, Velocity Curve
        knob(300, 298, "polyphony"),
        knob(364, 298, "oversampling"),
        knob(428, 298, "velocityCurve"),

        -- Section 3: Microphones & Dynamics
        -- Row 1: Close, Far, Piezo, Width
        knob(515, 86, "closeLevel"),
        knob(567, 86, "farLevel"),
        knob(619, 86, "piezoLevel"),
        knob(671, 86, "stereoWidth"),

        -- Row 2: Preamp Drive, Warmth, Comp Amount, Release
        knob(515, 194, "preampDrive"),
        knob(567, 194, "warmth"),
        knob(619, 194, "compAmount"),
        knob(671, 194, "compRelease"),

        -- Row 3: Detune Drift, Master Tune, Master Volume
        knob(515, 298, "detune"),
        knob(567, 298, "masterTune"),
        knob(626, 298, "volume"),
    }
}

folded_front = jbox.panel{
    backdrop = jbox.image{ path = "Reason_GUI_folded_front_root_Panel" },
    widgets = {
        jbox.patch_name{
            transform = { 235, 6 },
            width = 190,
            height = 18,
            text_style = "Bold LCD font",
            fg_color = { 245, 235, 215 },
            loader_alt_color = { 200, 160, 90 },
        },
        jbox.device_name{
            transform = { 505, 8 },
        },
        jbox.sequence_meter{
            transform = { 595, 9 },
            animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
            value = property("noteon"),
        },
    }
}

back = jbox.panel{
    backdrop = jbox.image{ path = "Reason_GUI_back_root_Panel" },
    widgets = {
        jbox.placeholder{
            transform = { 55, 245 },
        },
        jbox.device_name{
            transform = { 20, 150 },
            orientation = "vertical",
        },

        -- Audio Outputs
        jbox.audio_output_socket{
            transform = { 58, 150 },
            socket = "/audio_outputs/left",
        },
        jbox.audio_output_socket{
            transform = { 114, 150 },
            socket = "/audio_outputs/right",
        },
        jbox.audio_output_socket{
            transform = { 180, 150 },
            socket = "/audio_outputs/close_left",
        },
        jbox.audio_output_socket{
            transform = { 236, 150 },
            socket = "/audio_outputs/close_right",
        },
        jbox.audio_output_socket{
            transform = { 300, 150 },
            socket = "/audio_outputs/far_left",
        },
        jbox.audio_output_socket{
            transform = { 352, 150 },
            socket = "/audio_outputs/far_right",
        },
        jbox.audio_output_socket{
            transform = { 382, 250 },
            socket = "/audio_outputs/piezo",
        },

        -- CV Inputs
        jbox.cv_input_socket{
            transform = { 460, 150 },
            socket = "/cv_inputs/note_cv",
        },
        jbox.cv_input_socket{
            transform = { 512, 150 },
            socket = "/cv_inputs/gate_cv",
        },
        jbox.cv_input_socket{
            transform = { 564, 150 },
            socket = "/cv_inputs/mallet_cv",
        },
        jbox.cv_input_socket{
            transform = { 616, 150 },
            socket = "/cv_inputs/position_cv",
        },
        jbox.cv_input_socket{
            transform = { 668, 150 },
            socket = "/cv_inputs/coupling_cv",
        },
        jbox.cv_input_socket{
            transform = { 460, 250 },
            socket = "/cv_inputs/sympathetic_cv",
        },
        jbox.cv_input_socket{
            transform = { 564, 250 },
            socket = "/cv_inputs/roll_cv",
        },
        jbox.cv_input_socket{
            transform = { 668, 250 },
            socket = "/cv_inputs/volume_cv",
        },
    }
}

folded_back = jbox.panel{
    backdrop = jbox.image{ path = "Reason_GUI_folded_back_root_Panel" },
    cable_origin = { 377, 15 },
    widgets = {
        jbox.device_name{
            transform = { 605, 8 },
        },
    }
}
