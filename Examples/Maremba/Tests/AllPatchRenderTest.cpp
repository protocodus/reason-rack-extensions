// Loads every factory .repatch into a host-shim MOM and renders it through the
// shipped wrapper (CMaremba::RenderBatch), so the property -> engine mapping
// under test is the product's own. A patch must carry exactly the device's
// document properties (kParameterNames minus the performance controllers).
//
// Per patch and sample rate: a chord must sound, decay and fall silent after a
// transport stop; a melodic phrase must sit in the bank's loudness window with
// a mono-safe stereo image; a forte chord must keep every direct out below
// full scale. Every global operator new (plain, nothrow and over-aligned) is
// counted while RenderBatch runs and must never be called.
//
// Usage: all_patch_render_test [patch directory]
// (default: ../Resources/Public next to this source file)
#include "../Maremba.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <memory>
#include <new>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// Volatile, so the check inside the replaced operators is never folded away.
namespace {
volatile bool allocationForbidden = false;
volatile long forbiddenAllocations = 0;
}

void* operator new(std::size_t size)
{
    if (allocationForbidden) ++forbiddenAllocations;
    if (void* memory = std::malloc(size == 0 ? 1 : size)) return memory;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }
void* operator new(std::size_t size, const std::nothrow_t&) noexcept
{
    if (allocationForbidden) ++forbiddenAllocations;
    return std::malloc(size == 0 ? 1 : size);
}
void* operator new[](std::size_t size, const std::nothrow_t& tag) noexcept { return ::operator new(size, tag); }
void operator delete(void* memory, const std::nothrow_t&) noexcept { std::free(memory); }
void operator delete[](void* memory, const std::nothrow_t&) noexcept { std::free(memory); }

// Over-aligned types (e.g. alignas(32) SIMD blocks) allocate through the
// align_val_t forms, which do not route through the plain operator new.
void* operator new(std::size_t size, std::align_val_t alignment, const std::nothrow_t&) noexcept
{
    if (allocationForbidden) ++forbiddenAllocations;
    void* memory = nullptr;
    const std::size_t align = std::max(static_cast<std::size_t>(alignment), sizeof(void*));
    return posix_memalign(&memory, align, size == 0 ? 1 : size) == 0 ? memory : nullptr;
}
void* operator new(std::size_t size, std::align_val_t alignment)
{
    if (void* memory = ::operator new(size, alignment, std::nothrow)) return memory;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size, std::align_val_t alignment) { return ::operator new(size, alignment); }
void* operator new[](std::size_t size, std::align_val_t alignment, const std::nothrow_t& tag) noexcept
{
    return ::operator new(size, alignment, tag);
}
void operator delete(void* memory, std::align_val_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::align_val_t) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t, std::align_val_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t, std::align_val_t) noexcept { std::free(memory); }
void operator delete(void* memory, std::align_val_t, const std::nothrow_t&) noexcept { std::free(memory); }
void operator delete[](void* memory, std::align_val_t, const std::nothrow_t&) noexcept { std::free(memory); }

struct CMarembaTestAccess
{
    static constexpr int parameterCount = CMaremba::kParameterCount;
    static const char* parameterName(int index) { return CMaremba::kParameterNames[static_cast<std::size_t>(index)]; }
    static double parameterDefault(int index) { return CMaremba::kParameterDefaults[static_cast<std::size_t>(index)]; }
};

namespace {

[[noreturn]] void fail(const std::string& message)
{
    std::fprintf(stderr, "FAIL: %s\n", message.c_str());
    std::exit(1);
}

// --- Minimal MOM ---------------------------------------------------------------
enum class Kind : std::uint64_t { Number, Boolean, Buffer };
struct Encoded { Kind kind; double value; };
static_assert(sizeof(Encoded) == sizeof(TJBox_Value), "TJBox_Value holds a kind and a double");

struct Property
{
    TJBox_ObjectRef object;
    std::string key;
    TJBox_Value value;
};

constexpr int kFrames = 64;
constexpr int kOutputs = 7;
const char* const kOutputPaths[kOutputs] {
    "/audio_outputs/left", "/audio_outputs/right",
    "/audio_outputs/close_left", "/audio_outputs/close_right",
    "/audio_outputs/far_left", "/audio_outputs/far_right",
    "/audio_outputs/piezo",
};
const std::set<std::string> kPerformanceProperties { "modWheel", "pitchBend" };

// Voicing bounds for every factory patch (the bank's level range on the
// phrase below, measured through this wrapper). The mono fold-down, (L+R)/2
// against the stereo RMS, is what a mono PA or phone plays; with S/M <= 0 dB it
// cannot fall below -3 dB, and it is asserted as the listener-facing number.
constexpr double kPhraseRmsMinDb = -24.0;
constexpr double kPhraseRmsMaxDb = -17.0;
constexpr double kSideToMidMaxDb = 0.0;
constexpr double kMonoFoldDownMinDb = -4.0;
// The direct outs are pre-compressor stems; a forte chord must not clip them.
constexpr double kDirectPeakMax = 1.0;

std::vector<std::string> objects { std::string() };
std::vector<Property> properties { Property {} };
bool transportPlaying = true;
std::array<std::array<float, kFrames>, kOutputs> captured {};
std::array<bool, kOutputs> wrote {};

TJBox_Value encode(Kind kind, double value)
{
    const Encoded encoded { kind, value };
    TJBox_Value result {};
    std::memcpy(&result, &encoded, sizeof(result));
    return result;
}

Encoded decode(TJBox_Value value)
{
    Encoded result {};
    std::memcpy(&result, &value, sizeof(result));
    return result;
}

TJBox_ObjectRef objectFor(const char* path)
{
    for (std::size_t index = 1; index < objects.size(); ++index)
        if (objects[index] == path) return static_cast<TJBox_ObjectRef>(index);
    objects.emplace_back(path);
    return static_cast<TJBox_ObjectRef>(objects.size() - 1);
}

TJBox_PropertyRef propertyFor(TJBox_ObjectRef object, const char* key)
{
    for (std::size_t index = 1; index < properties.size(); ++index)
        if (properties[index].object == object && properties[index].key == key)
            return static_cast<TJBox_PropertyRef>(index);
    const std::string name { key };
    const Kind kind = name == "connected" || name == "noteon" ? Kind::Boolean : Kind::Number;
    properties.push_back({ object, name, encode(kind, 0.0) });
    return static_cast<TJBox_PropertyRef>(properties.size() - 1);
}

void set(const char* path, const char* key, Kind kind, double value)
{
    properties[propertyFor(objectFor(path), key)].value = encode(kind, value);
}

TJBox_PropertyDiff noteDiff(int note, double velocity, int frame)
{
    TJBox_PropertyDiff diff {};
    diff.fObjectRef = objectFor("/note_states");
    diff.fPropertyTag = static_cast<TJBox_Tag>(note);
    diff.fPreviousValue = encode(Kind::Number, 0.0);
    diff.fCurrentValue = encode(Kind::Number, velocity);
    diff.fAtFrameIndex = static_cast<TJBox_UInt16>(frame);
    return diff;
}

double toDb(double value) { return 20.0 * std::log10(std::max(value, 1e-12)); }

// --- Patches ---------------------------------------------------------------------
struct Patch
{
    std::string name;
    std::map<std::string, double> values;
};

Patch loadPatch(const fs::path& path)
{
    Patch patch { path.filename().string(), {} };
    std::ifstream file(path);
    if (!file) fail("cannot open " + path.string());
    std::stringstream text;
    text << file.rdbuf();
    const std::string xml = text.str();

    const std::regex value(R"re(<Value\s+property="([^"]+)"\s+type="([^"]+)"\s*>([^<]*)</Value>)re");
    for (auto it = std::sregex_iterator(xml.begin(), xml.end(), value); it != std::sregex_iterator(); ++it)
    {
        const std::string name = (*it)[1];
        if ((*it)[2] != "number") fail(patch.name + ": property " + name + " is not a number");
        if (patch.values.count(name) != 0) fail(patch.name + ": property " + name + " appears twice");
        char* end = nullptr;
        const std::string raw = (*it)[3];
        const double number = std::strtod(raw.c_str(), &end);
        if (end == raw.c_str() || !std::isfinite(number)) fail(patch.name + ": bad value for " + name);
        patch.values[name] = number;
    }

    // Exactly the device's document properties: nothing unknown, nothing missing.
    std::set<std::string> expected;
    for (int index = 0; index < CMarembaTestAccess::parameterCount; ++index)
        if (kPerformanceProperties.count(CMarembaTestAccess::parameterName(index)) == 0)
            expected.insert(CMarembaTestAccess::parameterName(index));
    for (const auto& entry : patch.values)
        if (expected.count(entry.first) == 0) fail(patch.name + ": unknown property " + entry.first);
    for (const auto& name : expected)
        if (patch.values.count(name) == 0) fail(patch.name + ": missing property " + name);
    return patch;
}

// Every property at its default, then the patch's values; performance
// controllers at rest; all seven outputs cabled; transport running.
void configureHost(const Patch& patch)
{
    for (int index = 0; index < CMarembaTestAccess::parameterCount; ++index)
    {
        const char* name = CMarembaTestAccess::parameterName(index);
        const auto found = patch.values.find(name);
        set("/custom_properties", name, Kind::Number,
            found != patch.values.end() ? found->second : CMarembaTestAccess::parameterDefault(index));
    }
    set("/custom_properties", "noteon", Kind::Boolean, 0.0);
    for (const char* cv : { "/cv_inputs/note_cv", "/cv_inputs/gate_cv", "/cv_inputs/mallet_cv", "/cv_inputs/position_cv",
                            "/cv_inputs/coupling_cv", "/cv_inputs/volume_cv", "/cv_inputs/sympathetic_cv" })
    {
        set(cv, "connected", Kind::Boolean, 0.0);
        set(cv, "value", Kind::Number, 0.0);
    }
    for (const char* output : kOutputPaths) set(output, "connected", Kind::Boolean, 1.0);
    transportPlaying = true;
}

struct Levels
{
    double mainPeak = 0.0;
    double directPeak = 0.0;
    double lastBatchPeak = 0.0;
    bool anyWritten = false;
};

Levels renderBatch(CMaremba& device, const std::vector<TJBox_PropertyDiff>& diffs = {})
{
    for (auto& buffer : captured) buffer.fill(0.0f);
    wrote.fill(false);
    forbiddenAllocations = 0;
    allocationForbidden = true;
    device.RenderBatch(diffs.empty() ? nullptr : diffs.data(), static_cast<TJBox_UInt32>(diffs.size()));
    allocationForbidden = false;
    if (forbiddenAllocations != 0) fail(std::to_string(forbiddenAllocations) + " heap allocation(s) inside RenderBatch");

    Levels levels;
    for (int output = 0; output < kOutputs; ++output)
    {
        levels.anyWritten = levels.anyWritten || wrote[static_cast<std::size_t>(output)];
        for (float sample : captured[static_cast<std::size_t>(output)])
        {
            const double magnitude = std::abs(static_cast<double>(sample));
            if (output < 2) levels.mainPeak = std::max(levels.mainPeak, magnitude);
            else levels.directPeak = std::max(levels.directPeak, magnitude);
        }
    }
    levels.lastBatchPeak = levels.mainPeak;
    return levels;
}

int batchesFor(double seconds, double sampleRate) { return static_cast<int>(seconds * sampleRate / kFrames); }

std::string where(const Patch& patch, double sampleRate)
{
    char text[160];
    std::snprintf(text, sizeof(text), "%s @ %.0f Hz", patch.name.c_str(), sampleRate);
    return text;
}

void renderChordAndStop(const Patch& patch, double sampleRate)
{
    configureHost(patch);
    auto device = std::make_unique<CMaremba>(sampleRate);

    // A C3-G3-C4 chord, struck across the first batch, released after 0.5 s.
    Levels total;
    double finalPeak = 0.0;
    const int ringBatches = batchesFor(1.0, sampleRate);
    for (int batch = 0; batch < ringBatches; ++batch)
    {
        std::vector<TJBox_PropertyDiff> diffs;
        if (batch == 0) diffs = { noteDiff(48, 96, 0), noteDiff(55, 83, 7), noteDiff(60, 108, 13) };
        if (batch == batchesFor(0.5, sampleRate)) diffs = { noteDiff(48, 0, 0), noteDiff(55, 0, 0), noteDiff(60, 0, 0) };
        const Levels levels = renderBatch(*device, diffs);
        total.mainPeak = std::max(total.mainPeak, levels.mainPeak);
        total.directPeak = std::max(total.directPeak, levels.directPeak);
        if (batch == ringBatches - 1) finalPeak = levels.lastBatchPeak;
    }

    const std::string at = where(patch, sampleRate);
    if (total.mainPeak < 0.005) fail(at + ": silent (main peak " + std::to_string(total.mainPeak) + ")");
    if (total.mainPeak > 1.25) fail(at + ": main output exploded (peak " + std::to_string(total.mainPeak) + ")");
    if (!(finalPeak < total.mainPeak)) fail(at + ": did not decay after the strike");

    // Transport stop damps the bars; the device must then fall silent and stop
    // writing its outputs (no voice or tail may run forever).
    transportPlaying = false;
    int silentAfter = -1;
    for (int batch = 0; batch < batchesFor(20.0, sampleRate); ++batch)
    {
        if (!renderBatch(*device).anyWritten)
        {
            silentAfter = batch;
            break;
        }
    }
    if (silentAfter < 0) fail(at + ": still sounding 20 s after transport stop");
    std::printf("  PASS %-34s main peak %.3f, direct peak %.3f, silent %.2f s after stop\n",
                at.c_str(), total.mainPeak, total.directPeak, silentAfter * kFrames / sampleRate);
}

// A melodic phrase, one strike every 0.15 s over four octaves at velocities
// 60..119, each key held for 0.1 s, rendered for 5 s including its tail.
constexpr int kPhraseNotes[] { 60, 64, 67, 72, 67, 64, 60, 60, 62, 65, 69, 74, 69, 65, 62, 62, 48, 55, 36, 84 };
constexpr double kPhraseStepSeconds = 0.15;
constexpr double kPhraseHoldSeconds = 0.10;
constexpr double kPhraseSeconds = 5.0;

struct PhraseLevels
{
    double rmsDb = 0.0;          // L and R together
    double peakDb = 0.0;
    double sideToMidDb = 0.0;    // RMS of (R-L)/2 against (L+R)/2
    double monoFoldDownDb = 0.0; // RMS of (L+R)/2 against the stereo RMS
};

PhraseLevels renderPhrase(const Patch& patch, double sampleRate)
{
    configureHost(patch);
    auto device = std::make_unique<CMaremba>(sampleRate);

    struct Event { long sample; int note; double velocity; };
    std::vector<Event> events;
    for (int step = 0; step < static_cast<int>(std::size(kPhraseNotes)); ++step)
    {
        const double onset = step * kPhraseStepSeconds;
        events.push_back({ std::lround(onset * sampleRate), kPhraseNotes[step], 60.0 + (step * 23) % 60 });
        events.push_back({ std::lround((onset + kPhraseHoldSeconds) * sampleRate), kPhraseNotes[step], 0.0 });
    }
    std::stable_sort(events.begin(), events.end(), [](const Event& a, const Event& b) { return a.sample < b.sample; });

    double sumSquares = 0.0, sumMid = 0.0, sumSide = 0.0, peak = 0.0;
    long frames = 0;
    std::size_t next = 0;
    for (int batch = 0; batch < batchesFor(kPhraseSeconds, sampleRate); ++batch)
    {
        const long start = static_cast<long>(batch) * kFrames;
        std::vector<TJBox_PropertyDiff> diffs;
        for (; next < events.size() && events[next].sample < start + kFrames; ++next)
            diffs.push_back(noteDiff(events[next].note, events[next].velocity, static_cast<int>(events[next].sample - start)));
        renderBatch(*device, diffs);
        for (int frame = 0; frame < kFrames; ++frame)
        {
            const double left = captured[0][static_cast<std::size_t>(frame)];
            const double right = captured[1][static_cast<std::size_t>(frame)];
            sumSquares += 0.5 * (left * left + right * right);
            sumMid += 0.25 * (left + right) * (left + right);
            sumSide += 0.25 * (right - left) * (right - left);
            peak = std::max({ peak, std::abs(left), std::abs(right) });
        }
        frames += kFrames;
    }

    PhraseLevels levels;
    levels.rmsDb = toDb(std::sqrt(sumSquares / static_cast<double>(frames)));
    levels.peakDb = toDb(peak);
    levels.sideToMidDb = toDb(std::sqrt(sumSide / std::max(sumMid, 1e-30)));
    levels.monoFoldDownDb = toDb(std::sqrt(sumMid / std::max(sumSquares, 1e-30)));
    return levels;
}

// The loudest of the five direct outs on a C3-E3-G3-C4 chord struck at
// velocity 127 with the patch's own mallet, over its first second.
double renderForteChordDirectPeak(const Patch& patch, double sampleRate)
{
    configureHost(patch);
    auto device = std::make_unique<CMaremba>(sampleRate);
    double peak = 0.0;
    for (int batch = 0; batch < batchesFor(1.0, sampleRate); ++batch)
    {
        std::vector<TJBox_PropertyDiff> diffs;
        if (batch == 0) diffs = { noteDiff(48, 127, 0), noteDiff(52, 127, 0), noteDiff(55, 127, 0), noteDiff(60, 127, 0) };
        peak = std::max(peak, renderBatch(*device, diffs).directPeak);
    }
    return peak;
}

void checkVoicing(const Patch& patch, double sampleRate)
{
    const std::string at = where(patch, sampleRate);
    const PhraseLevels phrase = renderPhrase(patch, sampleRate);
    const double directPeak = renderForteChordDirectPeak(patch, sampleRate);

    char detail[200];
    std::snprintf(detail, sizeof(detail), "phrase RMS %.1f dBFS, peak %.1f dBFS, S/M %+.1f dB, mono %+.1f dB; "
                  "ff chord direct peak %+.1f dBFS", phrase.rmsDb, phrase.peakDb, phrase.sideToMidDb,
                  phrase.monoFoldDownDb, toDb(directPeak));
    if (!(phrase.rmsDb >= kPhraseRmsMinDb && phrase.rmsDb <= kPhraseRmsMaxDb))
        fail(at + ": phrase loudness outside the bank's window (" + detail + ")");
    if (!(phrase.sideToMidDb <= kSideToMidMaxDb)) fail(at + ": side-heavy stereo image (" + detail + ")");
    if (!(phrase.monoFoldDownDb >= kMonoFoldDownMinDb)) fail(at + ": loses too much in mono (" + detail + ")");
    if (!(directPeak <= kDirectPeakMax)) fail(at + ": a direct out clips on a forte chord (" + detail + ")");
    std::printf("       %-34s %s\n", "", detail);
}

// The trap must see what the realtime path could allocate with: plain,
// nothrow and over-aligned new.
void checkAllocationTrap()
{
    struct alignas(64) Aligned { float values[16]; };
    static Aligned* volatile aligned = nullptr;
    static float* volatile nothrow = nullptr;
    static float* volatile plain = nullptr;
    forbiddenAllocations = 0;
    allocationForbidden = true;
    aligned = new Aligned;
    nothrow = new (std::nothrow) float[8];
    plain = new float[8];
    allocationForbidden = false;
    delete aligned;
    delete[] nothrow;
    delete[] plain;
    if (forbiddenAllocations != 3)
        fail("the allocation trap saw " + std::to_string(forbiddenAllocations) + " of 3 plain/nothrow/aligned allocations");
}

} // namespace

// --- JBox shim -------------------------------------------------------------------
TJBox_ObjectRef JBox_GetMotherboardObjectRef(const char* path) { return objectFor(path); }
TJBox_PropertyRef JBox_MakePropertyRef(TJBox_ObjectRef object, const char* key) { return propertyFor(object, key); }
TJBox_Value JBox_LoadMOMProperty(TJBox_PropertyRef property) { return properties[property].value; }

void JBox_StoreMOMProperty(TJBox_PropertyRef property, TJBox_Value value)
{
    if (properties[property].key != "noteon") fail("RenderBatch stored " + properties[property].key);
    properties[property].value = value;
}

TJBox_Float64 JBox_GetNumber(TJBox_Value value)
{
    if (decode(value).kind != Kind::Number) fail("JBox_GetNumber on a non-number");
    return decode(value).value;
}

TJBox_Bool JBox_GetBoolean(TJBox_Value value)
{
    if (decode(value).kind != Kind::Boolean) fail("JBox_GetBoolean on a non-boolean");
    return decode(value).value != 0.0;
}

TJBox_ValueType JBox_GetType(TJBox_Value value)
{
    const Kind kind = decode(value).kind;
    return kind == Kind::Number ? kJBox_Number : kind == Kind::Boolean ? kJBox_Boolean : kJBox_DSPBuffer;
}

TJBox_Value JBox_MakeBoolean(TJBox_Bool value) { return encode(Kind::Boolean, value != 0); }

TJBox_Float64 JBox_LoadMOMPropertyAsNumber(TJBox_ObjectRef object, TJBox_Tag tag)
{
    if (objects[object] == "/environment" && tag == kJBox_EnvironmentMasterTune) return 0.0;
    if (objects[object] == "/transport" && tag == kJBox_TransportRequestResetAudio) return 0.0;
    fail("unexpected JBox_LoadMOMPropertyAsNumber on " + objects[object]);
}

TJBox_Value JBox_LoadMOMPropertyByTag(TJBox_ObjectRef object, TJBox_Tag tag)
{
    if (objects[object] == "/transport" && tag == kJBox_TransportPlaying)
        return encode(Kind::Boolean, transportPlaying ? 1.0 : 0.0);
    if (tag != kJBox_AudioOutputBuffer) fail("unexpected JBox_LoadMOMPropertyByTag");
    return encode(Kind::Buffer, object);
}

void JBox_SetDSPBufferData(TJBox_Value value, TJBox_AudioFramePos first, TJBox_AudioFramePos last,
                           const TJBox_AudioSample audio[])
{
    if (first != 0 || last != kFrames) fail("partial DSP buffer write");
    const auto object = static_cast<TJBox_ObjectRef>(decode(value).value);
    for (int output = 0; output < kOutputs; ++output)
    {
        if (objects[object] != kOutputPaths[output]) continue;
        for (int frame = 0; frame < kFrames; ++frame)
            if (!std::isfinite(audio[frame])) fail(std::string("nonfinite sample on ") + kOutputPaths[output]);
        std::copy(audio, audio + kFrames, captured[static_cast<std::size_t>(output)].begin());
        wrote[static_cast<std::size_t>(output)] = true;
        return;
    }
    fail("write to an unknown output");
}

int main(int argc, char** argv)
{
    std::printf("=== All-patch render through CMaremba (host shim) ===\n");
    checkAllocationTrap();
    const fs::path directory = argc > 1 ? fs::path(argv[1])
                                        : fs::path(__FILE__).parent_path() / ".." / "Resources" / "Public";
    std::vector<fs::path> files;
    for (const auto& entry : fs::directory_iterator(directory))
        if (entry.path().extension() == ".repatch") files.push_back(entry.path());
    std::sort(files.begin(), files.end());
    if (files.empty()) fail("no .repatch files in " + directory.string());

    std::vector<Patch> patches;
    for (const auto& file : files) patches.push_back(loadPatch(file));
    std::printf("  %zu patches carry exactly the %d document properties\n", patches.size(),
                CMarembaTestAccess::parameterCount - static_cast<int>(kPerformanceProperties.size()));
    std::printf("  voicing: phrase RMS %.0f..%.0f dBFS, S/M <= %.0f dB, mono fold-down >= %.0f dB, "
                "ff chord direct outs <= 0 dBFS\n", kPhraseRmsMinDb, kPhraseRmsMaxDb, kSideToMidMaxDb, kMonoFoldDownMinDb);

    for (const auto& patch : patches)
        for (const double sampleRate : { 44100.0, 48000.0, 96000.0 })
        {
            renderChordAndStop(patch, sampleRate);
            checkVoicing(patch, sampleRate);
        }

    std::printf(">>> SUCCESS: all %zu factory patches render cleanly and sit in the bank's voicing window <<<\n",
                patches.size());
    return 0;
}
