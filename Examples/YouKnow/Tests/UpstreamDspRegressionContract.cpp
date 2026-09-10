// Focused regressions from protocodus/virtual-instrument-youknow c9d3c57.
// These pin the changed circuit/firmware behavior in the C++17 Rack port.
// Test-only vectors and allocations do not enter the shipped DSP.
#include "../DSP/YouKnowEngine.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace youknow
{
struct YouKnowTestAccess
{
    static float chorusWetGain(const Chorus& chorus) noexcept
    {
        return chorus.wetGain_;
    }

    static void armFadeOut(YouKnowEngine& engine, int factor) noexcept
    {
        engine.oversamplingRequested_ = factor;
        engine.oversamplingIdleSamples_ = engine.oversamplingQuietSamples_;
        engine.rateTransition_ = YouKnowEngine::RateTransition::FadingOut;
        engine.rateTransitionGain_ = 1.0f;
    }

    static int cardIndex(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].cardIndex;
    }

    static constexpr int correctionHalfWidth() noexcept
    {
        return YouKnowEngine::correctionHalfWidth;
    }

    static float cutoffTarget(
        const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)]
            .cutoffCountsTarget;
    }

    static float dcoRenderScale(const YouKnowEngine& engine,
                                int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].dco.renderScale;
    }

    static int latencyPadSamples(const YouKnowEngine& engine) noexcept
    {
        return engine.latencyPadSamples_;
    }

    static std::uint8_t lfoDelayByte(
        const YouKnowEngine& engine) noexcept
    {
        return engine.lfoDelayByte_;
    }

    static float mainNoiseDraw(YouKnowEngine& engine) noexcept
    {
        return engine.gaussianFromNoiseState();
    }

    static double measuredDecimatorCentre(YouKnowEngine& engine)
    {
        engine.firstDecimator_.reset();
        engine.secondDecimator_.reset();
        engine.latencyPadLeft_.fill(0.0f);
        engine.latencyPadRight_.fill(0.0f);
        engine.latencyPadWriteIndex_ = 0;
        const int factor = engine.oversampling_;
        double weighted = 0.0;
        double total = 0.0;
        for (int frame = 0; frame < 512; ++frame)
        {
            std::array<float, 4> stage {};
            if (frame == 0)
                stage[0] = 1.0f;
            float outputLeft = 0.0f;
            float outputRight = 0.0f;
            if (factor == 4)
            {
                float firstLeft = 0.0f, firstRight = 0.0f;
                float secondLeft = 0.0f, secondRight = 0.0f;
                engine.downsamplePair(engine.firstDecimator_, stage[0], stage[0],
                                      stage[1], stage[1], firstLeft, firstRight);
                engine.downsamplePair(engine.firstDecimator_, stage[2], stage[2],
                                      stage[3], stage[3], secondLeft, secondRight);
                engine.downsamplePair(engine.secondDecimator_, firstLeft,
                                      firstRight, secondLeft, secondRight,
                                      outputLeft, outputRight);
            }
            else if (factor == 2)
            {
                engine.downsamplePair(engine.firstDecimator_, stage[0], stage[0],
                                      stage[1], stage[1], outputLeft, outputRight);
            }
            else
            {
                outputLeft = stage[0];
                outputRight = stage[0];
            }
            engine.applyLatencyPad(outputLeft, outputRight);
            weighted += static_cast<double>(frame) * outputLeft;
            total += outputLeft;
        }
        return weighted / total;
    }

    static double numericalLatencyCentre(int factor) noexcept
    {
        return YouKnowEngine::totalLatencySamples(factor);
    }

    static float outputJackBlend(const YouKnowEngine& engine) noexcept
    {
        return engine.outputJackBlend_;
    }

    static void performVcfWrite(YouKnowEngine& engine, int slot,
                                const EngineParameters& parameters) noexcept
    {
        engine.performConverterWrite(
            { YouKnowEngine::ConverterDestination::Vcf, slot }, parameters);
    }

    static float pulseDuty(const YouKnowEngine& engine, int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].pulseDuty;
    }

    static float pulseLogicState(const YouKnowEngine& engine,
                                 int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)].dco.pulseState;
    }

    static float pulseThresholdVolts(const YouKnowEngine& engine,
                                     int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)]
            .pulseThresholdVolts;
    }

    static double pwmHeld(const YouKnowEngine& engine) noexcept
    {
        return engine.pwmVolts_;
    }

    static float rampCurrentScale(const YouKnowEngine& engine,
                                  int slot) noexcept
    {
        return engine.voices_[static_cast<std::size_t>(slot)]
            .rampCurrentScale;
    }

    static float rateTransitionGain(const YouKnowEngine& engine) noexcept
    {
        return engine.rateTransitionGain_;
    }

    static float rateTransitionStep(const YouKnowEngine& engine) noexcept
    {
        return engine.rateTransitionStep_;
    }

    static std::array<float, YouKnowEngine::correctionRing> renderedStepEdge(
        const YouKnowEngine& engine, float samplesAgo) noexcept
    {
        YouKnowEngine::BandlimitedTrack track;
        for (int sample = 0; sample < YouKnowEngine::correctionRing; ++sample)
            static_cast<void>(track.advance(-1.0f));
        engine.addStep(track, 2.0f, samplesAgo);
        std::array<float, YouKnowEngine::correctionRing> output {};
        for (auto& sample : output)
            sample = track.advance(1.0f);
        return output;
    }

    static std::pair<std::uint16_t, bool> runAttack(
        std::uint16_t increment, int passes) noexcept
    {
        YouKnowEngine::Envelope envelope;
        envelope.stage = YouKnowEngine::EnvelopeStage::Attack;
        envelope.level = 0;
        for (int pass = 0; pass < passes; ++pass)
            envelope.tick(increment, 0u, 0u, 0u);
        return { envelope.level,
                 envelope.stage == YouKnowEngine::EnvelopeStage::Attack };
    }

    static void setThermalWarmupSeconds(YouKnowEngine& engine,
                                        double seconds) noexcept
    {
        engine.thermalWarmupSeconds_ = seconds;
        engine.thermalWarmupFraction_ =
            1.0f - std::exp(-static_cast<float>(seconds) / 900.0f);
    }

    static std::int32_t vcfBendCountsWord(
        const YouKnowEngine& engine) noexcept
    {
        return engine.vcfBendCountsWord_;
    }

    static std::int32_t vcfLfoCountsWord(
        const YouKnowEngine& engine) noexcept
    {
        return engine.vcfLfoCountsWord_;
    }
};
} // namespace youknow

namespace
{
using namespace youknow;
constexpr int blockSize = 64;
constexpr double pi = 3.1415926535897932384626433832795;
struct Render { std::vector<float> left, right; };
void expect(bool valid, const std::string& message)
{
    if (!valid) { std::fprintf(stderr, "%s\n", message.c_str()); std::exit(1); }
}
void expectNear(double actual, double expected, double tolerance,
                const std::string& message)
{
    expect(std::isfinite(actual) && std::abs(actual - expected) <= tolerance,
           message + " (actual=" + std::to_string(actual)
               + ", expected=" + std::to_string(expected) + ")");
}
Render renderExact(YouKnowEngine& engine, int samples)
{
    Render result;
    result.left.assign(static_cast<std::size_t>(samples), 0.0f);
    result.right.assign(static_cast<std::size_t>(samples), 0.0f);
    for (int offset = 0; offset < samples; offset += blockSize)
    {
        const int count = std::min(blockSize, samples - offset);
        engine.process(result.left.data() + offset,
                       result.right.data() + offset, count);
    }
    return result;
}

double maximumDifference(const std::vector<float>& first,
                         const std::vector<float>& second)
{
    const std::size_t count = std::min(first.size(), second.size());
    double difference = 0.0;
    for (std::size_t index = 0; index < count; ++index)
        difference = std::max(
            difference,
            static_cast<double>(std::abs(first[index] - second[index])));
    return difference;
}

EngineParameters plainPatch()
{
    EngineParameters parameters;
    parameters.sawEnabled = true;
    parameters.pulseEnabled = false;
    parameters.subLevel = 0.0f;
    parameters.noiseLevel = 0.0f;
    parameters.highPass = HighPassMode::One;
    parameters.cutoff = 1.0f;
    parameters.resonance = 0.0f;
    parameters.envDepth = 0.0f;
    parameters.keyFollow = 0.0f;
    parameters.attack = 0.0f;
    parameters.decay = 1.0f;
    parameters.sustain = 1.0f;
    parameters.release = 0.0f;
    // The stored LEVEL slider is a shared post-sum trim. Byte 99 is the nearest
    // stored setting to 0 dB in the nominal jack-board/NEC solve (+0.073 dB);
    // full travel adds 4.71 dB and changes the downstream chorus drive.
    parameters.vcaLevel = 99.0f / 127.0f;
    parameters.volume = 1.0f;
    parameters.chorus = ChorusMode::Off;
    // The plain reference patch carries no character at all: no component
    // spread, no drift, and none of the inherent circuit non-linearities --
    // all of it answers to this one control.
    parameters.calibration = 0.0f;
    return parameters;
}

void testStepAtTheIntervalBoundaryIsThePreviousSamplesEdge()
{
    // eventSamplesAgo(0.0) is exactly 1.0, and three call sites pass that
    // literal: the left-boundary comparator reconciliation and the two
    // control-word sub flips. Output slot halfWidth - 1 is then the naive
    // sample sitting on the event, rendered before the event at the old
    // level, so subtracting the ideal step from it wrote h * (0.5 - 1) rather
    // than h * 0.5: a full-swing spike one sample before the edge, with the
    // edge itself continuous in samplesAgo everywhere else.
    YouKnowEngine engine;
    constexpr int slot = YouKnowTestAccess::correctionHalfWidth() - 1;
    constexpr float justInside = 1.0f - 1.0f / 1024.0f;
    const auto inside = YouKnowTestAccess::renderedStepEdge(engine, justInside);
    const auto boundary = YouKnowTestAccess::renderedStepEdge(engine, 1.0f);
    expectNear(boundary[slot], inside[slot], 0.05,
               "the step at samplesAgo 1.0 is discontinuous with 0.999 on the "
               "sample before the edge: " + std::to_string(boundary[slot])
                   + " against " + std::to_string(inside[slot]));

    // An event one whole sample ago is the previous sample's samplesAgo 0.0
    // event: the same edge, one output earlier. Every table read lands on
    // the same 1/64 grid point, so the two renders agree bit for bit.
    const auto previous = YouKnowTestAccess::renderedStepEdge(engine, 0.0f);
    bool shifted = true;
    for (std::size_t index = 0; index + 1 < previous.size(); ++index)
        shifted &= boundary[index] == previous[index + 1];
    expect(shifted,
           "the samplesAgo 1.0 edge is not the samplesAgo 0.0 edge one sample "
           "earlier");

    // Whatever the event position, the rendered edge swings no further than
    // the bandlimited step's own pre-ring, 1.177 one sample either side of
    // the edge for a -1..+1 step; 1.2 is the fence the -2.0 spike broke.
    for (const float samplesAgo : { 0.0f, 0.5f, justInside, 1.0f })
    {
        const auto edge = YouKnowTestAccess::renderedStepEdge(engine, samplesAgo);
        float peak = 0.0f;
        for (const float sample : edge)
            peak = std::max(peak, std::abs(sample));
        expect(peak < 1.2f,
               "a +2 step at samplesAgo " + std::to_string(samplesAgo)
                   + " swung to " + std::to_string(peak));
    }
}

void testReportedPulseDutyIsTheSolvedDutyAtTheTrimPoint()
{
    // ADJUSTMENT s. 10 trims CH1 to exactly 50 % with PWM at 5 and accepts
    // the other cards inside 48-52 % as they stand. updatePulseComparator
    // forms each card's threshold as the shared 6 V hold plus its own offset
    // -- above 6 V on a card with a positive ramp-current error, 6.12 V at
    // rampCurrentScale 1.02 -- and the event walk solves the crossing against
    // that threshold. pwmDutyCycle's own 6 V ceiling clamped it back and
    // reported 0.5098 for a card the render holds at 0.5000, which
    // pulseWaveNodeMean then primed C56/C50 with as 0.118 V of DC the
    // rendered comparator never carries. Meter every card's rendered duty at
    // the trim point against the duty it reports.
    constexpr double sampleRate = 192000.0;
    YouKnowEngine engine;
    engine.prepare(sampleRate, blockSize, false);
    auto parameters = plainPatch();
    parameters.calibration = 1.0f;
    parameters.sawEnabled = false;
    parameters.pulseEnabled = true;
    parameters.pwmSource = PwmSource::Manual;
    parameters.pwmDepth = 0.0f; // +6 V, the 50 % trim point
    engine.setParameters(parameters);
    constexpr std::array notes { 48, 50, 52, 53, 55, 57 };
    for (const int note : notes)
        engine.noteOn(note, 1.0f);
    renderExact(engine, static_cast<int>(sampleRate * 0.1));
    expectNear(YouKnowTestAccess::pwmHeld(engine), 6.0, 1.0e-6,
               "the PWM trim point did not hold the shared +6 V");

    // Count each comparator's high samples between its first and last rising
    // edge: 30-odd cycles at note 48, so the sample grid's edge quantisation
    // averages well below the 1e-3 the reported duty has to meet.
    struct Meter
    {
        int firstRise { -1 };
        int lastRise { -1 };
        int high { 0 };
        int highAtLastRise { 0 };
        float previous { 0.0f };
    };
    std::array<Meter, notes.size()> meters {};
    const int samples = static_cast<int>(sampleRate * 0.25);
    for (int sample = 0; sample < samples; ++sample)
    {
        for (std::size_t slot = 0; slot < meters.size(); ++slot)
        {
            auto& meter = meters[slot];
            const float state = YouKnowTestAccess::pulseLogicState(
                engine, static_cast<int>(slot));
            if (state > 0.0f && meter.previous < 0.0f)
            {
                if (meter.firstRise < 0)
                    meter.firstRise = sample;
                else
                {
                    meter.lastRise = sample;
                    meter.highAtLastRise = meter.high;
                }
            }
            if (meter.firstRise >= 0 && state > 0.0f)
                ++meter.high;
            meter.previous = state;
        }
        renderExact(engine, 1);
    }

    int liftedCards = 0;
    for (std::size_t slot = 0; slot < meters.size(); ++slot)
    {
        const auto& meter = meters[slot];
        const int index = static_cast<int>(slot);
        expect(YouKnowTestAccess::cardIndex(engine, index) == index
                   && meter.lastRise > meter.firstRise,
               "card " + std::to_string(slot) + " did not render its pulse");
        const double measured = static_cast<double>(meter.highAtLastRise)
                              / (meter.lastRise - meter.firstRise);
        const float reported = YouKnowTestAccess::pulseDuty(engine, index);
        const float threshold =
            YouKnowTestAccess::pulseThresholdVolts(engine, index);
        expectNear(reported, measured, 1.0e-3,
                   "card " + std::to_string(slot) + " reports duty "
                       + std::to_string(reported) + " at a "
                       + std::to_string(threshold) + " V threshold but "
                       + "renders " + std::to_string(measured));
        // The 6 V-ceiling law is what the report used to be. On a card whose
        // threshold sits above 6 V it misses the render by exactly the lift's
        // share of the ramp, (threshold - 6 V) / (12 V * scale): 0.0029 on
        // card 0's 6.035 V and 0.0168 on card 5's 6.204 V with the default
        // unit.
        if (threshold > 6.0f)
        {
            ++liftedCards;
            const float scale =
                YouKnowTestAccess::dcoRenderScale(engine, index)
                * YouKnowTestAccess::rampCurrentScale(engine, index);
            const float clamped = YouKnowEngine::pwmDutyCycle(threshold, scale);
            expectNear(clamped - measured, (threshold - 6.0f) / (12.0f * scale),
                       1.0e-3,
                       "card " + std::to_string(slot)
                           + " no longer exposes the 6 V hold ceiling");
        }
    }
    expect(liftedCards > 0,
           "no card's threshold sits above the 6 V hold at Unit Character 1");
}

void testVcfLfoUsesRecoveredIntegerWord()
{
    const auto word = [](std::uint8_t delay, std::uint8_t panel,
                         bool positive = true) {
        return YouKnowEngine::vcfLfoCountsWord(0x1fffu, positive, delay, panel);
    };
    expect(word(255u, 1u) == 15 && word(255u, 2u) == 47,
           "VCF-LFO panel bytes 1 and 2 lost B-2's 15 and 47-count words");
    expect(word(255u, 127u) == 4047,
           "full VCF-LFO depth left B-2's 4047-count endpoint");
    expect(word(127u, 1u) == 0 && word(128u, 1u) == 15,
           "VCF-LFO depth lost the doubled-byte times onset high-byte truncation");
    expect(word(255u, 127u, false) == -4047 && word(255u, 1u, false) == -15,
           "VCF-LFO polarity stopped signing the cutoff word");

    // Panel byte 1 against byte 0, rendered in lockstep so both engines see
    // the same accumulator on every pass. The peak word is 15 counts; on the
    // converter's 4-count grid that is +12 above and -16 below the static
    // cutoff, where the old proportional 4047/127 law gave +28 and -32.
    constexpr double sampleRate = 48000.0;
    YouKnowEngine silent;
    YouKnowEngine byteOne;
    auto parameters = plainPatch();
    parameters.cutoff = 0.5f;
    parameters.lfoRate = 1.0f;
    parameters.lfoDelay = 0.0f;
    silent.prepare(sampleRate, blockSize, false);
    silent.setParameters(parameters);
    parameters.vcfLfoDepth = 1.0f / 127.0f;
    byteOne.prepare(sampleRate, blockSize, false);
    byteOne.setParameters(parameters);
    silent.noteOn(60, 1.0f);
    byteOne.noteOn(60, 1.0f);

    std::int32_t peakWord = 0;
    float maximumRise = 0.0f;
    float maximumFall = 0.0f;
    for (int chunk = 0; chunk < 1500; ++chunk)
    {
        renderExact(silent, 32);
        renderExact(byteOne, 32);
        peakWord = std::max(
            peakWord, std::abs(YouKnowTestAccess::vcfLfoCountsWord(byteOne)));
        const float difference = YouKnowTestAccess::cutoffTarget(byteOne, 0)
                               - YouKnowTestAccess::cutoffTarget(silent, 0);
        maximumRise = std::max(maximumRise, difference);
        maximumFall = std::min(maximumFall, difference);
    }
    expect(peakWord == 15,
           "VCF-LFO panel byte 1 did not peak at B-2's 15-count word");
    expect(maximumRise == 12.0f && maximumFall == -16.0f,
           "VCF-LFO panel byte 1 did not move the cutoff by 15 counts on the "
           "converter's 4-count grid");
}

void testVcfBendUsesRecoveredIntegerWord()
{
    expect(YouKnowEngine::vcfBendCountsWord(127, 255u) == 4064
               && YouKnowEngine::vcfBendCountsWord(-127, 255u) == -4064,
           "full VCF bend left B-2's 4064-count endpoint");
    expect(YouKnowEngine::vcfBendCountsWord(1, 255u) == 47
               && YouKnowEngine::vcfBendCountsWord(-1, 255u) == -47
               && YouKnowEngine::vcfBendCountsWord(0, 255u) == 0,
           "VCF bend lost the assigner's one-sided 2|cmd|+1 byte or its rest");
    expect(YouKnowEngine::vcfBendCountsWord(127, 128u) == 2040
               && YouKnowEngine::vcfBendCountsWord(127, 0u) == 0,
           "VCF bend sensitivity stopped using the eight-bit ADC product");
    // +0.4 % of travel is inside the assigner's two-bin centre: the command
    // is zero, so neither axis moves. The old 255-step VCF magnitude read it
    // as one step and added about 16 counts.
    expect(YouKnowEngine::dcoPitchBendWordOffset(0.004f, 1.0f) == 0,
           "the bend command left the assigner's two-bin centre dead zone");

    const auto cutoffAfterBend = [](float bend) {
        YouKnowEngine engine;
        engine.prepare(192000.0, blockSize, false);
        auto parameters = plainPatch();
        parameters.cutoff = 0.5f;
        parameters.benderVcfDepth = 1.0f;
        engine.setParameters(parameters);
        engine.setPitchBend(bend);
        engine.noteOn(60, 1.0f);
        // The lever is sampled at the converter-pass boundary, not when the
        // host event happens. Construction begins on exactly that boundary.
        renderExact(engine, 1);
        YouKnowTestAccess::performVcfWrite(engine, 0, parameters);
        return std::pair {
            YouKnowTestAccess::vcfBendCountsWord(engine),
            YouKnowTestAccess::cutoffTarget(engine, 0)
        };
    };
    const auto rest = cutoffAfterBend(0.0f);
    const auto deadZone = cutoffAfterBend(0.004f);
    const auto full = cutoffAfterBend(1.0f);
    const auto fullDown = cutoffAfterBend(-1.0f);
    // Byte 64 * 128 = 8192 counts; +/-4064 lands on the 4-count grid.
    expect(rest.first == 0 && rest.second == 8192.0f,
           "the VCF bend fixture did not start from the static cutoff");
    expect(deadZone.first == 0 && deadZone.second == rest.second,
           "a bend inside the two-bin centre dead zone moved the VCF");
    expect(full.first == 4064 && full.second == 8192.0f + 4064.0f
               && fullDown.first == -4064
               && fullDown.second == 8192.0f - 4064.0f,
           "production VCF bend did not add its scan-held word to the cutoff");
}

void testPrepareSurvivesAnUnusableHostSampleRate()
{
    // Hosts do report nonsense: a rate of zero before the device is open, a
    // negative one from a mis-parsed setting, a NaN from an uninitialised
    // double. Every internal coefficient divides by this figure, so a bad one
    // must never reach the grid.
    const std::array<double, 7> hostile {
        0.0, -48000.0, std::numeric_limits<double>::quiet_NaN(),
        std::numeric_limits<double>::infinity(),
        -std::numeric_limits<double>::infinity(), 1.0,
        1.0e12
    };

    for (const double rate : hostile)
    {
        YouKnowEngine engine;
        engine.prepare(rate, blockSize, 4);
        const double running = engine.getSampleRate();
        expect(std::isfinite(running) && running >= 8000.0
                   && running <= YouKnowEngine::maximumSupportedSampleRate,
               "an unusable host rate reached the internal grid");
        // Zero, negative and non-finite reports all mean the host has no rate
        // yet; they share the 48 kHz default rather than splitting between
        // it and the 8 kHz floor. A positive finite rate is clamped instead.
        const bool unknown = !std::isfinite(rate) || rate <= 0.0;
        const double expected = unknown ? 48000.0
            : std::clamp(rate, YouKnowEngine::minimumSupportedSampleRate,
                         YouKnowEngine::maximumSupportedSampleRate);
        expect(running == expected,
               "host rate " + std::to_string(rate) + " prepared "
                   + std::to_string(running) + " Hz instead of "
                   + std::to_string(expected));
        expect(engine.getOversamplingFactor() >= 1
                   && engine.getOversamplingFactor() <= 4,
               "an unusable host rate produced an impossible quality factor");

        engine.setParameters(plainPatch());
        engine.noteOn(60, 1.0f);
        const auto rendered = renderExact(engine, 4096);
        for (std::size_t index = 0; index < rendered.left.size(); ++index)
            if (!std::isfinite(rendered.left[index])
                || !std::isfinite(rendered.right[index]))
            {
                expect(false, "an unusable host rate produced non-finite audio");
                break;
            }
    }
}

void testRateTransitionFadeReachesExactZeroOnItsScheduledSample()
{
    // process() splits a block at round(gain / step) samples so the rebuild
    // lands on the sample where the fade reaches zero. That only holds if the
    // per-sample decrement actually reaches zero there: subtracting a float
    // step 1/(0.005 fs) times leaves a crumb of about 1e-6 wherever
    // 0.005 * fs is an integer, which used to cost a second split and put the
    // rebuild one host sample late at 8, 48, 192, 384 and 768 kHz.
    for (const double sampleRate : { 8000.0, 44100.0, 48000.0, 96000.0,
                                     192000.0, 384000.0, 768000.0 })
    {
        YouKnowEngine engine;
        engine.prepare(sampleRate, blockSize, 4);
        engine.setParameters(plainPatch());
        const int deepFactor = engine.getOversamplingFactor();
        if (deepFactor == 1)
            continue;   // nothing to switch to on this host
        YouKnowTestAccess::armFadeOut(engine, 1);
        const float step = YouKnowTestAccess::rateTransitionStep(engine);
        const int scheduled = static_cast<int>(std::floor(1.0f / step + 0.5f));
        float left = 0.0f;
        float right = 0.0f;
        for (int sample = 0; sample < scheduled; ++sample)
        {
            expect(engine.getOversamplingFactor() == deepFactor,
                   "the rate changed before the fade reached zero at "
                       + std::to_string(sampleRate) + " Hz");
            engine.process(&left, &right, 1);
        }
        expect(YouKnowTestAccess::rateTransitionGain(engine) == 0.0f,
               "the fade-out did not reach exactly zero on its scheduled sample at "
                   + std::to_string(sampleRate) + " Hz (gain "
                   + std::to_string(YouKnowTestAccess::rateTransitionGain(engine))
                   + ")");
        engine.process(&left, &right, 1);
        expect(engine.getOversamplingFactor() == 1,
               "the rate did not change on the sample after the fade reached zero at "
                   + std::to_string(sampleRate) + " Hz");
    }
}

void testDecimatorGroupDelayMatchesTheLatencyFormula()
{
    // totalLatencySamples() is what the host is told and what sizes the 2x/1x
    // pads, so it has to equal the delay the decimators actually impose.
    // Measure that delay on an impulse through the shipping stage-to-host
    // reduction and compare the centroid with the formula, rung by rung. An
    // earlier formula credited each half-band stage with 47 input samples
    // where its pair read gives 46, overstating 4x by 0.75 host samples.
    for (const int factor : { 4, 2, 1 })
    {
        YouKnowEngine engine;
        engine.prepare(48000.0, blockSize, factor);
        expect(engine.getOversamplingFactor() == factor,
               "48 kHz did not run at the requested factor");
        const double measured =
            YouKnowTestAccess::measuredDecimatorCentre(engine);
        const double formula =
            YouKnowTestAccess::numericalLatencyCentre(factor)
            - static_cast<double>(YouKnowTestAccess::correctionHalfWidth())
                  / factor
            + YouKnowTestAccess::latencyPadSamples(engine);
        expect(std::abs(measured - formula) < 1.0e-6,
               "the decimator centroid at " + std::to_string(factor)
                   + "x is " + std::to_string(measured)
                   + " host samples against the formula's "
                   + std::to_string(formula));
    }
    // Every rung ends up within half a host sample of the figure the host is
    // told, and the two padded rungs land on it exactly.
    for (const int factor : { 4, 2, 1 })
    {
        YouKnowEngine engine;
        engine.prepare(48000.0, blockSize, factor);
        const int reported = engine.getProcessingLatencySamples();
        expect(reported == 41, "the reported DSP latency moved");
        const double endToEnd =
            YouKnowTestAccess::numericalLatencyCentre(factor)
            + YouKnowTestAccess::latencyPadSamples(engine);
        expect(std::abs(endToEnd - reported) <= 0.5 + 1.0e-9,
               "rung " + std::to_string(factor) + "x sits "
                   + std::to_string(endToEnd - reported)
                   + " host samples off the reported latency");
        if (factor != 4)
            expect(endToEnd == reported,
                   "the padded rung " + std::to_string(factor)
                       + "x does not land exactly on the reported latency");
    }
}

void testLfoDelayRearmsOnTheFirmwaresRunningVoiceMask()
{
    // B-2 re-arms the delay on the first voice-on that follows a pass with
    // $FF11_voiceRun clear, and voiceRun keeps a sustained voice while HOLD is
    // down (0x02f2..0x02ff, 0x030d, 0x036b). Three cases the held-key mask
    // this engine used to test cannot express.
    constexpr double sampleRate = 48000.0;
    constexpr int passSamples = static_cast<int>(sampleRate * 0.0042);
    const auto makeEngine = [](YouKnowEngine& engine) {
        engine.prepare(sampleRate, blockSize, true);
        auto parameters = plainPatch();
        parameters.lfoDelay = 0.6f;
        parameters.dcoLfoDepth = 1.0f;
        engine.setParameters(parameters);
    };
    // The fade byte only leaves zero once the holdoff has been crossed, so a
    // fully faded delay reads 255 and a re-armed one reads 0.
    const auto faded = [&](YouKnowEngine& engine) {
        return YouKnowTestAccess::lfoDelayByte(engine);
    };

    // (a) HOLD down, every key lifted: the sustained voice keeps voiceRun
    // non-zero, so the next key must not restart the delay.
    {
        YouKnowEngine engine;
        makeEngine(engine);
        engine.setSustainPedal(true);
        engine.noteOn(60, 1.0f);
        renderExact(engine, static_cast<int>(sampleRate * 5.0));
        expect(faded(engine) == 255u,
               "the delay fixture did not reach full depth before the pedal test");
        engine.noteOff(60);
        renderExact(engine, passSamples * 2);
        engine.noteOn(67, 1.0f);
        renderExact(engine, passSamples * 2);
        expect(faded(engine) == 255u,
               "a key played over HOLD-sustained voices restarted the LFO delay");

        // Pedal up, voices retired: the next key does re-arm.
        engine.noteOff(67);
        engine.setSustainPedal(false);
        renderExact(engine, static_cast<int>(sampleRate * 2.0));
        engine.noteOn(72, 1.0f);
        renderExact(engine, passSamples);
        expect(faded(engine) == 0u,
               "the delay did not re-arm once every voice had stopped running");
    }

    // (b) Solo Unison key-up with keys remaining gates all six off, so the
    // re-trigger that follows re-arms.
    {
        YouKnowEngine engine;
        engine.prepare(sampleRate, blockSize, true);
        auto parameters = plainPatch();
        parameters.lfoDelay = 0.6f;
        parameters.dcoLfoDepth = 1.0f;
        parameters.keyMode = KeyMode::Unison;
        engine.setParameters(parameters);
        engine.noteOn(60, 1.0f);
        engine.noteOn(67, 1.0f);
        renderExact(engine, static_cast<int>(sampleRate * 5.0));
        expect(faded(engine) == 255u,
               "the unison delay fixture did not reach full depth");
        engine.noteOff(67);
        renderExact(engine, passSamples * 4);
        expect(faded(engine) == 0u,
               "a Solo Unison key-up did not re-arm the LFO delay");
    }

    // (c) A seventh key still held after the six sounding ones are released:
    // voiceRun is clear even though the key table is not, so the next key
    // re-arms.
    {
        YouKnowEngine engine;
        makeEngine(engine);
        constexpr std::array sounding { 60, 62, 64, 65, 67, 69 };
        for (const int note : sounding)
            engine.noteOn(note, 1.0f);
        engine.noteOn(71, 1.0f); // dropped: the assigner has no voice left
        renderExact(engine, static_cast<int>(sampleRate * 5.0));
        expect(faded(engine) == 255u,
               "the dropped-key fixture did not reach full depth");
        for (const int note : sounding)
            engine.noteOff(note);
        renderExact(engine, static_cast<int>(sampleRate * 2.0));
        engine.noteOn(72, 1.0f);
        renderExact(engine, passSamples);
        expect(faded(engine) == 0u,
               "a key played while only a dropped key was held did not re-arm "
               "the LFO delay");
    }
}

void testAttackHandsOverOnTheOvershootingPass()
{
    // B-2 tests bits 14/15 of the sum (0x057c), so a sum that lands exactly
    // on 0x3FFF stays in attack one more pass. 0x3FFF = 3 x 43 x 127, so the
    // increments of attack bytes 100 (43) and 64 (127) divide it exactly.
    for (const std::uint16_t increment : { std::uint16_t { 43 },
                                           std::uint16_t { 127 } })
    {
        const int exactPasses = 0x3fff / increment;
        const auto atPeak =
            YouKnowTestAccess::runAttack(increment, exactPasses);
        expect(atPeak.first == 0x3fffu,
               "increment " + std::to_string(increment)
                   + " did not land exactly on the peak");
        expect(atPeak.second,
               "increment " + std::to_string(increment)
                   + " left attack on the pass that reached the peak exactly");
        const auto afterPeak =
            YouKnowTestAccess::runAttack(increment, exactPasses + 1);
        expect(afterPeak.first == 0x3fffu && !afterPeak.second,
               "increment " + std::to_string(increment)
                   + " did not hand over on the overshooting pass");
    }

    // An increment that does not divide the peak still hands over on the pass
    // that clamps, exactly as before.
    constexpr std::uint16_t increment = 42;
    constexpr int clampingPass = 0x3fff / increment + 1;
    const auto before = YouKnowTestAccess::runAttack(increment, clampingPass - 1);
    const auto after = YouKnowTestAccess::runAttack(increment, clampingPass);
    expect(before.second && !after.second && after.first == 0x3fffu,
           "a non-dividing increment did not hand over on its clamping pass");
}

void testVcaLevelGainWarmsWithTheChassis()
{
    // The common VCA's control constant is proportional to absolute
    // temperature (patchLevelGain), and the jack board follows the chassis
    // warm-up without the cards' spatial gradient. A quiet stored level
    // therefore grows towards 0 dB as the instrument warms: stored byte 0,
    // -16.32 dB at 25 C, reads -15.54 dB at the 40 C asymptote of Unit
    // Character 1. The drive is a small sub alone, so the cascade the same
    // warm-up also relaxes (dynamicOtaHeadroomVolts) stays linear to well
    // under a millidecibel and the render measures the VCA. Unit Character 0
    // holds the jack board at 25 C, so there the warm render is the cold one
    // bit for bit.
    constexpr double sampleRate = 48000.0;
    const int samples = static_cast<int>(sampleRate);
    const auto fixture = [](float calibration) {
        auto parameters = plainPatch();
        parameters.sawEnabled = false;
        parameters.subLevel = 0.1f;
        parameters.vcaLevel = 0.0f;
        parameters.calibration = calibration;
        parameters.enableSpatialThermalGradient = false;
        return parameters;
    };
    const auto renderWarmedTo = [&](float calibration, double warmupSeconds) {
        YouKnowEngine engine;
        engine.prepare(sampleRate, blockSize, true);
        engine.setParameters(fixture(calibration));
        YouKnowTestAccess::setThermalWarmupSeconds(engine, warmupSeconds);
        engine.noteOn(45, 1.0f);
        return renderExact(engine, samples);
    };
    const auto levelDb = [&](const Render& rendered) {
        const std::size_t from = rendered.left.size() / 2;
        double energy = 0.0;
        for (std::size_t index = from; index < rendered.left.size(); ++index)
            energy += static_cast<double>(rendered.left[index])
                    * rendered.left[index];
        return 10.0 * std::log10(
            energy / static_cast<double>(rendered.left.size() - from));
    };

    // A million seconds is the asymptote: 1 - exp(-1111) is exactly one.
    constexpr double asymptote = 1.0e6;
    const double cold = levelDb(renderWarmedTo(1.0f, 0.0));
    const double warm = levelDb(renderWarmedTo(1.0f, asymptote));
    expect(cold > -90.0, "fixture: the quiet sub is not above the noise floor ("
                             + std::to_string(cold) + " dBFS)");
    const double expected = 20.0 * std::log10(
        YouKnowEngine::patchLevelGain(0.0f, 40.0f)
        / YouKnowEngine::patchLevelGain(0.0f, 25.0f));
    expectNear(expected, 0.78, 0.01,
               "fixture: the law does not put +0.78 dB on stored byte 0 at "
               "40 C");
    expectNear(warm - cold, expected, 0.02,
               "a quiet VCA LEVEL does not grow by the warm control constant "
               "between t = 0 and the warm-up asymptote");

    const auto nominalCold = renderWarmedTo(0.0f, 0.0);
    const auto nominalWarm = renderWarmedTo(0.0f, asymptote);
    expect(maximumDifference(nominalCold.left, nominalWarm.left) == 0.0,
           "Unit Character 0 let the chassis warm-up reach the VCA LEVEL");
}

void testOutputJackPoleRollsOffTheTopOfTheBandAtHighHostRates()
{
    // R64/R65 with C22/C21 follow the coupling and the wiper noise at the
    // host rate (outputJackCornerHz). Everything ahead of the VOLUME wiper is
    // the same at two shaft positions -- the pot is passive, and the coupling
    // corner it also moves (1.5-1.8 Hz) is flat at 1 kHz to 1e-5 dB -- so
    // between two renders only the pot's gain, a scalar, and this pole's
    // corner differ. The 20th harmonic of a B5 saw against its fundamental,
    // one position against the other, is therefore the pole's own transfer
    // ratio and nothing else, rendered through the shipping path. The
    // 46.15 kHz and 33.32 kHz corners only tell apart at a high host rate:
    // at 192 kHz they are 0.57 dB apart at 19.8 kHz, while at 48 kHz both
    // blends sit within 0.04 dB of transparent, which is the numerical
    // limitation the engine's comment states.
    constexpr double hostRate = 192000.0;
    constexpr int midiNote = 83; // B5, 987.8 Hz; harmonic 20 at 19.76 kHz
    constexpr int harmonic = 20;
    const int samples = static_cast<int>(hostRate);
    const std::size_t analysisFrom = static_cast<std::size_t>(samples / 2);

    struct Rendered
    {
        std::vector<float> left;
        float blend;
    };
    const auto renderAt = [&](float volume) {
        YouKnowEngine engine;
        engine.prepare(hostRate, blockSize, true);
        auto parameters = plainPatch();
        parameters.volume = volume;
        engine.setParameters(parameters);
        engine.noteOn(midiNote, 1.0f);
        auto rendered = renderExact(engine, samples);
        return Rendered { std::move(rendered.left),
                          YouKnowTestAccess::outputJackBlend(engine) };
    };
    const auto full = renderAt(1.0f);
    const auto half = renderAt(0.5f);

    // Hann-windowed magnitude at one frequency over the settled second half.
    // A fixed-frequency window is linear in the signal, so the ratio between
    // the two renders does not depend on how exactly the bin sits on the
    // harmonic; the search below only keeps it inside the main lobe.
    const auto magnitudeAt = [&](const std::vector<float>& signal,
                                 double frequency) {
        const std::size_t count = signal.size() - analysisFrom;
        std::complex<double> sum { 0.0, 0.0 };
        for (std::size_t index = 0; index < count; ++index)
        {
            const double window = 0.5 - 0.5 * std::cos(
                2.0 * pi * static_cast<double>(index)
                / static_cast<double>(count));
            const double phase = -2.0 * pi * frequency
                               * static_cast<double>(index) / hostRate;
            sum += window * static_cast<double>(signal[analysisFrom + index])
                 * std::polar(1.0, phase);
        }
        return std::abs(sum);
    };
    const auto peakNear = [&](const std::vector<float>& signal, double centre,
                              double halfSpan, double step) {
        double best = centre;
        double bestMagnitude = -1.0;
        for (double frequency = centre - halfSpan; frequency <= centre + halfSpan;
             frequency += step)
        {
            const double magnitude = magnitudeAt(signal, frequency);
            if (magnitude > bestMagnitude)
            {
                bestMagnitude = magnitude;
                best = frequency;
            }
        }
        return best;
    };
    const double nominal = 440.0 * std::pow(2.0, (midiNote - 69) / 12.0);
    const double fundamental =
        peakNear(full.left, nominal, 0.02 * nominal, 0.25);
    const double top = peakNear(full.left, harmonic * fundamental, 6.0, 0.25);
    const auto ratioDb = [&](const std::vector<float>& signal) {
        return 20.0 * std::log10(magnitudeAt(signal, top)
                                 / magnitudeAt(signal, fundamental));
    };
    const double measured = ratioDb(full.left) - ratioDb(half.left);

    // |b / (1 - (1 - b) z^-1)| of the blend at a frequency.
    const auto blendMagnitudeDb = [](double blend, double frequency,
                                     double rate) {
        const double pole = 1.0 - blend;
        const double omega = 2.0 * pi * frequency / rate;
        return 10.0 * std::log10(
            blend * blend / (1.0 - 2.0 * pole * std::cos(omega) + pole * pole));
    };
    const auto analyticBlend = [](float volume, double rate) {
        return 1.0 - std::exp(-2.0 * pi
                              * YouKnowEngine::outputJackCornerHz(volume)
                              / rate);
    };
    expectNear(full.blend, analyticBlend(1.0f, hostRate), 1.0e-6,
               "the full-volume jack blend is not 1 - exp(-2 pi fc / fs) at "
               "a 192 kHz host");
    expectNear(half.blend, analyticBlend(0.5f, hostRate), 1.0e-6,
               "the half-volume jack blend is not 1 - exp(-2 pi fc / fs) at "
               "a 192 kHz host");
    const double expected =
        (blendMagnitudeDb(full.blend, top, hostRate)
         - blendMagnitudeDb(full.blend, fundamental, hostRate))
        - (blendMagnitudeDb(half.blend, top, hostRate)
           - blendMagnitudeDb(half.blend, fundamental, hostRate));
    expect(expected > 0.4,
           "fixture: the two jack corners are not telling apart at 192 kHz ("
               + std::to_string(expected) + " dB)");
    expectNear(measured, expected, 0.05,
               "the rendered jack pole does not match its blend's analytic "
               "magnitude at a 192 kHz host");
    // The absolute figures the README quotes for the same blend.
    expectNear(blendMagnitudeDb(full.blend, 20000.0, hostRate), -0.61, 0.01,
               "a 192 kHz host does not roll off 0.61 dB at 20 kHz");
    expectNear(blendMagnitudeDb(analyticBlend(1.0f, 96000.0), 20000.0, 96000.0),
               -0.33, 0.01, "a 96 kHz host does not roll off 0.33 dB at 20 kHz");
    {
        YouKnowEngine engine;
        engine.prepare(48000.0, blockSize, true);
        engine.setParameters(plainPatch());
        renderExact(engine, blockSize);
        const double blend = YouKnowTestAccess::outputJackBlend(engine);
        expectNear(blend, analyticBlend(1.0f, 48000.0), 1.0e-6,
                   "the jack blend at a 48 kHz host is not the matched-Z "
                   "blend of its above-Nyquist corner");
        expectNear(blendMagnitudeDb(blend, 20000.0, 48000.0), -0.04, 0.01,
                   "a 48 kHz host is not nearly transparent at 20 kHz");
    }
}

void testMainNoiseSourceIsGaussianAcrossQualityRungs()
{
    // Tr21's avalanche junction sums many carrier events per sample, so its
    // statistics are Gaussian; the generator has to be too, at the uniform
    // draw's 1/sqrt(3) RMS so no level coordinate moves. First the raw draw:
    // zero mean, that RMS, zero excess kurtosis, bounded at six sigma.
    {
        YouKnowEngine engine;
        engine.prepare(48000.0, blockSize, true);
        constexpr int draws = 1 << 20;
        double sum = 0.0, square = 0.0, fourth = 0.0, peak = 0.0;
        for (int index = 0; index < draws; ++index)
        {
            const double value = YouKnowTestAccess::mainNoiseDraw(engine);
            sum += value;
            square += value * value;
            fourth += value * value * value * value;
            peak = std::max(peak, std::abs(value));
        }
        const double mean = sum / draws;
        const double variance = square / draws - mean * mean;
        const double excessKurtosis = fourth / draws / (variance * variance) - 3.0;
        expectNear(mean, 0.0, 0.005, "the main-noise draw is biased");
        expectNear(std::sqrt(variance), 1.0 / std::sqrt(3.0), 0.005,
                   "the main-noise draw does not keep the uniform's RMS");
        expectNear(excessKurtosis, 0.0, 0.05,
                   "the main-noise draw is not Gaussian (excess kurtosis "
                       + std::to_string(excessKurtosis) + ")");
        expect(peak <= 6.0 / std::sqrt(3.0) + 1.0e-6,
               "the main-noise draw exceeded its six-sigma bound");
    }

    // Then the shaped rail through the whole instrument: the crest factor
    // and kurtosis at the output must no longer depend on the quality rung,
    // where the uniform source read 3.1 at 44.1 kHz/1x against 4.35 at
    // 192 kHz/4x for the same RMS.
    const auto statisticsAt = [](double sampleRate, bool oversampled) {
        YouKnowEngine engine;
        engine.prepare(sampleRate, blockSize, oversampled);
        auto parameters = plainPatch();
        parameters.calibration = 0.0f;
        parameters.sawEnabled = false;
        parameters.pulseEnabled = false;
        parameters.subLevel = 0.0f;
        parameters.noiseLevel = 1.0f;
        parameters.cutoff = YouKnowEngine::panelPositionForCutoff(2000.0f);
        parameters.resonance = 0.0f;
        parameters.vcaMode = VcaMode::Gate;
        engine.setParameters(parameters);
        engine.noteOn(60, 1.0f);
        const auto rendered = renderExact(
            engine, static_cast<int>(sampleRate * 3.0));
        const std::size_t from = rendered.left.size() / 6;
        double square = 0.0, fourth = 0.0, peak = 0.0;
        for (std::size_t index = from; index < rendered.left.size(); ++index)
        {
            const double value = rendered.left[index];
            square += value * value;
            fourth += value * value * value * value;
            peak = std::max(peak, std::abs(value));
        }
        const double count = static_cast<double>(rendered.left.size() - from);
        const double variance = square / count;
        return std::pair { fourth / count / (variance * variance) - 3.0,
                           peak / std::sqrt(variance) };
    };
    const auto coarse = statisticsAt(44100.0, false);
    const auto fine = statisticsAt(192000.0, true);
    expectNear(coarse.first, fine.first, 0.15,
               "the output's excess kurtosis depends on the quality rung ("
                   + std::to_string(coarse.first) + " at 44.1 kHz/1x, "
                   + std::to_string(fine.first) + " at 192 kHz/4x)");
    expectNear(20.0 * std::log10(coarse.second / fine.second), 0.0, 0.75,
               "the output's crest factor depends on the quality rung ("
                   + std::to_string(coarse.second) + " against "
                   + std::to_string(fine.second) + ")");
}

void testOutputJackPoleFollowsTheWiperSourceResistance()
{
    // Service Notes p. 15: each selector wiper reaches its jack through
    // 2.2 kOhm (R64 into JA2, R65 into JA1) with 1 nF (C22, C21) from the
    // jack node to ground. With the jack open, the pole's resistance is that
    // 2.2 kOhm plus the wiper's own Thevenin resistance -- R54/R57 plus the
    // unused track, in parallel with the loaded lower track -- solved here
    // independently of the engine's shared wiper network.
    constexpr double pot = 10000.0;
    constexpr double series = 1500.0;
    constexpr double selector = 41300.0;
    constexpr double headphone = 101000.0;
    constexpr double load = selector * headphone / (selector + headphone);
    constexpr double jackSeries = 2200.0;
    constexpr double jackCapacitance = 1.0e-9;
    const auto reference = [=](double position) {
        const double upper = series + (1.0 - position) * pot;
        const double lower = position * pot;
        const double loadedLower =
            lower > 0.0 ? lower * load / (lower + load) : 0.0;
        const double wiper = loadedLower > 0.0
            ? upper * loadedLower / (upper + loadedLower) : 0.0;
        return 1.0 / (2.0 * pi * jackCapacitance * (jackSeries + wiper));
    };
    for (const double position : { 0.0, 0.25, 0.5, 0.75, 1.0 })
        expectNear(YouKnowEngine::outputJackCornerHz(
                       static_cast<float>(position)),
                   reference(position), 1.0,
                   "the jack pole does not follow the wiper's source "
                   "resistance at shaft position "
                       + std::to_string(position));

    // The corners the README quotes -- 1.249 kOhm of wiper at full volume,
    // 2.578 kOhm at half, 2.396 kOhm at three quarters -- and the roll-off
    // they put on the top of the band with the jack open.
    const double full = YouKnowEngine::outputJackCornerHz(1.0f);
    const double half = YouKnowEngine::outputJackCornerHz(0.5f);
    expectNear(full, 46150.0, 10.0, "the full-volume jack corner is not 46.15 kHz");
    expectNear(half, 33316.0, 10.0, "the half-volume jack corner is not 33.32 kHz");
    expectNear(YouKnowEngine::outputJackCornerHz(0.75f), 34635.0, 10.0,
               "the three-quarter-volume jack corner is not 34.63 kHz");
    const auto rollOffDb = [](double corner, double frequency) {
        const double ratio = frequency / corner;
        return -10.0 * std::log10(1.0 + ratio * ratio);
    };
    expectNear(rollOffDb(full, 10000.0), -0.20, 0.01,
               "full volume does not roll off 0.20 dB at 10 kHz");
    expectNear(rollOffDb(full, 20000.0), -0.75, 0.01,
               "full volume does not roll off 0.75 dB at 20 kHz");
    expectNear(rollOffDb(half, 10000.0), -0.37, 0.01,
               "half volume does not roll off 0.37 dB at 10 kHz");
    expectNear(rollOffDb(half, 20000.0), -1.34, 0.01,
               "half volume does not roll off 1.34 dB at 20 kHz");
}

void testCommonVcaControlConstantIsProportionalToAbsoluteTemperature()
{
    // NEC p. 257 specifies -5.9 mV/dB at Ta = 25 C, and p. 260's gain-vs-
    // control graph draws the -25/25/75 C lines fanning about 0 dB: the
    // translinear gain cell's two thermal voltages per decibel, so the
    // constant scales with absolute temperature and a stored level's
    // decibels shrink by 298.15 K / T as the jack board warms.
    constexpr double boltzmann = 1.380649e-23;
    constexpr double electronCharge = 1.602176634e-19;
    const double twoThermalVoltsPerDecibel =
        2.0 * (boltzmann * 298.15 / electronCharge) * std::log(10.0) / 20.0;
    expectNear(twoThermalVoltsPerDecibel, 5.9e-3, 0.02e-3,
               "two thermal voltages per decibel at 25 C is not NEC's "
               "5.9 mV/dB");

    // The one-argument law is the 25 C law, bit for bit.
    for (int storedByte = 0; storedByte <= 127; ++storedByte)
    {
        const float position = static_cast<float>(storedByte) / 127.0f;
        expect(YouKnowEngine::patchLevelGain(position)
                   == YouKnowEngine::patchLevelGain(position, 25.0f),
               "patchLevelGain at 25 C is not the data-book law bit for bit "
               "at stored byte " + std::to_string(storedByte));
    }

    // Full warm-up at Unit Character 1 is 25 + 15 C: 313.15 / 298.15.
    constexpr float warm = 40.0f;
    constexpr double warmRatio = 313.15 / 298.15;
    const auto decibels = [](double gain) { return 20.0 * std::log10(gain); };
    const auto coldDb = [&](float position) {
        return decibels(YouKnowEngine::patchLevelGain(position));
    };
    const auto warmDb = [&](float position) {
        return decibels(YouKnowEngine::patchLevelGain(position, warm));
    };
    for (const float position : { 0.0f, 0.25f, 0.5f, 0.75f, 1.0f })
        expectNear(warmDb(position), coldDb(position) / warmRatio, 1.0e-4,
                   "the warm law is not the cold decibels over 313.15/298.15 "
                   "at position " + std::to_string(position));
    expectNear(coldDb(0.0f), -16.32, 0.01, "stored byte 0 is not -16.3 dB cold");
    expectNear(warmDb(0.0f), -15.54, 0.01,
               "stored byte 0 does not read -15.5 dB at full warm-up");
    expectNear(warmDb(0.0f) - coldDb(0.0f), 0.78, 0.01,
               "stored byte 0 does not gain 0.78 dB at full warm-up");
    expectNear(coldDb(1.0f), 4.71, 0.01, "full travel is not +4.7 dB cold");
    expectNear(warmDb(1.0f), 4.48, 0.01,
               "full travel does not read +4.48 dB at full warm-up");

    // The gain is monotone in position, so bisect the cold law for the
    // position reading -10 dB and the position where Vc = 0: the first warms
    // to -9.52 dB, the second is 0 dB at every temperature.
    const auto bisect = [](auto belowTarget) {
        double low = 0.0;
        double high = 1.0;
        for (int step = 0; step < 60; ++step)
        {
            const double middle = 0.5 * (low + high);
            if (belowTarget(static_cast<float>(middle)))
                low = middle;
            else
                high = middle;
        }
        return static_cast<float>(0.5 * (low + high));
    };
    const float minusTen = bisect([&](float position) {
        return coldDb(position) < -10.0;
    });
    expectNear(coldDb(minusTen), -10.0, 1.0e-3, "fixture: -10 dB cold");
    expectNear(warmDb(minusTen), -9.52, 0.01,
               "a -10 dB stored level does not read -9.52 dB at full warm-up");
    const float unity = bisect([](float position) {
        return YouKnowEngine::commonVcaControlVolts(position) > 0.0f;
    });
    expectNear(coldDb(unity), 0.0, 1.0e-3, "fixture: Vc = 0 is not 0 dB cold");
    expectNear(warmDb(unity), 0.0, 1.0e-3,
               "0 dB moved with temperature, but Vc = 0 is 0 dB at any T");
    expectNear(warmDb(unity) - coldDb(unity), 0.0, 1.0e-5,
               "temperature moved the 0 dB point");
}
void testWarmOutputIsIndependentOfBlockPartition()
{
    // Jack-board temperature belongs to the converter pass. Sampling it at
    // callback entry made identical event streams depend on Reason's splits.
    for (const int factor : { 1, 2, 4 })
    {
        for (const double warmup : { 0.0, 450.0, 900.0 })
        {
            YouKnowEngine regular;
            YouKnowEngine partitioned;
            auto parameters = plainPatch();
            parameters.calibration = 1.5f;
            parameters.vcaLevel = 0.1f;
            parameters.noiseLevel = 0.2f;
            for (auto* engine : { &regular, &partitioned })
            {
                engine->prepare(48000.0, blockSize, factor);
                engine->setParameters(parameters);
                YouKnowTestAccess::setThermalWarmupSeconds(*engine, warmup);
                engine->noteOn(60, 1.0f);
            }
            constexpr int samples = 4096;
            const auto reference = renderExact(regular, samples);
            Render result;
            result.left.resize(samples);
            result.right.resize(samples);
            constexpr std::array<int, 7> splits { 1, 17, 63, 2, 31, 64, 7 };
            int offset = 0;
            std::size_t index = 0;
            while (offset < samples)
            {
                const int count = std::min(splits[index++ % splits.size()],
                                           samples - offset);
                partitioned.process(result.left.data() + offset,
                                     result.right.data() + offset, count);
                offset += count;
            }
            expect(reference.left == result.left && reference.right == result.right,
                   "warm output changed with callback partition at factor "
                       + std::to_string(factor) + ", warmup "
                       + std::to_string(warmup));
        }
    }
}

void testChorusSettlesWithoutHostDenormalPolicy()
{
    for (const float rate : { 48000.0f, 192000.0f })
    {
        for (const bool muteDrive : { false, true })
        {
            Chorus chorus;
            chorus.prepare(rate);
            float left {}, right {};
            const auto run = [&](ChorusMode mode, float seconds) {
                for (int sample = 0; sample < static_cast<int>(rate * seconds);
                     ++sample)
                    chorus.process(0.0f, mode, 0.0f, left, right,
                                   false, false, 1.0f, false, true,
                                   muteDrive, false);
            };
            run(ChorusMode::One, 0.02f);
            expect(!chorus.processBypassedWhenSettled(0.0f, left, right),
                   "chorus bypass engaged while wet return was open");
            run(ChorusMode::Off, 1.0f);
            expect(YouKnowTestAccess::chorusWetGain(chorus) == 0.0f
                       && chorus.processBypassedWhenSettled(0.0f, left, right),
                   "chorus did not settle to exact zero without host FTZ");
        }
    }
}
} // namespace

int main()
{
    testStepAtTheIntervalBoundaryIsThePreviousSamplesEdge();
    testReportedPulseDutyIsTheSolvedDutyAtTheTrimPoint();
    testVcfLfoUsesRecoveredIntegerWord();
    testVcfBendUsesRecoveredIntegerWord();
    testPrepareSurvivesAnUnusableHostSampleRate();
    testRateTransitionFadeReachesExactZeroOnItsScheduledSample();
    testDecimatorGroupDelayMatchesTheLatencyFormula();
    testLfoDelayRearmsOnTheFirmwaresRunningVoiceMask();
    testAttackHandsOverOnTheOvershootingPass();
    testVcaLevelGainWarmsWithTheChassis();
    testOutputJackPoleRollsOffTheTopOfTheBandAtHighHostRates();
    testMainNoiseSourceIsGaussianAcrossQualityRungs();
    testOutputJackPoleFollowsTheWiperSourceResistance();
    testCommonVcaControlConstantIsProportionalToAbsoluteTemperature();
    testWarmOutputIsIndependentOfBlockPartition();
    testChorusSettlesWithoutHostDenormalPolicy();
    std::puts("upstream firmware/circuit regressions passed (16 groups)");
}
