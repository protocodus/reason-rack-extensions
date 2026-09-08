format_version = "4.0"

local function property(name)
	return "/custom_properties/" .. name
end

local function fader(x, y, name, path, show_automation, show_remote)
	return jbox.sequence_fader{
		transform = { x, y },
		animation = jbox.image_sequence{ path = path, frames = 32 },
		margins = { left = 2, top = 4, right = 2, bottom = 4 },
		value = property(name),
		handle_size = 14,
		inset1 = 8,
		inset2 = 8,
		orientation = "vertical",
		inverted = false,
		show_remote_box = show_remote ~= false,
		show_automation_rect = show_automation ~= false,
	}
end

local function toggle(x, y, name)
	return jbox.toggle_button{
		transform = { x, y },
		background = jbox.image_sequence{ path = "Toggle", frames = 2 },
		margins = { left = 2, top = 2, right = 2, bottom = 2 },
		value = property(name),
		show_remote_box = true,
		show_automation_rect = true,
	}
end

local function radio(x, y, name, index, show_remote, show_automation)
	return jbox.radio_button{
		transform = { x, y },
		background = jbox.image_sequence{ path = "Toggle", frames = 2 },
		margins = { left = 2, top = 1, right = 2, bottom = 1 },
		value = property(name),
		index = index,
		show_remote_box = show_remote ~= false,
		show_automation_rect = show_automation ~= false,
	}
end

local function active_reassert(x, y, index)
	return jbox.momentary_button{
		transform = { x, y },
		background = jbox.image_sequence{ path = "MomentaryOverlay", frames = 2 },
		margins = { left = 2, top = 1, right = 2, bottom = 1 },
		value = property("keyModeReassertPress"),
		visibility_switch = property("keyMode"),
		visibility_values = { index },
		show_remote_box = false,
		show_automation_rect = false,
	}
end

local function patch_name(x, y, height, text_style)
	return jbox.patch_name{
		transform = { x, y },
		center = true,
		fg_color = { 105, 183, 210 },
		height = height,
		loader_alt_color = { 239, 233, 216 },
		text_style = text_style,
		width = 204,
	}
end

local function status(x, y, name)
	return jbox.value_display{
		transform = { x, y },
		value = property(name),
		height = 16,
		horizontal_justification = "center",
		read_only = true,
		show_remote_box = true,
		show_automation_rect = true,
		text_color = { 105, 183, 210 },
		text_style = "Arial medium font",
		width = 56,
	}
end

front = jbox.panel{
	backdrop = jbox.image{ path = "Reason_GUI_front_root_Panel" },
	widgets = {
		patch_name(299, 16, 16, "Arial medium font"),
		jbox.patch_browse_group{
			transform = { 517, 13 },
			fx_patch = false,
		},
		jbox.device_name{
			transform = { 589, 17 },
		},
		jbox.sequence_meter{
			transform = { 724, 51 },
			animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
			value = property("noteOn"),
		},
		status(84, 48, "quality"),
		status(183, 48, "vcfTanhMode"),
		status(286, 48, "vcfFastEarlyMode"),
		status(395, 48, "vcfSolverMode"),
		status(524, 48, "calibration"),
		status(627, 48, "aging"),

		-- Row 1: LFO, oscillator, high-pass filter
		fader(31, 116, "lfoRate", "FaderSource"),
		fader(98, 116, "lfoDelay", "FaderSource"),
		fader(183, 116, "range", "FaderSource"),
		fader(248, 116, "dcoLfo", "FaderSource"),
		fader(307, 116, "pwm", "FaderSource"),
		fader(387, 116, "pwmMode", "FaderSource"),
		toggle(463, 134, "pulse"),
		toggle(463, 166, "saw"),
		fader(555, 116, "sub", "FaderSource"),
		fader(618, 116, "noise", "FaderSource"),
		fader(707, 116, "highPass", "FaderSource"),

		-- Row 2: filter, amplifier, envelope, chorus
		fader(29, 270, "cutoff", "FaderShape"),
		fader(74, 270, "resonance", "FaderShape"),
		fader(121, 270, "envPolarity", "FaderShape"),
		fader(163, 270, "vcfEnv", "FaderShape"),
		fader(204, 270, "vcfLfo", "FaderShape"),
		fader(249, 270, "keyFollow", "FaderShape"),
		fader(338, 270, "vcaMode", "FaderShape"),
		fader(391, 270, "vcaLevel", "FaderShape"),
		fader(457, 270, "attack", "FaderShape"),
		fader(496, 270, "decay", "FaderShape"),
		fader(534, 270, "sustain", "FaderShape"),
		fader(573, 270, "release", "FaderShape"),
		fader(649, 270, "chorus", "FaderEffect"),
		fader(702, 270, "chorusNoise", "FaderEffect"),

		-- Row 3: performance and keyboard
		jbox.pitch_wheel{
			transform = { 30, 427 },
			animation = jbox.image_sequence{ path = "PitchWheel", frames = 64 },
			value = property("pitchBend"),
			show_remote_box = true,
			show_automation_rect = true,
		},
		jbox.analog_knob{
			transform = { 82, 427 },
			animation = jbox.image_sequence{ path = "ModWheel", frames = 64 },
			value = property("modWheel"),
			show_remote_box = true,
			show_automation_rect = true,
		},
		fader(277, 434, "volume", "FaderPlay"),
		fader(129, 434, "benderDco", "FaderPlay"),
		fader(174, 434, "benderVcf", "FaderPlay"),
		fader(219, 434, "benderLfo", "FaderPlay"),
		jbox.analog_knob{
			transform = { 348, 452 },
			animation = jbox.image_sequence{ path = "Knob", frames = 63 },
			margins = { left = 2, top = 2, right = 2, bottom = 2 },
			value = property("portamento"),
			show_remote_box = true,
			show_automation_rect = true,
		},
		radio(423, 437, "keyMode", 0),
		radio(423, 468, "keyMode", 1),
		radio(423, 499, "keyMode", 2),
		active_reassert(423, 437, 0),
		active_reassert(423, 468, 1),
		active_reassert(423, 499, 2),

		fader(529, 434, "transpose", "FaderPlay"),
		fader(596, 434, "masterTune", "FaderPlay"),
		fader(645, 434, "velocity", "FaderPlay"),
		fader(700, 434, "polyphony", "FaderPlay"),
	},
}

folded_front = jbox.panel{
	backdrop = jbox.image{ path = "Reason_GUI_folded_front_root_Panel" },
	widgets = {
		patch_name(300, 10, 10, "Bold LCD font"),
		jbox.patch_browse_group{
			transform = { 510, 4 },
			fx_patch = false,
		},
		jbox.device_name{
			transform = { 600, 8 },
		},
		jbox.sequence_meter{
			transform = { 690, 10 },
			animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
			value = property("noteOn"),
		},
	},
}

back = jbox.panel{
	backdrop = jbox.image{ path = "Reason_GUI_back_root_Panel" },
	widgets = {
		jbox.placeholder{
			transform = { 347, 15 },
		},
		jbox.device_name{
			transform = { 20, 150 },
			orientation = "vertical",
		},
		radio(80, 146, "quality", 0),
		radio(80, 177, "quality", 1),
		radio(80, 208, "quality", 2),
		radio(188, 146, "vcfTanhMode", 0),
		radio(188, 177, "vcfTanhMode", 1),
		radio(188, 208, "vcfTanhMode", 2),
		radio(296, 161, "vcfFastEarlyMode", 0),
		radio(296, 192, "vcfFastEarlyMode", 1),
		radio(404, 146, "vcfSolverMode", 0),
		radio(404, 177, "vcfSolverMode", 1),
		radio(404, 208, "vcfSolverMode", 2),
		fader(544, 146, "calibration", "FaderPlay", true, true),
		fader(636, 146, "aging", "FaderPlay", true, true),
		jbox.cv_input_socket{
			transform = { 95, 387 },
			socket = "/cv_inputs/note_cv",
		},
		jbox.cv_input_socket{
			transform = { 167, 387 },
			socket = "/cv_inputs/gate_cv",
		},
		jbox.cv_input_socket{
			transform = { 239, 387 },
			socket = "/cv_inputs/cutoff_cv",
		},
		jbox.cv_input_socket{
			transform = { 311, 387 },
			socket = "/cv_inputs/resonance_cv",
		},
		jbox.cv_input_socket{
			transform = { 95, 477 },
			socket = "/cv_inputs/volume_cv",
		},
		jbox.cv_input_socket{
			transform = { 167, 477 },
			socket = "/cv_inputs/vca_level_cv",
		},
		jbox.cv_input_socket{
			transform = { 239, 477 },
			socket = "/cv_inputs/sub_cv",
		},
		jbox.cv_input_socket{
			transform = { 311, 477 },
			socket = "/cv_inputs/noise_cv",
		},
		jbox.audio_output_socket{
			transform = { 485, 462 },
			socket = "/audio_outputs/left",
		},
		jbox.audio_output_socket{
			transform = { 575, 462 },
			socket = "/audio_outputs/right",
		},
	},
}

folded_back = jbox.panel{
	backdrop = jbox.image{ path = "Reason_GUI_folded_back_root_Panel" },
	cable_origin = { 377, 15 },
	widgets = {
		jbox.device_name{
			transform = { 600, 8 },
		},
	},
}
