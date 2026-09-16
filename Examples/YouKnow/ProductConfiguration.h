#pragma once

#include "DSP/YouKnowProductFidelity.h"

namespace youknow
{
// The circuit selections the shipped Rack instrument renders with. They mirror
// the source plug-in's processor: ProductFidelityProfile once before the first
// prepare() and on every parameter snapshot, and the chart-geometry converter
// timing that the processor and its product renderers select before prepare()
// (an upstream listening decision of 2026-09-04). The engine's own defaults
// remain the reference configuration its fingerprints test.
//
// The wrapper and every native harness that measures the product -- patch
// levels, automation artifacts, timing -- share this one definition, so a
// calibration can never measure a different instrument from the one shipped.
struct RackProductConfiguration
{
    // Once, on a newly constructed engine, before its first prepare(). Returns
    // false if a circuit refused its configuration, which is a source defect.
    [[nodiscard]] static bool configureBeforePrepare(YouKnowEngine& engine) noexcept
    {
        engine.selectConverterTimingProfile(
            YouKnowEngine::ConverterTimingProfile::MeasuredChartGeometry);
        return ProductFidelityProfile::configureBeforePrepare(engine);
    }

    // On every newly formed parameter snapshot.
    static void applyTo(EngineParameters& parameters) noexcept
    {
        ProductFidelityProfile::applyTo(parameters);
    }
};
} // namespace youknow
