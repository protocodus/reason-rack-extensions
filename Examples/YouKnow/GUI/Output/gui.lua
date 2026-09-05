format_version = "4.0"

local function property(name)
	return "/custom_properties/" .. name
end

local function fader(x, y, name, show_automation, show_remote)
	return jbox.sequence_fader{
		transform = { x, y },
		animation = jbox.image_sequence{ path = "Fader", frames = 32 },
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
		patch_name(330, 21, 16, "Arial medium font"),
		jbox.patch_browse_group{
			transform = { 544, 17 },
			fx_patch = false,
		},
		jbox.device_name{
			transform = { 610, 23 },
		},
		jbox.sequence_meter{
			transform = { 709, 51 },
			animation = jbox.image_sequence{ path = "Lamp", frames = 2 },
			value = property("noteOn"),
		},
		status(304, 53, "quality"),
		status(370, 53, "vcfTanhMode"),
		status(436, 53, "vcfFastEarlyMode"),
		status(502, 53, "vcfSolverMode"),
		status(568, 53, "calibration"),
		status(634, 53, "aging"),

		-- Row 1: LFO, oscillator, high-pass filter
		fader(40, 119, "lfoRate"),
		fader(94, 119, "lfoDelay"),
		fader(168, 119, "range"),
		fader(224, 119, "dcoLfo"),
		fader(286, 119, "pwm"),
		fader(348, 119, "pwmMode"),
		toggle(416, 137, "pulse"),
		toggle(416, 169, "saw"),
		fader(530, 119, "sub"),
		fader(600, 119, "noise"),
		fader(698, 119, "highPass"),

		-- Row 2: filter, amplifier, envelope, chorus
		fader(31, 273, "cutoff"),
		fader(76, 273, "resonance"),
		fader(121, 273, "envPolarity"),
		fader(166, 273, "vcfEnv"),
		fader(211, 273, "vcfLfo"),
		fader(256, 273, "keyFollow"),
		fader(339, 273, "vcaMode"),
		fader(386, 273, "vcaLevel"),
		fader(455, 273, "attack"),
		fader(499, 273, "decay"),
		fader(543, 273, "sustain"),
		fader(587, 273, "release"),
		fader(661, 273, "chorus"),
		fader(711, 273, "chorusNoise"),

		-- Row 3: performance and keyboard
		jbox.pitch_wheel{
			transform = { 30, 430 },
			animation = jbox.image_sequence{ path = "PitchWheel", frames = 64 },
			value = property("pitchBend"),
			show_remote_box = true,
			show_automation_rect = true,
		},
		jbox.analog_knob{
			transform = { 88, 430 },
			animation = jbox.image_sequence{ path = "ModWheel", frames = 64 },
			value = property("modWheel"),
			show_remote_box = true,
			show_automation_rect = true,
		},
		fader(146, 437, "volume"),
		fader(204, 437, "benderDco"),
		fader(262, 437, "benderVcf"),
		fader(320, 437, "benderLfo"),
		jbox.analog_knob{
			transform = { 386, 455 },
			animation = jbox.image_sequence{ path = "Knob", frames = 63 },
			margins = { left = 2, top = 2, right = 2, bottom = 2 },
			value = property("portamento"),
			show_remote_box = true,
			show_automation_rect = true,
		},
		radio(448, 442, "keyMode", 0),
		radio(448, 471, "keyMode", 1),
		radio(448, 500, "keyMode", 2),
		active_reassert(448, 442, 0),
		active_reassert(448, 471, 1),
		active_reassert(448, 500, 2),

		fader(544, 437, "transpose"),
		fader(594, 437, "masterTune"),
		fader(646, 437, "velocity"),
		fader(700, 437, "polyphony"),
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
		radio(80, 378, "quality", 0),
		radio(80, 407, "quality", 1),
		radio(80, 436, "quality", 2),
		radio(188, 378, "vcfTanhMode", 0),
		radio(188, 407, "vcfTanhMode", 1),
		radio(188, 436, "vcfTanhMode", 2),
		radio(296, 393, "vcfFastEarlyMode", 0),
		radio(296, 422, "vcfFastEarlyMode", 1),
		radio(404, 378, "vcfSolverMode", 0),
		radio(404, 407, "vcfSolverMode", 1),
		radio(404, 436, "vcfSolverMode", 2),
		fader(544, 378, "calibration", true, true),
		fader(636, 378, "aging", true, true),
		jbox.cv_input_socket{
			transform = { 95, 155 },
			socket = "/cv_inputs/note_cv",
		},
		jbox.cv_input_socket{
			transform = { 167, 155 },
			socket = "/cv_inputs/gate_cv",
		},
		jbox.cv_input_socket{
			transform = { 239, 155 },
			socket = "/cv_inputs/cutoff_cv",
		},
		jbox.cv_input_socket{
			transform = { 311, 155 },
			socket = "/cv_inputs/resonance_cv",
		},
		jbox.cv_input_socket{
			transform = { 95, 245 },
			socket = "/cv_inputs/volume_cv",
		},
		jbox.cv_input_socket{
			transform = { 167, 245 },
			socket = "/cv_inputs/vca_level_cv",
		},
		jbox.cv_input_socket{
			transform = { 239, 245 },
			socket = "/cv_inputs/sub_cv",
		},
		jbox.cv_input_socket{
			transform = { 311, 245 },
			socket = "/cv_inputs/noise_cv",
		},
		jbox.audio_output_socket{
			transform = { 485, 230 },
			socket = "/audio_outputs/left",
		},
		jbox.audio_output_socket{
			transform = { 575, 230 },
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
