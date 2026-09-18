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
        jbox.store_property("/audio_outputs/left/dsp_latency", 0)
        jbox.store_property("/audio_outputs/right/dsp_latency", 0)
        jbox.store_property("/audio_outputs/close_left/dsp_latency", 0)
        jbox.store_property("/audio_outputs/close_right/dsp_latency", 0)
        jbox.store_property("/audio_outputs/far_left/dsp_latency", 0)
        jbox.store_property("/audio_outputs/far_right/dsp_latency", 0)
        jbox.store_property("/audio_outputs/piezo/dsp_latency", 0)
    end,
}

rt_input_setup = {
    notify = {
        "/note_states/*",
        "/custom_properties/*",
        "/cv_inputs/note_cv/value",
        "/cv_inputs/note_cv/connected",
        "/cv_inputs/gate_cv/value",
        "/cv_inputs/gate_cv/connected",
        "/cv_inputs/mallet_cv/value",
        "/cv_inputs/mallet_cv/connected",
        "/cv_inputs/position_cv/value",
        "/cv_inputs/position_cv/connected",
        "/cv_inputs/coupling_cv/value",
        "/cv_inputs/coupling_cv/connected",
        "/cv_inputs/volume_cv/value",
        "/cv_inputs/volume_cv/connected",
        "/cv_inputs/sympathetic_cv/value",
        "/cv_inputs/sympathetic_cv/connected",
        "/cv_inputs/roll_cv/value",
        "/cv_inputs/roll_cv/connected",
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
