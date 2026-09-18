format_version = "2.0"
Q = 5

local function widget(x, y, path, frames)
    return {
        offset = { x * Q, y * Q },
        { path = path, frames = frames },
    }
end

local function knob(x, y)
    return widget(x, y, "Knob", 63)
end

local function toggle(x, y)
    return widget(x, y, "Toggle", 2)
end

local function lamp(x, y)
    return widget(x, y, "Lamp", 2)
end

front = {
    S_backdrop = { { path = "Reason_GUI_front_root_Panel" } },
    {
        S_patch_name = {
            offset = { 380 * Q, 14 * Q },
            { size = { 190 * Q, 18 * Q } },
        },
        S_patch_browse_group = {
            offset = { 580 * Q, 12 * Q },
            { path = "PatchBrowseGroup" },
        },
        S_device_name = {
            offset = { 605 * Q, 16 * Q },
            { path = "TapeHorz" },
        },
        S_note_on = lamp(692, 16),

        -- Model Artwork Switch
        S_model_art = widget(30, 76, "ModelArt", 4),
        S_radio_model_0 = toggle(34, 178),
        S_radio_model_1 = toggle(94, 178),
        S_radio_model_2 = toggle(154, 178),
        S_radio_model_3 = toggle(214, 178),

        -- Section 1 Knobs
        S_knob_sympathetic = knob(42, 200),
        S_knob_bodyBloom = knob(124, 200),
        S_knob_pitchGlide = knob(206, 200),

        S_knob_rollSpeed = knob(42, 262),
        S_knob_buzz = knob(124, 262),
        S_knob_artifacts = knob(206, 262),

        S_knob_malletType = knob(294, 80),
        S_knob_malletHardness = knob(347, 80),
        S_knob_strikePosition = knob(400, 80),
        S_knob_strikeJitter = knob(453, 80),

        S_knob_resonatorTune = knob(298, 160),
        S_knob_resonatorCoupling = knob(369, 160),
        S_knob_decay = knob(440, 160),

        S_knob_polyphony = knob(298, 246),
        S_knob_oversampling = knob(369, 246),
        S_knob_velocityCurve = knob(440, 246),

        S_knob_closeLevel = knob(522, 80),
        S_knob_farLevel = knob(576, 80),
        S_knob_piezoLevel = knob(630, 80),
        S_knob_stereoWidth = knob(682, 80),

        S_knob_preampDrive = knob(522, 160),
        S_knob_warmth = knob(576, 160),
        S_knob_compAmount = knob(630, 160),
        S_knob_compRelease = knob(682, 160),

        S_knob_detune = knob(522, 246),
        S_knob_masterTune = knob(576, 246),
        S_knob_volume = knob(642, 246),
    },
}

folded_front = {
    S_backdrop = { { path = "Reason_GUI_folded_front_root_Panel" } },
    {
        S_patch_name = {
            offset = { 380 * Q, 6 * Q },
            { size = { 190 * Q, 18 * Q } },
        },
        S_device_name = {
            offset = { 605 * Q, 8 * Q },
            { path = "TapeHorz" },
        },
        S_note_on = lamp(692, 9),
    },
}

back = {
    S_backdrop = { { path = "Reason_GUI_back_root_Panel" } },
    {
        S_placeholder = {
            offset = { 55 * Q, 225 * Q },
            { path = "Placeholder" },
        },
        S_device_name = {
            offset = { 20 * Q, 130 * Q },
            { path = "TapeVert" },
        },

        S_out_left = { offset = { 60 * Q, 140 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_right = { offset = { 115 * Q, 140 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_close_l = { offset = { 185 * Q, 140 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_close_r = { offset = { 240 * Q, 140 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_far_l = { offset = { 305 * Q, 140 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_far_r = { offset = { 355 * Q, 140 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_piezo = { offset = { 385 * Q, 220 * Q }, { path = "AudioJack", frames = 3 } },

        S_cv_note = { offset = { 465 * Q, 140 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_gate = { offset = { 515 * Q, 140 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_mallet = { offset = { 565 * Q, 140 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_pos = { offset = { 615 * Q, 140 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_coup = { offset = { 665 * Q, 140 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_symp = { offset = { 465 * Q, 220 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_roll = { offset = { 565 * Q, 220 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_vol = { offset = { 665 * Q, 220 * Q }, { path = "CVJack", frames = 3 } },
    },
}

folded_back = {
    S_backdrop = { { path = "Reason_GUI_folded_back_root_Panel" } },
    S_cable_origin = { offset = { 377 * Q, 15 * Q } },
    {
        S_device_name = {
            offset = { 605 * Q, 8 * Q },
            { path = "TapeHorz" },
        },
    },
}
