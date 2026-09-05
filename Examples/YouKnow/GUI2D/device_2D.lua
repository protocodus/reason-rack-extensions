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

local function fader(x, y)
	return widget(x, y, "Fader", 32)
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
			offset = { 330 * Q, 21 * Q },
			{ size = { 204 * Q, 16 * Q } },
		},
		S_patch_browse_group = {
			offset = { 544 * Q, 17 * Q },
			{ path = "PatchBrowseGroup" },
		},
		S_device_name = {
			offset = { 610 * Q, 23 * Q },
			{ path = "TapeHorz" },
		},
		S_note_on = lamp(709, 51),
		S_status_quality = widget(304, 53, "EngineDisplay", 1),
		S_status_vcfTanhMode = widget(370, 53, "EngineDisplay", 1),
		S_status_vcfFastEarlyMode = widget(436, 53, "EngineDisplay", 1),
		S_status_vcfSolverMode = widget(502, 53, "EngineDisplay", 1),
		S_status_calibration = widget(568, 53, "EngineDisplay", 1),
		S_status_aging = widget(634, 53, "EngineDisplay", 1),

		-- Row 1: LFO, oscillator, high-pass filter
		S_fader_lfoRate = fader(40, 119),
		S_fader_lfoDelay = fader(94, 119),
		S_fader_range = fader(168, 119),
		S_fader_dcoLfo = fader(224, 119),
		S_fader_pwm = fader(286, 119),
		S_fader_pwmMode = fader(348, 119),
		S_toggle_pulse = toggle(416, 137),
		S_toggle_saw = toggle(416, 169),
		S_fader_sub = fader(530, 119),
		S_fader_noise = fader(600, 119),
		S_fader_highPass = fader(698, 119),

		-- Row 2: filter, amplifier, envelope, chorus
		S_fader_cutoff = fader(31, 273),
		S_fader_resonance = fader(76, 273),
		S_fader_envPolarity = fader(121, 273),
		S_fader_vcfEnv = fader(166, 273),
		S_fader_vcfLfo = fader(211, 273),
		S_fader_keyFollow = fader(256, 273),
		S_fader_vcaMode = fader(339, 273),
		S_fader_vcaLevel = fader(386, 273),
		S_fader_attack = fader(455, 273),
		S_fader_decay = fader(499, 273),
		S_fader_sustain = fader(543, 273),
		S_fader_release = fader(587, 273),
		S_fader_chorus = fader(661, 273),
		S_fader_chorusNoise = fader(711, 273),

		-- Row 3: performance and keyboard
		S_pitch_wheel = wheel(30, 430, "PitchWheel"),
		S_mod_wheel = wheel(88, 430, "ModWheel"),
		S_fader_volume = fader(146, 437),
		S_fader_benderDco = fader(204, 437),
		S_fader_benderVcf = fader(262, 437),
		S_fader_benderLfo = fader(320, 437),
		S_knob_portamento = knob(386, 455),
		S_radio_keyMode_0 = toggle(448, 442),
		S_radio_keyMode_1 = toggle(448, 471),
		S_radio_keyMode_2 = toggle(448, 500),
		S_momentary_keyMode_0 = momentary_overlay(448, 442),
		S_momentary_keyMode_1 = momentary_overlay(448, 471),
		S_momentary_keyMode_2 = momentary_overlay(448, 500),
		S_fader_transpose = fader(544, 437),
		S_fader_masterTune = fader(594, 437),
		S_fader_velocity = fader(646, 437),
		S_fader_polyphony = fader(700, 437),
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
		S_note_on = lamp(690, 10),
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
		S_radio_quality_1 = toggle(80, 407),
		S_radio_quality_2 = toggle(80, 436),
		S_radio_vcfTanhMode_0 = toggle(188, 378),
		S_radio_vcfTanhMode_1 = toggle(188, 407),
		S_radio_vcfTanhMode_2 = toggle(188, 436),
		S_radio_vcfFastEarlyMode_0 = toggle(296, 393),
		S_radio_vcfFastEarlyMode_1 = toggle(296, 422),
		S_radio_vcfSolverMode_0 = toggle(404, 378),
		S_radio_vcfSolverMode_1 = toggle(404, 407),
		S_radio_vcfSolverMode_2 = toggle(404, 436),
		S_fader_calibration = fader(544, 378),
		S_fader_aging = fader(636, 378),
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
