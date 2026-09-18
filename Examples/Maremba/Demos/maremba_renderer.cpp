#include "DSP/MarembaEngine.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <cstring>
#include <cstdint>

#pragma pack(push, 1)
struct WavHeader {
    char riff[4] = {'R', 'I', 'F', 'F'};
    uint32_t chunkSize = 0;
    char wave[4] = {'W', 'A', 'V', 'E'};
    char fmt[4] = {'f', 'm', 't', ' '};
    uint32_t fmtSize = 16;
    uint16_t audioFormat = 1; // PCM
    uint16_t numChannels = 2; // Stereo
    uint32_t sampleRate = 44100;
    uint32_t byteRate = 44100 * 2 * 2;
    uint16_t blockAlign = 4;
    uint16_t bitsPerSample = 16;
    char data[4] = {'d', 'a', 't', 'a'};
    uint32_t dataSize = 0;
};
#pragma pack(pop)

struct MidiEvent {
    double timeSec;
    int type; // 1 = note_on, 0 = note_off
    int note;
    int velocity;
};

int main(int argc, char* argv[]) {
    std::string eventsFile = "";
    std::string outputFile = "";
    int model = 0; // 0: Rosewood, 1: Padauk, 2: Balafon, 3: Kalimba
    int mallet = 1; // 0: Yarn/Flesh, 1: Cord/Natural, 2: Rubber/Nail, 3: Wood/Pick
    int oversampling = 0; // 0: 2x, 1: 4x, 2: 8x
    int polyphony = 2; // 24 voices
    double maxDuration = 60.0;
    bool jsonOutput = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--events" && i + 1 < argc) eventsFile = argv[++i];
        else if (arg == "--output" && i + 1 < argc) outputFile = argv[++i];
        else if (arg == "--model" && i + 1 < argc) model = std::stoi(argv[++i]);
        else if (arg == "--mallet" && i + 1 < argc) mallet = std::stoi(argv[++i]);
        else if (arg == "--oversampling" && i + 1 < argc) oversampling = std::stoi(argv[++i]);
        else if (arg == "--polyphony" && i + 1 < argc) polyphony = std::stoi(argv[++i]);
        else if (arg == "--max-duration" && i + 1 < argc) maxDuration = std::stod(argv[++i]);
        else if (arg == "--json") jsonOutput = true;
    }

    if (eventsFile.empty() || outputFile.empty()) {
        std::cerr << "Usage: maremba_renderer --events <file> --output <file.wav> [--model 0|1|2|3] [--mallet 0|1|2|3] [--oversampling 0|1|2] [--max-duration <sec>] [--json]\n";
        return 1;
    }

    // 1. Read events
    std::ifstream inFile(eventsFile);
    if (!inFile.is_open()) {
        std::cerr << "Failed to open events file: " << eventsFile << std::endl;
        return 1;
    }

    std::vector<MidiEvent> events;
    std::string line;
    double lastEventTime = 0.0;
    int totalNoteOns = 0;

    while (std::getline(inFile, line)) {
        if (line.empty() || line[0] == '#') continue;
        MidiEvent ev;
        if (sscanf(line.c_str(), "%lf %d %d %d", &ev.timeSec, &ev.type, &ev.note, &ev.velocity) == 4) {
            if (ev.timeSec <= maxDuration) {
                events.push_back(ev);
                lastEventTime = std::max(lastEventTime, ev.timeSec);
                if (ev.type == 1) totalNoteOns++;
            }
        }
    }
    inFile.close();

    // Add acoustic ring-out tail (3.0 seconds after the last note)
    double totalAudioDuration = std::min(maxDuration, lastEventTime + 3.0);
    if (totalAudioDuration < 1.0) totalAudioDuration = maxDuration;

    // 2. Initialize Physical Modeling Engine
    constexpr double kSampleRate = 44100.0;
    maremba::MarembaEngine engine(kSampleRate);

    maremba::EngineParameters params;
    params.model = model;
    params.malletType = mallet;
    params.oversampling = oversampling;
    params.polyphony = polyphony;

    if (model == 0) {
        // Imperial Rosewood 5.0 (Concert Grand Hall)
        params.closeLevel = 0.85f;
        params.farLevel = 0.50f;
        params.piezoLevel = 0.15f;
        params.stereoWidth = 1.05f;
        params.sympathetic = 0.20f;
        params.bodyBloom = 0.25f;
        params.pitchGlide = 0.15f;
        params.decay = 1.00f;
        params.malletHardness = 0.45f;
        params.preampDrive = 0.0f; // Pristine acoustic concert recording
        params.warmth = 0.05f;
    } else if (model == 1) {
        // Mayan Padauk 4.3 (Artisan Wood Bark)
        params.closeLevel = 0.85f;
        params.farLevel = 0.40f;
        params.piezoLevel = 0.20f;
        params.stereoWidth = 1.00f;
        params.sympathetic = 0.20f;
        params.bodyBloom = 0.25f;
        params.pitchGlide = 0.20f;
        params.decay = 1.00f;
        params.malletHardness = 0.50f;
        params.preampDrive = 0.0f;
        params.warmth = 0.05f;
    } else if (model == 2) {
        // Balafon Ancestral (Calabash & Vibrating Mirliton Buzz)
        params.closeLevel = 0.85f;
        params.farLevel = 0.40f;
        params.piezoLevel = 0.25f;
        params.stereoWidth = 1.00f;
        params.buzzAmount = 0.25f;
        params.artifacts = 0.30f;
        params.sympathetic = 0.20f;
        params.bodyBloom = 0.25f;
        params.pitchGlide = 0.20f;
        params.decay = 0.95f;
        params.malletHardness = 0.55f;
        params.preampDrive = 0.0f;
        params.warmth = 0.05f;
    } else {
        // Kalimba Artisan 17-Key (African Thumb Piano - Cantilever Chime)
        params.closeLevel = 0.85f;
        params.farLevel = 0.35f;
        params.piezoLevel = 0.20f;
        params.stereoWidth = 1.00f;
        params.buzzAmount = 0.0f;
        params.artifacts = 0.15f;
        params.sympathetic = 0.20f;
        params.bodyBloom = 0.20f;
        params.pitchGlide = 0.05f;
        params.decay = 1.10f;
        params.malletHardness = 0.65f;
        params.preampDrive = 0.0f;
        params.warmth = 0.0f;
    }

    params.compAmount = 0.0f; // Pure uncompressed natural acoustic dynamics
    params.compAttack = 10.0f;
    params.compRelease = 120.0f;
    params.volume = 0.85f;

    engine.SetParameters(params);
    engine.Reset();

    // 3. Render audio loop with high-precision benchmarking
    size_t totalFrames = static_cast<size_t>(totalAudioDuration * kSampleRate);
    std::vector<float> audioL(totalFrames, 0.0f);
    std::vector<float> audioR(totalFrames, 0.0f);

    constexpr int kBatchSize = 64;
    float batchL[kBatchSize];
    float batchR[kBatchSize];

    size_t eventIdx = 0;
    size_t framePos = 0;

    auto tStart = std::chrono::high_resolution_clock::now();

    while (framePos < totalFrames) {
        int curBatch = static_cast<int>(std::min(static_cast<size_t>(kBatchSize), totalFrames - framePos));
        double batchEndSec = static_cast<double>(framePos + curBatch) / kSampleRate;

        // Process any MIDI events that trigger in this batch interval
        while (eventIdx < events.size() && events[eventIdx].timeSec < batchEndSec) {
            const auto& ev = events[eventIdx];
            if (ev.type == 1) {
                float vel = static_cast<float>(ev.velocity) / 127.0f;
                engine.NoteOn(ev.note, vel);
            } else {
                engine.NoteOff(ev.note);
            }
            eventIdx++;
        }

        engine.RenderBatch(batchL, batchR, nullptr, nullptr, nullptr, nullptr, nullptr, curBatch);

        for (int i = 0; i < curBatch; ++i) {
            audioL[framePos + i] = batchL[i];
            audioR[framePos + i] = batchR[i];
        }

        framePos += curBatch;
    }

    auto tEnd = std::chrono::high_resolution_clock::now();
    double renderTimeMs = std::chrono::duration<double, std::milli>(tEnd - tStart).count();
    double renderTimeSec = renderTimeMs / 1000.0;
    double realTimeFactor = (renderTimeSec > 0.0001) ? (totalAudioDuration / renderTimeSec) : 9999.9;

    // 4. Analyze Audio Metrics
    float maxAbs = 0.0f;
    double sumSq = 0.0;
    for (size_t i = 0; i < totalFrames; ++i) {
        float sL = audioL[i];
        float sR = audioR[i];
        maxAbs = std::max(maxAbs, std::max(std::abs(sL), std::abs(sR)));
        sumSq += sL * sL + sR * sR;
    }

    // Preserve true acoustic dynamics; only attenuate if signal exceeds -0.5 dBFS to prevent clipping
    float normGain = 1.0f;
    if (maxAbs > 0.95f) {
        normGain = 0.94f / maxAbs;
    }

    float peakDb = (maxAbs > 1e-5f) ? 20.0f * std::log10(maxAbs * normGain) : -96.0f;
    float rms = static_cast<float>(std::sqrt(sumSq / (totalFrames * 2.0))) * normGain;
    float rmsDb = (rms > 1e-5f) ? 20.0f * std::log10(rms) : -96.0f;

    // 5. Write 16-bit Stereo PCM WAV File
    std::ofstream outFile(outputFile, std::ios::binary);
    if (!outFile.is_open()) {
        std::cerr << "Failed to open output WAV file: " << outputFile << std::endl;
        return 1;
    }

    WavHeader hdr;
    hdr.sampleRate = static_cast<uint32_t>(kSampleRate);
    hdr.byteRate = hdr.sampleRate * hdr.numChannels * (hdr.bitsPerSample / 8);
    hdr.dataSize = static_cast<uint32_t>(totalFrames * hdr.numChannels * sizeof(int16_t));
    hdr.chunkSize = 36 + hdr.dataSize;

    outFile.write(reinterpret_cast<const char*>(&hdr), sizeof(hdr));

    std::vector<int16_t> pcmBuffer(totalFrames * 2);
    for (size_t i = 0; i < totalFrames; ++i) {
        float l = std::clamp(audioL[i] * normGain, -1.0f, 1.0f);
        float r = std::clamp(audioR[i] * normGain, -1.0f, 1.0f);
        pcmBuffer[i * 2 + 0] = static_cast<int16_t>(l * 32767.0f);
        pcmBuffer[i * 2 + 1] = static_cast<int16_t>(r * 32767.0f);
    }

    outFile.write(reinterpret_cast<const char*>(pcmBuffer.data()), pcmBuffer.size() * sizeof(int16_t));
    outFile.close();

    const char* modelNames[4] = {"Imperial Rosewood 5.0", "Mayan Padauk 4.3", "Balafon Ancestral", "Kalimba Artisan 17-Key"};
    const char* osNames[3] = {"2x Studio", "4x High-Res", "8x Archival"};
    const char* marimbaMalletNames[4] = {"Soft Wool Yarn", "Medium Concert Cord", "Hard Rubber", "Wood Baton"};
    const char* kalimbaThumbNames[4] = {"Thumb Flesh Pad", "Natural Thumb", "Thumbnail Snap", "Thumb Pick"};
    const char* strikerName = (model == 3) ? kalimbaThumbNames[std::clamp(mallet, 0, 3)] : marimbaMalletNames[std::clamp(mallet, 0, 3)];

    if (jsonOutput) {
        std::cout << "{\n"
                  << "  \"model\": \"" << modelNames[model] << "\",\n"
                  << "  \"model_id\": " << model << ",\n"
                  << "  \"striker\": \"" << strikerName << "\",\n"
                  << "  \"striker_id\": " << mallet << ",\n"
                  << "  \"oversampling\": \"" << osNames[oversampling] << "\",\n"
                  << "  \"audio_duration_sec\": " << totalAudioDuration << ",\n"
                  << "  \"render_time_ms\": " << renderTimeMs << ",\n"
                  << "  \"real_time_factor\": " << realTimeFactor << ",\n"
                  << "  \"throughput_samples_per_sec\": " << static_cast<uint64_t>(totalFrames / renderTimeSec) << ",\n"
                  << "  \"peak_db\": " << peakDb << ",\n"
                  << "  \"rms_db\": " << rmsDb << ",\n"
                  << "  \"notes_processed\": " << totalNoteOns << ",\n"
                  << "  \"output_file\": \"" << outputFile << "\"\n"
                  << "}\n";
    } else {
        std::cout << "Rendered " << outputFile << "\n"
                  << "  Model:       " << modelNames[model] << "\n"
                  << "  Striker:     " << strikerName << "\n"
                  << "  Oversample:  " << osNames[oversampling] << "\n"
                  << "  Audio Time:  " << totalAudioDuration << " s\n"
                  << "  Render Time: " << renderTimeMs << " ms\n"
                  << "  Speedup:     " << realTimeFactor << "x real-time\n"
                  << "  Peak / RMS:  " << peakDb << " dBFS / " << rmsDb << " dBFS\n"
                  << "  Notes:       " << totalNoteOns << "\n";
    }

    return 0;
}
