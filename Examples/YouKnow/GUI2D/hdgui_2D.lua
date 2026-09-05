format_version = "2.0"
Q = 5

local function property(name)
	return "/custom_properties/" .. name
end

-- Handle travel, in HD pixels, matching the strip Design/render_panels.py
-- draws: a 70 px cap sliding between 40 px margins inside a 440 px frame. If
-- these drift from the artwork the cap stops tracking the mouse.
local function fader(node, name, show_automation, show_remote)
	return jbox.sequence_fader{
		graphics = {
			node = node,
			hit_boundaries = { left = Q * 2, top = Q * 4, right = Q * 2, bottom = Q * 4 },
		},
		value = property(name),
		handle_size = 70,
		inset1 = 40,
		inset2 = 40,
		show_remote_box = show_remote ~= false,
		show_automation_rect = show_automation ~= false,
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

local function radio(node, name, index, show_remote, show_automation)
	return jbox.radio_button{
		graphics = {
			node = node,
			hit_boundaries = { left = Q * 2, top = Q, right = Q * 2, bottom = Q },
		},
		value = property(name),
		index = index,
		show_remote_box = show_remote ~= false,
		show_automation_rect = show_automation ~= false,
	}
end

-- The selected radio button normally ignores a second click. This invisible
-- momentary surface exists only over the selected position, preserving the
-- artwork while forwarding the original plug-in's active-button gesture.
local function active_reassert(node, index)
	return jbox.momentary_button{
		graphics = {
			node = node,
			hit_boundaries = { left = Q * 2, top = Q, right = Q * 2, bottom = Q },
		},
		value = property("keyModeReassertPress"),
		visibility_switch = property("keyMode"),
		visibility_values = { index },
		show_remote_box = false,
		show_automation_rect = false,
	}
end

local function status(node, name)
	return jbox.value_display{
		graphics = { node = node },
		value = property(name),
		read_only = true,
		show_remote_box = true,
		show_automation_rect = true,
		text_color = { 105, 183, 210, 255 },
		text_style = "Arial medium font",
	}
end

front = jbox.panel{
	graphics = { node = "S_backdrop" },
	widgets = {
		jbox.patch_name{
			graphics = { node = "S_patch_name" },
			center = true,
			fg_color = { 105, 183, 210 },
			loader_alt_color = { 239, 233, 216 },
			text_style = "Arial medium font",
		},
		jbox.patch_browse_group{
			graphics = { node = "S_patch_browse_group" },
		},
		jbox.device_name{
			graphics = { node = "S_device_name" },
		},
		jbox.sequence_meter{
			graphics = { node = "S_note_on" },
			value = property("noteOn"),
		},
		status("S_status_quality", "quality"),
		status("S_status_vcfTanhMode", "vcfTanhMode"),
		status("S_status_vcfFastEarlyMode", "vcfFastEarlyMode"),
		status("S_status_vcfSolverMode", "vcfSolverMode"),
		status("S_status_calibration", "calibration"),
		status("S_status_aging", "aging"),

		fader("S_fader_lfoRate", "lfoRate"),
		fader("S_fader_lfoDelay", "lfoDelay"),
		fader("S_fader_range", "range"),
		fader("S_fader_dcoLfo", "dcoLfo"),
		fader("S_fader_pwm", "pwm"),
		fader("S_fader_pwmMode", "pwmMode"),
		toggle("S_toggle_pulse", "pulse"),
		toggle("S_toggle_saw", "saw"),
		fader("S_fader_sub", "sub"),
		fader("S_fader_noise", "noise"),
		fader("S_fader_highPass", "highPass"),
		fader("S_fader_cutoff", "cutoff"),
		fader("S_fader_resonance", "resonance"),
		fader("S_fader_envPolarity", "envPolarity"),
		fader("S_fader_vcfEnv", "vcfEnv"),
		fader("S_fader_vcfLfo", "vcfLfo"),
		fader("S_fader_keyFollow", "keyFollow"),
		fader("S_fader_vcaMode", "vcaMode"),
		fader("S_fader_vcaLevel", "vcaLevel"),
		fader("S_fader_attack", "attack"),
		fader("S_fader_decay", "decay"),
		fader("S_fader_sustain", "sustain"),
		fader("S_fader_release", "release"),
		fader("S_fader_chorus", "chorus"),
		fader("S_fader_chorusNoise", "chorusNoise"),

		jbox.pitch_wheel{
			graphics = { node = "S_pitch_wheel" },
			value = property("pitchBend"),
		},
		jbox.analog_knob{
			graphics = { node = "S_mod_wheel" },
			value = property("modWheel"),
		},
		fader("S_fader_volume", "volume"),
		fader("S_fader_benderDco", "benderDco"),
		fader("S_fader_benderVcf", "benderVcf"),
		fader("S_fader_benderLfo", "benderLfo"),
		jbox.analog_knob{
			graphics = {
				node = "S_knob_portamento",
				hit_boundaries = { left = Q * 2, top = Q * 2, right = Q * 2, bottom = Q * 2 },
			},
			value = property("portamento"),
		},
		radio("S_radio_keyMode_0", "keyMode", 0),
		radio("S_radio_keyMode_1", "keyMode", 1),
		radio("S_radio_keyMode_2", "keyMode", 2),
		active_reassert("S_momentary_keyMode_0", 0),
		active_reassert("S_momentary_keyMode_1", 1),
		active_reassert("S_momentary_keyMode_2", 2),

		fader("S_fader_transpose", "transpose"),
		fader("S_fader_masterTune", "masterTune"),
		fader("S_fader_velocity", "velocity"),
		fader("S_fader_polyphony", "polyphony"),
	},
}

folded_front = jbox.panel{
	graphics = { node = "S_backdrop" },
	widgets = {
		jbox.patch_name{
			graphics = { node = "S_patch_name" },
			center = true,
			fg_color = { 105, 183, 210 },
			loader_alt_color = { 239, 233, 216 },
			text_style = "Bold LCD font",
		},
		jbox.patch_browse_group{
			graphics = { node = "S_patch_browse_group" },
		},
		jbox.device_name{
			graphics = { node = "S_device_name" },
		},
		jbox.sequence_meter{
			graphics = { node = "S_note_on" },
			value = property("noteOn"),
		},
	},
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
		radio("S_radio_quality_0", "quality", 0),
		radio("S_radio_quality_1", "quality", 1),
		radio("S_radio_quality_2", "quality", 2),
		radio("S_radio_vcfTanhMode_0", "vcfTanhMode", 0),
		radio("S_radio_vcfTanhMode_1", "vcfTanhMode", 1),
		radio("S_radio_vcfTanhMode_2", "vcfTanhMode", 2),
		radio("S_radio_vcfFastEarlyMode_0", "vcfFastEarlyMode", 0),
		radio("S_radio_vcfFastEarlyMode_1", "vcfFastEarlyMode", 1),
		radio("S_radio_vcfSolverMode_0", "vcfSolverMode", 0),
		radio("S_radio_vcfSolverMode_1", "vcfSolverMode", 1),
		radio("S_radio_vcfSolverMode_2", "vcfSolverMode", 2),
		fader("S_fader_calibration", "calibration", true, true),
		fader("S_fader_aging", "aging", true, true),
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_note" },
			socket = "/cv_inputs/note_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_gate" },
			socket = "/cv_inputs/gate_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_cutoff" },
			socket = "/cv_inputs/cutoff_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_resonance" },
			socket = "/cv_inputs/resonance_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_volume" },
			socket = "/cv_inputs/volume_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_vca_level" },
			socket = "/cv_inputs/vca_level_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_sub" },
			socket = "/cv_inputs/sub_cv",
		},
		jbox.cv_input_socket{
			graphics = { node = "S_cv_input_noise" },
			socket = "/cv_inputs/noise_cv",
		},
		jbox.audio_output_socket{
			graphics = { node = "S_audio_output_left" },
			socket = "/audio_outputs/left",
		},
		jbox.audio_output_socket{
			graphics = { node = "S_audio_output_right" },
			socket = "/audio_outputs/right",
		},
	},
}

folded_back = jbox.panel{
	graphics = { node = "S_backdrop" },
	cable_origin = { node = "S_cable_origin" },
	widgets = {
		jbox.device_name{
			graphics = { node = "S_device_name" },
		},
	},
}
