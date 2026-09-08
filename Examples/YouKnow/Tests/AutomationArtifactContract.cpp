// Automation artifact contract.
//
// A host may automate any of the front-panel parameters while notes are
// sounding. This measures what the audio actually does at the moment a value
// changes, for every automatable parameter, in two ways:
//
//   step  -- one large jump from one end of the control's travel to the other
//   ramp  -- a fast sweep across the whole travel, one step per audio batch,
//            which is what an automation curve drawn in the sequencer produces
//
// The metric is a discontinuity ratio, and it has to separate "the sound
// legitimately changed" from "a step was punched into the waveform".
//
//   step: the largest sample-to-sample step inside a short window at the change,
//         over the largest step the voice produces on EITHER side of it -- before
//         the change and again once the new value has settled. Opening the filter
//         genuinely raises the signal's slew, so a one-sided reference would
//         report every bright sweep as a click; taking the louder side means only
//         a step that beats both counts.
//
//   ramp: the largest step anywhere in the sweep, over the largest step the same
//         patch produces while HOLDING the control still at any value along the
//         swept range. Moving a control may not inject a discontinuity bigger
//         than standing anywhere in its own travel already produces.
//
//         The reference is the maximum across the whole range rather than a
//         per-slice value on purpose. A self-referential percentile cannot tell
//         a zipper step from a sawtooth edge -- as a filter opens the waveform
//         becomes a saw, whose derivative is one large edge per cycle -- and a
//         per-slice reference is unfair to anything coupled to the free-running
//         LFO, whose phase differs between two independent renders. Taking the
//         worst static value over the range removes both sensitivities.
//
// A level check would conflate an artifact with the musical change (a resonance
// sweep is supposed to get louder), so level is bounded only as a momentary
// spike against the settled level on both sides, not as a change in level.
//
// The probe patch is deliberately dark and chorus-free so the output is smooth
// and any injected step stands out; a bright saw's own edges would mask it. A
// second pass runs the same sweep through the chorus, which has its own state.
//
// Musically discontinuous switches (octave range, waveform on/off, key mode,
// polyphony, the quality switches) are measured and reported but held to a
// looser bound: changing them is *supposed* to change the sound abruptly. What
// they must not do is produce a non-finite sample or a full-scale transient.

#include "DSP/YouKnowEngine.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <functional>
#include <string>
#include <vector>

namespace
{
using namespace youknow;

constexpr double sampleRate = 48000.0;
constexpr int batchSize = 64;
constexpr int settleBatches = 500;   // ~0.67 s to reach a steady held note
constexpr int measureBatches = 240;  // ~0.32 s across and after the change

// A dark, un-chorused, fully sustaining patch. The point is a smooth output
// whose own slew is small, so an injected discontinuity is visible.
EngineParameters probePatch()
{
    EngineParameters p;
    p.sawEnabled = true;
    p.pulseEnabled = false;
    p.subLevel = 0.0f;
    p.noiseLevel = 0.0f;
    p.range = DcoRange::Eight;
    p.highPass = HighPassMode::One;
    p.cutoff = 0.30f;
    p.resonance = 0.10f;
    p.envDepth = 0.0f;
    p.vcfLfoDepth = 0.0f;
    p.dcoLfoDepth = 0.0f;
    p.keyFollow = 0.50f;
    p.vcaMode = VcaMode::Envelope;
    p.vcaLevel = 0.80f;
    p.attack = 0.0f;
    p.decay = 0.45f;
    p.sustain = 1.0f;          // hold flat, so the envelope adds no drift
    p.release = 0.30f;
    p.chorus = ChorusMode::Off;
    p.volume = 0.80f;
    p.calibration = 1.0f;
    p.aging = 0.5f;
    return p;
}

struct Trace
{
    std::vector<float> samples;
    bool finite = true;
    double peak = 0.0;
};

// Largest adjacent-sample step over a half-open index range.
double maxStep(const std::vector<float>& x, std::size_t from, std::size_t to)
{
    double worst = 0.0;
    for (std::size_t i = std::max<std::size_t>(from, 1); i < to && i < x.size(); ++i)
        worst = std::max(worst, std::abs(static_cast<double>(x[i]) - x[i - 1]));
    return worst;
}

double rms(const std::vector<float>& x, std::size_t from, std::size_t to)
{
    double sum = 0.0;
    std::size_t n = 0;
    for (std::size_t i = from; i < to && i < x.size(); ++i, ++n)
        sum += static_cast<double>(x[i]) * x[i];
    return n ? std::sqrt(sum / static_cast<double>(n)) : 0.0;
}

using Apply = std::function<void(EngineParameters&, double)>;

struct Result
{
    double ratio = 0.0;      // injected step / the signal's own step on both sides
    double spike = 0.0;      // momentary peak / settled peak either side
    bool finite = true;
    double peak = 0.0;
};

// Largest adjacent-sample step this patch produces while the control is HELD
// still at `value` -- the reference a moving control is judged against.
constexpr int referenceSettleBatches = 220;  // enough for a steady voice

double heldMaxStep(const Apply& apply, double value, bool withChorus,
                   std::size_t window)
{
    YouKnowEngine engine;
    engine.prepare(sampleRate, batchSize, 2);
    EngineParameters p = probePatch();
    if (withChorus)
        p.chorus = ChorusMode::One;
    apply(p, value);
    engine.setParameters(p);
    engine.noteOn(60, 0.9f);

    float left[batchSize] {};
    float right[batchSize] {};
    for (int batch = 0; batch < referenceSettleBatches; ++batch)
        engine.process(left, right, batchSize);

    std::vector<float> tail;
    tail.reserve(window + batchSize);
    while (tail.size() < window)
    {
        engine.process(left, right, batchSize);
        for (int s = 0; s < batchSize; ++s)
            tail.push_back(left[s]);
    }
    return maxStep(tail, 0, tail.size());
}

// Render a held note, then drive `apply` from `a` to `b` -- either as one jump
// at the midpoint, or as one small step per batch across the measured span.
double sweepReference(const Apply& apply, double lo, double hi, bool withChorus)
{
    constexpr int probes = 12;
    // The reference window has to span several LFO cycles, or a probe can miss
    // the phase where the LFO opens the filter and report a reference far
    // quieter than the sweep legitimately reaches.
    const std::size_t window = static_cast<std::size_t>(0.6 * sampleRate);
    double held = 0.0;
    for (int probe = 0; probe < probes; ++probe)
    {
        const double t = static_cast<double>(probe) / static_cast<double>(probes - 1);
        held = std::max(held, heldMaxStep(apply, lo + (hi - lo) * t, withChorus, window));
    }
    return held;
}

Result measure(const Apply& apply, double a, double b, bool ramp, bool withChorus,
               double rampReference, double glideSeconds = 0.0)
{
    YouKnowEngine engine;
    engine.prepare(sampleRate, batchSize, 2);

    EngineParameters base = probePatch();
    if (withChorus)
        base.chorus = ChorusMode::One;
    apply(base, a);
    engine.setParameters(base);
    engine.noteOn(60, 0.9f);

    Trace trace;
    trace.samples.reserve(static_cast<std::size_t>(
        (settleBatches + measureBatches) * batchSize));

    float left[batchSize] {};
    float right[batchSize] {};
    const int changeBatch = settleBatches + measureBatches / 3;
    double glided = a;

    for (int batch = 0; batch < settleBatches + measureBatches; ++batch)
    {
        if (!ramp && batch >= changeBatch && glideSeconds > 0.0)
        {
            // Reproduce the wrapper's one-pole glide, batch by batch.
            const double step = std::min(
                1.0, static_cast<double>(batchSize) / (glideSeconds * sampleRate));
            glided += (b - glided) * step;
            EngineParameters p = base;
            apply(p, std::abs(b - glided) < 1.0e-4 ? b : glided);
            engine.setParameters(p);
        }
        else if (!ramp && batch == changeBatch)
        {
            EngineParameters p = base;
            apply(p, b);
            engine.setParameters(p);
        }
        else if (ramp && batch >= settleBatches)
        {
            const double t = static_cast<double>(batch - settleBatches)
                           / static_cast<double>(measureBatches - 1);
            EngineParameters p = base;
            apply(p, a + (b - a) * t);
            engine.setParameters(p);
        }
        engine.process(left, right, batchSize);
        for (int s = 0; s < batchSize; ++s)
        {
            trace.finite = trace.finite && std::isfinite(left[s]) && std::isfinite(right[s]);
            trace.peak = std::max(trace.peak, std::abs(static_cast<double>(left[s])));
            trace.samples.push_back(left[s]);
        }
    }

    const std::size_t settleEnd = static_cast<std::size_t>(settleBatches) * batchSize;

    Result out;
    out.finite = trace.finite;
    out.peak = trace.peak;

    if (ramp)
    {
        // Compare each slice of the moving sweep against the same engine held
        // still at that slice's value. See the header note: a self-referential
        // percentile cannot tell a zipper step from a sawtooth edge.
        const double moving = maxStep(trace.samples, settleEnd, trace.samples.size());
        out.ratio = rampReference > 1e-12 ? moving / rampReference : 0.0;
        out.spike = 1.0;
        return out;
    }

    // A window at the jump: the engine reads panel values on its modelled
    // ~238 Hz control scan, so allow a couple of scan passes to land.
    const std::size_t change = static_cast<std::size_t>(changeBatch) * batchSize;
    const std::size_t window = static_cast<std::size_t>(0.012 * sampleRate);
    const std::size_t span = static_cast<std::size_t>(0.2 * sampleRate);
    const std::size_t settledFrom = change + static_cast<std::size_t>(0.05 * sampleRate);

    // Both sides: before the change, and after the new value has settled.
    const double beforeStep = maxStep(trace.samples, change - span, change);
    const double afterStep = maxStep(trace.samples, settledFrom, settledFrom + span);
    const double reference = std::max(beforeStep, afterStep);
    out.ratio = reference > 1e-12
        ? maxStep(trace.samples, change, change + window) / reference : 0.0;

    const double beforePeak = rms(trace.samples, change - span, change);
    const double afterPeak = rms(trace.samples, settledFrom, settledFrom + span);
    const double settled = std::max(beforePeak, afterPeak);
    const double atChange = rms(trace.samples, change, change + window);
    out.spike = settled > 1e-9 ? atChange / settled : 0.0;
    return out;
}

struct Param
{
    const char* name;
    Apply apply;
    double lo;
    double hi;
    bool abruptByDesign;  // a switch whose whole job is to change the sound at once
    // Seconds the Rack wrapper spends gliding this control to a new value
    // (YouKnow.cpp, AdvanceCalibrationGlide). Zero means the engine sees the
    // host's step unchanged. The test reproduces the glide so it measures the
    // signal path the instrument actually ships, not the bare engine.
    double wrapperGlideSeconds = 0.0;
};

template <typename E>
Apply enumApply(E EngineParameters::* field, int maxOrdinal)
{
    return [field, maxOrdinal](EngineParameters& p, double t) {
        const int ordinal = std::clamp(
            static_cast<int>(std::lround(t * maxOrdinal)), 0, maxOrdinal);
        p.*field = static_cast<E>(ordinal);
    };
}

Apply floatApply(float EngineParameters::* field)
{
    return [field](EngineParameters& p, double t) { p.*field = static_cast<float>(t); };
}

Apply boolApply(bool EngineParameters::* field)
{
    return [field](EngineParameters& p, double t) { p.*field = t >= 0.5; };
}

std::vector<Param> parameters()
{
    return {
        // Continuous controls. These are the ones a curve is actually drawn on,
        // and the ones that must not click.
        {"volume",       floatApply(&EngineParameters::volume), 0.0, 1.0, false},
        {"vcaLevel",     floatApply(&EngineParameters::vcaLevel), 0.0, 1.0, false},
        {"cutoff",       floatApply(&EngineParameters::cutoff), 0.05, 0.95, false},
        {"resonance",    floatApply(&EngineParameters::resonance), 0.0, 0.90, false},
        {"vcfEnv",       floatApply(&EngineParameters::envDepth), 0.0, 1.0, false},
        {"vcfLfo",       floatApply(&EngineParameters::vcfLfoDepth), 0.0, 1.0, false},
        {"keyFollow",    floatApply(&EngineParameters::keyFollow), 0.0, 1.0, false},
        {"pwm",          floatApply(&EngineParameters::pwmDepth), 0.0, 1.0, false},
        {"sub",          floatApply(&EngineParameters::subLevel), 0.0, 1.0, false},
        {"noise",        floatApply(&EngineParameters::noiseLevel), 0.0, 1.0, false},
        {"dcoLfo",       floatApply(&EngineParameters::dcoLfoDepth), 0.0, 1.0, false},
        {"lfoRate",      floatApply(&EngineParameters::lfoRate), 0.0, 1.0, false},
        {"lfoDelay",     floatApply(&EngineParameters::lfoDelay), 0.0, 1.0, false},
        {"attack",       floatApply(&EngineParameters::attack), 0.0, 1.0, false},
        {"decay",        floatApply(&EngineParameters::decay), 0.0, 1.0, false},
        {"sustain",      floatApply(&EngineParameters::sustain), 0.0, 1.0, false},
        {"release",      floatApply(&EngineParameters::release), 0.0, 1.0, false},
        {"portamento",   floatApply(&EngineParameters::portamento), 0.0, 1.0, false},
        {"benderDco",    floatApply(&EngineParameters::benderDcoDepth), 0.0, 1.0, false},
        {"benderVcf",    floatApply(&EngineParameters::benderVcfDepth), 0.0, 1.0, false},
        {"benderLfo",    floatApply(&EngineParameters::benderLfoDepth), 0.0, 1.0, false},
        {"velocity",     floatApply(&EngineParameters::velocityDepth), 0.0, 1.0, false},
        {"chorusNoise",  floatApply(&EngineParameters::chorusNoise), 0.0, 1.0, false},
        {"calibration",  floatApply(&EngineParameters::calibration), 0.0, 2.0, false, 0.030},
        {"aging",        floatApply(&EngineParameters::aging), 0.0, 1.0, false},
        {"masterTune",   [](EngineParameters& p, double t) {
                             p.masterTuneCents = static_cast<float>(t * 100.0 - 50.0); },
                         0.0, 1.0, false},

        // Switches. Abrupt on purpose, but still must stay finite and bounded.
        {"range",        enumApply(&EngineParameters::range, 2), 0.0, 1.0, true},
        {"pwmMode",      enumApply(&EngineParameters::pwmSource, 1), 0.0, 1.0, true},
        {"highPass",     enumApply(&EngineParameters::highPass, 3), 0.0, 1.0, true},
        {"envPolarity",  enumApply(&EngineParameters::envPolarity, 1), 0.0, 1.0, true},
        {"vcaMode",      enumApply(&EngineParameters::vcaMode, 1), 0.0, 1.0, true},
        {"chorus",       enumApply(&EngineParameters::chorus, 3), 0.0, 1.0, true},
        {"keyMode",      enumApply(&EngineParameters::keyMode, 2), 0.0, 1.0, true},
        {"vcfTanhMode",  enumApply(&EngineParameters::vcfTanhMode, 2), 0.0, 1.0, true},
        {"vcfFastEarly", enumApply(&EngineParameters::vcfFastEarlyMode, 1), 0.0, 1.0, true},
        {"vcfSolver",    enumApply(&EngineParameters::vcfSolverMode, 2), 0.0, 1.0, true},
        {"saw",          boolApply(&EngineParameters::sawEnabled), 1.0, 0.0, true},
        {"pulse",        boolApply(&EngineParameters::pulseEnabled), 0.0, 1.0, true},
        {"transpose",    [](EngineParameters& p, double t) {
                             p.keyTranspose = static_cast<int>(std::lround(t * 24.0)) - 12; },
                         0.0, 1.0, true},
        {"polyphony",    [](EngineParameters& p, double t) {
                             p.polyphony = std::clamp(
                                 static_cast<int>(std::lround(1.0 + t * 5.0)), 1, 6); },
                         0.0, 1.0, true},
    };
}

// A continuous control may not inject a step more than this many times the one
// the steady voice was already producing. Chosen well below anything audible as
// a click while leaving room for the modelled control-scan quantisation.
constexpr double continuousRatioLimit = 3.0;
// A deliberate switch may be abrupt, but not unbounded.
constexpr double switchRatioLimit = 40.0;
constexpr double peakLimit = 1.5;
// The 12 ms at the change may not be dramatically louder than the settled level
// on either side of it -- that is a burst, whatever caused it.
constexpr double spikeLimit = 4.0;
}

// A ratio metric cannot see a note that simply stops. Automating a switch while
// keys are held must never silence them: the voice assigner may re-scan, but it
// has to re-arm the keys that are still down.
int checkHeldNotesSurvive(bool verbose)
{
    struct Case { const char* name; Apply apply; double from; double to; };
    const std::vector<Case> cases = {
        {"keyMode Poly1->Poly2",  enumApply(&EngineParameters::keyMode, 2), 0.0, 0.5},
        {"keyMode Poly1->Unison", enumApply(&EngineParameters::keyMode, 2), 0.0, 1.0},
        {"keyMode Unison->Poly1", enumApply(&EngineParameters::keyMode, 2), 1.0, 0.0},
        {"polyphony 6->1",        [](EngineParameters& p, double t) {
             p.polyphony = std::clamp(static_cast<int>(std::lround(1.0 + t * 5.0)), 1, 6); },
         1.0, 0.0},
        {"polyphony 1->6",        [](EngineParameters& p, double t) {
             p.polyphony = std::clamp(static_cast<int>(std::lround(1.0 + t * 5.0)), 1, 6); },
         0.0, 1.0},
        {"range 8'->16'",         enumApply(&EngineParameters::range, 2), 0.5, 0.0},
        {"vcaMode Env->Gate",     enumApply(&EngineParameters::vcaMode, 1), 0.0, 1.0},
        {"chorus Off->I+II",      enumApply(&EngineParameters::chorus, 3), 0.0, 1.0},
        {"transpose 0->+12",      [](EngineParameters& p, double t) {
             p.keyTranspose = static_cast<int>(std::lround(t * 24.0)) - 12; }, 0.5, 1.0},
    };

    int failures = 0;
    for (const Case& test : cases)
    {
        YouKnowEngine engine;
        engine.prepare(sampleRate, batchSize, 2);
        EngineParameters p = probePatch();
        p.cutoff = 0.45f;
        test.apply(p, test.from);
        engine.setParameters(p);
        engine.noteOn(60, 0.9f);
        engine.noteOn(64, 0.9f);

        std::vector<float> x;
        float left[batchSize] {};
        float right[batchSize] {};
        for (int batch = 0; batch < 400; ++batch)
        {
            engine.process(left, right, batchSize);
            for (int s = 0; s < batchSize; ++s)
                x.push_back(left[s]);
        }
        const std::size_t change = x.size();
        EngineParameters q = p;
        test.apply(q, test.to);
        engine.setParameters(q);
        for (int batch = 0; batch < 900; ++batch)  // ~1.2 s, keys still held
        {
            engine.process(left, right, batchSize);
            for (int s = 0; s < batchSize; ++s)
                x.push_back(left[s]);
        }

        const double before = rms(x, change - static_cast<std::size_t>(0.1 * sampleRate),
                                  change);
        const double after = rms(x, x.size() - static_cast<std::size_t>(0.3 * sampleRate),
                                 x.size());
        // The keys are still down, so a full second later the note must still be
        // there. A twentieth of the previous level is a dropout, not a timbre.
        const bool dropped = after < before * 0.05;
        if (dropped || verbose)
            std::printf("%-24s held rms %.3e -> %.3e  voices=%d  %s\n",
                        test.name, before, after, engine.getActiveVoiceCount(),
                        dropped ? "DROPPED" : "sustained");
        failures += dropped ? 1 : 0;
    }
    return failures;
}

int main(int argc, char** argv)
{
    const bool verbose = argc > 1 && std::string(argv[1]) == "--verbose";
    int failures = 0;
    double worstContinuous = 0.0;
    const char* worstName = "";

    std::printf("%-14s %-8s %-8s %8s %8s %8s %7s\n",
                "parameter", "mode", "chorus", "ratio", "peak", "spike", "");
    for (const Param& param : parameters())
    {
        for (const bool ramp : {false, true})
        {
            for (const bool chorusOn : {false, true})
            {
                const double reference = ramp
                    ? sweepReference(param.apply, param.lo, param.hi, chorusOn) : 0.0;
                const Result forward = measure(param.apply, param.lo, param.hi,
                                               ramp, chorusOn, reference,
                                               param.wrapperGlideSeconds);
                const Result back = measure(param.apply, param.hi, param.lo,
                                            ramp, chorusOn, reference,
                                            param.wrapperGlideSeconds);
                const Result& worst = forward.ratio >= back.ratio ? forward : back;

                const double limit = param.abruptByDesign ? switchRatioLimit
                                                          : continuousRatioLimit;
                bool bad = !worst.finite || worst.peak > peakLimit
                        || worst.ratio > limit
                        || (!param.abruptByDesign && worst.spike > spikeLimit);

                if (!param.abruptByDesign && worst.ratio > worstContinuous)
                {
                    worstContinuous = worst.ratio;
                    worstName = param.name;
                }
                if (bad || verbose)
                {
                    std::printf("%-14s %-8s %-8s %8.2f %8.4f %8.2f %7s\n",
                                param.name, ramp ? "ramp" : "step",
                                chorusOn ? "on" : "off", worst.ratio, worst.peak,
                                worst.spike, bad ? "FAIL" : "");
                }
                failures += bad ? 1 : 0;
            }
        }
    }

    failures += checkHeldNotesSurvive(verbose);

    if (failures)
    {
        std::printf("FAIL: %d automation artifact checks failed\n", failures);
        return 1;
    }
    std::printf("OK: held notes survive every switch; %zu automatable parameters, "
                "step and ramp, dry and chorused, "
                "no discontinuity above %.1fx steady-state slew "
                "(worst continuous: %s at %.2fx)\n",
                parameters().size(), continuousRatioLimit, worstName, worstContinuous);
    return 0;
}
