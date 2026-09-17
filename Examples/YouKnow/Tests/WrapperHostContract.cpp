#include "../YouKnow.h"
#include "../DSP/YouKnowProductFidelity.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <limits>
#include <new>
#include <random>
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

    static float velocity(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].velocity;
    }

    static bool anyLatchedVoice(const YouKnowEngine& engine) noexcept
    {
        return std::any_of(engine.voices_.begin(), engine.voices_.end(),
                           [](const auto& voice) { return voice.keyDown || voice.sustained; });
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

    static float modWheelTarget(const YouKnowEngine& engine) noexcept
    {
        return engine.modWheelTarget_;
    }

    static bool sustainPedalDown(const YouKnowEngine& engine) noexcept
    {
        return engine.sustainPedalDown_;
    }

    static const EngineParameters& parameters(const YouKnowEngine& engine) noexcept
    {
        return engine.activeParameters_;
    }

    // The pitch a voice slot is keyed to, or -1.
    static int keyedNote(const YouKnowEngine& engine, int slot) noexcept
    {
        const auto& voice = engine.voices_[static_cast<std::size_t>(slot)];
        return voice.active && voice.keyDown ? voice.rootMidi : -1;
    }

    static std::uint64_t generation(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].generation;
    }

    static int keyedVoiceCount(const YouKnowEngine& engine, int note) noexcept
    {
        return static_cast<int>(std::count_if(
            engine.voices_.begin(), engine.voices_.end(), [note](const auto& voice) {
                return voice.active && voice.keyDown && voice.rootMidi == note;
            }));
    }

    // A voice keyed to a pitch nobody holds is a stuck note.
    static bool keyedWithoutHeldKey(const YouKnowEngine& engine) noexcept
    {
        return std::any_of(
            engine.voices_.begin(), engine.voices_.end(), [&engine](const auto& voice) {
                return voice.active && voice.keyDown
                    && (voice.rootMidi < 0 || voice.rootMidi > 127
                        || engine.heldNoteCounts_[static_cast<std::size_t>(
                               voice.rootMidi)] == 0);
            });
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

    static std::uint16_t midiHeldCount(const CYouKnow& device, int note) noexcept
    {
        return device.fMidiHeldCounts[static_cast<std::size_t>(note)];
    }

    static const youknow::EngineParameters& engineParameters(
        const CYouKnow& device) noexcept
    {
        return device.fEngineParameters;
    }

    static int requestedOversamplingFactor(const CYouKnow& device) noexcept
    {
        return device.fRequestedOversamplingFactor;
    }

    static float calibrationTarget(const CYouKnow& device) noexcept
    {
        return device.fCalibrationTarget;
    }

    // The wrapper's declared default for a custom property, by name.
    static double parameterDefault(const CYouKnow& device, const char* name)
    {
        const auto property = JBox_MakePropertyRef(device.fCustomProperties, name);
        for (std::size_t index = 0; index < device.fProperties.size(); ++index)
            if (device.fProperties[index] == property)
                return CYouKnow::kParameterDefaults[index];
        assert(false);
        return 0.0;
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

void configureAttackHost(double sustain = 0.72, int voices = 6)
{
    configureCVHost();
    set("/custom_properties", "attack", Kind::Number,
        youknow::YouKnowEngine::panelPositionForAttack(0.240f));
    set("/custom_properties", "decay", Kind::Number, 0.0);
    set("/custom_properties", "sustain", Kind::Number, sustain);
    set("/custom_properties", "release", Kind::Number, 0.0);
    set("/custom_properties", "keyMode", Kind::Number, 0.0);
    set("/custom_properties", "polyphony", Kind::Number, voices - 1);
    set("/custom_properties", "vcaMode", Kind::Number, 0.0);
    set("/custom_properties", "cutoff", Kind::Number, 1.0);
    for (const char* name : { "vcfEnv", "vcfLfo", "dcoLfo", "portamento",
                               "calibration", "aging", "chorus", "noise",
                               "sub", "transpose" })
        set("/custom_properties", name, Kind::Number, 0.0);
    set("/custom_properties", "pulse", Kind::Boolean, 0.0);
}

void assertSameAudio(const Batch& first, const Batch& second)
{
    assert(first.left == second.left && first.right == second.right);
}

void checkSimultaneousMidiRetrigger()
{
    using Access = youknow::YouKnowTestAccess;
    const double savedRate = sampleRate;
    for (double rate : { 44100.0, 48000.0 })
        for (int frame : { 0, 17, 63 })
            for (double sustain : { 0.0, 0.72 })
            {
                sampleRate = rate;
                configureAttackHost(sustain);
                CYouKnow offFirst(rate), onFirst(rate), untouched(rate);
                const auto initial = noteDiff(57, 127, 0); // Reason A2 report
                renderBatch(offFirst, &initial, 1);
                renderBatch(onFirst, &initial, 1);
                renderBatch(untouched, &initial, 1);
                // Reach Sustain, including the zero-level, still-held case.
                for (int batch = 0; batch < static_cast<int>(rate / 64); ++batch)
                {
                    renderBatch(offFirst);
                    renderBatch(onFirst);
                    renderBatch(untouched);
                }
                auto& firstEngine = CYouKnowTestAccess::engine(offFirst);
                auto& secondEngine = CYouKnowTestAccess::engine(onFirst);
                const int previousSlot = Access::keyedSlotFor(firstEngine, 57);
                assert(previousSlot >= 0);
                assert(Access::envelopeStage(firstEngine, previousSlot) == 3);
                const auto previousLevel = Access::envelopeLevel(firstEngine, previousSlot);
                std::array boundary { noteDiff(57, 0, frame), noteDiff(57, 37, frame) };
                const auto expected = renderBatch(offFirst, boundary.data(), boundary.size());
                std::reverse(boundary.begin(), boundary.end());
                const auto actual = renderBatch(onFirst, boundary.data(), boundary.size());
                const auto unchanged = renderBatch(untouched);
                assertSameAudio(expected, actual);
                for (int sample = 0; sample < frame; ++sample)
                {
                    assert(actual.left[sample] == unchanged.left[sample]);
                    assert(actual.right[sample] == unchanged.right[sample]);
                }
                const int firstSlot = Access::keyedSlotFor(firstEngine, 57);
                const int secondSlot = Access::keyedSlotFor(secondEngine, 57);
                assert(firstSlot == previousSlot && secondSlot == firstSlot);
                assert(Access::heldCount(firstEngine, 57) == 1);
                assert(Access::heldCount(secondEngine, 57) == 1);
                assert(Access::envelopeStage(firstEngine, firstSlot) == 1);
                assert(Access::envelopeStage(secondEngine, secondSlot) == 1);
                assert(Access::velocity(firstEngine, firstSlot) == 37.0f / 127.0f);
                assert(Access::velocity(secondEngine, secondSlot) == 37.0f / 127.0f);
                // Hardware resumes the same voice's accumulator: the Rack
                // boundary must retrigger without imposing a hard-zero reset.
                assert(Access::envelopeLevel(firstEngine, firstSlot) >= previousLevel);
                assert(Access::envelopeLevel(firstEngine, firstSlot)
                       == Access::envelopeLevel(secondEngine, secondSlot));
                float peak = 0.0f;
                for (int batch = 0; batch < static_cast<int>(rate * 0.05 / 64); ++batch)
                {
                    const auto a = renderBatch(offFirst);
                    const auto b = renderBatch(onFirst);
                    assertSameAudio(a, b);
                    for (float sample : b.left)
                        peak = std::max(peak, std::abs(sample));
                }
                assert(peak > 1e-5f);
                const auto release = noteDiff(57, 0, frame);
                assertSameAudio(renderBatch(offFirst, &release, 1),
                                renderBatch(onFirst, &release, 1));
                assert(Access::heldCount(firstEngine, 57) == 0);
                assert(Access::heldCount(secondEngine, 57) == 0);
            }
    sampleRate = savedRate;
}

void checkSimultaneousFullPoolReplacement()
{
    using Access = youknow::YouKnowTestAccess;
    const double savedRate = sampleRate;
    for (double rate : { 44100.0, 48000.0 })
        for (int frame : { 0, 17, 63 })
            for (double mode : { 0.0, 1.0 })
            {
                sampleRate = rate;
                configureAttackHost();
                set("/custom_properties", "keyMode", Kind::Number, mode);
                CYouKnow offFirst(rate), onFirst(rate);
                for (int batch = 0; batch < 8; ++batch)
                {
                    renderBatch(offFirst);
                    renderBatch(onFirst);
                }
                std::array<TJBox_PropertyDiff, 6> initial {};
                std::array<TJBox_PropertyDiff, 12> boundary {};
                for (int index = 0; index < 6; ++index)
                {
                    initial[index] = noteDiff(60 + index, 127, 0);
                    boundary[index] = noteDiff(60 + index, 0, frame);
                    boundary[index + 6] = noteDiff(45 + index, 83, frame);
                }
                renderBatch(offFirst, initial.data(), initial.size());
                renderBatch(onFirst, initial.data(), initial.size());
                const auto expected = renderBatch(offFirst, boundary.data(), boundary.size());
                // Preserve each chord's pitch order; move all replacement ons
                // ahead of the old offs, as an unspecified host tie-break may.
                std::rotate(boundary.begin(), boundary.begin() + 6, boundary.end());
                const auto actual = renderBatch(onFirst, boundary.data(), boundary.size());
                assertSameAudio(expected, actual);
                auto& firstEngine = CYouKnowTestAccess::engine(offFirst);
                auto& secondEngine = CYouKnowTestAccess::engine(onFirst);
                for (int index = 0; index < 6; ++index)
                {
                    assert(Access::heldCount(secondEngine, 60 + index) == 0);
                    assert(Access::keyedSlotFor(secondEngine, 60 + index) < 0);
                    assert(Access::heldCount(secondEngine, 45 + index) == 1);
                    const int slot = Access::keyedSlotFor(secondEngine, 45 + index);
                    assert(slot >= 0 && slot == Access::keyedSlotFor(firstEngine, 45 + index));
                    assert(Access::envelopeStage(secondEngine, slot) == 1);
                }
                // Holding the replacement must keep every assigned voice,
                // including after the user's one-second silent-note interval.
                for (int batch = 0; batch < static_cast<int>(rate / 64); ++batch)
                    assertSameAudio(renderBatch(offFirst), renderBatch(onFirst));
                for (int index = 0; index < 6; ++index)
                    assert(Access::keyedSlotFor(secondEngine, 45 + index) >= 0);
            }
    sampleRate = savedRate;
}

void checkSameFrameMidiEdgeCounts()
{
    using Access = youknow::YouKnowTestAccess;
    // More than one same-pitch pair at a frame must not strand a hold. A
    // simple sort of every off before every on incorrectly loses excess offs.
    for (int initialHolds : { 0, 1, 2 })
        for (int offCount : { 1, 2, 3 })
        {
            std::vector<int> edges(static_cast<std::size_t>(offCount), 0);
            edges.insert(edges.end(), 2, 1);
            do
            {
                configureAttackHost();
                CYouKnow device(sampleRate);
                const auto on = noteDiff(57, 97, 0);
                renderBatch(device);
                for (int hold = 0; hold < initialHolds; ++hold)
                    renderBatch(device, &on, 1);
                std::vector<TJBox_PropertyDiff> boundary;
                for (int edge : edges)
                    boundary.push_back(noteDiff(57, edge ? 97 : 0, 17));
                renderBatch(device, boundary.data(), boundary.size());
                auto& engine = CYouKnowTestAccess::engine(device);
                const int remaining = std::max(0, initialHolds + 2 - offCount);
                assert(Access::heldCount(engine, 57) == remaining);
                assert((Access::keyedSlotFor(engine, 57) >= 0) == (remaining > 0));
                const auto off = noteDiff(57, 0, 31);
                for (int held = remaining; held > 0; --held)
                {
                    renderBatch(device, &off, 1);
                    assert(Access::heldCount(engine, 57) == held - 1);
                }
                assert(Access::keyedSlotFor(engine, 57) < 0);
            } while (std::next_permutation(edges.begin(), edges.end()));
        }
}

void checkMidiOwnershipAndOverlap()
{
    using Access = youknow::YouKnowTestAccess;
    configureAttackHost();
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 1.0);
    set("/cv_inputs/note_cv", "value", Kind::Number, 57.0 / 127.0);
    CYouKnow shared(sampleRate);
    renderBatch(shared);
    auto& sharedEngine = CYouKnowTestAccess::engine(shared);
    const auto unmatched = noteDiff(57, 0, 17);
    renderBatch(shared, &unmatched, 1);
    assert(Access::heldCount(sharedEngine, 57) == 1);
    assert(Access::keyedSlotFor(sharedEngine, 57) >= 0);
    const auto on = noteDiff(57, 97, 0);
    renderBatch(shared, &on, 1);
    assert(Access::heldCount(sharedEngine, 57) == 2);
    const std::array replacement { noteDiff(57, 83, 17), noteDiff(57, 0, 17) };
    renderBatch(shared, replacement.data(), replacement.size());
    assert(Access::heldCount(sharedEngine, 57) == 2);
    renderBatch(shared, &unmatched, 1);
    renderBatch(shared, &unmatched, 1);
    assert(Access::heldCount(sharedEngine, 57) == 1);
    assert(Access::keyedSlotFor(sharedEngine, 57) >= 0);
    // Audio reset clears MIDI ownership, then restores the high CV gate once.
    renderBatch(shared, &on, 1);
    resetCounter = 1.0;
    renderBatch(shared);
    renderBatch(shared, &unmatched, 1);
    assert(Access::heldCount(sharedEngine, 57) == 1);
    assert(Access::keyedSlotFor(sharedEngine, 57) >= 0);
    const auto cvOff = change("/cv_inputs/gate_cv", "value", Kind::Number, 0.0, 23);
    renderBatch(shared, &cvOff, 1);
    assert(Access::heldCount(sharedEngine, 57) == 0);

    configureAttackHost();
    CYouKnow overlap(sampleRate);
    renderBatch(overlap, &on, 1);
    auto& overlapEngine = CYouKnowTestAccess::engine(overlap);
    const int originalSlot = Access::keyedSlotFor(overlapEngine, 57);
    const std::array overlapping { noteDiff(57, 37, 17), noteDiff(57, 0, 18) };
    renderBatch(overlap, overlapping.data(), overlapping.size());
    assert(Access::heldCount(overlapEngine, 57) == 1);
    assert(Access::keyedSlotFor(overlapEngine, 57) == originalSlot);
    assert(Access::velocity(overlapEngine, originalSlot) == 97.0f / 127.0f);
    renderBatch(overlap, &unmatched, 1);
    assert(Access::heldCount(overlapEngine, 57) == 0);
    assert(Access::keyedSlotFor(overlapEngine, 57) < 0);

    // An old pitch's delayed off cannot release the new owner of its slot.
    configureAttackHost(0.72, 1);
    CYouKnow reused(sampleRate);
    const auto oldOn = noteDiff(45, 127, 0);
    renderBatch(reused, &oldOn, 1);
    const std::array reuse { noteDiff(45, 0, 0), noteDiff(57, 97, 17) };
    renderBatch(reused, reuse.data(), reuse.size());
    const auto lateOff = noteDiff(45, 0, 31);
    renderBatch(reused, &lateOff, 1);
    auto& reusedEngine = CYouKnowTestAccess::engine(reused);
    assert(Access::keyedSlotFor(reusedEngine, 57) == 0);
    assert(Access::heldCount(reusedEngine, 57) == 1);
    assert(Access::envelopeStage(reusedEngine, 0) == 1);
}

void checkSimultaneousMidiCVHandoff()
{
    using Access = youknow::YouKnowTestAccess;
    for (bool samePitch : { false, true })
        for (int frame : { 0, 17, 63 })
        {
            configureAttackHost();
            set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
            set("/cv_inputs/gate_cv", "value", Kind::Number, 1.0);
            set("/cv_inputs/note_cv", "value", Kind::Number, 57.0 / 127.0);
            CYouKnow gateFirst(sampleRate), midiFirst(sampleRate);
            std::array<TJBox_PropertyDiff, 5> chord {};
            for (int index = 0; index < 5; ++index)
                chord[index] = noteDiff(60 + index, 127, 0);
            renderBatch(gateFirst, chord.data(), chord.size());
            renderBatch(midiFirst, chord.data(), chord.size());
            const int nextPitch = samePitch ? 57 : 72;
            std::array boundary {
                change("/cv_inputs/gate_cv", "value", Kind::Number, 0.0, frame),
                noteDiff(nextPitch, 83, frame),
            };
            const auto expected = renderBatch(gateFirst, boundary.data(), boundary.size());
            std::reverse(boundary.begin(), boundary.end());
            const auto actual = renderBatch(midiFirst, boundary.data(), boundary.size());
            assertSameAudio(expected, actual);
            auto& engine = CYouKnowTestAccess::engine(midiFirst);
            assert(Access::heldCount(engine, nextPitch) == 1);
            const int slot = Access::keyedSlotFor(engine, nextPitch);
            assert(slot >= 0 && Access::envelopeStage(engine, slot) == 1);
            assert(Access::velocity(engine, slot) == 83.0f / 127.0f);
            assert(!CYouKnowTestAccess::cvActive(midiFirst));
            if (!samePitch)
                assert(Access::heldCount(engine, 57) == 0);
            for (int batch = 0; batch < 32; ++batch)
                assertSameAudio(renderBatch(gateFirst), renderBatch(midiFirst));
        }

    // The opposite handoff must release the outgoing MIDI owner before the
    // simultaneous high CV gate acquires that same pitch, regardless of order.
    configureAttackHost();
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/note_cv", "value", Kind::Number, 57.0 / 127.0);
    CYouKnow offFirst(sampleRate), gateFirst(sampleRate);
    const auto initial = noteDiff(57, 37, 0);
    renderBatch(offFirst, &initial, 1);
    renderBatch(gateFirst, &initial, 1);
    std::array boundary {
        noteDiff(57, 0, 17),
        change("/cv_inputs/gate_cv", "value", Kind::Number, 1.0, 17),
    };
    const auto expected = renderBatch(offFirst, boundary.data(), boundary.size());
    std::reverse(boundary.begin(), boundary.end());
    const auto actual = renderBatch(gateFirst, boundary.data(), boundary.size());
    assertSameAudio(expected, actual);
    auto& engine = CYouKnowTestAccess::engine(gateFirst);
    assert(Access::heldCount(engine, 57) == 1);
    const int slot = Access::keyedSlotFor(engine, 57);
    assert(slot >= 0 && Access::velocity(engine, slot) == 1.0f);
    assert(CYouKnowTestAccess::cvActive(gateFirst));
}

void checkAttackGridSampleTiming()
{
    // An independent one-sample engine render is the timing oracle. Test
    // touching notes with reversed ties and real 1/32-sample gaps; the latter
    // must retain their hardware release ticks, never be snapped to a tie.
    struct Event { int sample; int velocity; };
    const double savedRate = sampleRate;
    for (double rate : { 44100.0, 48000.0 })
        for (int gap : { 0, 1, 32 })
        {
            sampleRate = rate;
            configureAttackHost(1.0);
            CYouKnow wrapper(rate), reference(rate);
            renderBatch(wrapper);
            renderBatch(reference);
            auto& engine = CYouKnowTestAccess::engine(reference);
            const int period = static_cast<int>(rate * 0.125) + 7;
            constexpr int notes = 4;
            const int total = ((period * notes + 63) / 64 + 2) * 64;
            std::vector<Event> events;
            for (int note = 0; note < notes; ++note)
            {
                events.push_back({ note * period, 127 });
                events.push_back({ (note + 1) * period - gap, 0 });
            }
            std::stable_sort(events.begin(), events.end(), [](const Event& a, const Event& b) {
                return a.sample != b.sample ? a.sample < b.sample : a.velocity < b.velocity;
            });
            auto input = events;
            std::stable_sort(input.begin(), input.end(), [](const Event& a, const Event& b) {
                return a.sample != b.sample ? a.sample < b.sample : a.velocity > b.velocity;
            });
            std::size_t nextInput = 0, nextReference = 0;
            float peak = 0.0f;
            for (int first = 0; first < total; first += 64)
            {
                std::vector<TJBox_PropertyDiff> diffs;
                while (nextInput < input.size() && input[nextInput].sample < first + 64)
                {
                    const auto& event = input[nextInput++];
                    diffs.push_back(noteDiff(57, event.velocity, event.sample - first));
                }
                const auto actual = renderBatch(wrapper, diffs.empty() ? nullptr : diffs.data(),
                                                static_cast<TJBox_UInt32>(diffs.size()));
                for (int frame = 0; frame < 64; ++frame)
                {
                    const int sample = first + frame;
                    while (nextReference < events.size() && events[nextReference].sample == sample)
                    {
                        const auto& event = events[nextReference++];
                        if (event.velocity > 0)
                            engine.noteOn(57, event.velocity / 127.0f);
                        else
                            engine.noteOff(57);
                    }
                    float left = 0.0f, right = 0.0f;
                    engine.process(&left, &right, 1);
                    assert(std::isfinite(actual.left[frame]) && std::isfinite(actual.right[frame]));
                    // The wrapper may elide an entire sub-threshold block;
                    // differences must stay below that audible-output floor.
                    assert(std::abs(actual.left[frame] - left) < 1e-6f);
                    assert(std::abs(actual.right[frame] - right) < 1e-6f);
                    peak = std::max(peak, std::abs(actual.left[frame]));
                }
            }
            assert(peak > 1e-4f);
            assert(youknow::YouKnowTestAccess::heldCount(CYouKnowTestAccess::engine(wrapper), 57) == 0);
        }
    sampleRate = savedRate;
}

void checkRetriggerPedalAndGateModes()
{
    using Access = youknow::YouKnowTestAccess;
    for (double mode : { 0.0, 1.0, 2.0 })
        for (double vcaMode : { 0.0, 1.0 })
            for (bool pedalDown : { false, true })
            {
                configureAttackHost();
                set("/custom_properties", "keyMode", Kind::Number, mode);
                set("/custom_properties", "vcaMode", Kind::Number, vcaMode);
                set("/custom_properties", "sustainPedal", Kind::Number, pedalDown ? 0.0 : 1.0);
                CYouKnow offFirst(sampleRate), onFirst(sampleRate);
                // Allow a restored Unison/Poly2 assignment scan to finish.
                for (int batch = 0; batch < 8; ++batch)
                    assertSameAudio(renderBatch(offFirst), renderBatch(onFirst));
                const auto initial = noteDiff(57, 127, 0);
                assertSameAudio(renderBatch(offFirst, &initial, 1),
                                renderBatch(onFirst, &initial, 1));
                for (int batch = 0; batch < 32; ++batch)
                    assertSameAudio(renderBatch(offFirst), renderBatch(onFirst));
                // The pedal itself changes at the touching-note boundary.
                // Its final control image applies before either event order.
                std::array boundary {
                    noteDiff(57, 0, 17), noteDiff(57, 83, 17),
                    change("/custom_properties", "sustainPedal", Kind::Number,
                           pedalDown ? 1.0 : 0.0, 17),
                };
                const auto expected = renderBatch(offFirst, boundary.data(), boundary.size());
                std::reverse(boundary.begin(), boundary.end());
                const auto actual = renderBatch(onFirst, boundary.data(), boundary.size());
                assertSameAudio(expected, actual);
                auto& engine = CYouKnowTestAccess::engine(onFirst);
                const int slot = Access::keyedSlotFor(engine, 57);
                assert(Access::heldCount(engine, 57) == 1 && slot >= 0);
                assert(Access::envelopeStage(engine, slot) == 1);
                assert(Access::velocity(engine, slot) == 83.0f / 127.0f);
                const auto off = noteDiff(57, 0, 31);
                assertSameAudio(renderBatch(offFirst, &off, 1), renderBatch(onFirst, &off, 1));
                assert(Access::heldCount(engine, 57) == 0);
                assert(Access::keyedSlotFor(engine, 57) < 0);
                assert(Access::anyLatchedVoice(engine) == pedalDown);
                const auto pedalUp = change("/custom_properties", "sustainPedal", Kind::Number, 0.0, 23);
                assertSameAudio(renderBatch(offFirst, &pedalUp, 1), renderBatch(onFirst, &pedalUp, 1));
                assert(!Access::anyLatchedVoice(engine));
                assert(!Access::anyLatchedVoice(CYouKnowTestAccess::engine(offFirst)));
                for (int batch = 0; batch < 32; ++batch)
                    assertSameAudio(renderBatch(offFirst), renderBatch(onFirst));
            }
}

void checkInvalidMidiNoteTags()
{
    using Access = youknow::YouKnowTestAccess;
    for (int invalidNote : { 128, 255 })
    {
        configureAttackHost();
        CYouKnow tested(sampleRate), untouched(sampleRate);
        const auto invalidOn = noteDiff(invalidNote, 127, 17);
        assertSameAudio(renderBatch(tested, &invalidOn, 1), renderBatch(untouched));
        auto& engine = CYouKnowTestAccess::engine(tested);
        assert(Access::heldCount(engine, 127) == 0);
        assert(!Access::anyLatchedVoice(engine));
        const auto validOn = noteDiff(127, 37, 0);
        assertSameAudio(renderBatch(tested, &validOn, 1), renderBatch(untouched, &validOn, 1));
        const auto invalidOff = noteDiff(invalidNote, 0, 17);
        assertSameAudio(renderBatch(tested, &invalidOff, 1), renderBatch(untouched));
        assert(Access::heldCount(engine, 127) == 1);
        assert(Access::keyedSlotFor(engine, 127) >= 0);
        const auto validOff = noteDiff(127, 0, 31);
        assertSameAudio(renderBatch(tested, &validOff, 1), renderBatch(untouched, &validOff, 1));
        assert(Access::heldCount(engine, 127) == 0);
        assert(!Access::anyLatchedVoice(engine));
    }
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

void checkSameFrameCVPitchAndGate()
{
    using Access = youknow::YouKnowTestAccess;
    // Check initial restore as well as stable playback. At one frame, neither
    // socket is promised to precede the other in SDK 5's notification list.
    for (bool restored : { false, true })
    {
        configureCVHost();
        set("/custom_properties", "keyMode", Kind::Number, 0.0);
        set("/custom_properties", "portamento", Kind::Number, 0.80);
        set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
        set("/cv_inputs/note_cv", "connected", Kind::Boolean, 1.0);
        CYouKnow gateFirst(sampleRate);
        CYouKnow pitchFirst(sampleRate);
        if (!restored)
        {
            renderBatch(gateFirst);
            renderBatch(pitchFirst);
        }
        std::array start {
            change("/cv_inputs/gate_cv", "value", Kind::Number, 1.0, 17),
            change("/cv_inputs/note_cv", "value", Kind::Number, 67.0 / 127.0, 17),
        };
        const auto a = renderBatch(gateFirst, start.data(), start.size());
        std::reverse(start.begin(), start.end());
        const auto b = renderBatch(pitchFirst, start.data(), start.size());
        assert(a.left == b.left && a.right == b.right);
        auto& gateEngine = CYouKnowTestAccess::engine(gateFirst);
        auto& pitchEngine = CYouKnowTestAccess::engine(pitchFirst);
        const int slot = Access::keyedSlotFor(gateEngine, 67);
        assert(slot >= 0 && Access::currentMidi(gateEngine, slot) == 67.0f);
        for (int batch = 0; batch < 40; ++batch)
        {
            const auto x = renderBatch(gateFirst);
            const auto y = renderBatch(pitchFirst);
            assert(x.left == y.left && x.right == y.right);
        }

        // Keep both gate edges while moving their same-frame pitch change.
        // This must release 67 and retrigger 70, not retarget 67 before release.
        std::array retrigger {
            change("/cv_inputs/gate_cv", "value", Kind::Number, 0.0, 20),
            change("/cv_inputs/gate_cv", "value", Kind::Number, 1.0, 20),
            change("/cv_inputs/note_cv", "value", Kind::Number, 70.0 / 127.0, 20),
        };
        const auto gateThenPitch = renderBatch(gateFirst, retrigger.data(), retrigger.size());
        std::rotate(retrigger.begin(), retrigger.end() - 1, retrigger.end());
        const auto pitchThenGate = renderBatch(pitchFirst, retrigger.data(), retrigger.size());
        assert(gateThenPitch.left == pitchThenGate.left
               && gateThenPitch.right == pitchThenGate.right);
        assert(Access::heldCount(gateEngine, 67) == 0);
        assert(Access::heldCount(gateEngine, 70) == 1);
        assert(Access::heldCount(pitchEngine, 67) == 0);
        assert(Access::heldCount(pitchEngine, 70) == 1);

        // A disconnect/reconnect at a high gate has the same release/restart
        // contract, including when pitch is last in that frame's diff group.
        std::array reconnect {
            change("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0, 31),
            change("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0, 31),
            change("/cv_inputs/note_cv", "value", Kind::Number, 74.0 / 127.0, 31),
        };
        const auto disconnectFirst = renderBatch(gateFirst, reconnect.data(), reconnect.size());
        std::rotate(reconnect.begin(), reconnect.end() - 1, reconnect.end());
        const auto reconnectPitchFirst = renderBatch(pitchFirst, reconnect.data(), reconnect.size());
        assert(disconnectFirst.left == reconnectPitchFirst.left
               && disconnectFirst.right == reconnectPitchFirst.right);
        assert(Access::heldCount(gateEngine, 70) == 0);
        assert(Access::heldCount(gateEngine, 74) == 1);
        assert(Access::heldCount(pitchEngine, 70) == 0);
        assert(Access::heldCount(pitchEngine, 74) == 1);
        for (int batch = 0; batch < 16; ++batch)
        {
            const auto x = renderBatch(gateFirst);
            const auto y = renderBatch(pitchFirst);
            assert(x.left == y.left && x.right == y.right);
        }
    }
}

void checkResetSnapsCalibration()
{
    using Access = youknow::YouKnowTestAccess;
    configureCVHost();
    set("/custom_properties", "keyMode", Kind::Number, 0.0);
    set("/custom_properties", "calibration", Kind::Number, 0.50);
    CYouKnow running(sampleRate);
    renderBatch(running);
    auto& engine = CYouKnowTestAccess::engine(running);
    const auto move = change("/custom_properties", "calibration", Kind::Number,
                              1.0, 32);
    renderBatch(running, &move, 1);
    assert(Access::parameters(engine).calibration > 1.0f
           && Access::parameters(engine).calibration < 2.0f);
    resetCounter = 1.0;
    renderBatch(running);
    assert(Access::parameters(engine).calibration == 2.0f);
    resetCounter = 0.0;
    CYouKnow restored(sampleRate);
    renderBatch(restored);
    assert(Access::parameters(engine).calibration
           == Access::parameters(CYouKnowTestAccess::engine(restored)).calibration);

    // Reset sees final MOM state, but a later event in this batch must not
    // replace the frame-zero restored value. Its glide starts at that event.
    const auto laterMove = change("/custom_properties", "calibration", Kind::Number,
                                   0.0, 31);
    resetCounter = 2.0;
    renderBatch(running, &laterMove, 1);
    const float expected = 2.0f - 2.0f * static_cast<float>(
        33.0 / (0.030 * sampleRate));
    assert(std::abs(Access::parameters(engine).calibration - expected) < 1.0e-6f);
    resetCounter = 0.0;
}

void checkRescanPreservesRenderedAudio()
{
    configureCVHost();
    set("/custom_properties", "keyMode", Kind::Number, 2.0);
    set("/custom_properties", "polyphony", Kind::Number, 5.0);
    set("/custom_properties", "chorus", Kind::Number, 0.0);
    CYouKnow whole(sampleRate);
    CYouKnow segmented(sampleRate);
    const auto note = noteDiff(60, 127, 0);
    // Notifications for the output lamp do not change engine state. They may
    // split a render interval but cannot reveal samples discarded by another
    // interval size when a pending assigner rescan starts voices mid-batch.
    std::array<TJBox_PropertyDiff, 64> ignored {};
    for (int frame = 0; frame < 64; ++frame)
    {
        ignored[frame] = customDiff("noteOn");
        ignored[frame].fAtFrameIndex = static_cast<TJBox_UInt16>(frame);
    }
    for (int batch = 0; batch < 12; ++batch)
    {
        const auto a = renderBatch(whole, batch == 0 ? &note : nullptr,
                                    batch == 0 ? 1 : 0);
        const auto firstIgnored = ignored[0];
        if (batch == 0)
            ignored[0] = note;
        const auto b = renderBatch(segmented, ignored.data(), ignored.size());
        ignored[0] = firstIgnored;
        assert(a.left == b.left && a.right == b.right);
    }
    assert(CYouKnowTestAccess::engine(whole).getActiveVoiceCount() == 6);
}

// A pitch CV may remain held after its note was dropped by a full poly pool.
// Once MIDI releases a slot, a gate-high pitch move must retry assignment.
void checkCVDroppedNoteRecovery()
{
    using Access = youknow::YouKnowTestAccess;
    for (double mode : { 0.0, 1.0 })
    {
        configureCVHost();
        set("/custom_properties", "keyMode", Kind::Number, mode);
        set("/custom_properties", "polyphony", Kind::Number, 0.0);
        set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
        set("/cv_inputs/note_cv", "connected", Kind::Boolean, 1.0);
        set("/cv_inputs/note_cv", "value", Kind::Number, 64.0 / 127.0);
        CYouKnow device(sampleRate);
        // Let a restored Poly 2 assigner rescan finish before filling its pool.
        for (int batch = 0; batch < 8; ++batch)
            renderBatch(device);
        auto& engine = CYouKnowTestAccess::engine(device);
        const auto midiOn = noteDiff(60, 127, 0);
        renderBatch(device, &midiOn, 1);
        assert(Access::keyedSlotFor(engine, 60) >= 0);
        const auto cvOn = change("/cv_inputs/gate_cv", "value", Kind::Number,
                                  1.0, 19);
        renderBatch(device, &cvOn, 1);
        assert(Access::heldCount(engine, 64) == 1);
        assert(Access::keyedSlotFor(engine, 64) < 0);

        const auto midiOff = noteDiff(60, 0, 5);
        renderBatch(device, &midiOff, 1);
        const auto cvPitch = change("/cv_inputs/note_cv", "value", Kind::Number,
                                     67.0 / 127.0, 23);
        renderBatch(device, &cvPitch, 1);
        assert(Access::heldCount(engine, 60) == 0);
        assert(Access::heldCount(engine, 64) == 0);
        assert(Access::heldCount(engine, 67) == 1);
        assert(Access::keyedSlotFor(engine, 67) >= 0);
        assert(CYouKnowTestAccess::lastCVNote(device) == 67);
        assert(CYouKnowTestAccess::cvActive(device));

        const auto cvOff = change("/cv_inputs/gate_cv", "value", Kind::Number,
                                   0.0, 11);
        renderBatch(device, &cvOff, 1);
        assert(Access::heldCount(engine, 67) == 0);
        assert(!CYouKnowTestAccess::cvActive(device));
    }
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

// --- Musical note phrases -----------------------------------------------------
// Phrases a player actually produces, rendered through the complete Rack MIDI
// path at sample-exact positions: an equal pitch pressed again while it is
// still held (in later batches and twice within one frame), legato runs over
// adjacent semitones whose notes touch, overlap or leave a one-sample gap
// (on batch edges, frame 63 and in between, in both same-frame diff orders),
// a rapid repeated note, and semitone clusters within and beyond the voice
// pool. Every key mode runs with and without the sustain pedal. After every
// batch the MIDI and engine hold counts must match an independent model, no
// voice may stay keyed to a released pitch, every keyed voice must carry the
// velocity of its pitch's first outstanding press, and once the converter scan
// has run every held pitch must own a voice (the pool permitting; Unison keys
// one held pitch). An extra press of a held pitch, in a later batch or in the
// same frame, must not reassign or retrigger it, and every phrase must end
// silent with nothing latched.
struct PhraseEvent
{
    int sample;
    int note;
    int velocity; // zero releases
};

struct Phrase
{
    std::string name;
    std::vector<PhraseEvent> events;
};

std::vector<Phrase> musicalPhrases(double rate)
{
    const auto ms = [rate](double milliseconds) {
        return static_cast<int>(std::lround(milliseconds * rate / 1000.0));
    };
    std::vector<Phrase> phrases;

    {
        Phrase phrase { "equal-pitch overlaps", {} };
        const int start = 64 * 2 + 20;
        phrase.events = {
            { start, 60, 100 },
            { start + ms(90), 60, 50 },  // second press of a held key
            { start + ms(200), 60, 0 },  // one of two presses released
            { start + ms(260), 60, 80 },
            { start + ms(330), 60, 0 },
            { start + ms(420), 60, 0 },  // the final release
            { start + ms(500), 62, 90 }, // two presses in one frame
            { start + ms(500), 62, 70 },
            { start + ms(640), 62, 0 },  // two releases in one frame
            { start + ms(640), 62, 0 },
        };
        phrases.push_back(std::move(phrase));
    }

    for (const int gap : { 0, 1, -ms(30) })
    {
        Phrase phrase { gap == 0 ? "touching semitone run"
                        : gap > 0 ? "one-sample-gap semitone run"
                                  : "overlapping semitone run", {} };
        constexpr int notes = 13;
        int onset = 64 * 3; // the first press on a batch edge
        phrase.events.push_back({ onset, gap < 0 ? 72 : 48, 64 });
        for (int step = 0; step < notes; ++step)
        {
            const int note = gap < 0 ? 72 - step : 48 + step;
            // Boundaries land on batch edges, on frame 63 and in between.
            const int length = step % 3 == 0 ? 64 * 7
                : step % 3 == 1 ? 64 * 6 + 63 : ms(143);
            const int release = onset + length;
            if (step + 1 == notes)
            {
                phrase.events.push_back({ release, note, 0 });
                break;
            }
            const int nextNote = gap < 0 ? note - 1 : note + 1;
            const int nextOnset = release + gap;
            const PhraseEvent press { nextOnset, nextNote, 64 + 4 * step };
            const PhraseEvent off { release, note, 0 };
            // A touching boundary is one frame; exercise both diff orders.
            if (gap == 0 && step % 2 == 1)
            {
                phrase.events.push_back(press);
                phrase.events.push_back(off);
            }
            else
            {
                phrase.events.push_back(off);
                phrase.events.push_back(press);
            }
            onset = nextOnset;
        }
        phrases.push_back(std::move(phrase));
    }

    {
        Phrase phrase { "rapid repeated note", {} };
        int onset = 64 * 2 + 5;
        for (int repeat = 0; repeat < 40; ++repeat)
        {
            const int length = 64 + 7 * repeat; // 1.3 to 7 ms at 48 kHz
            phrase.events.push_back({ onset, 64, 40 + repeat });
            phrase.events.push_back({ onset + length, 64, 0 });
            onset += length; // the next press shares the release frame
        }
        phrases.push_back(std::move(phrase));
    }

    {
        Phrase phrase { "adjacent-semitone cluster", {} };
        const int start = 64 * 4 + 9;
        for (int note = 60; note < 66; ++note)
            phrase.events.push_back({ start, note, 100 });
        for (int note = 65; note >= 60; --note)
            phrase.events.push_back({ start + ms(300) + (65 - note) * ms(10), note, 0 });
        phrases.push_back(std::move(phrase));
    }

    {
        Phrase phrase { "semitone cluster beyond the pool", {} };
        const int start = 64 * 4 + 33;
        for (int note = 60; note < 72; ++note)
            phrase.events.push_back({ start, note, 90 });
        for (int note = 60; note < 72; ++note)
            phrase.events.push_back({ start + ms(250), note, 0 });
        for (const int note : { 48, 52, 55 })
            phrase.events.push_back({ start + ms(300), note, 110 });
        for (const int note : { 48, 52, 55 })
            phrase.events.push_back({ start + ms(450), note, 0 });
        phrases.push_back(std::move(phrase));
    }

    // Time order; equal samples keep their authored diff order.
    for (auto& phrase : phrases)
        std::stable_sort(phrase.events.begin(), phrase.events.end(),
                         [](const PhraseEvent& a, const PhraseEvent& b) {
                             return a.sample < b.sample;
                         });
    return phrases;
}

void checkMusicalNotePhrases()
{
    using Access = youknow::YouKnowTestAccess;
    const double savedRate = sampleRate;
    for (const double rate : { 44100.0, 48000.0 })
        for (const double keyMode : { 0.0, 1.0, 2.0 })
            for (const bool pedal : { false, true })
                for (const auto& phrase : musicalPhrases(rate))
                {
                    sampleRate = rate;
                    configureAttackHost();
                    set("/custom_properties", "keyMode", Kind::Number, keyMode);
                    CYouKnow device(rate);
                    auto& engine = CYouKnowTestAccess::engine(device);
                    const bool unison = keyMode == 2.0;
                    // Let a restored Poly 2/Unison assignment scan finish.
                    for (int batch = 0; batch < 8; ++batch)
                        renderBatch(device);

                    const int settle = 64 * 8; // longer than one converter scan
                    const int lastEvent = phrase.events.back().sample;
                    const int total = ((lastEvent + static_cast<int>(rate)) / 64 + 1) * 64;
                    constexpr int voiceSlots = youknow::YouKnowEngine::maxVoices;
                    std::array<int, 128> held {};
                    std::array<int, 128> firstPressVelocity {};
                    int lastChange = 0;
                    float peak = 0.0f;
                    std::size_t next = 0;
                    for (int first = 0; first < total; first += 64)
                    {
                        std::vector<TJBox_PropertyDiff> diffs;
                        if (pedal && first == 0)
                            diffs.push_back(change("/custom_properties", "sustainPedal",
                                                   Kind::Number, 1.0, 0));
                        std::array<int, voiceSlots> noteBefore {};
                        std::array<std::uint64_t, voiceSlots> generationBefore {};
                        for (int slot = 0; slot < voiceSlots; ++slot)
                        {
                            noteBefore[slot] = Access::keyedNote(engine, slot);
                            generationBefore[slot] = Access::generation(engine, slot);
                        }
                        // True while this batch holds only extra presses of
                        // pitches that were already held when it began.
                        bool onlyExtraPresses = true;
                        bool anyEvent = false;
                        while (next < phrase.events.size()
                               && phrase.events[next].sample < first + 64)
                        {
                            const auto& event = phrase.events[next++];
                            diffs.push_back(noteDiff(event.note, event.velocity,
                                                     event.sample - first));
                            anyEvent = true;
                            onlyExtraPresses = onlyExtraPresses && event.velocity > 0
                                && held[event.note] > 0;
                            if (event.velocity > 0 && held[event.note] == 0)
                                firstPressVelocity[event.note] = event.velocity;
                            held[event.note] += event.velocity > 0 ? 1 : -1;
                            assert(held[event.note] >= 0);
                            lastChange = event.sample;
                        }
                        if (pedal && first <= lastEvent + static_cast<int>(rate / 50)
                            && first + 64 > lastEvent + static_cast<int>(rate / 50))
                            diffs.push_back(change("/custom_properties", "sustainPedal",
                                                   Kind::Number, 0.0, 0));
                        const auto audio = renderBatch(device, diffs.empty() ? nullptr : diffs.data(),
                                                       static_cast<TJBox_UInt32>(diffs.size()));
                        for (std::size_t frame = 0; frame < 64; ++frame)
                        {
                            assert(std::isfinite(audio.left[frame]) && std::isfinite(audio.right[frame]));
                            assert(std::abs(audio.left[frame]) <= 2.0f
                                   && std::abs(audio.right[frame]) <= 2.0f);
                            peak = std::max(peak, std::abs(audio.left[frame]));
                        }

                        int heldPitches = 0;
                        for (int note = 0; note < 128; ++note)
                        {
                            assert(CYouKnowTestAccess::midiHeldCount(device, note) == held[note]);
                            assert(Access::heldCount(engine, note) == held[note]);
                            heldPitches += held[note] > 0 ? 1 : 0;
                        }
                        assert(!Access::keyedWithoutHeldKey(engine));

                        // Keyed voices carry their pitch's first press velocity,
                        // so an extra press in the same frame cannot replace it.
                        for (int slot = 0; slot < voiceSlots; ++slot)
                        {
                            const int note = Access::keyedNote(engine, slot);
                            if (note >= 0)
                                assert(Access::velocity(engine, slot)
                                       == static_cast<float>(firstPressVelocity[note]) / 127.0f);
                        }
                        // A batch of nothing but extra presses changes no voice.
                        if (anyEvent && onlyExtraPresses)
                            for (int slot = 0; slot < voiceSlots; ++slot)
                            {
                                assert(Access::keyedNote(engine, slot) == noteBefore[slot]);
                                assert(Access::generation(engine, slot) == generationBefore[slot]);
                            }

                        if (first < lastChange + settle)
                            continue;
                        if (unison)
                        {
                            int keyedPitches = 0;
                            for (int note = 0; note < 128; ++note)
                                if (Access::keyedVoiceCount(engine, note) > 0)
                                {
                                    ++keyedPitches;
                                    assert(held[note] > 0);
                                }
                            assert(keyedPitches == (heldPitches > 0 ? 1 : 0));
                        }
                        else if (heldPitches <= youknow::YouKnowEngine::hardwareVoices)
                        {
                            for (int note = 0; note < 128; ++note)
                                assert((Access::keyedVoiceCount(engine, note) == 1) == (held[note] > 0));
                        }
                        else
                        {
                            int keyed = 0;
                            for (int note = 0; note < 128; ++note)
                                keyed += Access::keyedVoiceCount(engine, note);
                            assert(keyed == youknow::YouKnowEngine::hardwareVoices);
                        }
                    }
                    assert(peak > 1.0e-4f);
                    for (int note = 0; note < 128; ++note)
                        assert(held[note] == 0);
                    assert(engine.getActiveVoiceCount() == 0);
                    assert(!Access::anyLatchedVoice(engine));
                }
    sampleRate = savedRate;
}

// --- Product configuration ----------------------------------------------------
// The shipped instrument renders with the source plug-in's product circuit
// selections: ProductFidelityProfile before the first prepare() and on every
// parameter snapshot, plus the chart-geometry converter timing that the
// plug-in and its product renderers select before prepare(). An engine
// configured that way independently, given the wrapper's own control image and
// the same note, must reproduce the wrapper's output bit for bit.
void checkProductConfigurationMatchesSourcePlugin()
{
    using youknow::YouKnowEngine;
    const double savedRate = sampleRate;
    for (double rate : { 44100.0, 48000.0, 96000.0 })
    {
        sampleRate = rate;
        configureCVHost();
        CYouKnow device(rate);
        const auto on = noteDiff(60, 127, 0);
        Batch actual = renderBatch(device, &on, 1);

        YouKnowEngine reference;
        const bool configured =
            youknow::ProductFidelityProfile::configureBeforePrepare(reference);
        assert(configured);
        reference.selectConverterTimingProfile(
            YouKnowEngine::ConverterTimingProfile::MeasuredChartGeometry);
        reference.prepare(rate, 64, 1);
        const auto& image = CYouKnowTestAccess::engineParameters(device);
        assert(image.useServiced439522VcfCalibration);
        reference.setParameters(image);
        reference.setPitchBend(static_cast<float>(get("/custom_properties", "pitchBend") * 2.0 - 1.0));
        reference.setModWheel(static_cast<float>(get("/custom_properties", "modWheel")));
        reference.setSustainPedal(get("/custom_properties", "sustainPedal") >= 0.5);
        assert(reference.setOversamplingFactor(1));
        reference.noteOn(60, 1.0f);

        bool audible = false;
        for (int batch = 0; batch < static_cast<int>(rate / 64.0); ++batch)
        {
            if (batch > 0)
                actual = renderBatch(device);
            std::array<float, 64> left {}, right {};
            reference.process(left.data(), right.data(), 64);
            const bool wrote = wroteLeft || wroteRight;
            for (std::size_t frame = 0; frame < 64; ++frame)
            {
                if (wrote)
                {
                    assert(actual.left[frame] == left[frame]);
                    assert(actual.right[frame] == right[frame]);
                }
                else
                {
                    assert(std::abs(left[frame]) <= kJBox_SilentThreshold);
                    assert(std::abs(right[frame]) <= kJBox_SilentThreshold);
                }
            }
            audible = audible || wrote;
        }
        assert(audible);
    }
    sampleRate = savedRate;
}

// --- Nonfinite and out-of-range controls -------------------------------------
// Every control reaches the wrapper as a double from the host, songs and
// patches. No value may reach an undefined float-to-int or out-of-range float
// conversion or select an arbitrary state: a nonfinite number takes the
// property's declared default (checked against motherboard_def.lua by
// Tests/validate_patches.py) and a finite one rounds and clamps to the
// control's travel, whether it arrives in the restore snapshot or as a timed
// diff, and before any CV modulates it. Nonfinite Character, Reason master
// tune and audio-reset values must not poison later valid input.
void checkNonFiniteAndOutOfRangeControls()
{
    using Access = youknow::YouKnowTestAccess;
    using Device = CYouKnowTestAccess;
    const double nan = std::numeric_limits<double>::quiet_NaN();
    const double infinity = std::numeric_limits<double>::infinity();
    const auto assertFinite = [](const Batch& batch) {
        for (std::size_t frame = 0; frame < 64; ++frame)
            assert(std::isfinite(batch.left[frame]) && std::isfinite(batch.right[frame]));
    };
    // Renders one device restored with `value` and one receiving it as an
    // automation diff, and hands both to `check`.
    const auto bothPaths = [&](const char* name, double value, const auto& check) {
        configureCVHost();
        set("/custom_properties", name, Kind::Number, value);
        CYouKnow restored(sampleRate);
        assertFinite(renderBatch(restored));
        check(restored);

        configureCVHost();
        CYouKnow automated(sampleRate);
        renderBatch(automated);
        const auto diff = change("/custom_properties", name, Kind::Number, value, 17);
        assertFinite(renderBatch(automated, &diff, 1));
        check(automated);
    };

    struct Stepped
    {
        const char* name;
        int steps;
        int (*resolved)(const CYouKnow&);
    };
    const Stepped stepped[] {
        { "keyMode", 3, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).keyMode); } },
        { "pwmMode", 2, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).pwmSource); } },
        { "range", 3, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).range); } },
        { "highPass", 4, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).highPass); } },
        { "envPolarity", 2, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).envPolarity); } },
        { "vcaMode", 2, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).vcaMode); } },
        { "chorus", 4, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).chorus); } },
        { "transpose", 25, [](const CYouKnow& device) {
            return Device::engineParameters(device).keyTranspose + 12; } },
        { "polyphony", 16, [](const CYouKnow& device) {
            return Device::engineParameters(device).polyphony - 1; } },
        { "quality", 3, [](const CYouKnow& device) {
            const int factor = Device::requestedOversamplingFactor(device);
            return factor == 4 ? 2 : factor - 1; } },
        { "vcfTanhMode", 3, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).vcfTanhMode); } },
        { "vcfFastEarlyMode", 2, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).vcfFastEarlyMode); } },
        { "vcfSolverMode", 3, [](const CYouKnow& device) {
            return static_cast<int>(Device::engineParameters(device).vcfSolverMode); } },
    };
    for (const auto& property : stepped)
    {
        configureCVHost();
        const int defaultIndex = static_cast<int>(
            Device::parameterDefault(CYouKnow(sampleRate), property.name));
        const int last = property.steps - 1;
        const std::pair<double, int> cases[] {
            { nan, defaultIndex }, { infinity, defaultIndex }, { -infinity, defaultIndex },
            { 1.0e300, last }, { -1.0e300, 0 }, { last + 0.4, last }, { 0.6, 1 }, { -0.4, 0 },
        };
        for (const auto& [value, index] : cases)
        {
            const int expected = index; // C++17 lambdas cannot capture bindings
            bothPaths(property.name, value, [&](const CYouKnow& device) {
                assert(property.resolved(device) == expected);
            });
        }
    }

    // Normalized controls: `resolved` maps a 0..1 position to what the wrapper
    // hands on, so every case compares against the same mapping of its
    // expected position.
    struct Continuous
    {
        const char* name;
        double (*resolved)(CYouKnow&);
        double (*mapped)(double position);
    };
    const auto unit = [](double position) { return position; };
    const Continuous continuous[] {
        { "volume", [](CYouKnow& d) { return double(Device::engineParameters(d).volume); }, unit },
        { "benderDco", [](CYouKnow& d) { return double(Device::engineParameters(d).benderDcoDepth); }, unit },
        { "benderVcf", [](CYouKnow& d) { return double(Device::engineParameters(d).benderVcfDepth); }, unit },
        { "benderLfo", [](CYouKnow& d) { return double(Device::engineParameters(d).benderLfoDepth); }, unit },
        { "portamento", [](CYouKnow& d) { return double(Device::engineParameters(d).portamento); }, unit },
        { "lfoRate", [](CYouKnow& d) { return double(Device::engineParameters(d).lfoRate); }, unit },
        { "lfoDelay", [](CYouKnow& d) { return double(Device::engineParameters(d).lfoDelay); }, unit },
        { "dcoLfo", [](CYouKnow& d) { return double(Device::engineParameters(d).dcoLfoDepth); }, unit },
        { "pwm", [](CYouKnow& d) { return double(Device::engineParameters(d).pwmDepth); }, unit },
        { "sub", [](CYouKnow& d) { return double(Device::engineParameters(d).subLevel); }, unit },
        { "noise", [](CYouKnow& d) { return double(Device::engineParameters(d).noiseLevel); }, unit },
        { "cutoff", [](CYouKnow& d) { return double(Device::engineParameters(d).cutoff); }, unit },
        { "resonance", [](CYouKnow& d) { return double(Device::engineParameters(d).resonance); }, unit },
        { "vcfEnv", [](CYouKnow& d) { return double(Device::engineParameters(d).envDepth); }, unit },
        { "vcfLfo", [](CYouKnow& d) { return double(Device::engineParameters(d).vcfLfoDepth); }, unit },
        { "keyFollow", [](CYouKnow& d) { return double(Device::engineParameters(d).keyFollow); }, unit },
        { "vcaLevel", [](CYouKnow& d) { return double(Device::engineParameters(d).vcaLevel); }, unit },
        { "attack", [](CYouKnow& d) { return double(Device::engineParameters(d).attack); }, unit },
        { "decay", [](CYouKnow& d) { return double(Device::engineParameters(d).decay); }, unit },
        { "sustain", [](CYouKnow& d) { return double(Device::engineParameters(d).sustain); }, unit },
        { "release", [](CYouKnow& d) { return double(Device::engineParameters(d).release); }, unit },
        { "velocity", [](CYouKnow& d) { return double(Device::engineParameters(d).velocityDepth); }, unit },
        { "aging", [](CYouKnow& d) { return double(Device::engineParameters(d).aging); }, unit },
        { "chorusNoise", [](CYouKnow& d) { return double(Device::engineParameters(d).chorusNoise); }, unit },
        { "masterTune", [](CYouKnow& d) { return double(Device::engineParameters(d).masterTuneCents); },
          [](double position) { return double(static_cast<float>(position * 100.0 - 50.0)); } },
        { "calibration", [](CYouKnow& d) { return double(Device::calibrationTarget(d)); },
          [](double position) { return double(static_cast<float>(position) * 2.0f); } },
        { "presetGain", [](CYouKnow& d) { return double(Device::patchGainTarget(d)); },
          [](double position) { return double(static_cast<float>(std::exp2((position - 0.5) * 6.0))); } },
        { "pitchBend", [](CYouKnow& d) { return double(Access::pitchBendTarget(Device::engine(d))); },
          [](double position) { return double(static_cast<float>(position) * 2.0f - 1.0f); } },
        { "modWheel", [](CYouKnow& d) { return double(Access::modWheelTarget(Device::engine(d))); }, unit },
        { "sustainPedal", [](CYouKnow& d) { return Access::sustainPedalDown(Device::engine(d)) ? 1.0 : 0.0; },
          [](double position) { return position >= 0.5 ? 1.0 : 0.0; } },
    };
    for (const auto& property : continuous)
    {
        configureCVHost();
        const double fallback = Device::parameterDefault(CYouKnow(sampleRate), property.name);
        const std::pair<double, double> cases[] {
            { nan, fallback }, { infinity, fallback }, { -infinity, fallback },
            { 1.0e300, 1.0 }, { -1.0e300, 0.0 }, { 0.25, 0.25 },
        };
        for (const auto& [value, position] : cases)
        {
            const double expected = property.mapped == unit
                ? double(static_cast<float>(position)) : property.mapped(position);
            bothPaths(property.name, value, [&](const CYouKnow& device) {
                auto& mutableDevice = const_cast<CYouKnow&>(device);
                assert(property.resolved(mutableDevice) == expected);
            });
        }
    }

    // CV modulates the default that replaced a nonfinite value, never NaN.
    {
        configureCVHost();
        set("/custom_properties", "volume", Kind::Number, infinity);
        set("/cv_inputs/volume_cv", "connected", Kind::Boolean, 1.0);
        set("/cv_inputs/volume_cv", "value", Kind::Number, 0.0);
        set("/custom_properties", "cutoff", Kind::Number, nan);
        set("/cv_inputs/cutoff_cv", "connected", Kind::Boolean, 1.0);
        set("/cv_inputs/cutoff_cv", "value", Kind::Number, 0.25);
        CYouKnow device(sampleRate);
        assertFinite(renderBatch(device));
        assert(Device::engineParameters(device).volume == 0.0f);
        assert(Device::engineParameters(device).cutoff
               == static_cast<float>(Device::parameterDefault(device, "cutoff") + 0.25));
    }

    // A nonfinite Character takes its default; a later valid move still
    // glides to its exact target instead of staying poisoned.
    {
        configureCVHost();
        set("/custom_properties", "calibration", Kind::Number, 0.50);
        CYouKnow device(sampleRate);
        renderBatch(device);
        const auto invalid = change("/custom_properties", "calibration",
                                    Kind::Number, nan, 0);
        assertFinite(renderBatch(device, &invalid, 1));
        assert(Device::engineParameters(device).calibration == 1.0f);
        const auto valid = change("/custom_properties", "calibration",
                                  Kind::Number, 0.25, 0);
        renderBatch(device, &valid, 1);
        // The 30 ms exponential glide snaps exactly once within 1e-4.
        for (int batch = 0; batch < static_cast<int>(0.5 * sampleRate / 64.0); ++batch)
            assertFinite(renderBatch(device));
        assert(Device::engineParameters(device).calibration == 0.5f);
        assert(Access::parameters(Device::engine(device)).calibration == 0.5f);
    }

    // Reason's global tuning is ignored while nonfinite, then honoured again.
    {
        configureCVHost();
        CYouKnow device(sampleRate);
        for (const double tune : { nan, infinity, 30.0, -infinity, -20.0 })
        {
            masterTune = tune;
            assertFinite(renderBatch(device));
            const float expected = std::isfinite(tune) ? static_cast<float>(tune) : 0.0f;
            assert(Device::engineParameters(device).masterTuneCents == expected);
        }
        masterTune = 0.0;
    }

    // A nonfinite audio-reset counter is not a reset request, in particular
    // not one repeated on every batch; a later finite change still resets.
    {
        configureAttackHost();
        CYouKnow device(sampleRate);
        auto& engine = Device::engine(device);
        const auto on = noteDiff(60, 100, 0);
        renderBatch(device, &on, 1);
        for (const double counter : { nan, infinity, -infinity })
        {
            resetCounter = counter;
            for (int batch = 0; batch < 4; ++batch)
                assertFinite(renderBatch(device));
            assert(Device::midiHeldCount(device, 60) == 1);
            assert(Access::heldCount(engine, 60) == 1);
            assert(engine.getActiveVoiceCount() == 1);
        }
        resetCounter = 7.0;
        renderBatch(device);
        assert(Device::midiHeldCount(device, 60) == 0);
        assert(Access::heldCount(engine, 60) == 0);
        resetCounter = 0.0;
    }
}

// --- Output cabling ----------------------------------------------------------
// Reason reports each audio jack's cable through its connected property. With
// both jacks cabled the pair passes through as rendered; with one jack cabled
// that jack alone carries the L/MONO fold of both channels (their mean,
// YouKnow.cpp kMonoJackFoldGain) and the other is left unwritten; with none
// the pair is written as before. Cabling is read from the restore snapshot and
// from notified diffs at any frame, and a change applies to its whole batch.
void checkOutputCabling()
{
    constexpr int kBatches = 40;
    const auto cable = [](bool left, bool right) {
        set("/audio_outputs/left", "connected", Kind::Boolean, left ? 1.0 : 0.0);
        set("/audio_outputs/right", "connected", Kind::Boolean, right ? 1.0 : 0.0);
    };
    struct Rendered
    {
        Batch audio;
        bool left;
        bool right;
    };
    // change() writes the MOM as it builds a diff, so cabling diffs are built
    // at the batch they belong to, after the device's restore snapshot.
    using Diffs = std::vector<TJBox_PropertyDiff>;
    const auto play = [](CYouKnow& device, int extraBatch,
                         const std::function<Diffs()>& extra = {}) {
        std::vector<Rendered> out;
        for (int batch = 0; batch < kBatches; ++batch)
        {
            Diffs diffs;
            if (batch == 0)
                diffs.push_back(noteDiff(60, 100, 0));
            if (batch == extraBatch)
            {
                const Diffs added = extra();
                diffs.insert(diffs.end(), added.begin(), added.end());
            }
            const auto audio = renderBatch(
                device, diffs.empty() ? nullptr : diffs.data(),
                static_cast<TJBox_UInt32>(diffs.size()));
            out.push_back({ audio, wroteLeft, wroteRight });
        }
        return out;
    };
    const auto fold = [](const Batch& batch) {
        std::array<float, 64> mono {};
        for (std::size_t frame = 0; frame < mono.size(); ++frame)
            mono[frame] = 0.5f * (batch.left[frame] + batch.right[frame]);
        return mono;
    };

    // Reference: both jacks cabled at restore. Chorus I keeps the channels
    // different, so a fold is distinguishable from either channel alone.
    configureCVHost();
    set("/custom_properties", "chorus", Kind::Number, 1.0);
    cable(true, true);
    CYouKnow stereo(sampleRate);
    const auto reference = play(stereo, -1);
    bool channelsDiffer = false, wrote = false;
    for (const auto& batch : reference)
    {
        assert(batch.left == batch.right);
        wrote = wrote || batch.left;
        channelsDiffer = channelsDiffer || batch.audio.left != batch.audio.right;
    }
    assert(wrote && channelsDiffer);

    // One jack from the restore snapshot: that jack carries the fold.
    for (const bool leftOnly : { true, false })
    {
        cable(leftOnly, !leftOnly);
        CYouKnow single(sampleRate);
        const auto rendered = play(single, -1);
        for (std::size_t batch = 0; batch < rendered.size(); ++batch)
        {
            const auto& expected = reference[batch];
            const auto& actual = rendered[batch];
            assert(actual.left == (expected.left && leftOnly));
            assert(actual.right == (expected.right && !leftOnly));
            if (!expected.left)
                continue;
            const auto& carried = leftOnly ? actual.audio.left : actual.audio.right;
            assert(carried == fold(expected.audio));
        }
    }

    // No jack at all: unchanged, both channels written as rendered.
    cable(false, false);
    CYouKnow none(sampleRate);
    const auto unplugged = play(none, -1);
    for (std::size_t batch = 0; batch < unplugged.size(); ++batch)
    {
        assert(unplugged[batch].left == reference[batch].left);
        assert(unplugged[batch].right == reference[batch].right);
        assert(unplugged[batch].audio.left == reference[batch].audio.left);
        assert(unplugged[batch].audio.right == reference[batch].audio.right);
    }

    // A cable pulled mid-note, notified at a late frame: the fold takes that
    // whole batch, and the re-plugged pair passes through again from its own
    // batch onward. Neither notification is a control change.
    cable(true, true);
    CYouKnow live(sampleRate);
    const auto pulled = play(live, 12, [] {
        return Diffs { change("/audio_outputs/right", "connected", Kind::Boolean, 0.0, 37) };
    });
    for (std::size_t batch = 0; batch < pulled.size(); ++batch)
    {
        const auto& expected = reference[batch];
        const auto& actual = pulled[batch];
        if (batch < 12)
        {
            assert(actual.left == expected.left && actual.right == expected.right);
            assert(actual.audio.left == expected.audio.left);
            assert(actual.audio.right == expected.audio.right);
            continue;
        }
        assert(actual.left == expected.left && !actual.right);
        if (expected.left)
            assert(actual.audio.left == fold(expected.audio));
    }
    cable(true, true);
    CYouKnow restored(sampleRate);
    const auto flicker = play(restored, 7, [] {
        return Diffs {
            change("/audio_outputs/left", "connected", Kind::Boolean, 0.0, 3),
            change("/audio_outputs/left", "connected", Kind::Boolean, 1.0, 9) };
    });
    for (std::size_t batch = 0; batch < flicker.size(); ++batch)
    {
        // A pull and re-plug inside one batch leaves the final state cabled.
        assert(flicker[batch].left == reference[batch].left);
        assert(flicker[batch].right == reference[batch].right);
        assert(flicker[batch].audio.left == reference[batch].audio.left);
        assert(flicker[batch].audio.right == reference[batch].audio.right);
    }

    // Silence stays silent whatever is cabled.
    for (const auto [left, right] : { std::pair { true, false }, std::pair { false, true },
                                      std::pair { true, true }, std::pair { false, false } })
    {
        cable(left, right);
        CYouKnow idle(sampleRate);
        for (int batch = 0; batch < 8; ++batch)
        {
            renderBatch(idle);
            assert(!wroteLeft && !wroteRight);
        }
    }
    cable(false, false);
}

// --- Randomized host fuzz ----------------------------------------------------
// Seeded programs of whatever the host contract allows plus what it does not:
// hostile property values (NaN, infinities, out-of-range numbers), note diffs
// with any tag, velocity and frame index (dense on a small pitch cluster and a
// few shared frames, so equal-pitch overlaps and same-frame collisions are
// common), CV connections and values, master-tune and audio-reset requests.
// After every batch the audio must be finite and bounded without allocating,
// the MIDI hold counts must match an independent model of the boundary rule
// (per frame, releases first and excess releases pair with presses), the engine
// counts must equal those plus the monophonic CV hold, and no voice may stay
// keyed to a released pitch. The program then releases every hold one off per
// press, disconnects the gate and the pool must empty; after an audio reset
// restores sane panel values a plain note must sound again. The same seed must
// render the same audio twice.
void checkRandomizedHostFuzz(int seeds, int batches)
{
    using Access = youknow::YouKnowTestAccess;
    const char* const cvPaths[] {
        "/cv_inputs/note_cv", "/cv_inputs/gate_cv", "/cv_inputs/cutoff_cv",
        "/cv_inputs/resonance_cv", "/cv_inputs/volume_cv",
        "/cv_inputs/vca_level_cv", "/cv_inputs/sub_cv", "/cv_inputs/noise_cv" };
    const double rates[] { 22050.0, 44100.0, 48000.0, 96000.0, 192000.0 };
    constexpr float outputBound = 8.0f; // +18 dB preset trim over a hot engine
    constexpr int sharedFrames[] { 0, 17, 63, 70 };

    // std::mt19937's output is standardized but the std distributions are
    // not; drawing from raw words replays a seed on every standard library.
    const auto uniform = [](std::mt19937& rng, int low, int high) {
        const auto span = static_cast<std::uint64_t>(
            static_cast<std::int64_t>(high) - static_cast<std::int64_t>(low) + 1);
        const std::uint64_t limit = (std::uint64_t { 1 } << 32) / span * span;
        std::uint64_t word = rng();
        while (word >= limit)
            word = rng();
        return static_cast<int>(static_cast<std::int64_t>(low)
                                + static_cast<std::int64_t>(word % span));
    };
    // Uniform in [0, 1) from two words' top 53 bits.
    const auto unit = [](std::mt19937& rng) {
        const std::uint64_t high = rng() >> 5;
        const std::uint64_t low = rng() >> 6;
        return static_cast<double>((high << 26) | low) * 0x1p-53;
    };
    const auto hostile = [&uniform, &unit](std::mt19937& rng) {
        switch (uniform(rng, 0, 11))
        {
            case 0: return std::numeric_limits<double>::quiet_NaN();
            case 1: return std::numeric_limits<double>::infinity();
            case 2: return -std::numeric_limits<double>::infinity();
            case 3: return unit(rng) * 10.0 - 5.0;
            case 4: return 1.0e300;
            default: return unit(rng);
        }
    };

    float peak = 0.0f;
    long events = 0;
    for (int seed = 1; seed <= seeds; ++seed)
    {
        std::uint64_t hashes[2] {};
        for (int pass = 0; pass < 2; ++pass)
        {
            std::mt19937 rng(static_cast<std::uint32_t>(seed));
            sampleRate = rates[static_cast<std::size_t>(uniform(rng, 0, 4))];
            configureCVHost();
            CYouKnow device(sampleRate);
            auto& engine = CYouKnowTestAccess::engine(device);
            std::uint64_t hash = 14695981039346656037ull;
            std::vector<TJBox_PropertyDiff> diffs;
            std::array<int, 128> modelled {};
            double lastReset = resetCounter;

            const auto verifyHolds = [&]() {
                for (int note = 0; note < 128; ++note)
                {
                    assert(CYouKnowTestAccess::midiHeldCount(device, note)
                           == modelled[static_cast<std::size_t>(note)]);
                    const int cv = CYouKnowTestAccess::cvActive(device)
                        && CYouKnowTestAccess::lastCVNote(device) == note ? 1 : 0;
                    assert(Access::heldCount(engine, note)
                           == modelled[static_cast<std::size_t>(note)] + cv);
                }
                assert(!Access::keyedWithoutHeldKey(engine));
            };
            // The wrapper's boundary rule for one sorted batch: diffs are
            // grouped by clamped frame; within a group a pitch's count becomes
            // max(count + presses - releases, 0).
            const auto modelBatch = [&]() {
                if (resetCounter != lastReset && std::isfinite(resetCounter)
                    && resetCounter != 0.0)
                    modelled.fill(0);
                lastReset = resetCounter;
                std::size_t index = 0;
                while (index < diffs.size())
                {
                    const auto frame = std::min<int>(diffs[index].fAtFrameIndex, 63);
                    std::array<int, 128> change {};
                    for (; index < diffs.size()
                           && std::min<int>(diffs[index].fAtFrameIndex, 63) == frame; ++index)
                    {
                        const auto& diff = diffs[index];
                        if (diff.fObjectRef != objectFor("/note_states") || diff.fPropertyTag > 127)
                            continue;
                        const double velocity = decode(diff.fCurrentValue).value;
                        change[diff.fPropertyTag] +=
                            std::isfinite(velocity) && velocity > 0.0 ? 1 : -1;
                    }
                    for (int note = 0; note < 128; ++note)
                        modelled[static_cast<std::size_t>(note)] = std::max(
                            modelled[static_cast<std::size_t>(note)]
                                + change[static_cast<std::size_t>(note)], 0);
                }
            };

            for (int batch = 0; batch < batches; ++batch)
            {
                diffs.clear();
                const int count = uniform(rng, 0, 6);
                for (int event = 0; event < count; ++event)
                {
                    ++events;
                    const int frame = uniform(rng, 0, 1) == 0
                        ? sharedFrames[static_cast<std::size_t>(uniform(rng, 0, 3))]
                        : uniform(rng, 0, 70);
                    switch (uniform(rng, 0, 11))
                    {
                        case 0: case 1: case 2: case 3: case 4:
                        {
                            const int note = uniform(rng, 0, 2) == 0
                                ? uniform(rng, 0, 140) : uniform(rng, 58, 64);
                            int velocity = uniform(rng, 0, 2) == 0 ? 0 : uniform(rng, 1, 127);
                            if (uniform(rng, 0, 7) == 0)
                                velocity = uniform(rng, -20, 400);
                            auto diff = noteDiff(note, velocity, frame);
                            if (uniform(rng, 0, 15) == 0)
                                diff.fCurrentValue = encode(Kind::Number, hostile(rng));
                            diffs.push_back(diff);
                            break;
                        }
                        case 5: case 6:
                        {
                            const auto& setting = kPanel[static_cast<std::size_t>(uniform(
                                rng, 0, static_cast<int>(sizeof(kPanel) / sizeof(kPanel[0])) - 1))];
                            const double value = setting.kind == Kind::Boolean
                                ? static_cast<double>(uniform(rng, 0, 1))
                                : hostile(rng);
                            diffs.push_back(change("/custom_properties", setting.name,
                                                   setting.kind, value, frame));
                            break;
                        }
                        case 7: case 8:
                        {
                            const char* path = cvPaths[static_cast<std::size_t>(uniform(rng, 0, 7))];
                            if (uniform(rng, 0, 2) == 0)
                                diffs.push_back(change(path, "connected", Kind::Boolean,
                                                       uniform(rng, 0, 1), frame));
                            else
                                diffs.push_back(change(path, "value", Kind::Number,
                                                       hostile(rng), frame));
                            break;
                        }
                        case 9:
                            diffs.push_back(change("/custom_properties", "keyModeReassertPress",
                                                   Kind::Boolean, uniform(rng, 0, 1), frame));
                            break;
                        case 10:
                            masterTune = uniform(rng, 0, 3) == 0
                                ? hostile(rng) * 100.0
                                : unit(rng) * 200.0 - 100.0;
                            break;
                        default:
                            if (uniform(rng, 0, 7) == 0)
                                resetCounter += 1.0;
                            break;
                    }
                }
                // The SDK delivers diffs ordered by frame index.
                std::stable_sort(diffs.begin(), diffs.end(),
                    [](const TJBox_PropertyDiff& a, const TJBox_PropertyDiff& b) {
                        return a.fAtFrameIndex < b.fAtFrameIndex; });
                modelBatch();
                const Batch rendered = renderBatch(
                    device, diffs.empty() ? nullptr : diffs.data(),
                    static_cast<TJBox_UInt32>(diffs.size()));
                for (std::size_t frame = 0; frame < 64; ++frame)
                    for (const float sample : { rendered.left[frame], rendered.right[frame] })
                    {
                        assert(std::isfinite(sample));
                        assert(std::abs(sample) <= outputBound);
                        peak = std::max(peak, std::abs(sample));
                        std::uint32_t bits {};
                        std::memcpy(&bits, &sample, sizeof(bits));
                        for (int byte = 0; byte < 4; ++byte)
                        {
                            hash ^= (bits >> (8 * byte)) & 0xffu;
                            hash *= 1099511628211ull;
                        }
                    }
                verifyHolds();
            }

            // Drain: every outstanding MIDI hold released one off per press in
            // one frame, the gate disconnected, pedal up, instant release.
            diffs.clear();
            for (int note = 0; note < 128; ++note)
                for (int hold = 0; hold < modelled[static_cast<std::size_t>(note)]; ++hold)
                    diffs.push_back(noteDiff(note, 0, 0));
            diffs.push_back(change("/cv_inputs/gate_cv", "connected", Kind::Boolean, 0.0, 0));
            diffs.push_back(change("/custom_properties", "sustainPedal", Kind::Number, 0.0, 0));
            diffs.push_back(change("/custom_properties", "release", Kind::Number, 0.0, 0));
            diffs.push_back(change("/custom_properties", "decay", Kind::Number, 0.0, 0));
            diffs.push_back(change("/custom_properties", "quality", Kind::Number, 0.0, 0));
            modelBatch();
            renderBatch(device, diffs.data(), static_cast<TJBox_UInt32>(diffs.size()));
            verifyHolds();
            for (int note = 0; note < 128; ++note)
                assert(Access::heldCount(engine, note) == 0);
            assert(!CYouKnowTestAccess::cvActive(device));
            const int drainBatches = static_cast<int>(sampleRate * 3.0 / 64.0);
            for (int batch = 0; batch < drainBatches; ++batch)
                renderBatch(device);
            assert(engine.getActiveVoiceCount() == 0);
            assert(!Access::anyLatchedVoice(engine));

            // Recovery: an audio reset re-reads a sane panel; a note sounds.
            configureCVHost();
            resetCounter = lastReset + 1.0;
            renderBatch(device);
            const auto on = noteDiff(60, 110, 0);
            float recovered = 0.0f;
            for (int batch = 0; batch < static_cast<int>(sampleRate * 0.3 / 64.0); ++batch)
            {
                const auto audio = renderBatch(device, batch == 0 ? &on : nullptr, batch == 0 ? 1 : 0);
                for (const float sample : audio.left)
                    recovered = std::max(recovered, std::abs(sample));
            }
            assert(recovered > 1.0e-3f);
            const auto off = noteDiff(60, 0, 0);
            renderBatch(device, &off, 1);
            assert(Access::heldCount(engine, 60) == 0);
            resetCounter = 0.0;
            hashes[pass] = hash;
        }
        assert(hashes[0] == hashes[1]);
    }
    std::printf("host fuzz: %d seeds x %d batches, %ld events, peak %.6f\n",
                seeds, batches, events, static_cast<double>(peak));
    sampleRate = 48000.0;
    masterTune = resetCounter = 0.0;
}

int main()
{
    // See EngineRenderContract: a growth guard, not an SDK ceiling.
    static_assert(sizeof(CYouKnow) <= 96 * 1024);
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
    checkCVDroppedNoteRecovery();
    checkSameFrameCVPitchAndGate();
    checkRescanPreservesRenderedAudio();
    checkResetSnapsCalibration();
    checkSimultaneousMidiRetrigger();
    checkSimultaneousFullPoolReplacement();
    checkSameFrameMidiEdgeCounts();
    checkMidiOwnershipAndOverlap();
    checkSimultaneousMidiCVHandoff();
    checkAttackGridSampleTiming();
    checkRetriggerPedalAndGateModes();
    checkInvalidMidiNoteTags();
    checkMusicalNotePhrases();
    checkProductConfigurationMatchesSourcePlugin();
    checkNonFiniteAndOutOfRangeControls();
    checkOutputCabling();
    checkRandomizedHostFuzz(24, 400);
    std::puts("Wrapper: frame-accurate automation, MIDI/CV ownership and retriggers, attack timing, gates/reset/restore, output cabling, randomized host fuzz, and five host rates PASS");
    return 0;
}
