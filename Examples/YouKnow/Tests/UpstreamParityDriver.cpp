// Scalar parity driver: the same scenario set rendered through whichever
// YouKnow engine sources it is compiled against, one FNV-1a hash of every
// output sample's bits per scenario. Build it once against this port and once
// against the upstream checkout's Source/DSP with its SIMD kernels undefined,
// then diff the two logs; every line must match. Run it whenever the shared
// DSP changes.
//
//   clang++ -std=c++17 -O3 -DNDEBUG -I. Tests/UpstreamParityDriver.cpp \
//     DSP/YouKnowEngine.cpp DSP/YouKnowChorus.cpp DSP/YouKnowFirmwareTrace.cpp \
//     -o /tmp/parity-port
//   clang++ -std=c++20 -O3 -DNDEBUG -U__SSE2__ -U__AVX__ -U__AVX2__ -U__ARM_NEON \
//     -I"$UPSTREAM/Source" Tests/UpstreamParityDriver.cpp \
//     "$UPSTREAM"/Source/DSP/YouKnow{Engine,Chorus,FirmwareTrace}.cpp \
//     -o /tmp/parity-upstream
//   diff <(/tmp/parity-port) <(/tmp/parity-upstream)
//
// Only the API both engines share is used, so the Rack-only sanitising of
// out-of-range enumerations is not exercised here; the engine port contract
// covers it. The quality switch mid-run scenario changes the factor while
// voices sound, which both engines hold until the output is silent, so its
// hash equals the plain product render's by design.
#include "DSP/YouKnowEngine.h"
#include "DSP/YouKnowProductFidelity.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <functional>
#include <vector>

using namespace youknow;

namespace
{
constexpr int block = 64;
constexpr int blocks = 480;

struct Hash
{
    std::uint64_t h = 1469598103934665603ull;
    void add(float value)
    {
        std::uint32_t bits;
        std::memcpy(&bits, &value, sizeof bits);
        for (int i = 0; i < 4; ++i)
        {
            h ^= (bits >> (8 * i)) & 0xffu;
            h *= 1099511628211ull;
        }
    }
};

struct Scenario
{
    const char* name;
    double rate;
    int factor;
    bool product;
    std::function<void(EngineParameters&)> tweak;
    std::function<void(YouKnowEngine&, int)> extra; // per-block extra events
};

std::uint64_t run(const Scenario& s)
{
    YouKnowEngine engine;
    if (s.product)
    {
        (void) ProductFidelityProfile::configureBeforePrepare(engine);
        engine.selectConverterTimingProfile(
            YouKnowEngine::ConverterTimingProfile::MeasuredChartGeometry);
    }
    engine.prepare(s.rate, block, s.factor);
    EngineParameters p;
    if (s.product)
        ProductFidelityProfile::applyTo(p);
    if (s.tweak)
        s.tweak(p);
    engine.setParameters(p);

    Hash hash;
    float left[block], right[block];
    for (int b = 0; b < blocks; ++b)
    {
        switch (b)
        {
            case 0: engine.noteOn(60, 0.8f); break;
            case 40: engine.noteOn(64, 0.6f); engine.noteOn(67, 1.0f); break;
            case 100: engine.setPitchBend(0.5f); break;
            case 130: engine.setModWheel(0.7f); break;
            case 160: engine.setSustainPedal(true); break;
            case 200: engine.noteOff(60); engine.noteOff(64); break;
            case 260: engine.setPitchBend(0.0f); engine.setModWheel(0.0f); break;
            case 300: engine.setSustainPedal(false); break;
            case 330: engine.noteOn(48, 0.9f); engine.noteOff(67); break;
            case 400: engine.noteOff(48); break;
            default: break;
        }
        if (s.extra)
            s.extra(engine, b);
        engine.process(left, right, block);
        for (int i = 0; i < block; ++i)
        {
            hash.add(left[i]);
            hash.add(right[i]);
        }
    }
    return hash.h;
}
} // namespace

int main()
{
    std::vector<Scenario> scenarios;
    const auto add = [&](const char* name, double rate, int factor, bool product,
                         std::function<void(EngineParameters&)> tweak = nullptr,
                         std::function<void(YouKnowEngine&, int)> extra = nullptr)
    {
        scenarios.push_back({ name, rate, factor, product, tweak, extra });
    };
    add("reference 48k 1x", 48000.0, 1, false);
    add("reference 48k 2x", 48000.0, 2, false);
    add("reference 48k 4x", 48000.0, 4, false);
    add("reference 44.1k 1x", 44100.0, 1, false);
    add("reference 96k 1x", 96000.0, 1, false);
    add("product 48k 1x", 48000.0, 1, true);
    add("product 48k 2x", 48000.0, 2, true);
    add("product 44.1k 1x", 44100.0, 1, true);
    add("product chorus I", 48000.0, 1, true, [](EngineParameters& p) { p.chorus = ChorusMode::One; });
    add("product chorus II", 48000.0, 1, true, [](EngineParameters& p) { p.chorus = ChorusMode::Two; });
    add("product chorus I+II", 48000.0, 1, true, [](EngineParameters& p) { p.chorus = ChorusMode::OneTwo; });
    for (int profile = 0; profile < 5; ++profile)
        add("reference chorus I timing profile", 48000.0, 1, false,
            [profile](EngineParameters& p) { p.chorus = ChorusMode::One;
                p.chorusTimingProfile = static_cast<ChorusTimingProfile>(profile); });
    add("product Poly 2", 48000.0, 1, true, [](EngineParameters& p) { p.keyMode = KeyMode::Poly2; });
    add("product Unison", 48000.0, 1, true, [](EngineParameters& p) { p.keyMode = KeyMode::Unison; });
    add("product gate, inverted, PWM LFO", 48000.0, 1, true, [](EngineParameters& p) {
        p.vcaMode = VcaMode::Gate; p.envPolarity = EnvPolarity::Inverted;
        p.pwmSource = PwmSource::Lfo; p.pulseEnabled = true; p.pwmDepth = 0.7f; p.lfoRate = 0.6f; });
    for (int mode = 0; mode < 3; ++mode)
        add("product tanh mode", 48000.0, 2, true,
            [mode](EngineParameters& p) { p.vcfTanhMode = static_cast<VcfTanhMode>(mode); p.resonance = 0.8f; });
    for (int mode = 0; mode < 2; ++mode)
        add("product fast-early mode", 48000.0, 1, true,
            [mode](EngineParameters& p) { p.vcfTanhMode = static_cast<VcfTanhMode>(1);
                p.vcfFastEarlyMode = static_cast<VcfFastEarlyMode>(mode); p.resonance = 0.9f; });
    for (int mode = 0; mode < 3; ++mode)
        add("product solver mode", 48000.0, 1, true,
            [mode](EngineParameters& p) { p.vcfSolverMode = static_cast<VcfSolverMode>(mode); p.resonance = 0.95f; p.cutoff = 0.4f; });
    add("product character 0", 48000.0, 1, true, [](EngineParameters& p) { p.calibration = 0.0f; });
    add("product character 2", 48000.0, 1, true, [](EngineParameters& p) { p.calibration = 2.0f; });
    add("product aging 1", 48000.0, 1, true, [](EngineParameters& p) { p.aging = 1.0f; });
    add("product boost, 16', sub, noise", 48000.0, 1, true, [](EngineParameters& p) {
        p.highPass = HighPassMode::Boost; p.range = DcoRange::Sixteen; p.subLevel = 0.8f; p.noiseLevel = 0.5f; });
    add("product portamento unison", 48000.0, 1, true, [](EngineParameters& p) {
        p.keyMode = KeyMode::Unison; p.portamento = 0.6f; });
    add("reference droop and ripple on", 48000.0, 1, false, [](EngineParameters& p) {
        p.enableConverterHoldDroop = true; p.enableRailRipple = true; p.calibration = 1.0f; });
    add("product droop and ripple off", 48000.0, 1, true, [](EngineParameters& p) {
        p.enableConverterHoldDroop = false; p.enableRailRipple = false; });
    add("product self-oscillation", 48000.0, 1, true, [](EngineParameters& p) {
        p.resonance = 1.0f; p.keyFollow = 1.0f; p.cutoff = 0.55f; p.envDepth = 0.0f; });
    add("product reset mid-run", 48000.0, 1, true, nullptr,
        [](YouKnowEngine& e, int b) { if (b == 240) e.reset(); if (b == 250) e.noteOn(55, 0.7f); });
    add("product quality switch mid-run", 48000.0, 1, true, nullptr,
        [](YouKnowEngine& e, int b) { if (b == 240) (void) e.setOversamplingFactor(2); });
    add("product chorus noise 1", 48000.0, 1, true, [](EngineParameters& p) {
        p.chorus = ChorusMode::Two; p.chorusNoise = 1.0f; });
    add("product 16 voices cluster", 48000.0, 1, true,
        [](EngineParameters& p) { p.polyphony = 16; },
        [](YouKnowEngine& e, int b) { if (b == 20) for (int n = 50; n < 62; ++n) e.noteOn(n, 0.5f + 0.02f * n); if (b == 380) for (int n = 50; n < 62; ++n) e.noteOff(n); });
    add("product velocity depth 1", 48000.0, 1, true, [](EngineParameters& p) { p.velocityDepth = 1.0f; });
    add("product transpose and tune", 48000.0, 1, true, [](EngineParameters& p) {
        p.keyTranspose = 7; p.masterTuneCents = -33.0f; });
    add("product bender depths", 48000.0, 1, true, [](EngineParameters& p) {
        p.benderDcoDepth = 1.0f; p.benderVcfDepth = 0.8f; p.benderLfoDepth = 1.0f; });
    add("product envelope extremes", 48000.0, 1, true, [](EngineParameters& p) {
        p.attack = 0.2f; p.decay = 0.9f; p.sustain = 0.0f; p.release = 0.9f; p.envDepth = 1.0f; p.cutoff = 0.1f; });

    int index = 0;
    for (const auto& s : scenarios)
        std::printf("%02d %016llx %s\n", index++,
                    static_cast<unsigned long long>(run(s)), s.name);
    return 0;
}
