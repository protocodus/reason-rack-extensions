format_version = "4.0"

custom_properties = jbox.property_set{
    document_owner = {
        properties = {
            -- Instrument Model (0: Imperial Rosewood 5.0, 1: Mayan Padauk 4.3, 2: Balafon Ancestral, 3: Kalimba Artisan)
            model = jbox.number{
                default = 0,
                steps = 4,
                ui_name = jbox.ui_text("propertyname Model"),
                ui_type = jbox.ui_selector{
                    jbox.ui_text("model Imperial Rosewood 5.0"),
                    jbox.ui_text("model Mayan Padauk 4.3"),
                    jbox.ui_text("model Balafon Ancestral"),
                    jbox.ui_text("model Kalimba Artisan")
                },
            },

            -- Striker / Mallet Type (0: Soft Yarn / Thumb Flesh, 1: Medium Cord / Natural Thumb, 2: Hard Rubber / Thumb Nail, 3: Wood Baton / Thumb Pick)
            malletType = jbox.number{
                default = 1,
                steps = 4,
                ui_name = jbox.ui_text("propertyname Mallet Type"),
                ui_type = jbox.ui_selector{
                    jbox.ui_text("mallet Soft Yarn"),
                    jbox.ui_text("mallet Medium Cord"),
                    jbox.ui_text("mallet Hard Rubber"),
                    jbox.ui_text("mallet Wood Baton")
                },
            },

            -- Acoustic Bar & Mallet Modeling
            malletHardness = jbox.number{
                default = 0.40,
                ui_name = jbox.ui_text("propertyname Mallet Hardness"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            strikePosition = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("propertyname Strike Position"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            strikeJitter = jbox.number{
                default = 0.15,
                ui_name = jbox.ui_text("propertyname Strike Variance"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 100.0, units = { { decimals = 0, unit = { template = jbox.ui_text("percent template") } } } },
            },
            resonatorTune = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("propertyname Resonator Tune"),
                ui_type = jbox.ui_linear{ min = -50.0, max = 50.0, units = { { decimals = 1, unit = { template = jbox.ui_text("cents template") } } } },
            },
            resonatorCoupling = jbox.number{
                default = 0.70,
                ui_name = jbox.ui_text("propertyname Resonator Coupling"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            decay = jbox.number{
                default = 0.1139,
                ui_name = jbox.ui_text("propertyname Bar Decay"),
                ui_type = jbox.ui_linear{ min = 0.10, max = 8.0, units = { { decimals = 2, unit = { template = jbox.ui_text("s template") } } } },
            },
            buzzAmount = jbox.number{
                default = 0.15,
                ui_name = jbox.ui_text("propertyname Mirliton Buzz"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            artifacts = jbox.number{
                default = 0.35,
                ui_name = jbox.ui_text("propertyname Acoustic Artifacts"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },

            -- Premium Physical Modeling Phenomena
            sympathetic = jbox.number{
                default = 0.40,
                ui_name = jbox.ui_text("propertyname Sympathetic Halo"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            pitchGlide = jbox.number{
                default = 0.30,
                ui_name = jbox.ui_text("propertyname Attack Pitch Glide"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            bodyBloom = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("propertyname Frame Body Bloom"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            rollSpeed = jbox.number{
                default = 0.0,
                ui_name = jbox.ui_text("propertyname Mallet Roll Speed"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 20.0, units = { { decimals = 1, unit = { template = jbox.ui_text("hz template") } } } },
            },

            -- 3-Microphone Mixer
            closeLevel = jbox.number{
                default = 0.85,
                ui_name = jbox.ui_text("propertyname Close Mic"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            farLevel = jbox.number{
                default = 0.45,
                ui_name = jbox.ui_text("propertyname Far Room Mic"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            piezoLevel = jbox.number{
                default = 0.30,
                ui_name = jbox.ui_text("propertyname Piezo Pickup"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            stereoWidth = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("propertyname Stereo Width"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 2.0, units = { { decimals = 2 } } },
            },

            -- Analog Preamp & Compressor
            preampDrive = jbox.number{
                default = 0.15,
                ui_name = jbox.ui_text("propertyname Preamp Drive"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            warmth = jbox.number{
                default = 0.55,
                ui_name = jbox.ui_text("propertyname Warmth Tone"),
                ui_type = jbox.ui_linear{ min = -1.0, max = 1.0, units = { { decimals = 2 } } },
            },
            compAmount = jbox.number{
                default = 0.25,
                ui_name = jbox.ui_text("propertyname Comp Amount"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            compAttack = jbox.number{
                default = 0.1837,
                ui_name = jbox.ui_text("propertyname Comp Attack"),
                ui_type = jbox.ui_linear{ min = 1.0, max = 50.0, units = { { decimals = 1, unit = { template = jbox.ui_text("ms template") } } } },
            },
            compRelease = jbox.number{
                default = 0.2083,
                ui_name = jbox.ui_text("propertyname Comp Release"),
                ui_type = jbox.ui_linear{ min = 20.0, max = 500.0, units = { { decimals = 0, unit = { template = jbox.ui_text("ms template") } } } },
            },

            -- Master & Engine Options
            volume = jbox.number{
                default = 0.80,
                ui_name = jbox.ui_text("propertyname Master Volume"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            oversampling = jbox.number{
                default = 0,
                steps = 3,
                ui_name = jbox.ui_text("propertyname Oversampling"),
                ui_type = jbox.ui_selector{
                    jbox.ui_text("oversampling 2x (Studio Standard)"),
                    jbox.ui_text("oversampling 4x (High Resolution)"),
                    jbox.ui_text("oversampling 8x (Pristine Archival)")
                },
            },
            velocityCurve = jbox.number{
                default = 1,
                steps = 4,
                ui_name = jbox.ui_text("propertyname Velocity Curve"),
                ui_type = jbox.ui_selector{
                    jbox.ui_text("velcurve Soft"),
                    jbox.ui_text("velcurve Linear"),
                    jbox.ui_text("velcurve Hard"),
                    jbox.ui_text("velcurve Expressive")
                },
            },
            polyphony = jbox.number{
                default = 1,
                steps = 3,
                ui_name = jbox.ui_text("propertyname Polyphony"),
                ui_type = jbox.ui_selector{
                    jbox.ui_text("poly 8 Voices"),
                    jbox.ui_text("poly 16 Voices"),
                    jbox.ui_text("poly 24 Voices")
                },
            },
            masterTune = jbox.number{
                default = 0.50,
                ui_name = jbox.ui_text("propertyname Master Tune"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 1.0, units = { { decimals = 2 } } },
            },
            detune = jbox.number{
                default = 0.0,
                ui_name = jbox.ui_text("propertyname Detune"),
                ui_type = jbox.ui_linear{ min = 0.0, max = 100.0, units = { { decimals = 0, unit = { template = jbox.ui_text("detune template") } } } },
            },

            -- Performance Controllers
            modWheel = jbox.performance_modwheel{},
            pitchBend = jbox.performance_pitchbend{},
            sustainPedal = jbox.performance_sustainpedal{},
        }
    },

    rtc_owner = {
        properties = {
            instance = jbox.native_object{},
        }
    },

    rt_owner = {
        properties = {
            noteon = jbox.boolean{
                default = false,
                ui_name = jbox.ui_text("propertyname NoteOn Lamp"),
                ui_type = jbox.ui_linear{ min = 0, max = 1, units = { { decimals = 0 } } },
            },
        }
    }
}

midi_implementation_chart = {
    -- IDs above the physical MIDI-CC range expose stable Reason automation
    -- lanes without claiming hardware CCs or conflicting with reserved performance properties.
    midi_cc_chart = {
        [256] = "/custom_properties/volume",
        [257] = "/custom_properties/stereoWidth",
        [258] = "/custom_properties/rollSpeed",
        [259] = "/custom_properties/sympathetic",
        [260] = "/custom_properties/bodyBloom",
        [261] = "/custom_properties/model",
        [262] = "/custom_properties/malletType",
        [263] = "/custom_properties/malletHardness",
        [264] = "/custom_properties/strikePosition",
        [265] = "/custom_properties/resonatorTune",
        [266] = "/custom_properties/resonatorCoupling",
        [267] = "/custom_properties/decay",
        [268] = "/custom_properties/buzzAmount",
        [269] = "/custom_properties/artifacts",
        [270] = "/custom_properties/closeLevel",
        [271] = "/custom_properties/farLevel",
        [272] = "/custom_properties/piezoLevel",
        [273] = "/custom_properties/preampDrive",
        [274] = "/custom_properties/warmth",
        [275] = "/custom_properties/compAmount",
        [276] = "/custom_properties/pitchGlide",
        [277] = "/custom_properties/detune",
        [278] = "/custom_properties/strikeJitter",
        [279] = "/custom_properties/compAttack",
        [280] = "/custom_properties/compRelease",
        [281] = "/custom_properties/velocityCurve",
        [282] = "/custom_properties/polyphony",
        [283] = "/custom_properties/masterTune",
    }
}

remote_implementation_chart = {
    ["/custom_properties/model"] = { internal_name = "Model", short_ui_name = jbox.ui_text("rem_model"), shortest_ui_name = jbox.ui_text("rem_mod") },
    ["/custom_properties/malletType"] = { internal_name = "Mallet Type", short_ui_name = jbox.ui_text("rem_mallet"), shortest_ui_name = jbox.ui_text("rem_mlt") },
    ["/custom_properties/malletHardness"] = { internal_name = "Mallet Hardness", short_ui_name = jbox.ui_text("rem_malthrd"), shortest_ui_name = jbox.ui_text("rem_hrd") },
    ["/custom_properties/strikePosition"] = { internal_name = "Strike Position", short_ui_name = jbox.ui_text("rem_pos"), shortest_ui_name = jbox.ui_text("rem_psi") },
    ["/custom_properties/strikeJitter"] = { internal_name = "Strike Variance", short_ui_name = jbox.ui_text("rem_variance"), shortest_ui_name = jbox.ui_text("rem_var") },
    ["/custom_properties/resonatorTune"] = { internal_name = "Resonator Tune", short_ui_name = jbox.ui_text("rem_restun"), shortest_ui_name = jbox.ui_text("rem_rtn") },
    ["/custom_properties/resonatorCoupling"] = { internal_name = "Resonator Coupling", short_ui_name = jbox.ui_text("rem_rescoup"), shortest_ui_name = jbox.ui_text("rem_rcp") },
    ["/custom_properties/decay"] = { internal_name = "Decay", short_ui_name = jbox.ui_text("rem_decay"), shortest_ui_name = jbox.ui_text("rem_dcy") },
    ["/custom_properties/buzzAmount"] = { internal_name = "Mirliton Buzz", short_ui_name = jbox.ui_text("rem_buzz"), shortest_ui_name = jbox.ui_text("rem_buz") },
    ["/custom_properties/artifacts"] = { internal_name = "Artifacts", short_ui_name = jbox.ui_text("rem_art"), shortest_ui_name = jbox.ui_text("rem_ati") },
    ["/custom_properties/sympathetic"] = { internal_name = "Sympathetic Halo", short_ui_name = jbox.ui_text("rem_symp"), shortest_ui_name = jbox.ui_text("rem_sym") },
    ["/custom_properties/pitchGlide"] = { internal_name = "Attack Pitch Glide", short_ui_name = jbox.ui_text("rem_glide"), shortest_ui_name = jbox.ui_text("rem_gld") },
    ["/custom_properties/bodyBloom"] = { internal_name = "Frame Body Bloom", short_ui_name = jbox.ui_text("rem_body"), shortest_ui_name = jbox.ui_text("rem_bdy") },
    ["/custom_properties/rollSpeed"] = { internal_name = "Mallet Roll Speed", short_ui_name = jbox.ui_text("rem_roll"), shortest_ui_name = jbox.ui_text("rem_rol") },
    ["/custom_properties/closeLevel"] = { internal_name = "Close Mic", short_ui_name = jbox.ui_text("rem_close"), shortest_ui_name = jbox.ui_text("rem_cls") },
    ["/custom_properties/farLevel"] = { internal_name = "Far Mic", short_ui_name = jbox.ui_text("rem_far"), shortest_ui_name = jbox.ui_text("rem_far") },
    ["/custom_properties/piezoLevel"] = { internal_name = "Piezo Pickup", short_ui_name = jbox.ui_text("rem_piezo"), shortest_ui_name = jbox.ui_text("rem_pzo") },
    ["/custom_properties/stereoWidth"] = { internal_name = "Stereo Width", short_ui_name = jbox.ui_text("rem_width"), shortest_ui_name = jbox.ui_text("rem_wdt") },
    ["/custom_properties/preampDrive"] = { internal_name = "Preamp Drive", short_ui_name = jbox.ui_text("rem_drive"), shortest_ui_name = jbox.ui_text("rem_drv") },
    ["/custom_properties/warmth"] = { internal_name = "Warmth", short_ui_name = jbox.ui_text("rem_warm"), shortest_ui_name = jbox.ui_text("rem_wrm") },
    ["/custom_properties/compAmount"] = { internal_name = "Comp Amount", short_ui_name = jbox.ui_text("rem_comp"), shortest_ui_name = jbox.ui_text("rem_cmp") },
    ["/custom_properties/compAttack"] = { internal_name = "Comp Attack", short_ui_name = jbox.ui_text("rem_attack"), shortest_ui_name = jbox.ui_text("rem_atk") },
    ["/custom_properties/compRelease"] = { internal_name = "Comp Release", short_ui_name = jbox.ui_text("rem_release"), shortest_ui_name = jbox.ui_text("rem_rel") },
    ["/custom_properties/volume"] = { internal_name = "Master Volume", short_ui_name = jbox.ui_text("rem_vol"), shortest_ui_name = jbox.ui_text("rem_vlm") },
    ["/custom_properties/oversampling"] = { internal_name = "Oversampling", short_ui_name = jbox.ui_text("rem_osamp"), shortest_ui_name = jbox.ui_text("rem_os") },
    ["/custom_properties/velocityCurve"] = { internal_name = "Velocity Curve", short_ui_name = jbox.ui_text("rem_velcurve"), shortest_ui_name = jbox.ui_text("rem_vel") },
    ["/custom_properties/polyphony"] = { internal_name = "Polyphony", short_ui_name = jbox.ui_text("rem_poly"), shortest_ui_name = jbox.ui_text("rem_ply") },
    ["/custom_properties/masterTune"] = { internal_name = "Master Tune", short_ui_name = jbox.ui_text("rem_mtune"), shortest_ui_name = jbox.ui_text("rem_mtn") },
    ["/custom_properties/detune"] = { internal_name = "Detune Drift", short_ui_name = jbox.ui_text("rem_detune"), shortest_ui_name = jbox.ui_text("rem_dtn") },
}

cv_inputs = {
    note_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_note") },
    gate_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_gate") },
    mallet_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_mallet") },
    position_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_position") },
    coupling_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_coupling") },
    volume_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_volume") },
    sympathetic_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_sympathetic") },
    roll_cv = jbox.cv_input{ ui_name = jbox.ui_text("cv_roll") },
}

audio_outputs = {
    left = jbox.audio_output{ ui_name = jbox.ui_text("out_left") },
    right = jbox.audio_output{ ui_name = jbox.ui_text("out_right") },
    close_left = jbox.audio_output{ ui_name = jbox.ui_text("out_close_l") },
    close_right = jbox.audio_output{ ui_name = jbox.ui_text("out_close_r") },
    far_left = jbox.audio_output{ ui_name = jbox.ui_text("out_far_l") },
    far_right = jbox.audio_output{ ui_name = jbox.ui_text("out_far_r") },
    piezo = jbox.audio_output{ ui_name = jbox.ui_text("out_piezo") },
}

jbox.add_stereo_audio_routing_pair{ left = "/audio_outputs/left", right = "/audio_outputs/right" }
jbox.add_stereo_audio_routing_pair{ left = "/audio_outputs/close_left", right = "/audio_outputs/close_right" }
jbox.add_stereo_audio_routing_pair{ left = "/audio_outputs/far_left", right = "/audio_outputs/far_right" }
jbox.add_stereo_instrument_routing_hint{ left_output = "/audio_outputs/left", right_output = "/audio_outputs/right" }
jbox.add_stereo_audio_routing_target{ signal_type = "normal", left = "/audio_outputs/left", right = "/audio_outputs/right", auto_route_enable = true }

jbox.add_cv_routing_target{ signal_type = "gate", path = "/cv_inputs/gate_cv", auto_route_enable = true }
jbox.add_cv_routing_target{ signal_type = "pitch", path = "/cv_inputs/note_cv", auto_route_enable = true }
