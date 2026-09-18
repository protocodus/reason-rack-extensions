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
            offset = { 235 * Q, 14 * Q },
            { size = { 190 * Q, 22 * Q } },
        },
        S_patch_browse_group = {
            offset = { 435 * Q, 14 * Q },
            { path = "PatchBrowseGroup" },
        },
        S_device_name = {
            offset = { 505 * Q, 18 * Q },
            { path = "TapeHorz" },
        },
        S_note_on = lamp(595, 20),

        -- Model Artwork Switch
        S_model_art = widget(28, 84, "ModelArt", 4),
        S_radio_model_0 = toggle(32, 190),
        S_radio_model_1 = toggle(92, 190),
        S_radio_model_2 = toggle(152, 190),
        S_radio_model_3 = toggle(212, 190),

        -- Section 1 Knobs
        S_knob_sympathetic = knob(39, 228),
        S_knob_bodyBloom = knob(122, 228),
        S_knob_pitchGlide = knob(205, 228),

        S_knob_buzz = knob(80, 310),
        S_knob_artifacts = knob(164, 310),

        -- Section 2 Knobs
        S_knob_malletType = knob(286, 86),
        S_knob_malletHardness = knob(338, 86),
        S_knob_strikePosition = knob(390, 86),
        S_knob_strikeJitter = knob(442, 86),

        S_knob_resonatorTune = knob(300, 194),
        S_knob_resonatorCoupling = knob(364, 194),
        S_knob_decay = knob(428, 194),

        S_knob_polyphony = knob(300, 298),
        S_knob_oversampling = knob(364, 298),
        S_knob_velocityCurve = knob(428, 298),

        -- Section 3 Knobs
        S_knob_closeLevel = knob(515, 86),
        S_knob_farLevel = knob(567, 86),
        S_knob_piezoLevel = knob(619, 86),
        S_knob_stereoWidth = knob(671, 86),

        S_knob_preampDrive = knob(515, 194),
        S_knob_warmth = knob(567, 194),
        S_knob_compAmount = knob(619, 194),
        S_knob_compRelease = knob(671, 194),

        S_knob_detune = knob(515, 298),
        S_knob_masterTune = knob(567, 298),
        S_knob_volume = knob(626, 298),
    },
}

folded_front = {
    S_backdrop = { { path = "Reason_GUI_folded_front_root_Panel" } },
    {
        S_patch_name = {
            offset = { 235 * Q, 6 * Q },
            { size = { 190 * Q, 18 * Q } },
        },
        S_device_name = {
            offset = { 505 * Q, 8 * Q },
            { path = "TapeHorz" },
        },
        S_note_on = lamp(595, 9),
    },
}

back = {
    S_backdrop = { { path = "Reason_GUI_back_root_Panel" } },
    {
        S_placeholder = {
            offset = { 55 * Q, 245 * Q },
            { path = "Placeholder" },
        },
        S_device_name = {
            offset = { 20 * Q, 150 * Q },
            { path = "TapeVert" },
        },

        S_out_left = { offset = { 58 * Q, 150 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_right = { offset = { 114 * Q, 150 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_close_l = { offset = { 180 * Q, 150 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_close_r = { offset = { 236 * Q, 150 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_far_l = { offset = { 300 * Q, 150 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_far_r = { offset = { 352 * Q, 150 * Q }, { path = "AudioJack", frames = 3 } },
        S_out_piezo = { offset = { 382 * Q, 250 * Q }, { path = "AudioJack", frames = 3 } },

        S_cv_note = { offset = { 460 * Q, 150 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_gate = { offset = { 512 * Q, 150 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_mallet = { offset = { 564 * Q, 150 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_pos = { offset = { 616 * Q, 150 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_coup = { offset = { 668 * Q, 150 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_symp = { offset = { 460 * Q, 250 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_roll = { offset = { 564 * Q, 250 * Q }, { path = "CVJack", frames = 3 } },
        S_cv_vol = { offset = { 668 * Q, 250 * Q }, { path = "CVJack", frames = 3 } },
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
