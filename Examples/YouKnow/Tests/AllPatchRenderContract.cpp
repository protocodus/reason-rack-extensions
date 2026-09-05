#include "../DSP/YouKnowEngine.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>

namespace
{
constexpr int blockSize = 64;
constexpr int renderBlocks = 2250; // Three seconds at 48 kHz.
constexpr double silencePeak = 1.0e-5;
constexpr double silenceRms = 1.0e-6;
constexpr double minimumLevelledPeak = 4.0e-2;
constexpr double maximumLevelledPeak = 1.85e-1;
constexpr double maximumLevelledRms = 4.1e-2;
constexpr double pathologicalPeak = 1.25;
constexpr double stressMaximumPeak = 1.0;

struct Workload
{
    std::array<int, 6> notes;
    std::size_t noteCount;
    bool enforceLevelledLimits;
    const char* name;
};

constexpr Workload calibrationWorkload {
    { 48, 55, 60, 0, 0, 0 }, 3, true, "calibration",
};
constexpr Workload lowStressWorkload {
    { 36, 43, 48, 52, 55, 60 }, 6, false, "low six-note stress",
};
constexpr Workload highStressWorkload {
    { 60, 67, 72, 76, 79, 84 }, 6, false, "high six-note stress",
};

struct Patch
{
    std::string name;
    std::unordered_map<std::string, double> values;
};

double value(const Patch& patch, const char* name)
{
    const auto found = patch.values.find(name);
    if (found == patch.values.end())
        throw std::runtime_error(patch.name + ": missing property " + name);
    return found->second;
}

template <typename Enum>
Enum choice(const Patch& patch, const char* name, int maximum)
{
    const int rounded = static_cast<int>(std::floor(value(patch, name) + 0.5));
    return static_cast<Enum>(std::clamp(rounded, 0, maximum));
}

youknow::EngineParameters parametersFor(const Patch& patch)
{
    using namespace youknow;
    EngineParameters parameters;
    parameters.volume = static_cast<float>(value(patch, "volume"));
    parameters.benderDcoDepth = static_cast<float>(value(patch, "benderDco"));
    parameters.benderVcfDepth = static_cast<float>(value(patch, "benderVcf"));
    parameters.benderLfoDepth = static_cast<float>(value(patch, "benderLfo"));
    parameters.portamento = static_cast<float>(value(patch, "portamento"));
    parameters.keyMode = choice<KeyMode>(patch, "keyMode", 2);
    parameters.lfoRate = static_cast<float>(value(patch, "lfoRate"));
    parameters.lfoDelay = static_cast<float>(value(patch, "lfoDelay"));
    parameters.dcoLfoDepth = static_cast<float>(value(patch, "dcoLfo"));
    parameters.pwmDepth = static_cast<float>(value(patch, "pwm"));
    parameters.pwmSource = choice<PwmSource>(patch, "pwmMode", 1);
    parameters.range = choice<DcoRange>(patch, "range", 2);
    parameters.sawEnabled = value(patch, "saw") != 0.0;
    parameters.pulseEnabled = value(patch, "pulse") != 0.0;
    parameters.subLevel = static_cast<float>(value(patch, "sub"));
    parameters.noiseLevel = static_cast<float>(value(patch, "noise"));
    parameters.highPass = choice<HighPassMode>(patch, "highPass", 3);
    parameters.cutoff = static_cast<float>(value(patch, "cutoff"));
    parameters.resonance = static_cast<float>(value(patch, "resonance"));
    parameters.envPolarity = choice<EnvPolarity>(patch, "envPolarity", 1);
    parameters.envDepth = static_cast<float>(value(patch, "vcfEnv"));
    parameters.vcfLfoDepth = static_cast<float>(value(patch, "vcfLfo"));
    parameters.keyFollow = static_cast<float>(value(patch, "keyFollow"));
    parameters.vcaMode = choice<VcaMode>(patch, "vcaMode", 1);
    parameters.vcaLevel = static_cast<float>(value(patch, "vcaLevel"));
    parameters.attack = static_cast<float>(value(patch, "attack"));
    parameters.decay = static_cast<float>(value(patch, "decay"));
    parameters.sustain = static_cast<float>(value(patch, "sustain"));
    parameters.release = static_cast<float>(value(patch, "release"));
    parameters.chorus = choice<ChorusMode>(patch, "chorus", 3);
    parameters.keyTranspose = std::clamp(
        static_cast<int>(value(patch, "transpose")) - 12, -12, 12);
    parameters.masterTuneCents = static_cast<float>(
        value(patch, "masterTune") * 100.0 - 50.0);
    parameters.velocityDepth = static_cast<float>(value(patch, "velocity"));
    parameters.calibration = static_cast<float>(value(patch, "calibration") * 2.0);
    parameters.chorusNoise = static_cast<float>(value(patch, "chorusNoise"));
    parameters.polyphony = std::clamp(
        static_cast<int>(value(patch, "polyphony")) + 1,
        1, YouKnowEngine::maxVoices);

    // Rear policy controls are song state rather than patch state. Exercise
    // the shipped defaults while validating the public patch bank.
    parameters.aging = static_cast<float>(value(patch, "_aging"));
    parameters.vcfTanhMode = VcfTanhMode::PolyZoned;
    parameters.vcfFastEarlyMode = VcfFastEarlyMode::Cubic;
    parameters.vcfSolverMode = VcfSolverMode::Rk4Single;
    return parameters;
}

Patch parsePatch(const std::string& line)
{
    Patch patch;
    std::size_t begin = 0;
    std::size_t end = line.find('\t');
    patch.name = line.substr(0, end);
    while (end != std::string::npos)
    {
        begin = end + 1;
        end = line.find('\t', begin);
        const std::string field = line.substr(begin, end - begin);
        const std::size_t separator = field.find('=');
        if (separator == std::string::npos)
            throw std::runtime_error(patch.name + ": malformed manifest field");
        const std::string name = field.substr(0, separator);
        std::size_t consumed = 0;
        const double parsed = std::stod(field.substr(separator + 1), &consumed);
        if (consumed != field.size() - separator - 1
            || !patch.values.emplace(name, parsed).second)
            throw std::runtime_error(patch.name + ": invalid property " + name);
    }
    if (patch.name.empty() || patch.values.empty())
        throw std::runtime_error("empty patch manifest row");
    return patch;
}

void hashFloat(std::uint64_t& hash, float sample)
{
    std::uint32_t bits {};
    std::memcpy(&bits, &sample, sizeof(bits));
    for (unsigned int shift = 0; shift < 32; shift += 8)
    {
        hash ^= static_cast<std::uint8_t>(bits >> shift);
        hash *= 1099511628211ull;
    }
}

void checkPatch(const Patch& patch, const Workload& workload)
{
    using youknow::YouKnowEngine;
    YouKnowEngine first;
    YouKnowEngine second;
    first.prepare(48000.0, blockSize, 1);
    second.prepare(48000.0, blockSize, 1);
    const auto parameters = parametersFor(patch);
    const double presetGain = std::exp2(
        (std::clamp(value(patch, "presetGain"), 0.0, 1.0) - 0.5) * 6.0);
    const bool measuringUnity = patch.values.find("_measureUnity")
                             != patch.values.end();
    first.setParameters(parameters);
    second.setParameters(parameters);
    for (std::size_t index = 0; index < workload.noteCount; ++index)
    {
        const int note = workload.notes[index];
        first.noteOn(note, 1.0f);
        second.noteOn(note, 1.0f);
    }

    std::array<float, blockSize> firstLeft {};
    std::array<float, blockSize> firstRight {};
    std::array<float, blockSize> secondLeft {};
    std::array<float, blockSize> secondRight {};
    double peak = 0.0;
    double sumSquares = 0.0;
    std::uint64_t hash = 14695981039346656037ull;
    for (int block = 0; block < renderBlocks; ++block)
    {
        first.process(firstLeft.data(), firstRight.data(), blockSize);
        second.process(secondLeft.data(), secondRight.data(), blockSize);
        if (std::memcmp(firstLeft.data(), secondLeft.data(), sizeof(firstLeft)) != 0
            || std::memcmp(firstRight.data(), secondRight.data(), sizeof(firstRight)) != 0)
            throw std::runtime_error(patch.name + ": non-deterministic render");

        for (int frame = 0; frame < blockSize; ++frame)
        {
            const float left = static_cast<float>(
                firstLeft[static_cast<std::size_t>(frame)] * presetGain);
            const float right = static_cast<float>(
                firstRight[static_cast<std::size_t>(frame)] * presetGain);
            const float secondLeftLevelled = static_cast<float>(
                secondLeft[static_cast<std::size_t>(frame)] * presetGain);
            const float secondRightLevelled = static_cast<float>(
                secondRight[static_cast<std::size_t>(frame)] * presetGain);
            if (left != secondLeftLevelled || right != secondRightLevelled)
                throw std::runtime_error(patch.name + ": non-deterministic level trim");
            if (!std::isfinite(left) || !std::isfinite(right))
                throw std::runtime_error(patch.name + ": non-finite output");
            peak = std::max(peak, std::max(std::abs(static_cast<double>(left)),
                                           std::abs(static_cast<double>(right))));
            sumSquares += static_cast<double>(left) * left
                        + static_cast<double>(right) * right;
            hashFloat(hash, left);
            hashFloat(hash, right);
        }
    }

    const double rms = std::sqrt(sumSquares / (2.0 * blockSize * renderBlocks));
    if (peak <= silencePeak || rms <= silenceRms)
        throw std::runtime_error(patch.name + ": silent render");
    if (!measuringUnity && workload.enforceLevelledLimits
        && peak < minimumLevelledPeak)
        throw std::runtime_error(patch.name + ": levelled preset is too quiet");
    if (!measuringUnity && workload.enforceLevelledLimits
        && (peak > maximumLevelledPeak || rms > maximumLevelledRms))
        throw std::runtime_error(patch.name + ": level calibration ceiling exceeded");
    if (!workload.enforceLevelledLimits && peak >= stressMaximumPeak)
        throw std::runtime_error(patch.name + ": six-note stress reached full scale");
    if (peak > pathologicalPeak || !std::isfinite(rms))
        throw std::runtime_error(patch.name + ": pathological output level");
    std::printf("OK: %-38s peak %.6f rms %.6f hash %016llx\n",
                patch.name.c_str(), peak, rms,
                static_cast<unsigned long long>(hash));
}
} // namespace

int main(int argc, char* argv[])
{
    try
    {
        const Workload* workload = &calibrationWorkload;
        if (argc == 2 && std::string(argv[1]) == "--stress-low")
            workload = &lowStressWorkload;
        else if (argc == 2 && std::string(argv[1]) == "--stress-high")
            workload = &highStressWorkload;
        else if (argc != 1)
            throw std::runtime_error("usage: all-patch-render [--stress-low|--stress-high]");

        std::string line;
        int count = 0;
        while (std::getline(std::cin, line))
        {
            if (line.empty())
                continue;
            checkPatch(parsePatch(line), *workload);
            ++count;
        }
        if (count == 0)
            throw std::runtime_error("no public patches supplied");
        std::printf(
            "OK: %d/%d public patches audible, finite, bounded, deterministic (%s)\n",
            count, count, workload->name);
        return 0;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "FAIL: %s\n", error.what());
        return 1;
    }
}
