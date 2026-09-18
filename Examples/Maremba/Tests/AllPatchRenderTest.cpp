#include "../DSP/MarembaEngine.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <cmath>
#include <cassert>
#include <filesystem>
#include <algorithm>

namespace fs = std::filesystem;

struct PatchData {
    std::string name;
    std::unordered_map<std::string, float> numbers;
};

PatchData LoadRepatch(const fs::path& filepath) {
    PatchData patch;
    patch.name = filepath.filename().string();

    std::ifstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + filepath.string());
    }

    std::string line;
    while (std::getline(file, line)) {
        if (line.find("property=\"") != std::string::npos && line.find("type=\"number\"") != std::string::npos) {
            auto propStart = line.find("property=\"") + 10;
            auto propEnd = line.find("\"", propStart);
            std::string prop = line.substr(propStart, propEnd - propStart);

            auto valStart = line.find(">", propEnd) + 1;
            auto valEnd = line.find("</Value>", valStart);
            std::string valStr = line.substr(valStart, valEnd - valStart);

            patch.numbers[prop] = std::stof(valStr);
        }
    }
    return patch;
}

maremba::EngineParameters ConvertToEngineParams(const PatchData& p) {
    maremba::EngineParameters ep;

    auto Get = [&](const std::string& key, float defaultVal) -> float {
        auto it = p.numbers.find(key);
        return (it != p.numbers.end()) ? it->second : defaultVal;
    };

    ep.model = static_cast<int>(Get("model", 0.0f));
    ep.malletType = static_cast<int>(Get("malletType", 1.0f));
    ep.malletHardness = std::clamp(Get("malletHardness", 0.40f), 0.0f, 1.0f);
    ep.strikePosition = std::clamp(Get("strikePosition", 0.50f), 0.0f, 1.0f);
    ep.strikeJitter = Get("strikeJitter", 0.15f) * 100.0f;
    ep.resonatorTune = (Get("resonatorTune", 0.50f) - 0.50f) * 100.0f;
    ep.resonatorCoupling = std::clamp(Get("resonatorCoupling", 0.70f), 0.0f, 1.0f);
    ep.decay = 0.10f + Get("decay", 0.1139f) * 7.90f;
    ep.buzzAmount = Get("buzzAmount", 0.15f);
    ep.artifacts = Get("artifacts", 0.35f);
    ep.sympathetic = std::clamp(Get("sympathetic", 0.40f), 0.0f, 1.0f);
    ep.pitchGlide = Get("pitchGlide", 0.30f);
    ep.bodyBloom = Get("bodyBloom", 0.50f);
    ep.rollSpeed = std::clamp(Get("rollSpeed", 0.0f) * 20.0f, 0.0f, 20.0f);
    ep.closeLevel = Get("closeLevel", 0.85f);
    ep.farLevel = Get("farLevel", 0.45f);
    ep.piezoLevel = Get("piezoLevel", 0.30f);
    ep.stereoWidth = Get("stereoWidth", 0.50f) * 2.0f;
    ep.preampDrive = Get("preampDrive", 0.15f);
    ep.warmth = (Get("warmth", 0.55f) - 0.50f) * 2.0f;
    ep.compAmount = Get("compAmount", 0.25f);
    ep.compAttack = 1.0f + Get("compAttack", 0.1837f) * 49.0f;
    ep.compRelease = 20.0f + Get("compRelease", 0.2083f) * 480.0f;
    ep.volume = std::clamp(Get("volume", 0.80f), 0.0f, 1.0f);
    ep.oversampling = static_cast<int>(Get("oversampling", 0.0f));
    ep.velocityCurve = static_cast<int>(Get("velocityCurve", 1.0f));
    ep.polyphony = static_cast<int>(Get("polyphony", 1.0f));
    ep.masterTune = Get("masterTune", 0.50f);
    ep.detune = Get("detune", 0.0f) * 100.0f;

    return ep;
}

int main() {
    std::cout << "=== Running All-Patch Audio Render & Integrity Test ===" << std::endl;

    fs::path publicDir = "Resources/Public";
    std::vector<fs::path> patchFiles;
    for (const auto& entry : fs::directory_iterator(publicDir)) {
        if (entry.path().extension() == ".repatch") {
            patchFiles.push_back(entry.path());
        }
    }
    std::sort(patchFiles.begin(), patchFiles.end());

    std::cout << "Discovered " << patchFiles.size() << " patches in " << publicDir << std::endl;
    assert(!patchFiles.empty() && "No patches found!");

    constexpr int kBatch = 64;
    float outL[kBatch], outR[kBatch];
    float cL[kBatch], cR[kBatch], fL[kBatch], fR[kBatch], pz[kBatch];

    int passedCount = 0;

    for (const auto& pPath : patchFiles) {
        PatchData patch = LoadRepatch(pPath);
        maremba::EngineParameters ep = ConvertToEngineParams(patch);

        // Test at 44.1 kHz and 48 kHz
        for (double sr : { 44100.0, 48000.0 }) {
            maremba::MarembaEngine engine(sr);
            engine.SetParameters(ep);

            // Strike a 3-note chord: C3, G3, C4
            engine.NoteOn(48, 0.75f);
            engine.NoteOn(55, 0.65f);
            engine.NoteOn(60, 0.85f);

            float peak = 0.0f;
            double sumSq = 0.0;
            int totalSamples = 0;

            // Render 1.5 seconds of audio (~1000 batches)
            int batches = static_cast<int>(1.5 * sr / kBatch);
            for (int b = 0; b < batches; ++b) {
                engine.RenderBatch(outL, outR, cL, cR, fL, fR, pz, kBatch);

                for (int i = 0; i < kBatch; ++i) {
                    float sL = outL[i];
                    float sR = outR[i];

                    // Check for NaNs and Infs
                    if (std::isnan(sL) || std::isnan(sR) || std::isinf(sL) || std::isinf(sR)) {
                        std::cerr << "FAIL: " << patch.name << " produced NaN/Inf at sample " << totalSamples << std::endl;
                        return 1;
                    }

                    // Check for explosive buffer clipping (> 1.25)
                    if (std::abs(sL) > 1.25f || std::abs(sR) > 1.25f) {
                        std::cerr << "FAIL: " << patch.name << " output exploded (peak > 1.25): L=" << sL << " R=" << sR << std::endl;
                        return 1;
                    }

                    peak = std::max(peak, std::max(std::abs(sL), std::abs(sR)));
                    sumSq += (sL * sL + sR * sR) * 0.5;
                    totalSamples++;
                }

                // Release notes after 0.5s
                if (b == static_cast<int>(0.5 * sr / kBatch)) {
                    engine.NoteOff(48);
                    engine.NoteOff(55);
                    engine.NoteOff(60);
                }
            }

            float rms = static_cast<float>(std::sqrt(sumSq / totalSamples));
            assert(rms > 0.0001f && "Patch RMS energy must be positive");

            // Verify non-zero output
            if (peak < 0.005f) {
                std::cerr << "FAIL: " << patch.name << " produced silence (peak=" << peak << ")" << std::endl;
                return 1;
            }

            // Verify tail decay (last batch should be decaying smoothly)
            float tailPeak = 0.0f;
            for (int i = 0; i < kBatch; ++i) {
                tailPeak = std::max(tailPeak, std::max(std::abs(outL[i]), std::abs(outR[i])));
            }
            if (tailPeak > peak * 0.9f && ep.decay < 6.0f) {
                std::cerr << "FAIL: " << patch.name << " did not decay (tailPeak=" << tailPeak << ", peak=" << peak << ")" << std::endl;
                return 1;
            }
        }

        std::cout << "  PASS: " << patch.name << std::endl;
        passedCount++;
    }

    std::cout << "\n>>> SUCCESS: ALL " << passedCount << " FACTORY PATCHES RENDERED CLEANLY (No NaNs, No Infs, Controlled Levels) <<<" << std::endl;
    return 0;
}
