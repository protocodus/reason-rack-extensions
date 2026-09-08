format_version = "2.0"
Q = 5

-- Front-panel coordinates are logical (1x) units; Reason's authoring
-- resolution is 5x. Design/render_panels.py draws the silkscreen from the same
-- table and asserts that every node below sits where its caption was drawn.
local function widget(x, y, path, frames)
	return {
		offset = { x * Q, y * Q },
		{ path = path, frames = frames },
	}
end

local function fader(x, y, path)
	return widget(x, y, path, 32)
end

local function toggle(x, y)
	return widget(x, y, "Toggle", 2)
end

local function momentary_overlay(x, y)
	return widget(x, y, "MomentaryOverlay", 2)
end

local function knob(x, y)
	return widget(x, y, "Knob", 63)
end

local function wheel(x, y, path)
	return widget(x, y, path, 64)
end

local function lamp(x, y)
	return widget(x, y, "Lamp", 2)
end

front = {
	S_backdrop = { { path = "Reason_GUI_front_root_Panel" } },
	{
		S_patch_name = {
			offset = { 299 * Q, 16 * Q },
			{ size = { 204 * Q, 16 * Q } },
		},
		S_patch_browse_group = {
			offset = { 517 * Q, 13 * Q },
			{ path = "PatchBrowseGroup" },
		},
		S_device_name = {
			offset = { 589 * Q, 17 * Q },
			{ path = "TapeHorz" },
		},
		S_note_on = lamp(724, 51),
		S_status_quality = widget(64, 48, "EngineDisplay", 1),
		S_status_vcfTanhMode = widget(166, 48, "EngineDisplay", 1),
		S_status_vcfFastEarlyMode = widget(272, 48, "EngineDisplay", 1),
		S_status_vcfSolverMode = widget(385, 48, "EngineDisplay", 1),
		S_status_calibration = widget(518, 48, "EngineDisplay", 1),
		S_status_aging = widget(623, 48, "EngineDisplay", 1),

		-- Row 1: LFO, oscillator, high-pass filter
		S_fader_lfoRate = fader(31, 116, "FaderSource"),
		S_fader_lfoDelay = fader(98, 116, "FaderSource"),
		S_fader_range = fader(183, 116, "FaderSource"),
		S_fader_dcoLfo = fader(248, 116, "FaderSource"),
		S_fader_pwm = fader(307, 116, "FaderSource"),
		S_fader_pwmMode = fader(387, 116, "FaderSource"),
		S_toggle_pulse = toggle(463, 134),
		S_toggle_saw = toggle(463, 166),
		S_fader_sub = fader(555, 116, "FaderSource"),
		S_fader_noise = fader(618, 116, "FaderSource"),
		S_fader_highPass = fader(707, 116, "FaderSource"),

		-- Row 2: filter, amplifier, envelope, chorus
		S_fader_cutoff = fader(29, 270, "FaderShape"),
		S_fader_resonance = fader(74, 270, "FaderShape"),
		S_fader_envPolarity = fader(121, 270, "FaderShape"),
		S_fader_vcfEnv = fader(163, 270, "FaderShape"),
		S_fader_vcfLfo = fader(204, 270, "FaderShape"),
		S_fader_keyFollow = fader(249, 270, "FaderShape"),
		S_fader_vcaMode = fader(338, 270, "FaderShape"),
		S_fader_vcaLevel = fader(391, 270, "FaderShape"),
		S_fader_attack = fader(457, 270, "FaderShape"),
		S_fader_decay = fader(496, 270, "FaderShape"),
		S_fader_sustain = fader(534, 270, "FaderShape"),
		S_fader_release = fader(573, 270, "FaderShape"),
		S_fader_chorus = fader(649, 270, "FaderEffect"),
		S_fader_chorusNoise = fader(702, 270, "FaderEffect"),

		-- Row 3: performance and keyboard
		S_pitch_wheel = wheel(30, 427, "PitchWheel"),
		S_mod_wheel = wheel(82, 427, "ModWheel"),
		S_fader_volume = fader(277, 434, "FaderPlay"),
		S_fader_benderDco = fader(129, 434, "FaderPlay"),
		S_fader_benderVcf = fader(174, 434, "FaderPlay"),
		S_fader_benderLfo = fader(219, 434, "FaderPlay"),
		S_knob_portamento = knob(348, 452),
		S_radio_keyMode_0 = toggle(423, 437),
		S_radio_keyMode_1 = toggle(423, 468),
		S_radio_keyMode_2 = toggle(423, 499),
		S_momentary_keyMode_0 = momentary_overlay(423, 437),
		S_momentary_keyMode_1 = momentary_overlay(423, 468),
		S_momentary_keyMode_2 = momentary_overlay(423, 499),
		S_fader_transpose = fader(529, 434, "FaderPlay"),
		S_fader_masterTune = fader(596, 434, "FaderPlay"),
		S_fader_velocity = fader(645, 434, "FaderPlay"),
		S_fader_polyphony = fader(700, 434, "FaderPlay"),
	},
}

folded_front = {
	S_backdrop = { { path = "Reason_GUI_folded_front_root_Panel" } },
	{
		S_patch_name = {
			offset = { 300 * Q, 10 * Q },
			{ path = "PatchName" },
		},
		S_patch_browse_group = {
			offset = { 510 * Q, 4 * Q },
			{ path = "PatchBrowseGroup" },
		},
		S_device_name = {
			offset = { 600 * Q, 8 * Q },
			{ path = "TapeHorz" },
		},
		S_note_on = lamp(724, 51),
	},
}

back = {
	S_backdrop = { { path = "Reason_GUI_back_root_Panel" } },
	{
		S_placeholder = widget(347, 15, "Placeholder", 1),
		S_device_name = {
			offset = { 20 * Q, 150 * Q },
			{ path = "TapeVert" },
		},
		S_radio_quality_0 = toggle(80, 378),
		S_radio_quality_1 = toggle(80, 409),
		S_radio_quality_2 = toggle(80, 440),
		S_radio_vcfTanhMode_0 = toggle(188, 378),
		S_radio_vcfTanhMode_1 = toggle(188, 409),
		S_radio_vcfTanhMode_2 = toggle(188, 440),
		S_radio_vcfFastEarlyMode_0 = toggle(296, 393),
		S_radio_vcfFastEarlyMode_1 = toggle(296, 424),
		S_radio_vcfSolverMode_0 = toggle(404, 378),
		S_radio_vcfSolverMode_1 = toggle(404, 409),
		S_radio_vcfSolverMode_2 = toggle(404, 440),
		S_fader_calibration = fader(544, 378, "FaderPlay"),
		S_fader_aging = fader(636, 378, "FaderPlay"),
		S_cv_input_note = widget(95, 155, "CVJack", 3),
		S_cv_input_gate = widget(167, 155, "CVJack", 3),
		S_cv_input_cutoff = widget(239, 155, "CVJack", 3),
		S_cv_input_resonance = widget(311, 155, "CVJack", 3),
		S_cv_input_volume = widget(95, 245, "CVJack", 3),
		S_cv_input_vca_level = widget(167, 245, "CVJack", 3),
		S_cv_input_sub = widget(239, 245, "CVJack", 3),
		S_cv_input_noise = widget(311, 245, "CVJack", 3),
		S_audio_output_left = {
			offset = { 485 * Q, 230 * Q },
			{ path = "AudioJack", frames = 3 },
		},
		S_audio_output_right = {
			offset = { 575 * Q, 230 * Q },
			{ path = "AudioJack", frames = 3 },
		},
	},
}

folded_back = {
	S_backdrop = { { path = "Reason_GUI_folded_back_root_Panel" } },
	S_cable_origin = { offset = { 377 * Q, 15 * Q } },
	{
		S_device_name = {
			offset = { 600 * Q, 8 * Q },
			{ path = "TapeHorz" },
		},
	},
}
