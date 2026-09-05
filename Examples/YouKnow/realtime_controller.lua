format_version = "1.0"

rtc_bindings = {
    { source = "/environment/instance_id", dest = "/global_rtc/init_instance" },
    { source = "/environment/system_sample_rate", dest = "/global_rtc/init_instance" },
}

global_rtc = {
    init_instance = function()
        local sample_rate = jbox.load_property("/environment/system_sample_rate")
        local instance = jbox.make_native_object_rw("Instance", { sample_rate })
        jbox.store_property("/custom_properties/instance", instance)
        -- The DSP keeps this fixed across quality modes by padding shallower paths.
        jbox.store_property("/audio_outputs/left/dsp_latency", 41)
        jbox.store_property("/audio_outputs/right/dsp_latency", 41)
    end,
}

rt_input_setup = {
    notify = {
        "/note_states/*",
        -- Preserve each parameter and CV edge at its supplied frame; polling
        -- MOM alone would lose multiple changes within a render batch.
        "/custom_properties/*",
        "/cv_inputs/note_cv/value",
        "/cv_inputs/note_cv/connected",
        "/cv_inputs/gate_cv/value",
        "/cv_inputs/gate_cv/connected",
        "/cv_inputs/cutoff_cv/value",
        "/cv_inputs/cutoff_cv/connected",
        "/cv_inputs/resonance_cv/value",
        "/cv_inputs/resonance_cv/connected",
        "/cv_inputs/volume_cv/value",
        "/cv_inputs/volume_cv/connected",
        "/cv_inputs/vca_level_cv/value",
        "/cv_inputs/vca_level_cv/connected",
        "/cv_inputs/sub_cv/value",
        "/cv_inputs/sub_cv/connected",
        "/cv_inputs/noise_cv/value",
        "/cv_inputs/noise_cv/connected",
    },
}

sample_rate_setup = {
    native = {
        44100,
        48000,
        88200,
        96000,
        192000,
    },
}
