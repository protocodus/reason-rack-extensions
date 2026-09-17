// Engine robustness fuzz: seeded random programs of hostile control input,
// note traffic, quality changes, re-preparation and resets across host rates
// and block partitions, on both the reference engine and the shipped product
// configuration.
//
// Invariants, checked continuously:
//   - every sample is finite and bounded, and every host-facing query finite;
//   - every pitch's press count matches an independent model of the note API
//     (overlapping equal pitches, unmatched offs, zero-gap handoffs, legato
//     retargets and the global releases), and no voice stays keyed to a pitch
//     nobody holds;
//   - the same seed renders bit-identically twice.
// At the end, the program's outstanding presses are released one off per on
// (or by a global release) and the pool must empty; a plain patch and note
// must then sound again, so no hostile input can leave latent damage behind.
// This is not a sound check -- the render contracts own that.
//
//   clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
//     Tests/EngineFuzzContract.cpp DSP/YouKnowEngine.cpp \
//     DSP/YouKnowChorus.cpp DSP/YouKnowFirmwareTrace.cpp -o /tmp/youknow-engine-fuzz
//   /tmp/youknow-engine-fuzz [--seeds N] [--blocks N] [--first-seed N]
//
// Build it with -fsanitize=address,undefined as well; see Tests/README.md.
#include "../ProductConfiguration.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <random>
#include <string>

namespace youknow
{
struct YouKnowTestAccess
{
    static std::uint16_t heldCount(const YouKnowEngine& engine, int note) noexcept
    {
        return engine.heldNoteCounts_[static_cast<std::size_t>(note)];
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

namespace
{
using namespace youknow;
using Access = YouKnowTestAccess;

// Output stays inside this bound whatever the program does. The shipped bank
// peaks below 0.19 and six-note stress below 0.47; a full Unison stack at
// every extreme is louder, but nothing in the model approaches twice full scale.
constexpr float outputBound = 2.0f;
constexpr int maximumBlock = 64;

struct Failure
{
    std::string message;
};

void require(bool condition, const std::string& message)
{
    if (!condition)
        throw Failure { message };
}

// std::mt19937's output sequence is standardized; the std distributions are
// not, so programs are drawn from its raw words. A seed then replays the same
// program on every standard library, including a failure found in CI.
int uniform(std::mt19937& rng, int low, int high)
{
    const auto span = static_cast<std::uint64_t>(
        static_cast<std::int64_t>(high) - static_cast<std::int64_t>(low) + 1);
    const std::uint64_t limit = (std::uint64_t { 1 } << 32) / span * span;
    std::uint64_t word = rng();
    while (word >= limit)
        word = rng();
    return static_cast<int>(static_cast<std::int64_t>(low)
                            + static_cast<std::int64_t>(word % span));
}

// Uniform in [0, 1), exactly representable from the word's top 24 bits.
float unitFloat(std::mt19937& rng)
{
    return static_cast<float>(rng() >> 8) * (1.0f / 16777216.0f);
}

// Mostly in range; sometimes outside it, NaN, infinite, denormal or huge.
float hostileUnit(std::mt19937& rng)
{
    switch (uniform(rng, 0, 15))
    {
        case 0: return std::numeric_limits<float>::quiet_NaN();
        case 1: return std::numeric_limits<float>::infinity();
        case 2: return -std::numeric_limits<float>::infinity();
        case 3: return unitFloat(rng) * 4.0f - 2.0f;
        case 4: return std::numeric_limits<float>::max();
        case 5: return -std::numeric_limits<float>::max();
        case 6: return std::numeric_limits<float>::denorm_min();
        case 7: return -0.0f;
        default: return unitFloat(rng);
    }
}

// Enumerations normally hold a declared value, but corrupted state can hold
// any integer; sanitise() must map those to a defined mode.
template <typename Enum>
Enum anyOf(std::mt19937& rng, int maximum)
{
    if (uniform(rng, 0, 15) == 0)
        return static_cast<Enum>(uniform(rng, 0, 1) == 0
                                     ? uniform(rng, -1000, -1)
                                     : uniform(rng, maximum + 1, 1000));
    return static_cast<Enum>(uniform(rng, 0, maximum));
}

EngineParameters randomParameters(std::mt19937& rng, bool product)
{
    EngineParameters p;
    if (product)
        RackProductConfiguration::applyTo(p);
    p.lfoRate = hostileUnit(rng);
    p.lfoDelay = hostileUnit(rng);
    p.dcoLfoDepth = hostileUnit(rng);
    p.pwmDepth = hostileUnit(rng);
    p.pwmSource = anyOf<PwmSource>(rng, 1);
    p.range = anyOf<DcoRange>(rng, 2);
    p.sawEnabled = uniform(rng, 0, 1) != 0;
    p.pulseEnabled = uniform(rng, 0, 1) != 0;
    p.subLevel = hostileUnit(rng);
    p.noiseLevel = hostileUnit(rng);
    p.highPass = anyOf<HighPassMode>(rng, 3);
    p.cutoff = hostileUnit(rng);
    p.resonance = hostileUnit(rng);
    p.envPolarity = anyOf<EnvPolarity>(rng, 1);
    p.envDepth = hostileUnit(rng);
    p.vcfLfoDepth = hostileUnit(rng);
    p.keyFollow = hostileUnit(rng);
    p.vcaMode = anyOf<VcaMode>(rng, 1);
    p.vcaLevel = hostileUnit(rng);
    p.attack = hostileUnit(rng);
    p.decay = hostileUnit(rng);
    p.sustain = hostileUnit(rng);
    p.release = hostileUnit(rng);
    p.chorus = anyOf<ChorusMode>(rng, 3);
    p.keyMode = anyOf<KeyMode>(rng, 2);
    p.portamento = hostileUnit(rng);
    p.keyTranspose = uniform(rng, -40, 40);
    p.benderDcoDepth = hostileUnit(rng);
    p.benderVcfDepth = hostileUnit(rng);
    p.benderLfoDepth = hostileUnit(rng);
    p.masterTuneCents = hostileUnit(rng) * 400.0f - 200.0f;
    p.volume = hostileUnit(rng);
    p.velocityDepth = hostileUnit(rng);
    p.calibration = hostileUnit(rng) * 3.0f;
    p.aging = hostileUnit(rng);
    p.chorusNoise = hostileUnit(rng);
    p.mainNoiseLevelScale = hostileUnit(rng) * 2.0f;
    p.mainNoiseCalibrationProfile = anyOf<MainNoiseCalibrationProfile>(rng, 1);
    p.polyphony = uniform(rng, -3, 40);
    p.vcfTanhMode = anyOf<VcfTanhMode>(rng, 2);
    p.vcfFastEarlyMode = anyOf<VcfFastEarlyMode>(rng, 1);
    p.vcfSolverMode = anyOf<VcfSolverMode>(rng, 2);
    p.chorusTimingProfile = anyOf<ChorusTimingProfile>(rng, 3);
    p.resonanceCompensationShape = anyOf<ResonanceCompensationShape>(rng, 2);
    // Comparison switches: any combination must render, not only the shipped one.
    for (bool* flag : { &p.enableVcfStageOffsets, &p.enableResonanceOtaOffset,
                        &p.enableOpAmpSlewLimiting,
                        &p.enableVcfEarlyEffect, &p.enableSpatialThermalGradient,
                        &p.enablePulseOffWaveNodeCoupling, &p.enableSubHalfWaveNodeCoupling,
                        &p.enableVoiceVcaSignalSaturation, &p.enableVoiceVcaServiceGain,
                        &p.enableVoiceVcaTemperature, &p.enableCoupledVoiceVcaControl,
                        &p.enableSubDiodeControl, &p.enableSubStorageSkew,
                        &p.enableResonanceHeadroomTemperature,
                        &p.enableResonanceServiceTrim,
                        &p.enableConverterHoldDroop, &p.enableRailRipple,
                        &p.enableNoiseLevelBeforeC41,
                        &p.useCircuitDerivedNoiseLevelShape, &p.enableNarrowOneTwoChorus,
                        &p.enableChorusMuteDrive, &p.enableChorusClockMuteCircuit,
                        &p.enableChorusLineGainSpread, &p.enableChorusClockBleed,
                        &p.enableChorusHyperbolicSweep, &p.useChorusRateNoiseHypothesis,
                        &p.enableElectrolyticC14Nonlinearity, &p.enableHighPassDepartingLegTail,
                        &p.useCircuitDerivedResonanceShape, &p.useFixedVcfServiceFrequencyTrim,
                        &p.useServiced439522VcfCalibration, &p.enableDifferentialResonanceInput,
                        &p.useSoftplusVoiceVcaCompatibilityLaw, &p.enableCommonVcaNoise,
                        &p.enableCardJohnsonFloor })
        if (uniform(rng, 0, 3) == 0)
            *flag = !*flag;
    return p;
}

// A plain, audible patch for the recovery check.
EngineParameters plainParameters(bool product)
{
    EngineParameters p;
    if (product)
        RackProductConfiguration::applyTo(p);
    p.sawEnabled = true;
    p.cutoff = 1.0f;
    p.attack = 0.0f;
    p.decay = 0.0f;
    p.sustain = 1.0f;
    p.release = 0.0f;
    p.vcaLevel = 0.8f;
    p.volume = 0.8f;
    return p;
}

// Mostly playable, sometimes beyond both ends of the MIDI range.
int hostileNote(std::mt19937& rng)
{
    return uniform(rng, 0, 9) == 0 ? uniform(rng, -40, 200) : uniform(rng, 0, 127);
}

// A dense pitch cluster makes equal-pitch overlaps, adjacent semitones and
// duplicate or unmatched edges common rather than rare.
int clusteredNote(std::mt19937& rng)
{
    return uniform(rng, 0, 2) == 0 ? hostileNote(rng) : uniform(rng, 58, 64);
}

double hostileRate(std::mt19937& rng)
{
    constexpr std::array<double, 11> rates {
        0.0, -48000.0, std::numeric_limits<double>::quiet_NaN(),
        std::numeric_limits<double>::infinity(), 8000.0, 22050.0, 44100.0,
        48000.0, 88200.0, 96000.0, 192000.0,
    };
    return rates[static_cast<std::size_t>(
        uniform(rng, 0, static_cast<int>(rates.size()) - 1))];
}

struct Run
{
    std::uint64_t hash { 14695981039346656037ull };
    float peak { 0.0f };
    long events { 0 };
};

void hashSample(Run& run, float value)
{
    std::uint32_t bits {};
    std::memcpy(&bits, &value, sizeof(bits));
    for (int byte = 0; byte < 4; ++byte)
    {
        run.hash ^= (bits >> (8 * byte)) & 0xffu;
        run.hash *= 1099511628211ull;
    }
}

class Program
{
public:
    Program(std::uint32_t seed, bool product)
        : seed_(seed), product_(product), rng_(seed)
    {
    }

    Run run(int blocks)
    {
        if (product_)
            require(RackProductConfiguration::configureBeforePrepare(engine_),
                    context() + "product configuration was refused");
        // A host may prepare with nonsense before its real rate.
        if (uniform(rng_, 0, 3) == 0)
            prepare(hostileRate(rng_));
        constexpr std::array<double, 7> rates {
            8000.0, 22050.0, 44100.0, 48000.0, 88200.0, 96000.0, 192000.0 };
        prepare(rates[static_cast<std::size_t>(uniform(rng_, 0, 6))]);
        engine_.setParameters(randomParameters(rng_, product_));

        for (block_ = 0; block_ < blocks; ++block_)
        {
            const int events = uniform(rng_, 0, 4);
            for (int event = 0; event < events; ++event)
                act();
            render(uniform(rng_, 1, maximumBlock));
        }
        drain();
        recover();
        return result_;
    }

private:
    std::string context() const
    {
        return "seed " + std::to_string(seed_) + (product_ ? " (product)" : "")
            + " block " + std::to_string(block_) + ": ";
    }

    void prepare(double rate)
    {
        constexpr std::array<int, 3> factors { 1, 2, 4 };
        engine_.prepare(rate, maximumBlock,
                        factors[static_cast<std::size_t>(uniform(rng_, 0, 2))]);
        held_.fill(0); // prepare() is a cold start
        verifyCounts();
    }

    void noteOn(int note, float velocity)
    {
        engine_.noteOn(note, velocity);
        if (note >= 0 && note < 128)
        {
            auto& count = held_[static_cast<std::size_t>(note)];
            if (count < std::numeric_limits<std::uint16_t>::max())
                ++count;
        }
    }

    void noteOff(int note)
    {
        engine_.noteOff(note);
        if (note >= 0 && note < 128 && held_[static_cast<std::size_t>(note)] > 0)
            --held_[static_cast<std::size_t>(note)];
    }

    void act()
    {
        ++result_.events;
        // Presses slightly outnumber releases, and the global clears are rare,
        // so equal pitches accumulate several overlapping presses.
        const int action = uniform(rng_, 0, 99);
        if (action < 30)
        {
            noteOn(clusteredNote(rng_), hostileUnit(rng_));
            verifyCounts();
            return;
        }
        if (action < 52)
        {
            noteOff(clusteredNote(rng_));
            verifyCounts();
            return;
        }
        switch (action < 58 ? 9 : action < 88 ? action - 48 : 99)
        {
            case 9:
            {
                // Zero-gap handoff: release a pitch and press another (or the
                // same) one with no render between them.
                const int from = clusteredNote(rng_);
                noteOff(from);
                noteOn(uniform(rng_, 0, 1) == 0 ? from : clusteredNote(rng_),
                       hostileUnit(rng_));
                break;
            }
            case 10: case 11: case 12:
                engine_.setSustainPedal(uniform(rng_, 0, 1) != 0);
                break;
            case 13: case 14: case 15:
                engine_.setPitchBend(hostileUnit(rng_) * 2.0f - 1.0f);
                break;
            case 16: case 17:
                engine_.setModWheel(hostileUnit(rng_));
                break;
            case 18: case 19: case 20: case 21: case 22: case 23:
                engine_.setParameters(randomParameters(rng_, product_));
                break;
            case 24: case 25:
                (void) engine_.setOversamplingFactor(uniform(rng_, -1, 9));
                break;
            case 26:
                engine_.reset();
                held_.fill(0);
                break;
            case 27:
                engine_.releaseAllNotes();
                held_.fill(0);
                break;
            case 28:
                engine_.allNotesOff();
                held_.fill(0);
                break;
            case 29: case 30: case 31:
            {
                const int from = clusteredNote(rng_);
                const int to = clusteredNote(rng_);
                if (engine_.retargetHeldNoteLegato(from, to) && from != to)
                {
                    require(held_[static_cast<std::size_t>(from)] == 1
                                && held_[static_cast<std::size_t>(to)] == 0,
                            context() + "a legato retarget moved an ambiguous press");
                    held_[static_cast<std::size_t>(from)] = 0;
                    held_[static_cast<std::size_t>(to)] = 1;
                }
                break;
            }
            case 32: engine_.reassertKeyMode(); break;
            case 33: case 34: case 35:
            {
                const int note = hostileNote(rng_);
                const bool modelled = note >= 0 && note < 128
                    && held_[static_cast<std::size_t>(note)] > 0;
                require(engine_.isNoteHeld(note) == modelled,
                        context() + "isNoteHeld disagrees with the press model");
                break;
            }
            case 36:
            {
                // Before the first note this selects the initial grid. A call
                // that changes the running grid resets, clearing every press;
                // one that leaves it unchanged must keep them.
                const int factor = engine_.getOversamplingFactor();
                engine_.setInitialOversamplingFactor(uniform(rng_, -1, 9));
                if (engine_.getOversamplingFactor() != factor)
                    held_.fill(0);
                break;
            }
            case 37:
                prepare(hostileRate(rng_));
                break;
            default:
                break; // a quiet interval is the common case in a host too
        }
        verifyCounts();
    }

    void verifyCounts()
    {
        for (int note = 0; note < 128; ++note)
        {
            const auto modelled = held_[static_cast<std::size_t>(note)];
            require(Access::heldCount(engine_, note) == modelled,
                    context() + "pitch " + std::to_string(note) + " holds "
                        + std::to_string(Access::heldCount(engine_, note))
                        + " presses, model " + std::to_string(modelled));
        }
    }

    void render(int count)
    {
        std::array<float, maximumBlock> left {};
        std::array<float, maximumBlock> right {};
        left.fill(std::numeric_limits<float>::quiet_NaN());
        right.fill(std::numeric_limits<float>::quiet_NaN());
        engine_.process(left.data(), right.data(), count);
        for (int frame = 0; frame < count; ++frame)
            for (const float sample : { left[static_cast<std::size_t>(frame)],
                                        right[static_cast<std::size_t>(frame)] })
            {
                require(std::isfinite(sample), context() + "nonfinite output");
                require(std::abs(sample) <= outputBound,
                        context() + "output " + std::to_string(sample)
                            + " beyond the bound");
                result_.peak = std::max(result_.peak, std::abs(sample));
                hashSample(result_, sample);
            }
        for (const float query : { engine_.getDisplayEnvelope(), engine_.getDisplayLfo(),
                                   engine_.getDisplayTemperatureC(),
                                   engine_.getDisplayRailDroopVolts() })
            require(std::isfinite(query), context() + "nonfinite display query");
        require(engine_.getActiveVoiceCount() >= 0
                    && engine_.getActiveVoiceCount() <= YouKnowEngine::maxVoices,
                context() + "active voice count outside the pool");
        require(engine_.getProcessingLatencySamples() == 41,
                context() + "declared latency moved");
        require(!Access::keyedWithoutHeldKey(engine_),
                context() + "a voice stayed keyed to a released pitch");
    }

    // Every outstanding press released, the pedal up and an instant release:
    // the pool must empty. Half the seeds balance each press with its own off,
    // which proves the counts; the rest use a global release.
    void drain()
    {
        auto parameters = randomParameters(rng_, product_);
        parameters.release = 0.0f;
        parameters.decay = 0.0f;
        engine_.setParameters(parameters);
        engine_.setSustainPedal(false);
        if (seed_ % 4 < 2)
        {
            for (int note = 0; note < 128; ++note)
                while (held_[static_cast<std::size_t>(note)] > 0)
                    noteOff(note);
            verifyCounts();
        }
        else
        {
            engine_.releaseAllNotes();
            held_.fill(0);
        }
        (void) engine_.setOversamplingFactor(1);
        const int blocks = static_cast<int>(engine_.getSampleRate() * 3.0 / maximumBlock);
        for (int block = 0; block < blocks; ++block)
            render(maximumBlock);
        require(engine_.getActiveVoiceCount() == 0,
                context() + "a voice stayed active after every press was released");
        for (int note = -1; note <= 128; ++note)
            require(!engine_.isNoteHeld(note), context() + "a pitch still reads held");
    }

    // No hostile program may leave latent damage: a plain patch must sound.
    void recover()
    {
        engine_.setParameters(plainParameters(product_));
        engine_.setPitchBend(0.0f);
        engine_.setModWheel(0.0f);
        const float programPeak = result_.peak;
        result_.peak = 0.0f;
        noteOn(60, 1.0f);
        const int blocks = static_cast<int>(engine_.getSampleRate() * 0.5 / maximumBlock);
        for (int block = 0; block < blocks; ++block)
            render(maximumBlock);
        require(result_.peak > 1.0e-3f,
                context() + "a plain note stayed silent after the program");
        noteOff(60);
        for (int block = 0; block < 6 * blocks; ++block)
            render(maximumBlock);
        require(engine_.getActiveVoiceCount() == 0,
                context() + "the recovery note did not release");
        result_.peak = std::max(programPeak, result_.peak);
    }

    std::uint32_t seed_;
    bool product_;
    std::mt19937 rng_;
    YouKnowEngine engine_;
    std::array<std::uint16_t, 128> held_ {};
    Run result_;
    int block_ { 0 };
};
} // namespace

int main(int argc, char** argv)
{
    int seeds = 48;
    int blocks = 600;
    int firstSeed = 1;
    for (int index = 1; index + 1 < argc; index += 2)
    {
        const int value = std::max(1, std::atoi(argv[index + 1]));
        if (std::strcmp(argv[index], "--seeds") == 0)
            seeds = value;
        else if (std::strcmp(argv[index], "--blocks") == 0)
            blocks = value;
        else if (std::strcmp(argv[index], "--first-seed") == 0)
            firstSeed = value;
    }
    try
    {
        float peak = 0.0f;
        long events = 0;
        for (int seed = firstSeed; seed < firstSeed + seeds; ++seed)
        {
            const bool product = (seed % 2) == 0;
            // A program owns a complete engine; keep it off the stack.
            const auto first = std::make_unique<Program>(
                static_cast<std::uint32_t>(seed), product);
            const Run a = first->run(blocks);
            const auto second = std::make_unique<Program>(
                static_cast<std::uint32_t>(seed), product);
            const Run b = second->run(blocks);
            require(a.hash == b.hash,
                    "seed " + std::to_string(seed) + " did not render deterministically");
            peak = std::max(peak, a.peak);
            events += a.events;
        }
        std::printf("engine fuzz: %d seeds x %d blocks, %ld events, peak %.6f; "
                    "finite, bounded, deterministic, exact press counts, "
                    "no stuck voices, recovered\n",
                    seeds, blocks, events, static_cast<double>(peak));
        return 0;
    }
    catch (const Failure& failure)
    {
        std::fprintf(stderr, "FAIL: %s\n", failure.message.c_str());
        return 1;
    }
}
