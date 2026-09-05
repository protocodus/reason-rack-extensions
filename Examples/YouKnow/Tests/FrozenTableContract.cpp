#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace
{
struct BbdNode
{
    double value {};
    double slope {};
};

struct VcfCoefficient
{
    double constant {};
    double linear {};
    double quadratic {};
    double cubic {};
};

constexpr std::array<BbdNode, 513> frozenBbd {{
#include "../DSP/YouKnowBbdTransferTable.inc"
}};

constexpr std::array<VcfCoefficient, 160> frozenVcfFine {{
#include "../DSP/YouKnowVcfTanhFineTable.inc"
}};

constexpr std::array<VcfCoefficient, 56> frozenVcfTail {{
#include "../DSP/YouKnowVcfTanhTailTable.inc"
}};

constexpr std::array<float, 129> frozenResonanceFrequencyTrim {{
#include "../DSP/YouKnowResonanceFrequencyTrimTable.inc"
}};

constexpr std::array<float, 3073> frozenCorrectionStep {{
#include "../DSP/YouKnowCorrectionStepTable.inc"
}};

constexpr std::array<float, 3073> frozenCorrectionSlope {{
#include "../DSP/YouKnowCorrectionSlopeTable.inc"
}};

constexpr std::array<double, 513> frozenDescribing {{
#include "../DSP/YouKnowDescribingTable.inc"
}};

constexpr std::array<float, 4097> frozenVoiceVcaGain {{
#include "../DSP/YouKnowVoiceVcaGainTable.inc"
}};

constexpr float frozenCardJohnsonNoise =
#include "../DSP/YouKnowCardJohnsonNoise.inc"
;

[[nodiscard]] std::uint64_t bits(double value) noexcept
{
    std::uint64_t result {};
    std::memcpy(&result, &value, sizeof(result));
    return result;
}

[[nodiscard]] std::uint32_t bits(float value) noexcept
{
    std::uint32_t result {};
    std::memcpy(&result, &value, sizeof(result));
    return result;
}

[[nodiscard]] bool same(double left, double right) noexcept
{
    return bits(left) == bits(right);
}

[[nodiscard]] bool same(float left, float right) noexcept
{
    return bits(left) == bits(right);
}

template <std::size_t size>
bool validateVcf(const std::array<VcfCoefficient, size>& frozen,
                 double start, double width, const char* name)
{
    struct Node
    {
        double value {};
        double slope {};
    };

    std::array<Node, size + 1> nodes {};
    for (std::size_t index = 0; index < nodes.size(); ++index)
    {
        const double value = std::tanh(
            start + width * static_cast<double>(index));
        nodes[index] = { value, 1.0 - value * value };
    }
    for (std::size_t index = 0; index < size; ++index)
        if (nodes[index + 1].value == nodes[index].value)
        {
            nodes[index].slope = 0.0;
            nodes[index + 1].slope = 0.0;
        }

    for (std::size_t index = 0; index < size; ++index)
    {
        const Node left = nodes[index];
        const Node right = nodes[index + 1];
        VcfCoefficient expected;
        if (right.value == left.value)
        {
            expected = { left.value, 0.0, 0.0, 0.0 };
        }
        else
        {
            const double delta = right.value - left.value;
            const double leftSlope = width * left.slope;
            const double rightSlope = width * right.slope;
            expected = {
                left.value,
                leftSlope,
                3.0 * delta - 2.0 * leftSlope - rightSlope,
                -2.0 * delta + leftSlope + rightSlope
            };
        }
        const auto& actual = frozen[index];
        if (!same(actual.constant, expected.constant)
            || !same(actual.linear, expected.linear)
            || !same(actual.quadratic, expected.quadratic)
            || !same(actual.cubic, expected.cubic))
        {
            std::cerr << name << " table mismatch at " << index << '\n';
            return false;
        }
    }
    return true;
}

constexpr double piHigh = 3.14159265358979323846;
constexpr double describingCeiling = 8.0;
constexpr int describingSteps = 512;
constexpr int resonanceTrimSteps = 128;
constexpr float resonanceTrimCeiling = 8.0f;
constexpr float nominalOscillationFeedback = 4.0f;
constexpr float thermalVoltage = 0.026f;
constexpr float stageAttenuation = 560.0f / (68000.0f + 560.0f);
constexpr float otaHeadroomVolts =
    2.0f * thermalVoltage / stageAttenuation;
constexpr float loopDividerRatio = 100000.0f / 1500.0f;
constexpr float loopHeadroomVolts =
    2.0f * 0.026f * loopDividerRatio;

double describingIntegral(double argument) noexcept
{
    constexpr int panels = 64;
    const double width = 0.5 * piHigh / static_cast<double>(panels);
    const auto sample = [argument](double time) {
        const double sine = std::sin(time);
        return std::tanh(argument * sine) * sine;
    };
    double sum = 0.0;
    for (int panel = 0; panel < panels; ++panel)
    {
        const double left = width * static_cast<double>(panel);
        sum += width / 6.0
             * (sample(left) + 4.0 * sample(left + 0.5 * width)
                + sample(left + width));
    }
    return 2.0 * sum;
}

using DescribingTable = std::array<double, describingSteps + 1>;

DescribingTable buildDescribingTable() noexcept
{
    DescribingTable values {};
    values[0] = 1.0;
    for (int index = 1; index <= describingSteps; ++index)
    {
        const double argument = describingCeiling
            * static_cast<double>(index) / static_cast<double>(describingSteps);
        values[static_cast<std::size_t>(index)] =
            2.0 / (piHigh * argument) * describingIntegral(argument);
    }
    return values;
}

double describingGain(double argument,
                      const DescribingTable& table) noexcept
{
    const double magnitude = std::abs(argument);
    if (magnitude >= describingCeiling)
        return table[describingSteps] * describingCeiling / magnitude;
    const double position = magnitude / describingCeiling
                          * static_cast<double>(describingSteps);
    const auto lower = static_cast<std::size_t>(position);
    const double fraction = position - static_cast<double>(lower);
    return table[lower] * (1.0 - fraction)
         + table[lower + 1] * fraction;
}

double oscillationRatio(const std::array<double, 4>& gains,
                        double seed) noexcept
{
    double ratio = std::max(seed, 1.0e-6);
    for (int iteration = 0; iteration < 24; ++iteration)
    {
        double phase = 0.0;
        double slope = 0.0;
        for (const double gain : gains)
        {
            const double position = ratio / gain;
            phase += std::atan(position);
            slope += (1.0 / gain) / (1.0 + position * position);
        }
        const double step = (piHigh - phase) / slope;
        ratio = std::max(1.0e-6, ratio + step);
        if (std::abs(step) < 1.0e-13 * ratio)
            break;
    }
    return ratio;
}

struct LimitCycle
{
    double loopGain {};
    double droop {};
};

LimitCycle limitCycleFor(double amplitude, double stageHeadroom,
                         double returnHeadroom,
                         std::array<double, 4>& gains,
                         const DescribingTable& describingTable) noexcept
{
    std::array<double, 4> ratios { 1.0, 1.0, 1.0, 1.0 };
    double droop = 1.0;
    for (int iteration = 0; iteration < 32; ++iteration)
    {
        droop = oscillationRatio(gains, droop);
        for (std::size_t stage = 0; stage < ratios.size(); ++stage)
            ratios[stage] = droop / gains[stage];

        std::array<double, 4> nodes {};
        nodes[3] = amplitude;
        for (int stage = 2; stage >= 0; --stage)
        {
            const auto index = static_cast<std::size_t>(stage);
            nodes[index] = nodes[index + 1]
                * std::sqrt(1.0 + ratios[index + 1] * ratios[index + 1]);
        }

        double moved = 0.0;
        for (std::size_t stage = 0; stage < gains.size(); ++stage)
        {
            const double next = describingGain(
                nodes[stage] * ratios[stage] / stageHeadroom,
                describingTable);
            moved = std::max(moved, std::abs(next - gains[stage]));
            gains[stage] = next;
        }
        if (moved < 1.0e-11)
            break;
    }

    double loss = describingGain(
        amplitude / returnHeadroom, describingTable);
    for (const double ratio : ratios)
        loss /= std::sqrt(1.0 + ratio * ratio);
    return { 1.0 / loss, droop };
}

std::array<float, resonanceTrimSteps + 1>
buildResonanceFrequencyTrim() noexcept
{
    constexpr int sweep = 1024;
    constexpr double amplitudeCeiling = 12.0;
    const auto describingTable = buildDescribingTable();
    std::array<float, resonanceTrimSteps + 1> values {};
    values[0] = 1.0f;
    const double step = (static_cast<double>(resonanceTrimCeiling)
                         - static_cast<double>(nominalOscillationFeedback))
                      / static_cast<double>(resonanceTrimSteps);
    int filled = 0;
    LimitCycle previous {
        static_cast<double>(nominalOscillationFeedback), 1.0 };
    std::array<double, 4> gains { 1.0, 1.0, 1.0, 1.0 };
    for (int index = 1;
         index <= sweep && filled < resonanceTrimSteps;
         ++index)
    {
        const double amplitude = amplitudeCeiling
            * static_cast<double>(index) / static_cast<double>(sweep);
        const LimitCycle current = limitCycleFor(
            amplitude, static_cast<double>(otaHeadroomVolts),
            static_cast<double>(loopHeadroomVolts), gains, describingTable);
        while (filled < resonanceTrimSteps)
        {
            const double wanted =
                static_cast<double>(nominalOscillationFeedback)
                + step * static_cast<double>(filled + 1);
            if (wanted > current.loopGain)
                break;
            const double span = current.loopGain - previous.loopGain;
            const double blend = span > 0.0
                ? (wanted - previous.loopGain) / span : 0.0;
            const double droop = previous.droop
                + blend * (current.droop - previous.droop);
            values[static_cast<std::size_t>(++filled)] =
                static_cast<float>(1.0 / droop);
        }
        previous = current;
    }
    for (int index = filled + 1; index <= resonanceTrimSteps; ++index)
        values[static_cast<std::size_t>(index)] =
            values[static_cast<std::size_t>(index - 1)];
    return values;
}

constexpr int correctionHalfWidth = 24;
constexpr int correctionRing = 2 * correctionHalfWidth;
constexpr int correctionOversample = 64;
constexpr int correctionTableLength =
    correctionRing * correctionOversample + 1;

struct CorrectionTables
{
    std::array<float, correctionTableLength> stepResponse {};
    std::array<float, correctionTableLength> slopeResidual {};
};

CorrectionTables buildCorrectionTables() noexcept
{
    constexpr int length = correctionTableLength;
    constexpr double step = 1.0 / correctionOversample;
    constexpr double cutoff = 0.985;
    std::array<double, length> impulse {};
    for (int index = 0; index < length; ++index)
    {
        const double time = static_cast<double>(index) * step
                          - correctionHalfWidth;
        const double sinc = std::abs(time) < 1.0e-12
            ? cutoff
            : std::sin(piHigh * cutoff * time) / (piHigh * time);
        const double phase = static_cast<double>(index)
                           / static_cast<double>(length - 1);
        const double window = 0.42
            - 0.5 * std::cos(2.0 * piHigh * phase)
            + 0.08 * std::cos(4.0 * piHigh * phase);
        impulse[static_cast<std::size_t>(index)] = sinc * window;
    }

    std::array<double, length> stepResponse {};
    double accumulator = 0.0;
    for (int index = 1; index < length; ++index)
    {
        accumulator += 0.5 * step
                     * (impulse[static_cast<std::size_t>(index - 1)]
                        + impulse[static_cast<std::size_t>(index)]);
        stepResponse[static_cast<std::size_t>(index)] = accumulator;
    }
    const double total = stepResponse[length - 1];
    if (std::abs(total) > 1.0e-12)
        for (auto& value : stepResponse)
            value /= total;

    std::array<double, length> rampResponse {};
    accumulator = 0.0;
    for (int index = 1; index < length; ++index)
    {
        accumulator += 0.5 * step
                     * (stepResponse[static_cast<std::size_t>(index - 1)]
                        + stepResponse[static_cast<std::size_t>(index)]);
        rampResponse[static_cast<std::size_t>(index)] = accumulator;
    }

    CorrectionTables result;
    for (int index = 0; index < length; ++index)
    {
        result.stepResponse[static_cast<std::size_t>(index)] =
            static_cast<float>(stepResponse[static_cast<std::size_t>(index)]);
        const double time = static_cast<double>(index) * step
                          - correctionHalfWidth;
        const double idealRamp = time >= 0.0 ? time : 0.0;
        result.slopeResidual[static_cast<std::size_t>(index)] =
            static_cast<float>(rampResponse[static_cast<std::size_t>(index)]
                               - idealRamp);
    }
    return result;
}

std::array<float, 4097> buildVoiceVcaGainTable()
{
    constexpr int tableSteps = 4096;
    constexpr float turnOn = 0.015f;
        std::array<double, tableSteps + 1> solved {};
        constexpr double voltsPerUnit =
        static_cast<double>(9.921875f)
        / static_cast<double>(thermalVoltage);
        for (int i = 0; i <= tableSteps; ++i)
        {
        const double v = (static_cast<double>(i) / tableSteps
                      - static_cast<double>(turnOn)) * voltsPerUnit;
        double y = v > 1.0 ? v - std::log(v) : std::exp(v);
        for (int step = 0; step < 12; ++step)
        {
            const double delta = (y + std::log(y) - v) * y / (y + 1.0);
            y -= delta;
            if (std::abs(delta) <= 1.0e-15 * y)
                break;
        }
        solved[static_cast<std::size_t>(i)] = y;
        }
        std::array<float, tableSteps + 1> result {};
        const double fullScale = solved[tableSteps];
        for (int i = 0; i <= tableSteps; ++i)
        result[static_cast<std::size_t>(i)] = static_cast<float>(
            solved[static_cast<std::size_t>(i)] / fullScale);
        return result;
}

template <typename Value, std::size_t size>
bool validateTable(const std::array<Value, size>& frozen,
                   const std::array<Value, size>& expected,
                        const char* name)
{
    for (std::size_t index = 0; index < size; ++index)
        if (!same(frozen[index], expected[index]))
        {
            std::cerr << name << " table mismatch at " << index << '\n';
            return false;
        }
    return true;
}
} // namespace

int main()
{
    constexpr float sourceOhms = 68000.0f * 560.0f / (68000.0f + 560.0f);
    constexpr float attenuation = 560.0f / (68000.0f + 560.0f);
    const float density = std::sqrt(4.0f * 1.380649e-23f * 298.15f * sourceOhms)
                        / attenuation;
    const float expectedCardNoise =
        std::sqrt(3.0f) * density * std::sqrt(192000.0f * 0.5f);
    if (!same(frozenCardJohnsonNoise, expectedCardNoise))
    {
        std::cerr << "card Johnson-noise constant mismatch\n";
        return 1;
    }

    constexpr double limit = 4.0;
    constexpr float curvatureFloat = 1.2044546f;
    constexpr float exponentFloat = 12.9395323f;
    const double curvature = static_cast<double>(curvatureFloat);
    const double exponent = static_cast<double>(exponentFloat);
    for (std::size_t index = 0; index < frozenBbd.size(); ++index)
    {
        const double normalised = limit * static_cast<double>(index) / 512.0;
        const double squared = normalised * normalised;
        const double base = 1.0 + curvature * squared
                          + std::pow(normalised, exponent);
        const double denominator = std::pow(base, 1.0 / exponent);
        const BbdNode expected {
            normalised / denominator,
            (1.0 + curvature * (1.0 - 2.0 / exponent) * squared)
                / (base * denominator)
        };
        if (!same(frozenBbd[index].value, expected.value)
            || !same(frozenBbd[index].slope, expected.slope))
        {
            std::cerr << "BBD table mismatch at " << index << '\n';
            return 1;
        }
    }

    if (!validateVcf(frozenVcfFine, 0.0, 1.0 / 32.0, "VCF fine")
        || !validateVcf(frozenVcfTail, 5.0, 1.0 / 4.0, "VCF tail"))
        return 1;

    const auto expectedResonance = buildResonanceFrequencyTrim();
    const auto expectedCorrection = buildCorrectionTables();
    if (!validateTable(frozenDescribing, buildDescribingTable(),
                        "harmonic describing")
        || !validateTable(frozenVoiceVcaGain, buildVoiceVcaGainTable(),
                          "voice VCA gain")
        || !validateTable(frozenResonanceFrequencyTrim,
                            expectedResonance, "resonance frequency trim")
        || !validateTable(frozenCorrectionStep,
                               expectedCorrection.stepResponse,
                               "correction step")
        || !validateTable(frozenCorrectionSlope,
                               expectedCorrection.slopeResidual,
                               "correction slope"))
        return 1;

    std::cout << "validated 513 BBD nodes, 216 VCF intervals, "
              << "129 resonance trims, 6146 correction samples, 513 describing nodes,\n"
              << "4097 voice VCA gains and the card Johnson-noise constant\n";
    return 0;
}
