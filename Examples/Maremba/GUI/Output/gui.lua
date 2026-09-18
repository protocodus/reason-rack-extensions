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
            transform = { 380, 14 },
            width = 190,
            height = 18,
            center = true,
            text_style = "Arial medium font",
            fg_color = { 245, 235, 215 },
            loader_alt_color = { 200, 160, 90 },
        },
        jbox.patch_browse_group{
            transform = { 580, 12 },
        },
        jbox.device_name{
            transform = { 605, 16 },
        },
        -- Header: Note On Lamp
        jbox.sequence_meter{
            transform = { 692, 16 },
            animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
            value = property("noteon"),
        },

        -- Section 1: Model Art Display (4 frames representing the 4 models)
        jbox.sequence_meter{
            transform = { 30, 76 },
            animation = jbox.image_sequence{ path = "ModelArt", frames = 4 },
            value = property("model"),
        },
        -- Model Selection Radio Buttons
        radio(34, 178, "model", 0),
        radio(94, 178, "model", 1),
        radio(154, 178, "model", 2),
        radio(214, 178, "model", 3),

        -- Section 1 Row 1: Sympathetic, Body Bloom, Pitch Glide
        knob(42, 200, "sympathetic"),
        knob(124, 200, "bodyBloom"),
        knob(206, 200, "pitchGlide"),

        -- Section 1 Row 2: Mallet Roll, Mirliton Buzz, Artifacts
        knob(42, 262, "rollSpeed"),
        knob(124, 262, "buzzAmount"),
        knob(206, 262, "artifacts"),

        -- Section 2: Excitation & Resonator Core
        -- Row 1: Striker, Hardness, Position, Variance
        knob(294, 80, "malletType"),
        knob(347, 80, "malletHardness"),
        knob(400, 80, "strikePosition"),
        knob(453, 80, "strikeJitter"),

        -- Row 2: Resonator Tune, Resonator Coupling, Bar Decay
        knob(298, 160, "resonatorTune"),
        knob(369, 160, "resonatorCoupling"),
        knob(440, 160, "decay"),

        -- Row 3: Polyphony, Oversampling, Velocity Curve
        knob(298, 246, "polyphony"),
        knob(369, 246, "oversampling"),
        knob(440, 246, "velocityCurve"),

        -- Section 3: Microphones & Dynamics
        -- Row 1: Close, Far, Piezo, Width
        knob(522, 80, "closeLevel"),
        knob(576, 80, "farLevel"),
        knob(630, 80, "piezoLevel"),
        knob(682, 80, "stereoWidth"),

        -- Row 2: Preamp Drive, Warmth, Comp Amount, Release
        knob(522, 160, "preampDrive"),
        knob(576, 160, "warmth"),
        knob(630, 160, "compAmount"),
        knob(682, 160, "compRelease"),

        -- Row 3: Detune Drift, Master Tune, Master Volume
        knob(522, 246, "detune"),
        knob(576, 246, "masterTune"),
        knob(642, 246, "volume"),
    }
}

folded_front = jbox.panel{
    backdrop = jbox.image{ path = "Reason_GUI_folded_front_root_Panel" },
    widgets = {
        jbox.patch_name{
            transform = { 380, 6 },
            width = 190,
            height = 18,
            text_style = "Bold LCD font",
            fg_color = { 245, 235, 215 },
            loader_alt_color = { 200, 160, 90 },
        },
        jbox.device_name{
            transform = { 605, 8 },
        },
        jbox.sequence_meter{
            transform = { 692, 9 },
            animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
            value = property("noteon"),
        },
    }
}

back = jbox.panel{
    backdrop = jbox.image{ path = "Reason_GUI_back_root_Panel" },
    widgets = {
        jbox.placeholder{
            transform = { 55, 225 },
        },
        jbox.device_name{
            transform = { 20, 130 },
            orientation = "vertical",
        },

        -- Audio Outputs
        jbox.audio_output_socket{
            transform = { 60, 140 },
            socket = "/audio_outputs/left",
        },
        jbox.audio_output_socket{
            transform = { 115, 140 },
            socket = "/audio_outputs/right",
        },
        jbox.audio_output_socket{
            transform = { 185, 140 },
            socket = "/audio_outputs/close_left",
        },
        jbox.audio_output_socket{
            transform = { 240, 140 },
            socket = "/audio_outputs/close_right",
        },
        jbox.audio_output_socket{
            transform = { 305, 140 },
            socket = "/audio_outputs/far_left",
        },
        jbox.audio_output_socket{
            transform = { 355, 140 },
            socket = "/audio_outputs/far_right",
        },
        jbox.audio_output_socket{
            transform = { 385, 220 },
            socket = "/audio_outputs/piezo",
        },

        -- CV Inputs
        jbox.cv_input_socket{
            transform = { 465, 140 },
            socket = "/cv_inputs/note_cv",
        },
        jbox.cv_input_socket{
            transform = { 515, 140 },
            socket = "/cv_inputs/gate_cv",
        },
        jbox.cv_input_socket{
            transform = { 565, 140 },
            socket = "/cv_inputs/mallet_cv",
        },
        jbox.cv_input_socket{
            transform = { 615, 140 },
            socket = "/cv_inputs/position_cv",
        },
        jbox.cv_input_socket{
            transform = { 665, 140 },
            socket = "/cv_inputs/coupling_cv",
        },
        jbox.cv_input_socket{
            transform = { 465, 220 },
            socket = "/cv_inputs/sympathetic_cv",
        },
        jbox.cv_input_socket{
            transform = { 565, 220 },
            socket = "/cv_inputs/roll_cv",
        },
        jbox.cv_input_socket{
            transform = { 665, 220 },
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
