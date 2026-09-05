#include "../DSP/YouKnowEngine.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <limits>

namespace
{
constexpr double sampleRate = 48000.0;
constexpr int blockSize = 64;
constexpr int repetitions = 5;
constexpr int blocksPerRepetition = 375;
constexpr int warmupBlocks = 188;
constexpr std::size_t timedBlocks =
    static_cast<std::size_t>(repetitions * blocksPerRepetition);
constexpr double secondsPerRepetition =
    static_cast<double>(blocksPerRepetition * blockSize) / sampleRate;
constexpr double deadlineMilliseconds = 1000.0 * blockSize / sampleRate;
constexpr std::array<int, 16> notes {
    36, 39, 42, 45, 48, 51, 54, 57,
    60, 63, 66, 69, 72, 75, 78, 81,
};

youknow::EngineParameters workloadPatch(
    int voiceCount, youknow::VcfTanhMode tanhMode,
    youknow::VcfFastEarlyMode earlyMode) noexcept
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
    parameters.chorusNoise = youknow::Chorus::defaultNoiseScale;
    parameters.aging = 0.50f;
    parameters.polyphony = voiceCount;
    // Measure the delivered Rack/VST player policy, not the conservative
    // Merson reference default retained for JUCE-free numerical audits.
    parameters.vcfSolverMode = youknow::VcfSolverMode::Rk4Single;
    parameters.vcfTanhMode = tanhMode;
    parameters.vcfFastEarlyMode = earlyMode;
    return parameters;
}

bool readThreadCpuSeconds(double& seconds) noexcept
{
#if defined(CLOCK_THREAD_CPUTIME_ID)
    timespec value {};
    if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &value) == 0)
    {
        seconds = static_cast<double>(value.tv_sec)
                + static_cast<double>(value.tv_nsec) * 1.0e-9;
        return true;
    }
#else
    static_cast<void>(seconds);
#endif
    return false;
}

double cpuSeconds(bool useThreadClock) noexcept
{
    double seconds = std::numeric_limits<double>::quiet_NaN();
    if (useThreadClock)
    {
        readThreadCpuSeconds(seconds);
        return seconds;
    }

    const std::clock_t ticks = std::clock();
    if (ticks != static_cast<std::clock_t>(-1))
        seconds = static_cast<double>(ticks) / static_cast<double>(CLOCKS_PER_SEC);
    return seconds;
}

template <std::size_t Size>
double percentile(const std::array<double, Size>& sorted, double fraction) noexcept
{
    const auto index = static_cast<std::size_t>(
        static_cast<double>(Size - 1) * fraction);
    return sorted[index];
}
} // namespace

int main(int argc, char* argv[])
{
    const bool stress = argc == 2 && std::strcmp(argv[1], "--stress") == 0;
    const bool quality2x = argc == 2
        && std::strcmp(argv[1], "--quality-2x") == 0;
    const bool idle = argc == 2 && std::strcmp(argv[1], "--idle") == 0;
    const bool idleExact = argc == 2
        && std::strcmp(argv[1], "--idle-exact") == 0;
    const bool exactTanh = (argc == 2
        && std::strcmp(argv[1], "--vcf-exact") == 0) || idleExact;
    const bool fastTanh = argc == 2
        && std::strcmp(argv[1], "--vcf-fast") == 0;
    const bool fastCubic = argc == 2
        && std::strcmp(argv[1], "--vcf-fast-cubic") == 0;
    if (argc != 1 && !stress && !quality2x && !idle && !idleExact && !exactTanh
        && !fastTanh && !fastCubic)
    {
        std::fprintf(stderr,
                     "usage: %s [--quality-2x | --idle | --idle-exact | "
                     "--vcf-exact | --vcf-fast | --vcf-fast-cubic | "
                     "--stress]\n",
                     argv[0]);
        return 2;
    }

    const int oversamplingFactor = stress ? 4 : quality2x ? 2 : 1;
    const int voiceCount = stress
        ? static_cast<int>(notes.size())
        : youknow::YouKnowEngine::hardwareVoices;
    const auto tanhMode = exactTanh
        ? youknow::VcfTanhMode::Exact
        : (fastTanh || fastCubic)
            ? youknow::VcfTanhMode::ZonedHermite
            : youknow::VcfTanhMode::PolyZoned;
    const auto earlyMode = (exactTanh || fastTanh)
        ? youknow::VcfFastEarlyMode::Hermite
        : youknow::VcfFastEarlyMode::Cubic;

    youknow::YouKnowEngine engine;
    engine.prepare(sampleRate, blockSize, oversamplingFactor);
    auto parameters = workloadPatch(voiceCount, tanhMode, earlyMode);
    if (idle || idleExact)
        parameters.chorus = youknow::ChorusMode::Off;
    engine.setParameters(parameters);
    if (!idle && !idleExact)
        for (int index = 0; index < voiceCount; ++index)
            engine.noteOn(notes[static_cast<std::size_t>(index)], 1.0f);

    std::array<float, blockSize> left {};
    std::array<float, blockSize> right {};
    for (int block = 0; block < warmupBlocks; ++block)
        engine.process(left.data(), right.data(), blockSize);

    const int expectedActiveVoices = idle || idleExact ? 0 : voiceCount;
    if (engine.getActiveVoiceCount() != expectedActiveVoices
        || engine.getOversamplingFactor() != oversamplingFactor)
    {
        std::fprintf(stderr, "probe setup failed: expected %d voices at %dx\n",
                     expectedActiveVoices, oversamplingFactor);
        return 2;
    }

    double ignored {};
    const bool useThreadClock = readThreadCpuSeconds(ignored);
    std::array<double, repetitions> cpuRealtime {};
    std::array<double, timedBlocks> blockMilliseconds {};
    std::size_t timingIndex = 0;
    double checksum = 0.0;

    for (int repetition = 0; repetition < repetitions; ++repetition)
    {
        const double cpuStarted = cpuSeconds(useThreadClock);
        for (int block = 0; block < blocksPerRepetition; ++block)
        {
            const auto started = std::chrono::steady_clock::now();
            engine.process(left.data(), right.data(), blockSize);
            const auto stopped = std::chrono::steady_clock::now();
            blockMilliseconds[timingIndex++] =
                std::chrono::duration<double, std::milli>(stopped - started).count();
            checksum += left[static_cast<std::size_t>(block % blockSize)];
        }
        const double cpuStopped = cpuSeconds(useThreadClock);
        cpuRealtime[static_cast<std::size_t>(repetition)] =
            (cpuStopped - cpuStarted) / secondsPerRepetition;
    }

    if (!std::all_of(cpuRealtime.begin(), cpuRealtime.end(),
                     [](double value) { return std::isfinite(value); }))
    {
        std::fprintf(stderr, "probe failed: no CPU clock is available\n");
        return 2;
    }

    std::sort(cpuRealtime.begin(), cpuRealtime.end());
    std::sort(blockMilliseconds.begin(), blockMilliseconds.end());
    const auto misses = static_cast<std::size_t>(std::count_if(
        blockMilliseconds.begin(), blockMilliseconds.end(),
        [](double milliseconds) { return milliseconds > deadlineMilliseconds; }));

    std::printf("scope=native-engine-only reason-host=no rack-wrapper=no target-chip=no\n");
    std::printf("workload=%s voices=%d factor=%dx solver=rk4-single "
                "vcf_tanh=%s fast_early=%s "
                "aging=%.2f rate=%.0f block=%d "
                "deadline_ms=%.6f\n",
                stress ? "max-stress"
                       : quality2x ? "quality-2x"
                       : idleExact ? "idle-exact"
                       : idle ? "idle-shipped-default"
                       : exactTanh ? "vcf-exact"
                       : fastCubic ? "vcf-fast-cubic"
                       : fastTanh ? "vcf-fast" : "shipped-default",
                expectedActiveVoices,
                engine.getOversamplingFactor(),
                tanhMode == youknow::VcfTanhMode::Exact ? "exact"
                    : tanhMode == youknow::VcfTanhMode::ZonedHermite
                        ? "fast" : "poly",
                earlyMode == youknow::VcfFastEarlyMode::Cubic
                    ? "cubic" : "hermite",
                static_cast<double>(parameters.aging), sampleRate, blockSize,
                deadlineMilliseconds);
    std::printf("cpu_clock=%s cpu_x_realtime median=%.6f min=%.6f max=%.6f "
                "repetitions=%d seconds_each=%.3f\n",
                useThreadClock ? "thread" : "process-fallback",
                percentile(cpuRealtime, 0.5), cpuRealtime.front(), cpuRealtime.back(),
                repetitions, secondsPerRepetition);
    std::printf("block_wall_ms p50=%.6f p95=%.6f p99=%.6f max=%.6f "
                "deadline_misses=%zu/%zu checksum=%.9f\n",
                percentile(blockMilliseconds, 0.5),
                percentile(blockMilliseconds, 0.95),
                percentile(blockMilliseconds, 0.99), blockMilliseconds.back(),
                misses, blockMilliseconds.size(), checksum);
    // The maximum 16-voice/4x workload is diagnostic coverage, not the shipped
    // CPU gate. Every other documented workload must meet its native deadline.
    return stress || misses == 0 ? 0 : 1;
}
