#include "../YouKnow.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>

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

    static int keyedVoiceCount(const YouKnowEngine& engine,
                               int note) noexcept
    {
        int count = 0;
        for (const auto& voice : engine.voices_)
            if (voice.active && voice.keyDown && voice.rootMidi == note)
                ++count;
        return count;
    }

    static int rootMidi(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].rootMidi;
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

    static float targetMidi(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].targetMidi;
    }

    static bool dcoResetPending(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].dcoResetPending;
    }

    static bool assignmentRescanPending(const YouKnowEngine& engine) noexcept
    {
        return engine.assignmentRescanPending_;
    }

    static std::uint64_t chorusSupportBuildCount(
        const YouKnowEngine& engine) noexcept
    {
        return engine.chorus_.supportBuildCount_;
    }

    static auto chorusOutputSupportTransition(float sampleRate,
                                               bool connected) noexcept
    {
        const auto support = Chorus::supportChainFor(sampleRate);
        return connected ? support.exactOutputConnected
                         : support.exactOutputMuted;
    }

    static bool freewheeling(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].freewheeling;
    }

    static bool anyFreewheeling(const YouKnowEngine& engine) noexcept
    {
        return std::any_of(engine.voices_.begin(), engine.voices_.end(),
                           [](const auto& voice) { return voice.freewheeling; });
    }

    static bool chorusFlushPending(const YouKnowEngine& engine) noexcept
    {
        return engine.chorus_.wetPathFlushPending_;
    }

    static std::uint32_t divider(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].dco.divider;
    }
};
} // namespace youknow

namespace
{
constexpr int blockSize = 64;
constexpr std::array<int, 6> notes { 36, 48, 55, 60, 64, 67 };

struct Result
{
    std::uint64_t hash { 14695981039346656037ull };
    float peak {};
    int voices {};
    int factor {};
};

void hashFloat(std::uint64_t& hash, float value) noexcept
{
    std::uint32_t bits {};
    std::memcpy(&bits, &value, sizeof(bits));
    for (unsigned int shift = 0; shift < 32; shift += 8)
    {
        hash ^= static_cast<std::uint8_t>(bits >> shift);
        hash *= 1099511628211ull;
    }
}

youknow::EngineParameters fullPathPatch()
{
    youknow::EngineParameters parameters;
    parameters.sawEnabled = true;
    parameters.pulseEnabled = true;
    parameters.subLevel = 0.5f;
    parameters.noiseLevel = 0.1f;
    parameters.cutoff = 1.0f;
    parameters.resonance = 0.7f;
    parameters.envDepth = 0.0f;
    parameters.keyFollow = 0.0f;
    parameters.attack = 0.0f;
    parameters.decay = 1.0f;
    parameters.sustain = 1.0f;
    parameters.release = 0.0f;
    parameters.vcaLevel = 99.0f / 127.0f;
    parameters.volume = 1.0f;
    parameters.chorus = youknow::ChorusMode::Two;
    parameters.chorusNoise = 1.0f;
    parameters.polyphony = 6;
    return parameters;
}

bool renderTwice(
    int oversamplingFactor, Result& result,
    youknow::VcfTanhMode tanhMode = youknow::VcfTanhMode::Exact,
    youknow::VcfFastEarlyMode earlyMode =
        youknow::VcfFastEarlyMode::Hermite,
    youknow::VcfSolverMode solverMode =
        youknow::VcfSolverMode::MersonHalfSteps,
    youknow::ChorusMode chorusMode = youknow::ChorusMode::Two)
{
    youknow::YouKnowEngine first;
    youknow::YouKnowEngine second;
    first.prepare(48000.0, blockSize, oversamplingFactor);
    second.prepare(48000.0, blockSize, oversamplingFactor);
    auto parameters = fullPathPatch();
    parameters.vcfTanhMode = tanhMode;
    parameters.vcfFastEarlyMode = earlyMode;
    parameters.vcfSolverMode = solverMode;
    parameters.chorus = chorusMode;
    first.setParameters(parameters);
    second.setParameters(parameters);
    for (const int note : notes)
    {
        first.noteOn(note, 1.0f);
        second.noteOn(note, 1.0f);
    }

    std::array<float, blockSize> firstLeft {};
    std::array<float, blockSize> firstRight {};
    std::array<float, blockSize> secondLeft {};
    std::array<float, blockSize> secondRight {};
    for (int block = 0; block < 128; ++block)
    {
        first.process(firstLeft.data(), firstRight.data(), blockSize);
        second.process(secondLeft.data(), secondRight.data(), blockSize);
        if (std::memcmp(firstLeft.data(), secondLeft.data(), sizeof(firstLeft)) != 0
            || std::memcmp(firstRight.data(), secondRight.data(), sizeof(firstRight)) != 0)
            return false;

        for (int frame = 0; frame < blockSize; ++frame)
        {
            const float left = firstLeft[static_cast<std::size_t>(frame)];
            const float right = firstRight[static_cast<std::size_t>(frame)];
            if (!std::isfinite(left) || !std::isfinite(right))
                return false;
            result.peak = std::max(result.peak,
                                   std::max(std::abs(left), std::abs(right)));
            hashFloat(result.hash, left);
            hashFloat(result.hash, right);
        }
    }

    result.voices = first.getActiveVoiceCount();
    result.factor = first.getOversamplingFactor();
    return true;
}

void renderBlocks(youknow::YouKnowEngine& engine, int count)
{
    std::array<float, blockSize> left {};
    std::array<float, blockSize> right {};
    for (int block = 0; block < count; ++block)
        engine.process(left.data(), right.data(), blockSize);
}

bool rendersFiniteAudio(youknow::YouKnowEngine& engine, int count)
{
    std::array<float, blockSize> left {};
    std::array<float, blockSize> right {};
    float peak = 0.0f;
    for (int block = 0; block < count; ++block)
    {
        engine.process(left.data(), right.data(), blockSize);
        for (int frame = 0; frame < blockSize; ++frame)
        {
            const float leftSample = left[static_cast<std::size_t>(frame)];
            const float rightSample = right[static_cast<std::size_t>(frame)];
            if (!std::isfinite(leftSample) || !std::isfinite(rightSample))
                return false;
            peak = std::max(peak,
                            std::max(std::abs(leftSample),
                                     std::abs(rightSample)));
        }
    }
    return peak > 0.0f;
}

bool testInitialQualitySelection()
{
    using Access = youknow::YouKnowTestAccess;
    using Engine = youknow::YouKnowEngine;

    for (const int factor : std::array<int, 2> { 1, 4 })
    {
        Engine restored;
        restored.prepare(48000.0, blockSize, 2);
        const auto supportBuilds = Access::chorusSupportBuildCount(restored);
        restored.setInitialOversamplingFactor(factor);

        Engine direct;
        direct.prepare(48000.0, blockSize, factor);
        if (restored.getOversamplingFactor() != factor
            || restored.getRequestedOversamplingFactor() != factor
            || Access::chorusSupportBuildCount(restored) != supportBuilds)
            return false;

        const auto parameters = fullPathPatch();
        restored.setParameters(parameters);
        direct.setParameters(parameters);
        for (const int note : notes)
        {
            restored.noteOn(note, 1.0f);
            direct.noteOn(note, 1.0f);
        }

        std::array<float, blockSize> restoredLeft {};
        std::array<float, blockSize> restoredRight {};
        std::array<float, blockSize> directLeft {};
        std::array<float, blockSize> directRight {};
        for (int block = 0; block < 32; ++block)
        {
            restored.process(restoredLeft.data(), restoredRight.data(), blockSize);
            direct.process(directLeft.data(), directRight.data(), blockSize);
            if (restoredLeft != directLeft || restoredRight != directRight)
                return false;
        }
    }
    return true;
}

bool testNewParameterEqualityFields()
{
    const youknow::EngineParameters base;

    using Parameters = youknow::EngineParameters;
    constexpr bool Parameters::* switches[] {
        &Parameters::enablePulseOffWaveNodeCoupling,
        &Parameters::enableSubHalfWaveNodeCoupling,
        &Parameters::enableVoiceVcaSignalSaturation,
        &Parameters::enableNoiseLevelBeforeC41,
        &Parameters::useCircuitDerivedNoiseLevelShape,
        &Parameters::enableNarrowOneTwoChorus,
        &Parameters::enableChorusMuteDrive,
        &Parameters::enableChorusLineGainSpread,
        &Parameters::enableHighPassDepartingLegTail,
        &Parameters::enableDifferentialResonanceInput,
        &Parameters::useSoftplusVoiceVcaCompatibilityLaw,
        &Parameters::enableCommonVcaNoise,
        &Parameters::enableCardJohnsonFloor,
    };
    for (const auto field : switches)
    {
        auto changed = base;
        changed.*field = !(changed.*field);
        if (base == changed)
            return false;
    }
    auto aged = base;
    aged.aging = 1.0f;
    auto noise = base;
    noise.mainNoiseLevelScale = 1.2f;
    auto resonance = base;
    resonance.resonanceCompensationShape =
        youknow::ResonanceCompensationShape::Drawn;
    return base == base && !(base == aged) && !(base == noise)
        && !(base == resonance);
}

bool testReasonMasterTuneRange()
{
    using Engine = youknow::YouKnowEngine;
    using Access = youknow::YouKnowTestAccess;
    for (int hundredths = -5000; hundredths <= 5000; ++hundredths)
    {
        const double cents = hundredths / 100.0;
        const auto hardware = std::clamp(std::lround(cents * 2.56), -128L, 127L);
        if (Engine::masterTunePitchWordOffset(cents) != hardware)
            return false;
    }
    if (Engine::masterTunePitchWordOffset(-150.0) != -384
        || Engine::masterTunePitchWordOffset(150.0) != 383
        || Engine::masterTunePitchWordOffset(-1.0e300) != -384
        || Engine::masterTunePitchWordOffset(1.0e300) != 383)
        return false;
    for (double invalid : { std::numeric_limits<double>::quiet_NaN(),
                            std::numeric_limits<double>::infinity(),
                            -std::numeric_limits<double>::infinity() })
        if (Engine::masterTunePitchWordOffset(invalid) != 0)
            return false;

    Engine engine;
    engine.prepare(48000.0, blockSize, 1);
    auto parameters = fullPathPatch();
    parameters.calibration = 0.0f;
    parameters.polyphony = 1;
    parameters.chorus = youknow::ChorusMode::Off;
    parameters.masterTuneCents = -150.0f;
    engine.setParameters(parameters);
    engine.noteOn(60, 1.0f);
    std::array<float, blockSize> left {};
    std::array<float, blockSize> right {};
    std::uint32_t previous = std::numeric_limits<std::uint32_t>::max();
    for (float cents : { -150.0f, -100.0f, -50.0f, 0.0f, 50.0f, 100.0f, 150.0f })
    {
        parameters.masterTuneCents = cents;
        engine.setParameters(parameters);
        for (int block = 0; block < 32; ++block)
            engine.process(left.data(), right.data(), blockSize);
        const int slot = Access::keyedSlotFor(engine, 60);
        if (slot < 0)
            return false;
        const auto divider = Access::divider(engine, slot);
        if (divider >= previous)
            return false;
        previous = divider;
    }
    return true;
}

bool testAgingPath()
{
    using Engine = youknow::YouKnowEngine;

    Engine fresh;
    Engine aged;
    Engine agedRepeat;
    for (Engine* engine : { &fresh, &aged, &agedRepeat })
        engine->prepare(48000.0, blockSize, 1);

    auto freshParameters = fullPathPatch();
    freshParameters.aging = 0.0f;
    auto agedParameters = freshParameters;
    agedParameters.aging = 1.0f;
    fresh.setParameters(freshParameters);
    aged.setParameters(agedParameters);
    agedRepeat.setParameters(agedParameters);
    for (const int note : notes)
    {
        fresh.noteOn(note, 1.0f);
        aged.noteOn(note, 1.0f);
        agedRepeat.noteOn(note, 1.0f);
    }

    std::array<float, blockSize> freshLeft {};
    std::array<float, blockSize> freshRight {};
    std::array<float, blockSize> agedLeft {};
    std::array<float, blockSize> agedRight {};
    std::array<float, blockSize> repeatLeft {};
    std::array<float, blockSize> repeatRight {};
    bool differsFromFresh = false;
    for (int block = 0; block < 128; ++block)
    {
        fresh.process(freshLeft.data(), freshRight.data(), blockSize);
        aged.process(agedLeft.data(), agedRight.data(), blockSize);
        agedRepeat.process(repeatLeft.data(), repeatRight.data(), blockSize);
        if (agedLeft != repeatLeft || agedRight != repeatRight)
            return false;
        differsFromFresh = differsFromFresh
            || freshLeft != agedLeft || freshRight != agedRight;
        for (int frame = 0; frame < blockSize; ++frame)
            if (!std::isfinite(agedLeft[static_cast<std::size_t>(frame)])
                || !std::isfinite(agedRight[static_cast<std::size_t>(frame)]))
                return false;
    }
    return differsFromFresh;
}

bool testLegatoRetarget()
{
    using Access = youknow::YouKnowTestAccess;
    using Engine = youknow::YouKnowEngine;

    auto parameters = fullPathPatch();
    parameters.chorus = youknow::ChorusMode::Off;
    parameters.chorusNoise = 0.0f;
    parameters.portamento = 0.60f;
    parameters.decay = 0.0f;
    parameters.sustain = 0.25f;
    parameters.polyphony = 2;

    Engine engine;
    engine.prepare(48000.0, blockSize, 2);
    engine.setParameters(parameters);
    engine.noteOn(60, 0.75f);

    const int slot = Access::keyedSlotFor(engine, 60);
    if (slot < 0)
        return false;
    for (int block = 0; block < 128
         && Access::envelopeStage(engine, slot) != 3; ++block)
        renderBlocks(engine, 1);
    if (Access::envelopeStage(engine, slot) != 3)
        return false;

    const int stage = Access::envelopeStage(engine, slot);
    const auto level = Access::envelopeLevel(engine, slot);
    const float current = Access::currentMidi(engine, slot);
    const bool resetPending = Access::dcoResetPending(engine, slot);
    if (!engine.retargetHeldNoteLegato(60, 67)
        || Access::heldCount(engine, 60) != 0
        || Access::heldCount(engine, 67) != 1
        || Access::keyedSlotFor(engine, 67) != slot
        || Access::rootMidi(engine, slot) != 67
        || Access::envelopeStage(engine, slot) != stage
        || Access::envelopeLevel(engine, slot) != level
        || Access::currentMidi(engine, slot) != current
        || Access::dcoResetPending(engine, slot) != resetPending)
        return false;

    // Pitch is consumed on the converter scan, while the held envelope and
    // free-running oscillator remain continuous.
    for (int block = 0; block < 16
         && Access::targetMidi(engine, slot) != 67.0f; ++block)
        renderBlocks(engine, 1);
    if (Access::targetMidi(engine, slot) != 67.0f
        || Access::currentMidi(engine, slot) <= current
        || Access::currentMidi(engine, slot) > 67.0f
        || Access::envelopeStage(engine, slot) != stage
        || Access::envelopeLevel(engine, slot) != level)
        return false;

    // Repeated-source and destination collisions are deliberately ambiguous;
    // a failed request must not mutate either keyboard bit.
    Engine duplicate;
    duplicate.prepare(48000.0, blockSize, 2);
    duplicate.setParameters(parameters);
    duplicate.noteOn(60, 1.0f);
    duplicate.noteOn(60, 0.5f);
    if (duplicate.retargetHeldNoteLegato(60, 67)
        || Access::heldCount(duplicate, 60) != 2
        || Access::heldCount(duplicate, 67) != 0)
        return false;

    Engine collision;
    collision.prepare(48000.0, blockSize, 2);
    collision.setParameters(parameters);
    collision.noteOn(60, 1.0f);
    collision.noteOn(67, 1.0f);
    if (collision.retargetHeldNoteLegato(60, 67)
        || Access::heldCount(collision, 60) != 1
        || Access::heldCount(collision, 67) != 1)
        return false;

    parameters.keyMode = youknow::KeyMode::Unison;
    Engine unisonSingle;
    unisonSingle.prepare(48000.0, blockSize, 2);
    unisonSingle.setParameters(parameters);
    for (int block = 0; block < 16
         && Access::assignmentRescanPending(unisonSingle); ++block)
        renderBlocks(unisonSingle, 1);
    unisonSingle.noteOn(60, 1.0f);
    const int unisonVoices = Access::keyedVoiceCount(unisonSingle, 60);
    if (unisonVoices != parameters.polyphony
        || !unisonSingle.retargetHeldNoteLegato(60, 67)
        || Access::heldCount(unisonSingle, 60) != 0
        || Access::heldCount(unisonSingle, 67) != 1
        || Access::keyedVoiceCount(unisonSingle, 60) != 0
        || Access::keyedVoiceCount(unisonSingle, 67) != unisonVoices)
        return false;

    Engine unison;
    unison.prepare(48000.0, blockSize, 2);
    unison.setParameters(parameters);
    for (int block = 0; block < 16
         && Access::assignmentRescanPending(unison); ++block)
        renderBlocks(unison, 1);
    unison.noteOn(60, 1.0f);
    unison.noteOn(64, 1.0f);
    if (unison.retargetHeldNoteLegato(64, 67)
        || Access::heldCount(unison, 60) != 1
        || Access::heldCount(unison, 64) != 1
        || Access::heldCount(unison, 67) != 0)
        return false;

    return true;
}

bool testFastIdlePolicies()
{
    using Access = youknow::YouKnowTestAccess;
    using Engine = youknow::YouKnowEngine;

    auto parameters = fullPathPatch();
    parameters.chorus = youknow::ChorusMode::Off;
    parameters.chorusNoise = 0.0f;
    parameters.vcfTanhMode = youknow::VcfTanhMode::PolyZoned;
    parameters.vcfFastEarlyMode = youknow::VcfFastEarlyMode::Cubic;
    parameters.vcfSolverMode = youknow::VcfSolverMode::Rk4Single;

    Engine fast;
    fast.prepare(48000.0, blockSize, 1);
    fast.setParameters(parameters);
    renderBlocks(fast, 1);
    if (!Access::anyFreewheeling(fast)
        || !Access::chorusFlushPending(fast))
        return false;

    fast.noteOn(60, 1.0f);
    const int firstSlot = Access::keyedSlotFor(fast, 60);
    if (firstSlot < 0 || Access::freewheeling(fast, firstSlot))
        return false;

    parameters.chorus = youknow::ChorusMode::Two;
    fast.setParameters(parameters);
    if (!rendersFiniteAudio(fast, 32)
        || Access::chorusFlushPending(fast))
        return false;

    fast.noteOff(60);
    for (int block = 0; block < 128
         && !Access::freewheeling(fast, firstSlot); ++block)
        renderBlocks(fast, 1);
    if (!Access::freewheeling(fast, firstSlot))
        return false;

    fast.noteOn(60, 1.0f);
    if (Access::keyedSlotFor(fast, 60) != firstSlot
        || Access::freewheeling(fast, firstSlot)
        || !rendersFiniteAudio(fast, 32))
        return false;

    fast.noteOff(60);
    renderBlocks(fast, 128);
    fast.noteOn(67, 1.0f);
    const int differentSlot = Access::keyedSlotFor(fast, 67);
    if (differentSlot < 0 || Access::freewheeling(fast, differentSlot)
        || !rendersFiniteAudio(fast, 32))
        return false;

    Engine resetCase;
    resetCase.prepare(48000.0, blockSize, 1);
    parameters.chorus = youknow::ChorusMode::Off;
    resetCase.setParameters(parameters);
    renderBlocks(resetCase, 1);
    if (!Access::chorusFlushPending(resetCase))
        return false;
    resetCase.reset();
    if (Access::chorusFlushPending(resetCase))
        return false;

    parameters.vcfTanhMode = youknow::VcfTanhMode::Exact;
    parameters.vcfFastEarlyMode = youknow::VcfFastEarlyMode::Hermite;
    parameters.chorus = youknow::ChorusMode::Off;
    Engine exact;
    exact.prepare(48000.0, blockSize, 1);
    exact.setParameters(parameters);
    renderBlocks(exact, 1);
    return !Access::anyFreewheeling(exact)
        && !Access::chorusFlushPending(exact);
}

bool testLoadedBbdOutputTopology()
{
    using State = std::array<double, 6>;
    constexpr double pi = 3.14159265358979323846;
    constexpr float sourceEstimate = 3700.0f;
    constexpr float tapSeries = 3300.0f;
    constexpr float tapReturn = 47000.0f;
    constexpr float tapShunt = 2.2e-9f;
    constexpr float parallelDrive = 0.5f * (sourceEstimate + tapSeries);
    constexpr float tapNodeResistance =
        parallelDrive * tapReturn / (parallelDrive + tapReturn);
    constexpr double isolatedCorner = static_cast<double>(
        1.0f / (2.0f * static_cast<float>(pi)
                * tapNodeResistance * tapShunt));
    if (std::abs(isolatedCorner - 22208.689) > 0.01)
        return false;

    constexpr double frequency = 10000.0;
    constexpr double series = 22000.0;
    constexpr double feedback = 820.0e-12;
    constexpr double shunt = 680.0e-12;
    const std::complex<double> s(0.0, 2.0 * pi * frequency);
    const double source = 0.5 * (3700.0 + 3300.0);
    const double sourceConductance = 1.0 / source + 1.0 / 47000.0;
    const double seriesConductance = 1.0 / series;
    const auto denominator = 1.0 + s * shunt * (2.0 * series)
        + s * s * series * series * feedback * shunt;
    const auto numeratorShape = 1.0 + s * series * shunt;
    const auto loaded = sourceConductance
        / ((s * 2.2e-9 + sourceConductance + seriesConductance) * denominator
           - seriesConductance * numeratorShape);
    const double tapResistance = source * 47000.0 / (source + 47000.0);
    const auto separable = 1.0
        / ((1.0 + s * tapResistance * 2.2e-9) * denominator);
    const auto relative = loaded / separable;
    if (std::abs(20.0 * std::log10(std::abs(relative)) - (-0.7883156))
            > 1.0e-5
        || std::abs(std::arg(relative) * 180.0 / pi - (-2.0290835))
            > 1.0e-5)
        return false;

    // Connect the independent component solve above to the production
    // prepared transition. A constant-input RK4 oracle avoids sharing the
    // matrix-exponential implementation under test.
    const auto transition =
        youknow::YouKnowTestAccess::chorusOutputSupportTransition(
            48000.0f, true);
    constexpr State equilibrium { 1.0, 1.0, 1.0, 1.0, 1.0, 1.0 };
    constexpr State initial { 0.03, -0.07, 0.11, -0.13, 0.17, -0.19 };
    constexpr std::array<double, 4> samples { 0.2, 0.2, 0.2, 0.2 };
    State exact {};
    for (std::size_t row = 0; row < exact.size(); ++row)
    {
        for (std::size_t column = 0; column < exact.size(); ++column)
            exact[row] += transition.stateByColumn[column][row]
                        * initial[column];
        for (std::size_t sample = 0; sample < samples.size(); ++sample)
            exact[row] += transition.driveBySample[sample][row]
                        * samples[sample];

        double equilibriumNext = 0.0;
        for (std::size_t column = 0; column < equilibrium.size(); ++column)
            equilibriumNext += transition.stateByColumn[column][row]
                             * equilibrium[column];
        for (const auto& drive : transition.driveBySample)
            equilibriumNext += drive[row];
        if (!std::isfinite(exact[row])
            || std::abs(equilibriumNext - equilibrium[row]) > 2.0e-15)
        {
            std::fprintf(stderr,
                         "loaded BBD transition equilibrium failed at row %zu: %.17g\n",
                         row, equilibriumNext - equilibrium[row]);
            return false;
        }
    }

    const double sourceG = 1.0 / source;
    const double returnG = 1.0 / 47000.0;
    const double totalG = sourceG + returnG;
    const double seriesG = 1.0 / series;
    constexpr double tapCap = static_cast<double>(2.2e-9f);
    constexpr double firstFeedback = static_cast<double>(820.0e-12f);
    constexpr double firstShunt = static_cast<double>(680.0e-12f);
    constexpr double secondFeedback = static_cast<double>(1.8e-9f);
    constexpr double secondShunt = static_cast<double>(270.0e-12f);
    constexpr float outputResistance =
        22000.0f * 39000.0f / (22000.0f + 39000.0f);
    constexpr float outputCorner = 1.0f
        / (2.0f * static_cast<float>(pi) * outputResistance * 1.0e-6f);
    const double wc = 2.0 * pi * static_cast<double>(outputCorner);
    const auto derivative = [&](const State& state) {
        State slope {};
        slope[0] = (totalG * samples[0]
                    - (totalG + seriesG) * state[0]
                    + seriesG * state[1]) / tapCap;
        slope[1] = seriesG * state[0] / firstFeedback
            + (seriesG / firstShunt
               - 2.0 * seriesG / firstFeedback) * state[1]
            + (-seriesG / firstShunt
               + seriesG / firstFeedback) * state[2];
        slope[2] = seriesG * (state[1] - state[2]) / firstShunt;
        slope[3] = seriesG * state[2] / secondFeedback
            + (seriesG / secondShunt
               - 2.0 * seriesG / secondFeedback) * state[3]
            + (-seriesG / secondShunt
               + seriesG / secondFeedback) * state[4];
        slope[4] = seriesG * (state[3] - state[4]) / secondShunt;
        slope[5] = wc * (state[4] - state[5]);
        return slope;
    };
    const auto advanced = [](const State& state, const State& slope,
                             double amount) {
        State result {};
        for (std::size_t index = 0; index < result.size(); ++index)
            result[index] = state[index] + amount * slope[index];
        return result;
    };
    State oracle = initial;
    constexpr int substeps = 4096;
    constexpr double step = 1.0 / (48000.0 * substeps);
    for (int substep = 0; substep < substeps; ++substep)
    {
        const auto k1 = derivative(oracle);
        const auto k2 = derivative(advanced(oracle, k1, 0.5 * step));
        const auto k3 = derivative(advanced(oracle, k2, 0.5 * step));
        const auto k4 = derivative(advanced(oracle, k3, step));
        for (std::size_t index = 0; index < oracle.size(); ++index)
            oracle[index] += step * (k1[index] + 2.0 * k2[index]
                                   + 2.0 * k3[index] + k4[index]) / 6.0;
    }
    double maximumError = 0.0;
    for (std::size_t index = 0; index < oracle.size(); ++index)
        maximumError = std::max(maximumError,
                                std::abs(exact[index] - oracle[index]));
    if (maximumError > 2.0e-11)
        std::fprintf(stderr,
                     "loaded BBD transition RK4 error %.17g\n",
                     maximumError);
    return maximumError <= 2.0e-11;
}
} // namespace

int main()
{
    static_assert(sizeof(youknow::YouKnowEngine) <= 64 * 1024,
                  "engine state exceeded its port memory budget");
    static_assert(sizeof(CYouKnow) <= 64 * 1024,
                  "Rack native object exceeded its port memory budget");

    Result low;
    Result balanced;
    Result high;
    Result fast;
    Result cubic;
    Result polyHermite;
    Result polyCubic;
    Result polyHigh;
    Result polyMax;
    Result oneTwo;
    const bool valid = renderTwice(1, low) && renderTwice(2, balanced)
        && renderTwice(4, high)
        && renderTwice(1, fast, youknow::VcfTanhMode::ZonedHermite,
                       youknow::VcfFastEarlyMode::Hermite,
                       youknow::VcfSolverMode::Rk4Single)
        && renderTwice(1, cubic, youknow::VcfTanhMode::ZonedHermite,
                       youknow::VcfFastEarlyMode::Cubic,
                       youknow::VcfSolverMode::Rk4Single)
        && renderTwice(1, polyHermite,
                       youknow::VcfTanhMode::PolyZoned,
                       youknow::VcfFastEarlyMode::Hermite,
                       youknow::VcfSolverMode::Rk4Single)
        && renderTwice(1, polyCubic,
                       youknow::VcfTanhMode::PolyZoned,
                       youknow::VcfFastEarlyMode::Cubic,
                       youknow::VcfSolverMode::Rk4Single)
        && renderTwice(1, polyHigh,
                       youknow::VcfTanhMode::PolyZoned,
                       youknow::VcfFastEarlyMode::Cubic,
                       youknow::VcfSolverMode::Rk4HalfSteps)
        && renderTwice(1, polyMax,
                       youknow::VcfTanhMode::PolyZoned,
                       youknow::VcfFastEarlyMode::Cubic,
                       youknow::VcfSolverMode::MersonHalfSteps)
        && renderTwice(1, oneTwo,
                       youknow::VcfTanhMode::Exact,
                       youknow::VcfFastEarlyMode::Hermite,
                       youknow::VcfSolverMode::MersonHalfSteps,
                       youknow::ChorusMode::OneTwo)
        && testNewParameterEqualityFields()
        && testReasonMasterTuneRange()
        && testAgingPath()
        && testInitialQualitySelection()
        && testLegatoRetarget()
        && testFastIdlePolicies()
        && testLoadedBbdOutputTopology()
        && low.factor == 1 && balanced.factor == 2 && high.factor == 4
        && low.voices == 6 && balanced.voices == 6 && high.voices == 6
        && low.peak > 0.0f && balanced.peak > 0.0f && high.peak > 0.0f
        && fast.peak > 0.0f && cubic.peak > 0.0f
        && polyHermite.peak > 0.0f && polyCubic.peak > 0.0f
        && polyHigh.peak > 0.0f && polyMax.peak > 0.0f
        && low.hash != balanced.hash && balanced.hash != high.hash
        && low.hash != high.hash && fast.hash != cubic.hash
        && polyHermite.hash != polyCubic.hash
        && polyCubic.hash != polyHigh.hash && polyHigh.hash != polyMax.hash
        && oneTwo.peak > 0.0f && oneTwo.hash != low.hash;
    if (!valid)
        return 1;

    std::printf("engine_bytes=%zu native_object_bytes=%zu q1=%016llx q2=%016llx "
                "q4=%016llx fast=%016llx cubic=%016llx "
                "poly=%016llx poly_cubic=%016llx poly_high=%016llx "
                "poly_max=%016llx one_two=%016llx\n",
                sizeof(youknow::YouKnowEngine),
                sizeof(CYouKnow),
                static_cast<unsigned long long>(low.hash),
                static_cast<unsigned long long>(balanced.hash),
                static_cast<unsigned long long>(high.hash),
                static_cast<unsigned long long>(fast.hash),
                static_cast<unsigned long long>(cubic.hash),
                static_cast<unsigned long long>(polyHermite.hash),
                static_cast<unsigned long long>(polyCubic.hash),
                static_cast<unsigned long long>(polyHigh.hash),
                static_cast<unsigned long long>(polyMax.hash),
                static_cast<unsigned long long>(oneTwo.hash));
    return 0;
}
