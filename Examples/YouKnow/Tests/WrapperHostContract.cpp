#include "../YouKnow.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <new>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace { bool allocationForbidden = false; }

void* operator new(std::size_t size)
{
    assert(!allocationForbidden);
    if (void* memory = std::malloc(size == 0 ? 1 : size))
        return memory;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }

namespace youknow
{
struct YouKnowTestAccess
{
    static std::uint16_t heldCount(const YouKnowEngine& engine, int note) noexcept
    {
        return engine.heldNoteCounts_[static_cast<std::size_t>(note)];
    }

    static int keyedSlotFor(const YouKnowEngine& engine, int note) noexcept
    {
        for (int slot = 0; slot < YouKnowEngine::maxVoices; ++slot)
        {
            const auto& voice = engine.voices_[static_cast<std::size_t>(slot)];
            if (voice.active && voice.keyDown && voice.rootMidi == note)
                return slot;
        }
        return -1;
    }

    static int envelopeStage(const YouKnowEngine& engine, int slot) noexcept
    {
        return static_cast<int>(
            engine.voices_[static_cast<std::size_t>(slot)].envelope.stage);
    }

    static std::uint16_t envelopeLevel(const YouKnowEngine& engine,
                                       int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].envelope.level;
    }

    static float currentMidi(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].currentMidi;
    }

    static bool dcoResetPending(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].dcoResetPending;
    }

    static VcfSolverMode solverMode(const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_.vcfSolverMode;
    }

    static VcfTanhMode tanhMode(const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_.vcfTanhMode;
    }

    static VcfFastEarlyMode fastEarlyMode(
        const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_.vcfFastEarlyMode;
    }

    static float masterTuneCents(const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_.masterTuneCents;
    }

    static float aging(const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_.aging;
    }

    static float pitchBendTarget(const YouKnowEngine& engine) noexcept
    {
        return engine.pitchBendTarget_;
    }

    static const EngineParameters& parameters(const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_;
    }

};
} // namespace youknow

struct CYouKnowTestAccess
{
    static youknow::YouKnowEngine& engine(CYouKnow& device) noexcept
    {
        return device.fEngine;
    }

    static void handleCV(CYouKnow& device)
    {
        device.SnapshotProperties();
        device.HandleCV();
    }

    static int lastCVNote(const CYouKnow& device) noexcept
    {
        return device.fLastCVNote;
    }

    static bool cvActive(const CYouKnow& device) noexcept
    {
        return device.fCVActive;
    }

    static int oversamplingFactor(const CYouKnow& device) noexcept
    {
        return device.fEngine.getOversamplingFactor();
    }

    static float patchGainTarget(const CYouKnow& device) noexcept
    {
        return device.fPatchGainTarget;
    }

    static float patchGainSmoothed(const CYouKnow& device) noexcept
    {
        return device.fPatchGainSmoothed;
    }
};

namespace
{
enum class Kind : std::uint64_t { Number, Boolean, Buffer };

struct Encoded
{
    Kind kind;
    double value;
};

static_assert(sizeof(Encoded) == sizeof(TJBox_Value));

struct Object
{
    std::string path;
};

struct Property
{
    TJBox_ObjectRef object;
    std::string key;
    TJBox_Value value;
};

std::vector<Object> objects { Object {} };
std::vector<Property> properties { Property {} };
double sampleRate = 48000.0;
double masterTune = 0.0;
double resetCounter = 0.0;
std::array<float, 64> capturedLeft {};
std::array<float, 64> capturedRight {};
bool wroteLeft = false;
bool wroteRight = false;
std::size_t momPropertyLoads = 0;
std::size_t momNumberLoads = 0;

TJBox_Value encode(Kind kind, double value)
{
    const Encoded encoded { kind, value };
    TJBox_Value result {};
    std::memcpy(&result, &encoded, sizeof(result));
    return result;
}

Encoded decode(TJBox_Value value)
{
    Encoded result {};
    std::memcpy(&result, &value, sizeof(result));
    return result;
}

TJBox_ObjectRef objectFor(const char* path)
{
    for (std::size_t index = 1; index < objects.size(); ++index)
        if (objects[index].path == path)
            return static_cast<TJBox_ObjectRef>(index);
    objects.push_back({ path });
    return static_cast<TJBox_ObjectRef>(objects.size() - 1);
}

TJBox_PropertyRef propertyFor(TJBox_ObjectRef object, const char* key)
{
    for (std::size_t index = 1; index < properties.size(); ++index)
        if (properties[index].object == object && properties[index].key == key)
            return static_cast<TJBox_PropertyRef>(index);

    Kind kind = Kind::Number;
    double value = 0.0;
    const std::string name { key };
    if (name == "saw") value = 1.0;
    else if (name == "quality") value = 0.0;
    else if (name == "vcfTanhMode") value = 2.0;
    else if (name == "vcfFastEarlyMode") value = 1.0;
    else if (name == "vcfSolverMode") value = 2.0;
    else if (name == "volume") value = 0.80;
    else if (name == "presetGain") value = 0.50;
    else if (name == "benderDco") value = 0.30;
    else if (name == "lfoRate") value = 0.42;
    else if (name == "pwm") value = 0.30;
    else if (name == "pwmMode") value = 1.0;
    else if (name == "range") value = 1.0;
    else if (name == "highPass") value = 1.0;
    else if (name == "cutoff") value = 0.62;
    else if (name == "resonance") value = 0.10;
    else if (name == "vcfEnv") value = 0.35;
    else if (name == "keyFollow") value = 0.50;
    else if (name == "vcaLevel") value = 0.80;
    else if (name == "decay") value = 0.45;
    else if (name == "sustain") value = 0.70;
    else if (name == "release") value = 0.30;
    else if (name == "transpose") value = 12.0;
    else if (name == "masterTune") value = 0.50;
    else if (name == "calibration") value = 0.50;
    else if (name == "aging") value = 0.50;
    else if (name == "chorusNoise")
        value = youknow::Chorus::defaultNoiseScale;
    else if (name == "polyphony") value = 5.0;
    else if (name == "pitchBend") value = 0.50;

    if (name == "saw" || name == "pulse"
        || name == "noteOn" || name == "connected"
        || name == "keyModeReassertPress")
        kind = Kind::Boolean;

    properties.push_back({ object, key, encode(kind, value) });
    return static_cast<TJBox_PropertyRef>(properties.size() - 1);
}

void set(const char* path, const char* key, Kind kind, double value)
{
    const auto property = propertyFor(objectFor(path), key);
    properties[property].value = encode(kind, value);
}

double get(const char* path, const char* key)
{
    const auto property = propertyFor(objectFor(path), key);
    return decode(properties[property].value).value;
}

void clearCapture()
{
    capturedLeft.fill(0.0f);
    capturedRight.fill(0.0f);
    wroteLeft = false;
    wroteRight = false;
}

TJBox_PropertyDiff noteDiff(int note, int velocity, int frame)
{
    TJBox_PropertyDiff diff {};
    diff.fObjectRef = objectFor("/note_states");
    diff.fPropertyTag = static_cast<TJBox_Tag>(note);
    diff.fCurrentValue = encode(Kind::Number, velocity);
    diff.fAtFrameIndex = static_cast<TJBox_UInt16>(frame);
    return diff;
}

TJBox_PropertyDiff customDiff(const char* name)
{
    TJBox_PropertyDiff diff {};
    diff.fObjectRef = objectFor("/custom_properties");
    diff.fPropertyRef = propertyFor(diff.fObjectRef, name);
    diff.fCurrentValue = properties[diff.fPropertyRef].value;
    return diff;
}

TJBox_PropertyDiff change(const char* path, const char* key, Kind kind,
                          double value, int frame)
{
    TJBox_PropertyDiff diff {};
    diff.fObjectRef = objectFor(path);
    diff.fPropertyRef = propertyFor(diff.fObjectRef, key);
    diff.fPreviousValue = properties[diff.fPropertyRef].value;
    diff.fCurrentValue = encode(kind, value);
    diff.fAtFrameIndex = static_cast<TJBox_UInt16>(frame);
    properties[diff.fPropertyRef].value = diff.fCurrentValue;
    return diff;
}

// --- Panel reach ---------------------------------------------------------
// A control that is drawn, remotable and persisted still does nothing unless
// the wrapper hands it to the engine. The sweep below plays the same short
// program twice per property -- once at the baseline, once at an alternate
// setting -- and requires the rendered stereo output to differ. The baseline
// is chosen so every property is observable: the pulse wave is on so PWM has
// something to shape, the LFO has depth so its rate and delay reach the
// signal, the bender is off centre so its three depth sliders bite, and the
// note velocity is mid-scale so velocity sensitivity is not a no-op.
struct Setting
{
    const char* name;
    Kind kind;
    double value;
    double alternate;
};

const Setting kPanel[] = {
    { "volume", Kind::Number, 0.80, 0.30 },
    { "benderDco", Kind::Number, 0.50, 0.00 },
    { "benderVcf", Kind::Number, 0.20, 0.00 },
    { "benderLfo", Kind::Number, 0.50, 0.00 },
    { "portamento", Kind::Number, 0.30, 0.00 },
    { "keyMode", Kind::Number, 0.0, 2.0 },
    { "lfoRate", Kind::Number, 0.60, 0.10 },
    { "lfoDelay", Kind::Number, 0.00, 1.00 },
    { "dcoLfo", Kind::Number, 0.40, 0.00 },
    { "pwm", Kind::Number, 0.40, 0.90 },
    { "pwmMode", Kind::Number, 1.0, 0.0 },
    { "range", Kind::Number, 1.0, 2.0 },
    { "saw", Kind::Boolean, 1.0, 0.0 },
    { "pulse", Kind::Boolean, 1.0, 0.0 },
    { "sub", Kind::Number, 0.50, 0.00 },
    { "noise", Kind::Number, 0.20, 0.00 },
    // The cutoff modulators below stay well inside the 14-bit converter
    // accumulator. Summed past its ceiling they all clamp together and a
    // depth slider stops making any difference at all.
    { "highPass", Kind::Number, 1.0, 3.0 },
    { "cutoff", Kind::Number, 0.30, 0.60 },
    { "resonance", Kind::Number, 0.40, 0.00 },
    { "envPolarity", Kind::Number, 0.0, 1.0 },
    { "vcfEnv", Kind::Number, 0.20, 0.00 },
    { "vcfLfo", Kind::Number, 0.30, 0.00 },
    { "keyFollow", Kind::Number, 0.20, 0.00 },
    { "vcaMode", Kind::Number, 0.0, 1.0 },
    { "vcaLevel", Kind::Number, 0.80, 0.30 },
    // A fast attack, so the short program actually reaches the decay segment.
    { "attack", Kind::Number, 0.00, 0.90 },
    { "decay", Kind::Number, 0.50, 0.00 },
    { "sustain", Kind::Number, 0.60, 0.00 },
    { "release", Kind::Number, 0.40, 0.00 },
    { "chorus", Kind::Number, 1.0, 3.0 },
    { "transpose", Kind::Number, 12.0, 0.0 },
    { "masterTune", Kind::Number, 0.50, 0.00 },
    { "velocity", Kind::Number, 0.50, 0.00 },
    { "calibration", Kind::Number, 0.50, 0.00 },
    { "aging", Kind::Number, 0.00, 1.00 },
    { "chorusNoise", Kind::Number,
      youknow::Chorus::defaultNoiseScale, 0.00 },
    // Three voices, so the second chord has to reuse the slots the first one
    // played. Portamento glides from a voice's own pitch history and does
    // nothing at all on a slot that has never sounded.
    { "polyphony", Kind::Number, 2.0, 0.0 },
    { "quality", Kind::Number, 1.0, 2.0 },
    { "pitchBend", Kind::Number, 0.75, 0.50 },
    { "modWheel", Kind::Number, 0.50, 0.00 },
    { "sustainPedal", Kind::Number, 0.0, 1.0 },
    { "vcfTanhMode", Kind::Number, 2.0, 0.0 },
    { "vcfFastEarlyMode", Kind::Number, 1.0, 0.0 },
    { "vcfSolverMode", Kind::Number, 2.0, 0.0 },
};

// Two three-note chords. The first fills the voices and is released, so the
// release and sustain-pedal paths are exercised; the second lands on voices
// that now carry pitch history, which is the only state in which the
// instrument's per-voice portamento glides at all.
std::vector<float> renderProgram(const Setting* override_, bool automate = false)
{
    set("/custom_properties", "presetGain", Kind::Number, 0.50);
    for (const auto& setting : kPanel)
        set("/custom_properties", setting.name, setting.kind, setting.value);
    if (override_ != nullptr && !automate)
        set("/custom_properties", override_->name, override_->kind,
            override_->alternate);
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0);
    resetCounter = 0.0;

    CYouKnow device(sampleRate);
    // Restored/live quality changes are deliberately applied only while the
    // output path is idle; allow its fade-down/rebuild/fade-up to finish
    // before the note program measures panel reach.
    for (int batch = 0; batch < 12; ++batch)
    {
        clearCapture();
        device.RenderBatch(nullptr, 0);
    }
    std::vector<float> rendered;
    for (int batch = 0; batch < 50; ++batch)
    {
        std::vector<TJBox_PropertyDiff> diffs;
        if (batch == 0) diffs.push_back(noteDiff(60, 64, 0));
        if (batch == 0 && override_ != nullptr && automate)
            diffs.push_back(change("/custom_properties", override_->name,
                override_->kind, override_->alternate, 17));
        if (batch == 1) diffs.push_back(noteDiff(67, 100, 10));
        if (batch == 2) diffs.push_back(noteDiff(72, 90, 5));
        if (batch == 18)
        {
            diffs.push_back(noteDiff(60, 0, 0));
            diffs.push_back(noteDiff(67, 0, 1));
            diffs.push_back(noteDiff(72, 0, 2));
        }
        if (batch == 24)
        {
            diffs.push_back(noteDiff(62, 96, 0));
            diffs.push_back(noteDiff(69, 96, 1));
            diffs.push_back(noteDiff(74, 96, 2));
        }
        if (batch == 42)
        {
            diffs.push_back(noteDiff(62, 0, 0));
            diffs.push_back(noteDiff(69, 0, 1));
            diffs.push_back(noteDiff(74, 0, 2));
        }
        clearCapture();
        device.RenderBatch(diffs.empty() ? nullptr : diffs.data(),
                           static_cast<TJBox_UInt32>(diffs.size()));
        rendered.insert(rendered.end(), capturedLeft.begin(), capturedLeft.end());
        rendered.insert(rendered.end(), capturedRight.begin(), capturedRight.end());
    }
    return rendered;
}

struct Stream
{
    std::array<float, 256> left {};
    std::array<float, 256> right {};
    bool wrote = false;
};

struct Batch
{
    std::array<float, 64> left {};
    std::array<float, 64> right {};
};

Batch renderBatch(CYouKnow& device, const TJBox_PropertyDiff* diffs = nullptr,
                  TJBox_UInt32 diffCount = 0)
{
    clearCapture();
    allocationForbidden = true;
    device.RenderBatch(diffs, diffCount);
    allocationForbidden = false;
    return { capturedLeft, capturedRight };
}

Stream renderNote(CYouKnow& device, const TJBox_PropertyDiff& diff)
{
    Stream stream;
    for (int batch = 0; batch < 4; ++batch)
    {
        clearCapture();
        device.RenderBatch(batch == 0 ? &diff : nullptr, batch == 0 ? 1 : 0);
        std::copy(capturedLeft.begin(), capturedLeft.end(),
                  stream.left.begin() + batch * 64);
        std::copy(capturedRight.begin(), capturedRight.end(),
                  stream.right.begin() + batch * 64);
        stream.wrote = stream.wrote || wroteLeft || wroteRight;
    }
    return stream;
}

void configureCVHost()
{
    for (const auto& setting : kPanel)
        set("/custom_properties", setting.name, setting.kind, setting.value);
    set("/custom_properties", "quality", Kind::Number, 0.0);
    set("/custom_properties", "presetGain", Kind::Number, 0.50);
    set("/custom_properties", "keyModeReassertPress", Kind::Boolean, 0.0);
    set("/custom_properties", "pitchBend", Kind::Number, 0.50);
    set("/custom_properties", "sustainPedal", Kind::Number, 0.0);
    for (const char* path : {
             "/cv_inputs/note_cv", "/cv_inputs/gate_cv",
             "/cv_inputs/cutoff_cv", "/cv_inputs/resonance_cv",
             "/cv_inputs/volume_cv", "/cv_inputs/vca_level_cv",
             "/cv_inputs/sub_cv", "/cv_inputs/noise_cv" })
    {
        set(path, "connected", Kind::Boolean, 0.0);
        set(path, "value", Kind::Number, 0.0);
    }
    set("/cv_inputs/note_cv", "value", Kind::Number, 60.0 / 127.0);
    masterTune = resetCounter = 0.0;
}

void checkTimedAutomationAndCV()
{
    using Access = youknow::YouKnowTestAccess;
    // First render sees final MOM values. Its nonzero-frame previous values
    // must reconstruct the untouched initial sound, including boolean controls.
    configureCVHost();
    CYouKnow reference(sampleRate);
    const auto note = noteDiff(60, 127, 0);
    const auto before = renderBatch(reference, &note, 1);
    configureCVHost();
    CYouKnow timed(sampleRate);
    const std::array firstEvents {
        noteDiff(60, 127, 0),
        change("/custom_properties", "volume", Kind::Number, 0.0, 37),
        change("/custom_properties", "pulse", Kind::Boolean, 0.0, 37),
        change("/cv_inputs/cutoff_cv", "connected", Kind::Boolean, 1.0, 37),
        change("/cv_inputs/cutoff_cv", "value", Kind::Number, 0.40, 37),
    };
    const auto after = renderBatch(timed, firstEvents.data(), firstEvents.size());
    for (int frame = 0; frame < 37; ++frame)
        assert(before.left[frame] == after.left[frame]
               && before.right[frame] == after.right[frame]);
    const auto& state = Access::parameters(CYouKnowTestAccess::engine(timed));
    assert(state.volume == 0.0f && !state.pulseEnabled);
    assert(std::abs(state.cutoff - 0.70f) < 1e-6f);
    assert(get("/custom_properties", "cutoff") == 0.30);

    // A same-frame control/CV/note group is independent of the host's ordering
    // of its control notifications. Multiple moves cannot collapse to MOM's end.
    configureCVHost();
    CYouKnow one(sampleRate);
    std::array group {
        change("/custom_properties", "cutoff", Kind::Number, 0.45, 19),
        change("/cv_inputs/cutoff_cv", "connected", Kind::Boolean, 1.0, 19),
        change("/cv_inputs/cutoff_cv", "value", Kind::Number, -0.20, 19),
        noteDiff(60, 127, 19),
    };
    const auto grouped = renderBatch(one, group.data(), group.size());
    configureCVHost();
    CYouKnow two(sampleRate);
    set("/custom_properties", "cutoff", Kind::Number, 0.45);
    set("/cv_inputs/cutoff_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/cutoff_cv", "value", Kind::Number, -0.20);
    std::reverse(group.begin(), group.end());
    const auto reversed = renderBatch(two, group.data(), group.size());
    assert(grouped.left == reversed.left && grouped.right == reversed.right);
    assert(Access::parameters(CYouKnowTestAccess::engine(one)).cutoff == 0.25f);

    // A short CV gate entirely inside one batch must reach the same note path
    // and exact frames as MIDI, even though final MOM Gate is already zero.
    configureCVHost();
    CYouKnow midi(sampleRate);
    const std::array notes { noteDiff(60, 127, 17), noteDiff(60, 0, 23) };
    const auto midiPulse = renderBatch(midi, notes.data(), notes.size());
    configureCVHost();
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    CYouKnow cv(sampleRate);
    const std::array gates {
        change("/cv_inputs/gate_cv", "value", Kind::Number, 1.0, 17),
        change("/cv_inputs/gate_cv", "value", Kind::Number, 0.0, 23),
    };
    const auto cvPulse = renderBatch(cv, gates.data(), gates.size());
    assert(cvPulse.left == midiPulse.left && cvPulse.right == midiPulse.right);
    assert(!CYouKnowTestAccess::cvActive(cv));
    assert(Access::heldCount(CYouKnowTestAccess::engine(cv), 60) == 0);
    for (int batch = 0; batch < 8; ++batch)
    {
        const auto a = renderBatch(midi);
        const auto b = renderBatch(cv);
        assert(a.left == b.left && a.right == b.right);
    }

    const auto midiOn = noteDiff(60, 127, 0);
    const auto cvOn = change("/cv_inputs/gate_cv", "value", Kind::Number, 1.0, 0);
    renderBatch(midi, &midiOn, 1);
    renderBatch(cv, &cvOn, 1);
    for (int batch = 0; batch < 16; ++batch)
    {
        renderBatch(midi);
        renderBatch(cv);
    }
    const std::array midiRetrigger { noteDiff(60, 0, 20), noteDiff(60, 127, 20) };
    const std::array cvRetrigger {
        change("/cv_inputs/gate_cv", "value", Kind::Number, 0.0, 20),
        change("/cv_inputs/gate_cv", "value", Kind::Number, 1.0, 20),
    };
    for (int batch = 0; batch < 8; ++batch)
    {
        const auto a = renderBatch(midi, batch == 0 ? midiRetrigger.data() : nullptr,
                                   batch == 0 ? midiRetrigger.size() : 0);
        const auto b = renderBatch(cv, batch == 0 ? cvRetrigger.data() : nullptr,
                                   batch == 0 ? cvRetrigger.size() : 0);
        assert(a.left == b.left && a.right == b.right);
    }

    // Timed press/release pairs must preserve the active-key-mode gesture,
    // including when the host places both edges at one sample.
    configureCVHost();
    CYouKnow pressed(sampleRate);
    CYouKnow untouched(sampleRate);
    renderBatch(pressed, &note, 1);
    renderBatch(untouched, &note, 1);
    for (int batch = 0; batch < 8; ++batch)
    {
        renderBatch(pressed);
        renderBatch(untouched);
    }
    const std::array presses {
        change("/custom_properties", "keyModeReassertPress", Kind::Boolean, 1.0, 27),
        change("/custom_properties", "keyModeReassertPress", Kind::Boolean, 0.0, 27),
    };
    const auto pressedBatch = renderBatch(pressed, presses.data(), presses.size());
    const auto untouchedBatch = renderBatch(untouched);
    for (int frame = 0; frame < 27; ++frame)
        assert(pressedBatch.left[frame] == untouchedBatch.left[frame]
               && pressedBatch.right[frame] == untouchedBatch.right[frame]);
    bool differs = pressedBatch.left != untouchedBatch.left
                || pressedBatch.right != untouchedBatch.right;
    for (int batch = 0; batch < 16; ++batch)
    {
        const auto a = renderBatch(pressed);
        const auto b = renderBatch(untouched);
        differs = differs || a.left != b.left || a.right != b.right;
    }
    assert(differs);
}

void checkCVRangesAndLifecycle()
{
    using Access = youknow::YouKnowTestAccess;
    struct Target {
        const char* path;
        const char* property;
        float youknow::EngineParameters::*field;
        bool multiply;
    };
    const Target targets[] {
        { "/cv_inputs/cutoff_cv", "cutoff", &youknow::EngineParameters::cutoff, false },
        { "/cv_inputs/resonance_cv", "resonance", &youknow::EngineParameters::resonance, false },
        { "/cv_inputs/volume_cv", "volume", &youknow::EngineParameters::volume, true },
        { "/cv_inputs/vca_level_cv", "vcaLevel", &youknow::EngineParameters::vcaLevel, true },
        { "/cv_inputs/sub_cv", "sub", &youknow::EngineParameters::subLevel, true },
        { "/cv_inputs/noise_cv", "noise", &youknow::EngineParameters::noiseLevel, true },
    };
    for (const auto& target : targets)
    {
        configureCVHost();
        set("/custom_properties", target.property, Kind::Number, 0.60);
        CYouKnow device(sampleRate);
        renderBatch(device);
        assert(Access::parameters(CYouKnowTestAccess::engine(device)).*target.field == 0.60f);
        const auto connected = change(target.path, "connected", Kind::Boolean, 1.0, 0);
        renderBatch(device, &connected, 1);
        for (double value : { -2.0, -0.25, 0.0, 0.50, 1.0, 2.0,
                              std::numeric_limits<double>::quiet_NaN(),
                              std::numeric_limits<double>::infinity() })
        {
            const auto diff = change(target.path, "value", Kind::Number, value, 11);
            renderBatch(device, &diff, 1);
            const double finite = std::isfinite(value) ? value : 0.0;
            const float expected = static_cast<float>(std::clamp(target.multiply
                ? 0.60 * std::clamp(finite, 0.0, 1.0) : 0.60 + finite, 0.0, 1.0));
            assert(Access::parameters(CYouKnowTestAccess::engine(device)).*target.field == expected);
            assert(get("/custom_properties", target.property) == 0.60);
        }
        const auto disconnected = change(target.path, "connected", Kind::Boolean, 0.0, 32);
        renderBatch(device, &disconnected, 1);
        assert(Access::parameters(CYouKnowTestAccess::engine(device)).*target.field == 0.60f);
    }

    // Disconnect releases only the CV hold when MIDI shares its note. Reset
    // forgets all old holds, then an already-high restored gate starts once.
    configureCVHost();
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 1.0);
    CYouKnow device(sampleRate);
    const auto note = noteDiff(60, 127, 0);
    renderBatch(device, &note, 1);
    auto& engine = CYouKnowTestAccess::engine(device);
    assert(Access::heldCount(engine, 60) == 2);
    const auto disconnected = change("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0, 12);
    renderBatch(device, &disconnected, 1);
    assert(Access::heldCount(engine, 60) == 1);
    const auto reconnected = change("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0, 7);
    renderBatch(device, &reconnected, 1);
    assert(Access::heldCount(engine, 60) == 2);
    resetCounter = 1.0;
    renderBatch(device);
    assert(Access::heldCount(engine, 60) == 1);
    const auto off = change("/cv_inputs/gate_cv", "value", Kind::Number, 0.0, 9);
    renderBatch(device, &off, 1);
    assert(Access::heldCount(engine, 60) == 0);

    // One representative simultaneous automation/CV program at every declared
    // host rate: muted notes must keep advancing and become audible on reopen.
    for (double rate : { 44100.0, 48000.0, 88200.0, 96000.0, 192000.0 })
    {
        configureCVHost();
        set("/cv_inputs/volume_cv", "connected", Kind::Boolean, 1.0);
        CYouKnow atRate(rate);
        renderBatch(atRate, &note, 1);
        assert(Access::heldCount(CYouKnowTestAccess::engine(atRate), 60) == 1);
        for (int batch = 0; batch < 8; ++batch)
            renderBatch(atRate);
        const std::array events {
            change("/custom_properties", "volume", Kind::Number, 0.90, 31),
            change("/cv_inputs/volume_cv", "value", Kind::Number, 1.0, 31),
            change("/cv_inputs/cutoff_cv", "connected", Kind::Boolean, 1.0, 31),
            change("/cv_inputs/cutoff_cv", "value", Kind::Number, 0.15, 31),
        };
        bool audible = false;
        for (int batch = 0; batch < 24; ++batch)
        {
            const auto audio = renderBatch(atRate, batch == 0 ? events.data() : nullptr,
                                          batch == 0 ? events.size() : 0);
            for (std::size_t frame = 0; frame < audio.left.size(); ++frame)
            {
                assert(std::isfinite(audio.left[frame]) && std::isfinite(audio.right[frame]));
                audible = audible || std::abs(audio.left[frame]) > 1e-5f
                                  || std::abs(audio.right[frame]) > 1e-5f;
            }
        }
        assert(audible);
        assert(get("/custom_properties", "volume") == 0.90);
    }
}

} // namespace

TJBox_ObjectRef JBox_GetMotherboardObjectRef(const char* path)
{
    return objectFor(path);
}

TJBox_PropertyRef JBox_MakePropertyRef(TJBox_ObjectRef object, const char* key)
{
    return propertyFor(object, key);
}

TJBox_Value JBox_LoadMOMProperty(TJBox_PropertyRef property)
{
    ++momPropertyLoads;
    assert(property > 0 && property < properties.size());
    return properties[property].value;
}

void JBox_StoreMOMProperty(TJBox_PropertyRef property, TJBox_Value value)
{
    assert(property > 0 && property < properties.size());
    // Modulation may report its note lamp, never rewrite an authored control.
    assert(properties[property].key == "noteOn");
    properties[property].value = value;
}

TJBox_Float64 JBox_GetNumber(TJBox_Value value)
{
    const auto decoded = decode(value);
    assert(decoded.kind == Kind::Number);
    return decoded.value;
}

TJBox_Bool JBox_GetBoolean(TJBox_Value value)
{
    const auto decoded = decode(value);
    assert(decoded.kind == Kind::Boolean);
    return decoded.value != 0.0;
}

TJBox_Value JBox_MakeBoolean(TJBox_Bool value)
{
    return encode(Kind::Boolean, value != 0);
}

TJBox_Float64 JBox_LoadMOMPropertyAsNumber(TJBox_ObjectRef object, TJBox_Tag tag)
{
    ++momNumberLoads;
    const auto& path = objects[object].path;
    if (path == "/environment" && tag == kJBox_EnvironmentSystemSampleRate)
        return sampleRate;
    if (path == "/environment" && tag == kJBox_EnvironmentMasterTune)
        return masterTune;
    if (path == "/transport" && tag == kJBox_TransportRequestResetAudio)
        return resetCounter;
    assert(false);
    return 0.0;
}

TJBox_Value JBox_LoadMOMPropertyByTag(TJBox_ObjectRef object, TJBox_Tag tag)
{
    assert(tag == kJBox_AudioOutputBuffer);
    return encode(Kind::Buffer, object);
}

void JBox_SetDSPBufferData(TJBox_Value value, TJBox_AudioFramePos first,
                          TJBox_AudioFramePos last,
                          const TJBox_AudioSample audio[])
{
    assert(first == 0 && last == 64);
    const auto object = static_cast<TJBox_ObjectRef>(decode(value).value);
    auto* destination = objects[object].path == "/audio_outputs/left"
        ? capturedLeft.data() : capturedRight.data();
    std::copy(audio, audio + 64, destination);
    if (objects[object].path == "/audio_outputs/left") wroteLeft = true;
    else wroteRight = true;
}

int main()
{
    static_assert(sizeof(CYouKnow) < 64 * 1024);
    set("/cv_inputs/note_cv", "value", Kind::Number, 60.0 / 127.0);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.0);
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0);

    CYouKnow silent(sampleRate);
    const std::set<std::string> expectedPaths {
        "/audio_outputs/left", "/audio_outputs/right", "/environment",
        "/transport", "/note_states", "/cv_inputs/note_cv",
        "/cv_inputs/gate_cv", "/custom_properties",
        "/cv_inputs/cutoff_cv", "/cv_inputs/resonance_cv",
        "/cv_inputs/volume_cv", "/cv_inputs/vca_level_cv",
        "/cv_inputs/sub_cv", "/cv_inputs/noise_cv",
    };
    std::set<std::string> actualPaths;
    for (std::size_t index = 1; index < objects.size(); ++index)
        actualPaths.insert(objects[index].path);
    assert(actualPaths == expectedPaths);

    const std::set<std::string> expectedProperties {
        "volume", "presetGain", "benderDco", "benderVcf", "benderLfo", "portamento",
        "keyMode", "lfoRate", "lfoDelay", "dcoLfo", "pwm", "pwmMode",
        "range", "saw", "pulse", "sub", "noise", "highPass", "cutoff",
        "resonance", "envPolarity", "vcfEnv", "vcfLfo", "keyFollow",
        "vcaMode", "vcaLevel", "attack", "decay", "sustain", "release",
        "chorus", "transpose", "masterTune", "velocity", "calibration",
        "aging", "chorusNoise", "polyphony", "quality", "vcfTanhMode",
        "vcfFastEarlyMode", "vcfSolverMode", "pitchBend", "modWheel",
        "sustainPedal", "noteOn", "keyModeReassertPress",
    };
    std::set<std::string> actualProperties;
    const auto customProperties = objectFor("/custom_properties");
    for (std::size_t index = 1; index < properties.size(); ++index)
        if (properties[index].object == customProperties)
            actualProperties.insert(properties[index].key);
    assert(actualProperties == expectedProperties);

    clearCapture();
    silent.RenderBatch(nullptr, 0);
    assert(!wroteLeft && !wroteRight);
    assert(youknow::YouKnowTestAccess::solverMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfSolverMode::Rk4Single);
    assert(youknow::YouKnowTestAccess::tanhMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfTanhMode::PolyZoned);
    assert(youknow::YouKnowTestAccess::fastEarlyMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfFastEarlyMode::Cubic);
    assert(youknow::YouKnowTestAccess::aging(
               CYouKnowTestAccess::engine(silent)) == 0.50f);

    // A stored song value replaces the fresh-device default before the first
    // render, including the former 0% default.
    for (const double savedAging : { 0.0, 0.75 })
    {
        set("/custom_properties", "aging", Kind::Number, savedAging);
        CYouKnow restored(sampleRate);
        restored.RenderBatch(nullptr, 0);
        assert(youknow::YouKnowTestAccess::aging(
                   CYouKnowTestAccess::engine(restored)) == savedAging);
    }

    set("/custom_properties", "aging", Kind::Number, 0.75);
    const auto agingDiff = customDiff("aging");
    silent.RenderBatch(&agingDiff, 1);
    assert(youknow::YouKnowTestAccess::aging(
               CYouKnowTestAccess::engine(silent)) == 0.75f);
    set("/custom_properties", "aging", Kind::Number, 0.50);
    const auto defaultAgingDiff = customDiff("aging");
    silent.RenderBatch(&defaultAgingDiff, 1);

    const auto stablePropertyLoads = momPropertyLoads;
    const auto stableNumberLoads = momNumberLoads;
    silent.RenderBatch(nullptr, 0);
    // Plain-number caches cover controls and all CVs. Stable playback polls
    // only the host-owned master tune and audio-reset counter.
    assert(momPropertyLoads - stablePropertyLoads == 0);
    assert(momNumberLoads - stableNumberLoads == 2);

    set("/custom_properties", "vcfTanhMode", Kind::Number, 1.0);
    set("/custom_properties", "vcfFastEarlyMode", Kind::Number, 1.0);
    set("/custom_properties", "vcfSolverMode", Kind::Number, 0.0);
    const std::array modeDiffs {
        customDiff("vcfTanhMode"), customDiff("vcfFastEarlyMode"),
        customDiff("vcfSolverMode"),
    };
    silent.RenderBatch(modeDiffs.data(),
                       static_cast<TJBox_UInt32>(modeDiffs.size()));
    assert(youknow::YouKnowTestAccess::tanhMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfTanhMode::ZonedHermite);
    assert(youknow::YouKnowTestAccess::fastEarlyMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfFastEarlyMode::Cubic);
    assert(youknow::YouKnowTestAccess::solverMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfSolverMode::MersonHalfSteps);
    set("/custom_properties", "vcfTanhMode", Kind::Number, 2.0);
    set("/custom_properties", "vcfFastEarlyMode", Kind::Number, 0.0);
    set("/custom_properties", "vcfSolverMode", Kind::Number, 2.0);
    const std::array polyDiffs {
        customDiff("vcfTanhMode"), customDiff("vcfFastEarlyMode"),
        customDiff("vcfSolverMode"),
    };
    silent.RenderBatch(polyDiffs.data(),
                       static_cast<TJBox_UInt32>(polyDiffs.size()));
    assert(youknow::YouKnowTestAccess::tanhMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfTanhMode::PolyZoned);
    assert(youknow::YouKnowTestAccess::fastEarlyMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfFastEarlyMode::Hermite);
    set("/custom_properties", "vcfFastEarlyMode", Kind::Number, 1.0);
    const auto cubicDiff = customDiff("vcfFastEarlyMode");
    silent.RenderBatch(&cubicDiff, 1);
    assert(youknow::YouKnowTestAccess::fastEarlyMode(
               CYouKnowTestAccess::engine(silent))
           == youknow::VcfFastEarlyMode::Cubic);

    masterTune = 12.5;
    silent.RenderBatch(nullptr, 0);
    assert(youknow::YouKnowTestAccess::masterTuneCents(
               CYouKnowTestAccess::engine(silent)) == 12.5f);
    masterTune = 0.0;
    silent.RenderBatch(nullptr, 0);

    set("/custom_properties", "pitchBend", Kind::Number, 0.75);
    const auto pitchBendDiff = customDiff("pitchBend");
    silent.RenderBatch(&pitchBendDiff, 1);
    assert(youknow::YouKnowTestAccess::pitchBendTarget(
               CYouKnowTestAccess::engine(silent)) == 0.5f);
    resetCounter = 1.0;
    silent.RenderBatch(nullptr, 0);
    // reset() clears controller targets, so a reset-only batch must force the
    // cached custom-property snapshot to be applied again.
    assert(youknow::YouKnowTestAccess::pitchBendTarget(
               CYouKnowTestAccess::engine(silent)) == 0.5f);
    resetCounter = 0.0;
    set("/custom_properties", "pitchBend", Kind::Number, 0.50);

    // The RTC must construct without reading document-owned Quality. The first
    // render therefore replaces its 1x placeholder before accepting either a
    // frame-zero MIDI event or a Gate CV that was already high on restore.
    for (const auto& quality : std::array<std::pair<double, int>, 2> {{
             { 1.0, 2 }, { 2.0, 4 }
         }})
    {
        set("/custom_properties", "quality", Kind::Number, quality.first);
        set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0);
        set("/cv_inputs/gate_cv", "value", Kind::Number, 0.0);
        CYouKnow midiQuality(sampleRate);
        assert(CYouKnowTestAccess::oversamplingFactor(midiQuality) == 1);
        auto firstNote = noteDiff(60, 127, 0);
        clearCapture();
        midiQuality.RenderBatch(&firstNote, 1);
        assert(CYouKnowTestAccess::oversamplingFactor(midiQuality)
               == quality.second);
        assert(youknow::YouKnowTestAccess::heldCount(
                   CYouKnowTestAccess::engine(midiQuality), 60) == 1);

        set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
        set("/cv_inputs/gate_cv", "value", Kind::Number, 1.0);
        CYouKnow cvQuality(sampleRate);
        assert(CYouKnowTestAccess::oversamplingFactor(cvQuality) == 1);
        clearCapture();
        cvQuality.RenderBatch(nullptr, 0);
        assert(CYouKnowTestAccess::oversamplingFactor(cvQuality)
               == quality.second);
        assert(CYouKnowTestAccess::cvActive(cvQuality));
        assert(youknow::YouKnowTestAccess::heldCount(
                   CYouKnowTestAccess::engine(cvQuality), 60) == 1);
    }
    set("/custom_properties", "quality", Kind::Number, 0.0);
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.0);

    // Upward makeup changes glide monotonically. Downward changes must clamp
    // before rendering so a quiet preset's hot trim cannot overdrive the next,
    // intrinsically louder patch. Audio reset discards an upward transition's
    // history and snaps to the restored target, matching a fresh device state.
    set("/custom_properties", "presetGain", Kind::Number, 0.50);
    CYouKnow gainSmoothing(sampleRate);
    gainSmoothing.RenderBatch(nullptr, 0);
    set("/custom_properties", "presetGain", Kind::Number, 0.75);
    const auto raisedGain = customDiff("presetGain");
    gainSmoothing.RenderBatch(&raisedGain, 1);
    const float raisedTarget =
        CYouKnowTestAccess::patchGainTarget(gainSmoothing);
    float previousGain =
        CYouKnowTestAccess::patchGainSmoothed(gainSmoothing);
    assert(std::isfinite(previousGain));
    assert(previousGain > 1.0f && previousGain < raisedTarget);
    for (int batch = 0; batch < 30; ++batch)
    {
        gainSmoothing.RenderBatch(nullptr, 0);
        const float currentGain =
            CYouKnowTestAccess::patchGainSmoothed(gainSmoothing);
        assert(std::isfinite(currentGain));
        assert(currentGain >= previousGain && currentGain <= raisedTarget);
        previousGain = currentGain;
    }
    assert(std::abs(previousGain - raisedTarget) < 0.001f);

    set("/custom_properties", "presetGain", Kind::Number, 0.25);
    const auto loweredGain = customDiff("presetGain");
    gainSmoothing.RenderBatch(&loweredGain, 1);
    assert(CYouKnowTestAccess::patchGainSmoothed(gainSmoothing)
           == CYouKnowTestAccess::patchGainTarget(gainSmoothing));

    set("/custom_properties", "presetGain", Kind::Number, 0.75);
    gainSmoothing.RenderBatch(&raisedGain, 1);
    assert(CYouKnowTestAccess::patchGainSmoothed(gainSmoothing)
           < CYouKnowTestAccess::patchGainTarget(gainSmoothing));
    resetCounter = 1.0;
    gainSmoothing.RenderBatch(nullptr, 0);
    assert(CYouKnowTestAccess::patchGainSmoothed(gainSmoothing)
           == CYouKnowTestAccess::patchGainTarget(gainSmoothing));
    resetCounter = 0.0;
    set("/custom_properties", "presetGain", Kind::Number, 0.50);

    // Exercise the current bank's full downward span without an audio reset:
    // +18.0618 dB (8x) into Sub Current's -13.075 dB trim. A frame-zero note
    // must see only the new calibrated multiplier, never the previous 8x gain.
    set("/custom_properties", "presetGain", Kind::Number, 1.0);
    CYouKnow extremeGainDrop(sampleRate);
    extremeGainDrop.RenderBatch(nullptr, 0);
    assert(CYouKnowTestAccess::patchGainSmoothed(extremeGainDrop) == 8.0f);

    constexpr double subCurrentPresetGain = 0.138048128;
    set("/custom_properties", "presetGain", Kind::Number,
        subCurrentPresetGain);
    const std::array extremeDropDiffs {
        customDiff("presetGain"), noteDiff(60, 127, 0),
    };
    double extremeDropPeak = 0.0;
    bool extremeDropAudible = false;
    for (int batch = 0; batch < 64; ++batch)
    {
        const auto rendered = renderBatch(
            extremeGainDrop,
            batch == 0 ? extremeDropDiffs.data() : nullptr,
            batch == 0 ? static_cast<TJBox_UInt32>(extremeDropDiffs.size()) : 0);
        assert(CYouKnowTestAccess::patchGainSmoothed(extremeGainDrop)
               <= CYouKnowTestAccess::patchGainTarget(extremeGainDrop));
        for (std::size_t sample = 0; sample < rendered.left.size(); ++sample)
        {
            const float left = rendered.left[sample];
            const float right = rendered.right[sample];
            assert(std::isfinite(left) && std::isfinite(right));
            extremeDropPeak = std::max(
                extremeDropPeak,
                static_cast<double>(std::max(std::abs(left), std::abs(right))));
            extremeDropAudible = extremeDropAudible
                              || left != 0.0f || right != 0.0f;
        }
    }
    const float subCurrentGain = static_cast<float>(std::exp2(
        (subCurrentPresetGain - 0.5) * 6.0));
    assert(CYouKnowTestAccess::patchGainTarget(extremeGainDrop)
           == subCurrentGain);
    assert(extremeDropAudible && extremeDropPeak <= 0.185);
    set("/custom_properties", "presetGain", Kind::Number, 0.50);

    // A preset can change Key Mode while the instrument is fully idle. Prime
    // ordinary audio time through an idle Quality transition, then reproduce
    // that patch snapshot followed by a Note On. The engine may defer the
    // assigner rebuild to its physical converter scan, but the Rack wrapper
    // must keep servicing it even while no voice is active yet.
    set("/custom_properties", "keyMode", Kind::Number, 0.0);
    CYouKnow presetSwitch(sampleRate);
    presetSwitch.RenderBatch(nullptr, 0);
    set("/custom_properties", "quality", Kind::Number, 1.0);
    const auto primeQuality = customDiff("quality");
    for (int batch = 0; batch < 12; ++batch)
        presetSwitch.RenderBatch(batch == 0 ? &primeQuality : nullptr,
                                 batch == 0 ? 1 : 0);
    assert(CYouKnowTestAccess::oversamplingFactor(presetSwitch) == 2);

    set("/custom_properties", "keyMode", Kind::Number, 2.0);
    const auto presetKeyMode = customDiff("keyMode");
    presetSwitch.RenderBatch(&presetKeyMode, 1);
    const auto postPresetNote = noteDiff(60, 127, 0);
    bool postPresetWrote = false;
    for (int batch = 0; batch < 8; ++batch)
    {
        clearCapture();
        presetSwitch.RenderBatch(batch == 0 ? &postPresetNote : nullptr,
                                 batch == 0 ? 1 : 0);
        postPresetWrote = postPresetWrote || wroteLeft || wroteRight;
    }
    const auto& presetEngine = CYouKnowTestAccess::engine(presetSwitch);
    assert(youknow::YouKnowTestAccess::heldCount(presetEngine, 60) == 1);
    assert(youknow::YouKnowTestAccess::keyedSlotFor(presetEngine, 60)
           >= 0);
    assert(postPresetWrote);
    set("/custom_properties", "keyMode", Kind::Number, 0.0);
    set("/custom_properties", "quality", Kind::Number, 0.0);

    CYouKnow immediate(sampleRate);
    auto atZero = noteDiff(60, 127, 0);
    const auto reference = renderNote(immediate, atZero);
    assert(reference.wrote);

    CYouKnow delayed(sampleRate);
    auto atSeventeen = noteDiff(60, 127, 17);
    const auto shifted = renderNote(delayed, atSeventeen);
    assert(shifted.wrote);
    for (int frame = 0; frame < 17; ++frame)
        assert(shifted.left[frame] == 0.0f && shifted.right[frame] == 0.0f);
    // Compare after both host batches have crossed the silence threshold;
    // before then, whole-buffer silence elision intentionally quantises the
    // otherwise identical streams at different batch boundaries.
    for (int frame = 81; frame < 256; ++frame)
    {
        assert(std::abs(shifted.left[frame] - reference.left[frame - 17])
               < 1.0e-6f);
        assert(std::abs(shifted.right[frame] - reference.right[frame - 17])
               < 1.0e-6f);
    }

    CYouKnow legacyFrame(sampleRate);
    auto aboveBatch = noteDiff(60, 127, 96);
    clearCapture();
    legacyFrame.RenderBatch(&aboveBatch, 1);
    // Reason 6.5's out-of-range frame is clamped to the final sample. The
    // modeled analogue output floor may now make that one rendered sample
    // audible even though the 41-sample note path is still latent; the wrapper
    // contract is that no earlier frame is touched and both outputs stay
    // finite.
    assert(wroteLeft && wroteRight);
    for (int frame = 0; frame < 63; ++frame)
        assert(capturedLeft[frame] == 0.0f && capturedRight[frame] == 0.0f);
    assert(std::isfinite(capturedLeft[63])
           && std::isfinite(capturedRight[63]));
    assert(get("/custom_properties", "noteOn") == 1.0);

    resetCounter = 1.0;
    clearCapture();
    immediate.RenderBatch(nullptr, 0);
    assert(!wroteLeft && !wroteRight);
    assert(get("/custom_properties", "noteOn") == 0.0);
    resetCounter = 0.0;

    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 1.0);
    set("/custom_properties", "decay", Kind::Number, 0.0);
    set("/custom_properties", "sustain", Kind::Number, 0.25);
    set("/custom_properties", "portamento", Kind::Number, 0.60);
    CYouKnow cv(sampleRate);
    bool cvWrote = false;
    auto& cvEngine = CYouKnowTestAccess::engine(cv);
    using EngineAccess = youknow::YouKnowTestAccess;
    int cvSlot = -1;
    for (int batch = 0; batch < 128; ++batch)
    {
        clearCapture();
        cv.RenderBatch(nullptr, 0);
        cvWrote = cvWrote || wroteLeft || wroteRight;
        cvSlot = EngineAccess::keyedSlotFor(cvEngine, 60);
        if (cvSlot >= 0 && EngineAccess::envelopeStage(cvEngine, cvSlot) == 3)
            break;
    }
    assert(cvWrote && cvSlot >= 0);
    assert(EngineAccess::envelopeStage(cvEngine, cvSlot) == 3);

    const int cvStage = EngineAccess::envelopeStage(cvEngine, cvSlot);
    const auto cvLevel = EngineAccess::envelopeLevel(cvEngine, cvSlot);
    const float cvMidi = EngineAccess::currentMidi(cvEngine, cvSlot);
    const bool cvResetPending = EngineAccess::dcoResetPending(cvEngine, cvSlot);
    set("/cv_inputs/note_cv", "value", Kind::Number, 67.0 / 127.0);
    // Isolate the adapter event from audio time: a gate-high Note CV move must
    // change only the held pitch, not run note-off/note-on on the envelope.
    CYouKnowTestAccess::handleCV(cv);
    assert(CYouKnowTestAccess::cvActive(cv));
    assert(CYouKnowTestAccess::lastCVNote(cv) == 67);
    assert(EngineAccess::heldCount(cvEngine, 60) == 0);
    assert(EngineAccess::heldCount(cvEngine, 67) == 1);
    assert(EngineAccess::keyedSlotFor(cvEngine, 67) == cvSlot);
    assert(EngineAccess::envelopeStage(cvEngine, cvSlot) == cvStage);
    assert(EngineAccess::envelopeLevel(cvEngine, cvSlot) == cvLevel);
    assert(EngineAccess::currentMidi(cvEngine, cvSlot) == cvMidi);
    assert(EngineAccess::dcoResetPending(cvEngine, cvSlot) == cvResetPending);

    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.0);
    CYouKnowTestAccess::handleCV(cv);
    assert(!CYouKnowTestAccess::cvActive(cv));
    assert(EngineAccess::heldCount(cvEngine, 67) == 0);
    const auto baseline = renderProgram(nullptr);
    assert(std::any_of(baseline.begin(), baseline.end(),
                       [](float sample) { return sample != 0.0f; }));
    assert(std::none_of(baseline.begin(), baseline.end(),
                        [](float sample) { return !std::isfinite(sample); }));
    const Setting presetLevel {
        "presetGain", Kind::Number, 0.50, 0.75
    };
    const auto levelled = renderProgram(&presetLevel);
    assert(levelled.size() == baseline.size() && levelled != baseline);
    for (const auto& setting : kPanel)
    {
        const auto moved = renderProgram(&setting);
        assert(moved.size() == baseline.size());
        assert(std::none_of(moved.begin(), moved.end(),
                            [](float sample) { return !std::isfinite(sample); }));
        // Fails loudly with the property name if a control stops reaching the
        // engine -- the failure mode a silent panel wiring mistake produces.
        if (moved == baseline)
        {
            std::fprintf(stderr, "%s does not reach the engine\n", setting.name);
            return 1;
        }
        if (std::strcmp(setting.name, "quality") != 0)
        {
            const auto automated = renderProgram(&setting, true);
            if (automated == baseline)
            {
                std::fprintf(stderr, "%s timed automation does not reach the engine\n", setting.name);
                return 1;
            }
            assert(std::all_of(automated.begin(), automated.end(),
                [](float value) { return std::isfinite(value); }));
        }
    }

    // A selected Key Mode press is a non-persistent momentary property. It
    // must reassert on the low->high edge, then remain a no-op while
    // the mouse stays down. Two engines receiving the same single rising edge
    // therefore remain sample-identical even when one shadow stays high.
    for (const auto& setting : kPanel)
        set("/custom_properties", setting.name, setting.kind, setting.value);
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0);
    set("/custom_properties", "keyModeReassertPress", Kind::Boolean, 0.0);
    CYouKnow heldHigh(sampleRate);
    CYouKnow released(sampleRate);
    CYouKnow untouched(sampleRate);
    const auto heldNote = noteDiff(60, 100, 0);
    renderBatch(heldHigh, &heldNote, 1);
    renderBatch(released, &heldNote, 1);
    renderBatch(untouched, &heldNote, 1);
    for (int batch = 0; batch < 8; ++batch)
    {
        set("/custom_properties", "keyModeReassertPress", Kind::Boolean, 0.0);
        renderBatch(heldHigh);
        renderBatch(released);
        renderBatch(untouched);
    }

    bool reassertChangedAudio = false;
    for (int batch = 0; batch < 48; ++batch)
    {
        set("/custom_properties", "keyModeReassertPress", Kind::Boolean, 1.0);
        const auto highDiff = customDiff("keyModeReassertPress");
        const auto high = renderBatch(heldHigh, &highDiff, 1);
        set("/custom_properties", "keyModeReassertPress", Kind::Boolean,
            batch == 0 ? 1.0 : 0.0);
        const auto releasedDiff = customDiff("keyModeReassertPress");
        const auto oneShot = renderBatch(released, &releasedDiff, 1);
        set("/custom_properties", "keyModeReassertPress", Kind::Boolean, 0.0);
        const auto untouchedDiff = customDiff("keyModeReassertPress");
        const auto none = renderBatch(untouched, &untouchedDiff, 1);
        assert(high.left == oneShot.left && high.right == oneShot.right);
        reassertChangedAudio = reassertChangedAudio
            || high.left != none.left || high.right != none.right;
    }
    assert(reassertChangedAudio);

    // Reason's global tune and the panel trim must both reach oscillator
    // pitch beyond the hardware-only +/-50-cent interval.
    for (const double direction : { -1.0, 1.0 })
    {
        masterTune = direction * 50.0;
        const auto atFifty = renderProgram(nullptr);
        masterTune = direction * 100.0;
        const auto atHundred = renderProgram(nullptr);
        const Setting panelTrim {
            "masterTune", Kind::Number, 0.50, direction > 0.0 ? 1.0 : 0.0
        };
        const auto combined = renderProgram(&panelTrim);
        assert(atFifty != atHundred && atHundred != combined);
        assert(std::all_of(combined.begin(), combined.end(),
                           [](float sample) { return std::isfinite(sample); }));
    }
    masterTune = 0.0;

    checkTimedAutomationAndCV();
    checkCVRangesAndLifecycle();
    std::puts("Wrapper: frame-accurate automation, six modulation CVs, gates/reset/restore, and five host rates PASS");
    return 0;
}
