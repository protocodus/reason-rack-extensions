#pragma once

#include "YouKnowEngine.h"

namespace youknow
{
// Product selections: the two 2026-09-11 auditions (upstream
// Docs/decisions.md), plus the approximate thermal clock coupling and the
// 2026-09-15 C56 selection. Raw engine fixtures keep their nominal reference
// defaults. The plug-in, the maintained product renderers and the Rack
// wrapper select these settings centrally.
//
// Rack adaptation: the source throws std::logic_error when a circuit refuses
// its configuration. A Rack native object has no exception path to the host,
// so configureBeforePrepare() reports the outcome instead: the selections are
// constants the wrapper contract proves accepted, and debug builds assert on
// the result during JBox_Export_CreateNativeObject. The selections are identical.
struct ProductFidelityProfile
{
    // The B audition used this datasheet comparison coordinate. It is not a
    // measurement of the installed JUNO-106 switch's on-resistance.
    static constexpr double highPassSwitchOhms = 110.0;

    // Owner-delegated evidence choice, coupling B (2026-09-15). C56=10uF
    // feeds the reconstructed hybrid's 4.7k summing path in parallel with
    // its 24k+1.5k resonance-input leg: about 3.969k and 39.685ms. This is
    // the low-frequency, ideal-feedback/stiff-source reduction, not a claim
    // that WAVE source impedance or the full active input network is known.
    // JUNO-6/60 has the same topology with 10k and 47k+1.5k; retain the
    // hybrid's documented proportions rather than copying that 8.291k load.
    // https://github.com/ThomHPL/Open80017a/blob/5561ee3ea8eaa6299c9ce0c79df4df43658f9efa/Outputs/Open80017a.pdf
    // https://www.synfo.nl/servicemanuals/Roland/JUNO-6_SERVICE_NOTES.pdf#page=9
    static constexpr double moduleInputCouplingResistanceOhms =
        4700.0 * (24000.0 + 1500.0) / (4700.0 + 24000.0 + 1500.0);

    // Configure a newly constructed engine exactly once, before prepare().
    // Circuit configuration persists across prepare()/reset(), but changing
    // it live is unsupported. A full coupled-mixer comparison replaces the
    // independent C56 pole; configure that alternative here so both mutually
    // exclusive paths still receive the same remaining product selections.
    // Returns false if any circuit rejected its configuration; the engine is
    // then not a product-fidelity instrument and must not be used as one.
    [[nodiscard]] static bool configureBeforePrepare(
        YouKnowEngine& engine,
        const CoupledSubMixer::Calibration* coupledMixer = nullptr) noexcept
    {
        // User-authorized approximate thermal coupling (2026-09-14): use the
        // named Murata CSA8.00MTZ shape, anchored at 8 MHz/25 C, on the shared
        // chassis temperature. This is not an installed KMFC calibration.
        // The common 3-second startup is an explicit software UX choice.
        return engine.configureHighPassSwitch(highPassSwitchOhms)
            && engine.configureDcoTemperatureProxy(true, 25.0)
            && (coupledMixer != nullptr
                    ? engine.configureCoupledMixer(*coupledMixer)
                    : engine.configureModuleInputCouplingResistanceOhms(
                          moduleInputCouplingResistanceOhms));
    }

    // A product choice, not a stored tone parameter. Apply to every newly
    // formed snapshot so INIT, patch recall and song restore retain it.
    static void applyTo(EngineParameters& parameters) noexcept
    {
        parameters.useServiced439522VcfCalibration = true;
    }
};
} // namespace youknow
