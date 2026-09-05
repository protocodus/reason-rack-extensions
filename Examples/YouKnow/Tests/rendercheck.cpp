#include "DSP/YouKnowEngine.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>

namespace
{
constexpr int batchSize = 64;

struct Stats
{
    double peak = 0.0;
    double energy = 0.0;
    bool finite = true;
};

Stats render(youknow::YouKnowEngine& engine, int batches)
{
    Stats stats;
    float left[batchSize] {};
    float right[batchSize] {};
    for (int batch = 0; batch < batches; ++batch)
    {
        engine.process(left, right, batchSize);
        for (int sample = 0; sample < batchSize; ++sample)
        {
            stats.finite = stats.finite && std::isfinite(left[sample])
                                         && std::isfinite(right[sample]);
            stats.peak = std::max(stats.peak,
                                  std::max(std::abs(static_cast<double>(left[sample])),
                                           std::abs(static_cast<double>(right[sample]))));
            stats.energy += static_cast<double>(left[sample]) * left[sample]
                          + static_cast<double>(right[sample]) * right[sample];
        }
    }
    return stats;
}
}

int main()
{
    constexpr double sampleRate = 48000.0;
    youknow::YouKnowEngine engine;
    engine.prepare(sampleRate, batchSize, 2);
    engine.setParameters(youknow::EngineParameters {});

    assert(engine.getProcessingLatencySamples() == 41);
    assert(engine.getOversamplingFactor() == 2);
    assert(engine.getActiveVoiceCount() == 0);

    engine.noteOn(60, 0.9f);
    assert(engine.getActiveVoiceCount() == 1);
    const Stats held = render(engine, 375); // 0.5 seconds
    assert(held.finite);
    assert(held.peak > 1.0e-4);
    assert(held.energy > 1.0e-6);

    engine.setSustainPedal(true);
    engine.noteOff(60);
    render(engine, 75);
    assert(engine.getActiveVoiceCount() == 1);

    engine.setSustainPedal(false);
    for (int batch = 0; batch < 4000 && engine.getActiveVoiceCount() != 0; ++batch)
        render(engine, 1);
    assert(engine.getActiveVoiceCount() == 0);

    // Exercise the same idle quality transition the Rack wrapper advances in
    // private scratch buffers, moving from this test's initial 2x rung to 4x.
    bool qualityReady = engine.setOversamplingFactor(4);
    for (int batch = 0; batch < 100 && !qualityReady; ++batch)
    {
        render(engine, 1);
        qualityReady = engine.setOversamplingFactor(4);
    }
    assert(qualityReady);
    assert(engine.getOversamplingFactor() == 4);
    assert(engine.getProcessingLatencySamples() == 41);

    // When the fade-out ends exactly at a call boundary, applying the new
    // rate is not readiness: the fade-in still has to reach unity. At 51.2 kHz
    // the five-millisecond half-transition is exactly four 64-frame batches.
    youknow::YouKnowEngine boundary;
    boundary.prepare(51200.0, batchSize, 1);
    boundary.setParameters(youknow::EngineParameters {});
    assert(!boundary.setOversamplingFactor(2));
    render(boundary, 4);
    assert(!boundary.setOversamplingFactor(2));
    assert(boundary.getOversamplingFactor() == 2);
    render(boundary, 4);
    assert(boundary.setOversamplingFactor(2));

    engine.reset();
    assert(engine.getActiveVoiceCount() == 0);

    std::printf("OK: peak %.6f, finite note/sustain/release, 1x/2x/4x quality, latency 41\n",
                held.peak);
    return 0;
}
