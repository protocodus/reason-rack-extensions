// Host-shim contract for the Rack wrapper (CMaremba::RenderBatch) running the
// real MarembaEngine. The JBox_* functions below emulate the Jukebox MOM: they
// assert on realtime-illegal calls (MOM access from the constructor, stores to
// anything but the note lamp, nonfinite samples) and every global operator new
// (plain, nothrow and over-aligned) asserts while RenderBatch runs.
#include "../Maremba.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <new>
#include <string>
#include <vector>

// Volatile, so the check inside the replaced operators is never folded away.
namespace { volatile bool allocationForbidden = false; }

void* operator new(std::size_t size)
{
    assert(!allocationForbidden);
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
    assert(!allocationForbidden);
    return std::malloc(size == 0 ? 1 : size);
}
void* operator new[](std::size_t size, const std::nothrow_t& tag) noexcept { return ::operator new(size, tag); }
void operator delete(void* memory, const std::nothrow_t&) noexcept { std::free(memory); }
void operator delete[](void* memory, const std::nothrow_t&) noexcept { std::free(memory); }

// Over-aligned types (e.g. alignas(32) SIMD blocks) allocate through the
// align_val_t forms, which do not route through the plain operator new.
void* operator new(std::size_t size, std::align_val_t alignment, const std::nothrow_t&) noexcept
{
    assert(!allocationForbidden);
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
    static const maremba::MarembaEngine& engine(const CMaremba& device) { return device.fEngine; }
    static bool cvGateOn(const CMaremba& device) { return device.fCVGateOn; }
};

namespace {

// --- MOM emulation ----------------------------------------------------------
enum class Kind : std::uint64_t { Number, Boolean, Buffer };

struct Encoded
{
    Kind kind;
    double value;
};
static_assert(sizeof(Encoded) == sizeof(TJBox_Value), "TJBox_Value holds a kind and a double");

struct Property
{
    TJBox_ObjectRef object;
    std::string key;
    TJBox_Value value;
};

constexpr int kFrames = 64;
constexpr double kPi = 3.14159265358979323846;
const char* const kOutputPaths[] {
    "/audio_outputs/left", "/audio_outputs/right",
    "/audio_outputs/close_left", "/audio_outputs/close_right",
    "/audio_outputs/far_left", "/audio_outputs/far_right",
    "/audio_outputs/piezo",
};
constexpr int kOutputs = 7;
const char* const kCVPaths[] {
    "/cv_inputs/note_cv", "/cv_inputs/gate_cv", "/cv_inputs/mallet_cv",
    "/cv_inputs/position_cv", "/cv_inputs/coupling_cv", "/cv_inputs/volume_cv",
    "/cv_inputs/sympathetic_cv",
};

std::vector<std::string> objects { std::string() };
std::vector<Property> properties { Property {} };
double sampleRate = 48000.0;
double masterTune = 0.0;
double resetCounter = 0.0;
bool transportPlaying = false;
bool constructing = false;

struct Capture
{
    std::array<std::array<float, kFrames>, kOutputs> audio {};
    std::array<bool, kOutputs> wrote {};
    bool any() const { return std::find(wrote.begin(), wrote.end(), true) != wrote.end(); }
    float main(int frame) const { return audio[0][static_cast<std::size_t>(frame)] + audio[1][static_cast<std::size_t>(frame)]; }
};
Capture captured;

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
    Kind kind = Kind::Number;
    double value = 0.0;
    if (name == "connected" || name == "noteon") kind = Kind::Boolean;
    for (int index = 0; index < CMarembaTestAccess::parameterCount; ++index)
        if (name == CMarembaTestAccess::parameterName(index)) value = CMarembaTestAccess::parameterDefault(index);
    properties.push_back({ object, name, encode(kind, value) });
    return static_cast<TJBox_PropertyRef>(properties.size() - 1);
}

void set(const char* path, const char* key, Kind kind, double value)
{
    properties[propertyFor(objectFor(path), key)].value = encode(kind, value);
}

void setParam(const char* name, double value) { set("/custom_properties", name, Kind::Number, value); }

double get(const char* path, const char* key)
{
    return decode(properties[propertyFor(objectFor(path), key)].value).value;
}

bool lamp() { return get("/custom_properties", "noteon") != 0.0; }

int outputIndex(TJBox_ObjectRef object)
{
    for (int index = 0; index < kOutputs; ++index)
        if (objects[object] == kOutputPaths[index]) return index;
    assert(false);
    return 0;
}

// --- Diffs (a change also updates the MOM, as the host does) ------------------
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

TJBox_PropertyDiff change(const char* path, const char* key, Kind kind, double value, int frame)
{
    TJBox_PropertyDiff diff {};
    diff.fObjectRef = objectFor(path);
    diff.fPropertyRef = propertyFor(diff.fObjectRef, key);
    diff.fPreviousValue = properties[diff.fPropertyRef].value;
    diff.fCurrentValue = encode(kind, value);
    diff.fAtFrameIndex = static_cast<TJBox_UInt16>(frame);
    properties[diff.fPropertyRef].value = diff.fCurrentValue;
    return diff;
}

TJBox_PropertyDiff paramDiff(const char* name, double value, int frame)
{
    return change("/custom_properties", name, Kind::Number, value, frame);
}

TJBox_PropertyDiff cvDiff(const char* cv, double value, int frame)
{
    const std::string path = std::string("/cv_inputs/") + cv;
    return change(path.c_str(), "value", Kind::Number, value, frame);
}

TJBox_PropertyDiff cvConnect(const char* cv, bool connected, int frame)
{
    const std::string path = std::string("/cv_inputs/") + cv;
    return change(path.c_str(), "connected", Kind::Boolean, connected ? 1.0 : 0.0, frame);
}

TJBox_PropertyDiff outputConnect(const char* output, bool connected, int frame)
{
    const std::string path = std::string("/audio_outputs/") + output;
    return change(path.c_str(), "connected", Kind::Boolean, connected ? 1.0 : 0.0, frame);
}

// --- Host set-up and rendering -----------------------------------------------
// Every property at its default, no CV cables, the main pair cabled, the
// direct outputs not, transport stopped, no global tuning.
void configureHost()
{
    for (int index = 0; index < CMarembaTestAccess::parameterCount; ++index)
        setParam(CMarembaTestAccess::parameterName(index), CMarembaTestAccess::parameterDefault(index));
    set("/custom_properties", "noteon", Kind::Boolean, 0.0);
    for (const char* path : kCVPaths)
    {
        set(path, "connected", Kind::Boolean, 0.0);
        set(path, "value", Kind::Number, 0.0);
    }
    for (int index = 0; index < kOutputs; ++index)
        set(kOutputPaths[index], "connected", Kind::Boolean, index < 2 ? 1.0 : 0.0);
    masterTune = 0.0;
    resetCounter = 0.0;
    transportPlaying = false;
}

// A single clean partial to measure pitch on: no halo, body, buzz, glide,
// jitter or detune, and a long ring.
void configurePitchHost()
{
    configureHost();
    setParam("sympathetic", 0.0);
    setParam("bodyBloom", 0.0);
    setParam("buzzAmount", 0.0);
    setParam("artifacts", 0.0);
    setParam("pitchGlide", 0.0);
    setParam("strikeJitter", 0.0);
    setParam("detune", 0.0);
    setParam("decay", 0.4);
}

std::unique_ptr<CMaremba> makeDevice(double rate = sampleRate)
{
    constructing = true;
    auto device = std::make_unique<CMaremba>(rate);
    constructing = false;
    return device;
}

Capture render(CMaremba& device, const std::vector<TJBox_PropertyDiff>& diffs = {})
{
    captured = Capture {};
    allocationForbidden = true;
    device.RenderBatch(diffs.empty() ? nullptr : diffs.data(), static_cast<TJBox_UInt32>(diffs.size()));
    allocationForbidden = false;
    return captured;
}

// Main L+R over a number of batches; the first batch carries the diffs.
std::vector<float> renderMain(CMaremba& device, int batches, const std::vector<TJBox_PropertyDiff>& diffs = {})
{
    std::vector<float> out;
    out.reserve(static_cast<std::size_t>(batches * kFrames));
    for (int batch = 0; batch < batches; ++batch)
    {
        const Capture c = render(device, batch == 0 ? diffs : std::vector<TJBox_PropertyDiff> {});
        for (int frame = 0; frame < kFrames; ++frame) out.push_back(c.main(frame));
    }
    return out;
}

int batchesFor(double seconds) { return static_cast<int>(seconds * sampleRate / kFrames) + 1; }

double rms(const std::vector<float>& x, std::size_t first, std::size_t last)
{
    double sum = 0.0;
    for (std::size_t i = first; i < last; ++i) sum += static_cast<double>(x[i]) * x[i];
    return std::sqrt(sum / static_cast<double>(std::max<std::size_t>(1, last - first)));
}

double peak(const std::vector<float>& x)
{
    double result = 0.0;
    for (float s : x) result = std::max(result, static_cast<double>(std::abs(s)));
    return result;
}

// The strongest frequency within +/-spanCents of `expected` (Hann-windowed
// DFT scanned in 0.25-cent steps).
double peakFrequency(const std::vector<float>& x, double expected, double spanCents = 120.0)
{
    const std::size_t n = x.size();
    std::vector<double> windowed(n);
    for (std::size_t i = 0; i < n; ++i)
        windowed[i] = x[i] * (0.5 - 0.5 * std::cos(2.0 * kPi * static_cast<double>(i) / static_cast<double>(n - 1)));
    double bestFrequency = expected;
    double bestMagnitude = -1.0;
    for (double cents = -spanCents; cents <= spanCents; cents += 0.25)
    {
        const double frequency = expected * std::exp2(cents / 1200.0);
        const std::complex<double> step = std::polar(1.0, -2.0 * kPi * frequency / sampleRate);
        std::complex<double> phasor { 1.0, 0.0 };
        std::complex<double> sum { 0.0, 0.0 };
        for (std::size_t i = 0; i < n; ++i)
        {
            sum += windowed[i] * phasor;
            phasor *= step;
        }
        if (std::abs(sum) > bestMagnitude)
        {
            bestMagnitude = std::abs(sum);
            bestFrequency = frequency;
        }
    }
    return bestFrequency;
}

double cents(double frequency, double reference) { return 1200.0 * std::log2(frequency / reference); }
double noteHz(int note) { return 440.0 * std::exp2((note - 69) / 12.0); }

std::vector<float> slice(const std::vector<float>& x, double fromSeconds, double toSeconds)
{
    const auto first = static_cast<std::size_t>(fromSeconds * sampleRate);
    const auto last = std::min(x.size(), static_cast<std::size_t>(toSeconds * sampleRate));
    return std::vector<float>(x.begin() + static_cast<std::ptrdiff_t>(first), x.begin() + static_cast<std::ptrdiff_t>(last));
}

void expectPitch(const char* label, const std::vector<float>& x, double expectedHz, double toleranceCents = 4.0)
{
    const double measured = peakFrequency(x, expectedHz);
    const double error = cents(measured, expectedHz);
    std::printf("    %-44s %8.2f Hz (expected %8.2f, %+5.2f c)\n", label, measured, expectedHz, error);
    assert(std::abs(error) <= toleranceCents);
}

// True when b matches a within a small fraction of a's level over [first, last)
// (splitting a render at an event frame may round differently, a strike may not).
bool nearlyEqual(const std::vector<float>& a, const std::vector<float>& b, std::size_t first, std::size_t last)
{
    double difference = 0.0;
    double level = 0.0;
    for (std::size_t i = first; i < last; ++i)
    {
        difference += std::abs(static_cast<double>(a[i]) - b[i]);
        level += std::abs(static_cast<double>(a[i]));
    }
    return difference <= 1e-4 * level + 1e-9;
}

int firstAudible(const std::vector<float>& x, float threshold = 1e-7f)
{
    for (std::size_t i = 0; i < x.size(); ++i)
        if (std::abs(x[i]) > threshold) return static_cast<int>(i);
    return -1;
}

// --- Contracts ---------------------------------------------------------------
void testConstructionAndFirstBatch()
{
    configureHost();
    set("/custom_properties", "noteon", Kind::Boolean, 1.0); // left lit by a previous instance
    auto device = makeDevice();                               // asserts on any MOM access
    const Capture c = render(*device);
    assert(!lamp());      // JB-20: the first batch clears the inherited lamp
    assert(!c.any());     // nothing ever played: nothing written
    std::printf("  PASS construction touches no MOM; first batch clears the lamp\n");
}

void testSilentDeviceWritesNothing()
{
    configureHost();
    auto device = makeDevice();
    for (int batch = 0; batch < 50; ++batch) assert(!render(*device).any());
    // Knob moves, cable changes and CV on a silent device render nothing either.
    assert(!render(*device, { paramDiff("volume", 0.3, 5), outputConnect("close_left", true, 9),
                              cvConnect("mallet_cv", true, 12), cvDiff("mallet_cv", 0.4, 12) }).any());
    // A strike is written; once the bar and every tail have died, writes stop.
    const Capture c = render(*device, { noteDiff(72, 100, 0) });
    assert(c.wrote[0] && c.wrote[1] && c.wrote[2]);
    assert(!c.wrote[4] && !c.wrote[5] && !c.wrote[6]); // far and piezo have no cable
    render(*device, { paramDiff("decay", 0.0, 0) });
    transportPlaying = true;
    render(*device);
    transportPlaying = false; // stop: hand damping ends the ring
    // The engine reports silence (every voice and tail gone) in bounded time,
    // and from then on the device writes nothing.
    int silentAfter = -1;
    int lastWrite = -1;
    for (int batch = 0; batch < batchesFor(30.0); ++batch)
    {
        if (render(*device).any()) lastWrite = batch;
        if (CMarembaTestAccess::engine(*device).IsSilent())
        {
            silentAfter = batch;
            break;
        }
    }
    std::printf("    last write %d, engine silent %d batches after the stop\n", lastWrite, silentAfter);
    assert(silentAfter >= 0);
    assert(CMarembaTestAccess::engine(*device).GetActiveVoiceCount() == 0);
    for (int batch = 0; batch < 20; ++batch) assert(!render(*device).any());
    std::printf("  PASS silent device writes nothing (went silent %.2f s after the stop)\n",
                silentAfter * kFrames / sampleRate);
}

void testSampleAccurateNotes()
{
    configureHost();
    auto early = makeDevice();
    auto late = makeDevice();
    render(*early);
    render(*late);
    const auto a = renderMain(*early, 8, { noteDiff(69, 100, 0) });
    const auto b = renderMain(*late, 8, { noteDiff(69, 100, 40) });
    const int onsetA = firstAudible(a);
    const int onsetB = firstAudible(b);
    assert(onsetA >= 0 && onsetB >= 0);
    assert(onsetB - onsetA == 40);
    for (int i = 0; i < 40; ++i) assert(b[static_cast<std::size_t>(i)] == 0.0f);

    // Two keys at frames 5 and 40 of one batch both sound.
    auto two = makeDevice();
    render(*two);
    render(*two, { noteDiff(60, 90, 5), noteDiff(67, 90, 40) });
    assert(CMarembaTestAccess::engine(*two).GetActiveVoiceCount() == 2);

    // Frame indices above 63 (legacy hosts) clamp to the last frame.
    auto legacy = makeDevice();
    render(*legacy);
    const auto c = renderMain(*legacy, 8, { noteDiff(69, 100, 200) });
    assert(firstAudible(c) - onsetA == 63);
    std::printf("  PASS notes start at their frame (onset %d vs %d)\n", onsetB, onsetA);
}

// A strike takes the frame's parameters. The model is fixed at the strike
// (tuning is not: the engine retunes ringing bars, so it could not tell).
void testParameterBeforeNoteInSameFrame()
{
    configureHost();
    auto same = makeDevice();
    for (int batch = 0; batch < 4; ++batch) render(*same);
    // The note is listed before the model change; both are at frame 8.
    const auto a = renderMain(*same, 20, { noteDiff(60, 100, 8), paramDiff("model", 3.0, 8) });
    configureHost();
    setParam("model", 3.0);
    auto preset = makeDevice();
    for (int batch = 0; batch < 4; ++batch) render(*preset);
    const auto b = renderMain(*preset, 20, { noteDiff(60, 100, 8) });
    assert(peak(b) > 1e-3);
    assert(nearlyEqual(b, a, 0, a.size()));
    std::printf("  PASS a same-frame parameter change reaches the note\n");
}

void testFirstBatchSnapshot()
{
    // A song loads with masterTune +100 c and a note in the very first batch.
    configurePitchHost();
    setParam("masterTune", 1.0);
    auto loaded = makeDevice();
    const auto x = renderMain(*loaded, batchesFor(0.6), { noteDiff(69, 100, 0) });
    expectPitch("first-batch note uses the song's masterTune", slice(x, 0.15, 0.55), noteHz(70));

    // The MOM holds the batch's final value. Replayed from the pre-batch state,
    // frames before a model change at frame 60 must sound exactly as without
    // it, and a note after it is struck with the new model (a strike-time
    // parameter, so a late reload cannot hide behind a retune).
    configureHost();
    auto reference = makeDevice();
    const auto r = renderMain(*reference, 1, { noteDiff(81, 100, 0) });
    configureHost();
    auto device = makeDevice();
    const auto y = renderMain(*device, 1, { noteDiff(81, 100, 0), paramDiff("model", 3.0, 60) });
    assert(peak(r) > 1e-4);
    assert(nearlyEqual(r, y, 0, 60));

    configureHost();
    auto changed = makeDevice();
    const auto z = renderMain(*changed, 20, { paramDiff("model", 3.0, 60), noteDiff(69, 100, 62) });
    configureHost();
    setParam("model", 3.0);
    auto preset = makeDevice();
    const auto p = renderMain(*preset, 20, { noteDiff(69, 100, 62) });
    assert(peak(p) > 1e-3);
    assert(nearlyEqual(p, z, 0, p.size()));
    std::printf("  PASS first batch replays the batch from its pre-batch state\n");
}

void connectCVKeyboard(int note)
{
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/note_cv", "connected", Kind::Boolean, 1.0);
    set("/cv_inputs/note_cv", "value", Kind::Number, note / 127.0);
}

void testGateEdgesReplay()
{
    configureHost();
    connectCVKeyboard(60);
    auto a = makeDevice();
    render(*a);
    render(*a, { cvDiff("gate_cv", 0.8, 0) });
    assert(CMarembaTestAccess::engine(*a).GetActiveVoiceCount() == 1);
    for (int batch = 0; batch < 10; ++batch) render(*a);

    configureHost();
    connectCVKeyboard(60);
    auto b = makeDevice();
    render(*b);
    render(*b, { cvDiff("gate_cv", 0.8, 0) });
    for (int batch = 0; batch < 10; ++batch) render(*b);

    // Same pitch, gate low at 10 and high again at 40: a re-strike at 40.
    const auto ra = renderMain(*a, 4, { cvDiff("gate_cv", 0.0, 10), cvDiff("gate_cv", 0.8, 40) });
    const auto rb = renderMain(*b, 4);
    assert(nearlyEqual(rb, ra, 0, 40));
    assert(!nearlyEqual(rb, ra, 40, ra.size()));

    // Off and on at the same frame with a new pitch strikes the new pitch.
    const int before = CMarembaTestAccess::engine(*a).GetActiveVoiceCount();
    render(*a, { cvDiff("gate_cv", 0.0, 20), cvDiff("note_cv", 64 / 127.0, 20), cvDiff("gate_cv", 0.7, 20) });
    assert(CMarembaTestAccess::engine(*a).GetActiveVoiceCount() == before + 1);
    assert(CMarembaTestAccess::cvGateOn(*a));
    std::printf("  PASS every gate edge in a batch is replayed at its frame\n");
}

// WR-1: a first batch (new instance, or the batch after request_reset_audio)
// whose Note or Gate CV changes at frame 0 plays only the frame-0 state. The
// pre-batch state must not strike: a bar released in the same frame rings on.
void testFirstBatchCVKeyAtFrameZero()
{
    // Reference: the gate is already high on E4 when the instance starts.
    configureHost();
    connectCVKeyboard(64);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.8);
    auto reference = makeDevice();
    const auto r = renderMain(*reference, 20);
    assert(peak(r) > 1e-3);

    // Gate held on C4 before the batch, Note CV moves to E4 at frame 0: E4 only.
    configureHost();
    connectCVKeyboard(60);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.8);
    auto moved = makeDevice();
    const auto y = renderMain(*moved, 20, { cvDiff("note_cv", 64 / 127.0, 0) });
    assert(CMarembaTestAccess::engine(*moved).GetActiveVoiceCount() == 1);
    assert(nearlyEqual(r, y, 0, r.size()));

    // The same after an audio reset under a held C4 gate.
    configureHost();
    connectCVKeyboard(60);
    auto reset = makeDevice();
    render(*reset);
    render(*reset, { cvDiff("gate_cv", 0.8, 0) });
    for (int batch = 0; batch < 10; ++batch) render(*reset);
    resetCounter = 1.0;
    const auto x = renderMain(*reset, 20, { cvDiff("note_cv", 64 / 127.0, 0) });
    assert(CMarembaTestAccess::engine(*reset).GetActiveVoiceCount() == 1);
    assert(nearlyEqual(r, x, 0, r.size()));

    // Gate held on E4 and the Note CV cable pulled at frame 0: E4, the last
    // CV pitch, still strikes (not the unplugged default C4).
    configureHost();
    connectCVKeyboard(64);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.8);
    auto unplugged = makeDevice();
    const auto u = renderMain(*unplugged, 20, { cvConnect("note_cv", false, 0) });
    assert(CMarembaTestAccess::engine(*unplugged).GetActiveVoiceCount() == 1);
    assert(nearlyEqual(r, u, 0, r.size()));

    // Gate held before the batch and dropped at frame 0: nothing sounds.
    configureHost();
    connectCVKeyboard(60);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.8);
    auto dropped = makeDevice();
    const Capture c = render(*dropped, { cvDiff("gate_cv", 0.0, 0) });
    assert(CMarembaTestAccess::engine(*dropped).GetActiveVoiceCount() == 0);
    assert(!CMarembaTestAccess::cvGateOn(*dropped));
    assert(!lamp());
    assert(!c.any());
    std::printf("  PASS a first batch with a frame-0 Note/Gate CV edge plays only the frame-0 state\n");
}

void testGateUnplug()
{
    configureHost();
    connectCVKeyboard(62);
    auto a = makeDevice();
    render(*a);
    render(*a, { cvDiff("gate_cv", 0.8, 0) });
    configureHost();
    connectCVKeyboard(62);
    auto b = makeDevice();
    render(*b);
    render(*b, { cvDiff("gate_cv", 0.8, 0) });
    for (int batch = 0; batch < 20; ++batch)
    {
        render(*a);
        render(*b);
    }
    // Pull the gate cable while it is high: the latch clears.
    render(*a, { cvConnect("gate_cv", false, 10) });
    render(*b);
    assert(!CMarembaTestAccess::cvGateOn(*a));
    // Plug it back in with the gate still high: that is a new strike.
    const auto ra = renderMain(*a, 4, { cvConnect("gate_cv", true, 16) });
    const auto rb = renderMain(*b, 4);
    assert(CMarembaTestAccess::cvGateOn(*a));
    assert(!nearlyEqual(rb, ra, 0, ra.size()));
    std::printf("  PASS unplugging a high gate releases it; re-plugging strikes\n");
}

void testNoteCVUnplugged()
{
    // Gate-only: the pitch is the last CV note, initially 60.
    configurePitchHost();
    set("/cv_inputs/gate_cv", "connected", Kind::Boolean, 1.0);
    auto device = makeDevice();
    render(*device);
    const auto x = renderMain(*device, batchesFor(0.6), { cvDiff("gate_cv", 0.8, 0) });
    expectPitch("gate CV without note CV plays C4", slice(x, 0.15, 0.55), noteHz(60));

    // Pulling the Note CV cable under a held gate changes nothing at all.
    configureHost();
    connectCVKeyboard(64);
    auto a = makeDevice();
    render(*a);
    render(*a, { cvDiff("gate_cv", 0.8, 0) });
    configureHost();
    connectCVKeyboard(64);
    auto b = makeDevice();
    render(*b);
    render(*b, { cvDiff("gate_cv", 0.8, 0) });
    const auto ra = renderMain(*a, 20, { cvConnect("note_cv", false, 3) });
    const auto rb = renderMain(*b, 20);
    assert(nearlyEqual(rb, ra, 0, ra.size()));
    assert(CMarembaTestAccess::engine(*a).GetActiveVoiceCount() == CMarembaTestAccess::engine(*b).GetActiveVoiceCount());
    std::printf("  PASS unconnected note CV plays the last CV note and never re-strikes\n");
}

void testGateVelocityOne()
{
    configureHost();
    connectCVKeyboard(67);
    auto device = makeDevice();
    render(*device);
    const auto x = renderMain(*device, 10, { cvDiff("gate_cv", 1.0 / 127.0, 0) });
    assert(CMarembaTestAccess::cvGateOn(*device));
    assert(CMarembaTestAccess::engine(*device).GetActiveVoiceCount() == 1);
    assert(peak(x) > 1e-6);
    std::printf("  PASS a gate of velocity 1/127 strikes (peak %.2e)\n", peak(x));
}

// Note-state velocity (0..127) and the Gate CV level (velocity / 127) scale
// the strike (default Linear velocity curve).
void testVelocityScales()
{
    auto midi = [](int velocity) {
        configureHost();
        auto device = makeDevice();
        render(*device);
        return peak(renderMain(*device, 20, { noteDiff(60, velocity, 0) }));
    };
    auto gate = [](double level) {
        configureHost();
        connectCVKeyboard(60);
        auto device = makeDevice();
        render(*device);
        return peak(renderMain(*device, 20, { cvDiff("gate_cv", level, 0) }));
    };
    const double soft = midi(32), medium = midi(100), loud = midi(127);
    const double softGate = gate(0.25), loudGate = gate(1.0);
    std::printf("    peak at velocity 32/100/127: %.3f/%.3f/%.3f; gate 0.25/1.0: %.3f/%.3f\n",
                soft, medium, loud, softGate, loudGate);
    assert(soft < 0.5 * loud);
    assert(medium < 0.95 * loud);
    assert(softGate < 0.5 * loudGate);
    std::printf("  PASS MIDI velocity and gate level scale the strike\n");
}

void testMasterTune()
{
    const struct { double reason; double knob; double cents; const char* label; } cases[] {
        { 50.0, 0.5, 50.0, "Reason master tune +50 c" },
        { 0.0, 0.75, 50.0, "device masterTune +50 c" },
        { -100.0, 0.0, -200.0, "Reason -100 c + device -100 c" },
        { 250.0, 0.5, 100.0, "Reason master tune clamps to +100 c" },
        { std::numeric_limits<double>::quiet_NaN(), 0.5, 0.0, "nonfinite Reason master tune is 0 c" },
    };
    for (const auto& item : cases)
    {
        configurePitchHost();
        setParam("masterTune", item.knob);
        masterTune = item.reason;
        auto device = makeDevice();
        render(*device);
        const auto x = renderMain(*device, batchesFor(0.6), { noteDiff(69, 100, 0) });
        expectPitch(item.label, slice(x, 0.15, 0.55), 440.0 * std::exp2(item.cents / 1200.0));
    }
    // A change of the global tuning while the device runs is picked up.
    configurePitchHost();
    auto device = makeDevice();
    render(*device);
    masterTune = -50.0;
    const auto x = renderMain(*device, batchesFor(0.6), { noteDiff(69, 100, 0) });
    expectPitch("Reason master tune changed at run time", slice(x, 0.15, 0.55), 440.0 * std::exp2(-50.0 / 1200.0));
    std::printf("  PASS Reason master tune and device masterTune shift pitch\n");
}

void testPitchBendOnRingingNote()
{
    for (const double bend : { 1.0, 0.0 })
    {
        configurePitchHost();
        auto device = makeDevice();
        render(*device);
        renderMain(*device, batchesFor(0.1), { noteDiff(69, 100, 0) });
        // The bar is ringing; now move the wheel all the way.
        const auto x = renderMain(*device, batchesFor(0.5), { paramDiff("pitchBend", bend, 0) });
        expectPitch(bend > 0.5 ? "full bend up on a ringing A4" : "full bend down on a ringing A4",
                    slice(x, 0.1, 0.45), 440.0 * std::exp2((bend > 0.5 ? 200.0 : -200.0) / 1200.0));
    }
    std::printf("  PASS full pitch bend is +/-200 cents on a ringing note\n");
}

// Note-off never damps: a released MIDI key leaves every bar ringing exactly
// as a held one.
void testMidiNoteOffRingsFreely()
{
    auto play = [](bool release) {
        configureHost();
        auto device = makeDevice();
        render(*device);
        renderMain(*device, 10, { noteDiff(48, 110, 0), noteDiff(60, 110, 0) });
        return renderMain(*device, batchesFor(1.0), release ? std::vector<TJBox_PropertyDiff> { noteDiff(60, 0, 5) }
                                                             : std::vector<TJBox_PropertyDiff> {});
    };
    const auto held = play(false);
    const auto released = play(true);
    assert(peak(held) > 1e-3);
    assert(nearlyEqual(held, released, 0, held.size()));
    std::printf("  PASS a MIDI note-off leaves the bars ringing\n");
}

void testTransportStopDamps()
{
    auto play = [](bool stop) {
        configureHost();
        setParam("decay", 1.0);
        transportPlaying = true;
        auto device = makeDevice();
        render(*device);
        renderMain(*device, batchesFor(0.3), { noteDiff(48, 110, 0), noteDiff(60, 110, 0) });
        if (stop) transportPlaying = false;
        return renderMain(*device, batchesFor(1.5));
    };
    const auto ringing = play(false);
    const auto stopped = play(true);
    const std::size_t from = static_cast<std::size_t>(1.2 * sampleRate);
    const double ringingLevel = rms(ringing, from, ringing.size());
    const double stoppedLevel = rms(stopped, from, stopped.size());
    std::printf("    level 1.2 s after stop: %.2e vs %.2e still playing\n", stoppedLevel, ringingLevel);
    assert(ringingLevel > 1e-4);
    assert(stoppedLevel < 0.05 * ringingLevel);

    // A hand damp (T60 ~0.3-0.6 s), not a cut or a click: the first batch
    // after the stop keeps its level, and 50-100 ms later the bars are
    // clearly quieter but still sounding.
    const std::size_t early = static_cast<std::size_t>(0.05 * sampleRate);
    const std::size_t late = static_cast<std::size_t>(0.10 * sampleRate);
    const double first = rms(stopped, 0, kFrames) / rms(ringing, 0, kFrames);
    const double later = rms(stopped, early, late) / rms(ringing, early, late);
    std::printf("    after stop: first batch %.3f, 50-100 ms %.3f of the ringing level\n", first, later);
    assert(first >= 0.9);
    assert(later > 0.1 && later < 0.7);

    // Live play with the transport already stopped rings freely.
    configureHost();
    setParam("decay", 1.0);
    auto live = makeDevice();
    render(*live);
    renderMain(*live, batchesFor(0.3), { noteDiff(48, 110, 0), noteDiff(60, 110, 0) });
    const auto liveTail = renderMain(*live, batchesFor(1.5));
    assert(liveTail == ringing);
    std::printf("  PASS transport stop damps the ringing bars gently\n");
}

void testReset()
{
    configureHost();
    connectCVKeyboard(60);
    auto device = makeDevice();
    render(*device);
    render(*device, { noteDiff(64, 100, 0), cvDiff("gate_cv", 0.9, 0) });
    assert(lamp());
    for (int batch = 0; batch < 5; ++batch) assert(render(*device).any());
    resetCounter = 1.0;
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.0);
    const Capture c = render(*device);
    assert(!c.any());
    assert(!lamp());
    assert(!CMarembaTestAccess::cvGateOn(*device));
    assert(CMarembaTestAccess::engine(*device).GetActiveVoiceCount() == 0);

    // A nonfinite counter is not a reset request (it would otherwise reset
    // every batch).
    render(*device, { noteDiff(64, 100, 0) });
    resetCounter = std::numeric_limits<double>::quiet_NaN();
    for (int batch = 0; batch < 10; ++batch) assert(render(*device).any());
    assert(CMarembaTestAccess::engine(*device).GetActiveVoiceCount() > 0);
    std::printf("  PASS request_reset_audio silences the device and clears CV state\n");
}

// EV-16: request_reset_audio clears the gate latch, so a gate still held high
// through the reset strikes, as on a fresh instance.
void testResetClearsGateLatch()
{
    configureHost();
    connectCVKeyboard(60);
    auto device = makeDevice();
    render(*device);
    render(*device, { cvDiff("gate_cv", 0.9, 0) });
    for (int batch = 0; batch < 5; ++batch) render(*device);
    resetCounter = 1.0;
    const auto a = renderMain(*device, 10);

    configureHost();
    connectCVKeyboard(60);
    set("/cv_inputs/gate_cv", "value", Kind::Number, 0.9);
    auto fresh = makeDevice();
    const auto b = renderMain(*fresh, 10);
    assert(peak(b) > 1e-3);
    assert(nearlyEqual(b, a, 0, a.size()));
    std::printf("  PASS reset clears the gate latch: a held gate strikes again\n");
}

void testFuzz()
{
    const double bad[] {
        std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::infinity(),
        -std::numeric_limits<double>::infinity(), 1e30, -1e30, 7.3, -2.5,
    };
    configureHost();
    for (const char* cv : kCVPaths) set(cv, "connected", Kind::Boolean, 1.0);
    for (int index = 2; index < kOutputs; ++index) set(kOutputPaths[index], "connected", Kind::Boolean, 1.0);
    transportPlaying = true;
    auto device = makeDevice();
    render(*device);
    int note = 36;
    for (int index = 0; index < CMarembaTestAccess::parameterCount; ++index)
    {
        for (const double value : bad)
        {
            const char* name = CMarembaTestAccess::parameterName(index);
            render(*device, { paramDiff(name, value, 3), noteDiff(note, 100, 3), noteDiff(note, 0, 50) });
            render(*device); // SetDSPBufferData asserts every written sample is finite
            note = note >= 96 ? 36 : note + 5;
        }
        setParam(CMarembaTestAccess::parameterName(index), CMarembaTestAccess::parameterDefault(index));
        render(*device, { paramDiff(CMarembaTestAccess::parameterName(index), CMarembaTestAccess::parameterDefault(index), 0) });
    }
    for (const char* cv : { "note_cv", "gate_cv", "mallet_cv", "position_cv", "coupling_cv", "volume_cv", "sympathetic_cv" })
    {
        for (const double value : bad)
        {
            render(*device, { cvDiff(cv, value, 7), cvDiff("gate_cv", 0.0, 7), cvDiff("gate_cv", 0.9, 8),
                              noteDiff(note, 100, 9) });
            render(*device);
            note = note >= 96 ? 36 : note + 5;
        }
        render(*device, { cvDiff(cv, 0.0, 0) });
    }
    // A nonfinite note velocity reads as a release; a nonfinite note-on is ignored.
    render(*device, { noteDiff(60, std::numeric_limits<double>::quiet_NaN(), 0), noteDiff(61, 1e300, 1) });
    // Unsupported sample rates are sanitised.
    for (const double rate : { std::numeric_limits<double>::quiet_NaN(), -1.0, 1e9 })
    {
        auto odd = makeDevice(rate);
        render(*odd);
        render(*odd, { noteDiff(60, 100, 0) });
        render(*odd);
    }

    // Valid notes play again on the same instance.
    for (const char* cv : kCVPaths) set(cv, "value", Kind::Number, 0.0);
    render(*device, { cvDiff("gate_cv", 0.0, 0) });
    const auto x = renderMain(*device, 30, { noteDiff(72, 100, 0) });
    for (float s : x) assert(std::isfinite(s));
    assert(peak(x) > 1e-3);
    std::printf("  PASS NaN/Inf/out-of-range properties and CV keep every output finite\n");
}

void testMonoFold()
{
    auto program = [](bool left, bool right, bool close) {
        configureHost();
        set("/audio_outputs/left", "connected", Kind::Boolean, left ? 1.0 : 0.0);
        set("/audio_outputs/right", "connected", Kind::Boolean, right ? 1.0 : 0.0);
        set("/audio_outputs/close_left", "connected", Kind::Boolean, close ? 1.0 : 0.0);
        set("/audio_outputs/close_right", "connected", Kind::Boolean, close ? 1.0 : 0.0);
        auto device = makeDevice();
        render(*device);
        std::vector<Capture> out;
        for (int batch = 0; batch < 12; ++batch)
            out.push_back(render(*device, batch == 0 ? std::vector<TJBox_PropertyDiff> { noteDiff(36, 110, 0), noteDiff(96, 110, 0) }
                                                     : std::vector<TJBox_PropertyDiff> {}));
        return out;
    };
    const auto stereo = program(true, true, true);
    const auto leftOnly = program(true, false, false);
    const auto rightOnly = program(false, true, false);
    double side = 0.0;
    for (std::size_t batch = 0; batch < stereo.size(); ++batch)
    {
        assert(stereo[batch].wrote[0] && stereo[batch].wrote[1] && stereo[batch].wrote[2] && stereo[batch].wrote[3]);
        assert(leftOnly[batch].wrote[0] && !leftOnly[batch].wrote[1] && !leftOnly[batch].wrote[2]);
        assert(rightOnly[batch].wrote[1] && !rightOnly[batch].wrote[0]);
        for (std::size_t i = 0; i < kFrames; ++i)
        {
            const float mean = 0.5f * (stereo[batch].audio[0][i] + stereo[batch].audio[1][i]);
            assert(std::abs(leftOnly[batch].audio[0][i] - mean) <= 1e-6f);
            assert(std::abs(rightOnly[batch].audio[1][i] - mean) <= 1e-6f);
            side += std::abs(stereo[batch].audio[0][i] - stereo[batch].audio[1][i]);
        }
    }
    assert(side > 1e-3); // the pair really is stereo, so the fold is observable
    std::printf("  PASS one cable on the main pair carries the mean of L and R\n");
}

void testLamp()
{
    configureHost();
    connectCVKeyboard(60);
    auto device = makeDevice();
    render(*device);
    assert(!lamp());
    render(*device, { noteDiff(60, 100, 30) });
    assert(lamp());
    for (int batch = 0; batch < batchesFor(0.3); ++batch) render(*device);
    assert(!lamp()); // a ~0.25 s pulse per strike, not "while any voice rings"

    render(*device, { cvDiff("gate_cv", 0.8, 0) });
    assert(lamp());
    for (int batch = 0; batch < batchesFor(0.3); ++batch) render(*device);
    assert(!lamp());
    // A legato CV note under the held gate is a strike, so it lights the lamp.
    render(*device, { cvDiff("note_cv", 67 / 127.0, 12) });
    assert(lamp());
    std::printf("  PASS the Note On lamp pulses on every MIDI, gate and legato strike\n");
}

void testParameterChangesMidNote()
{
    // Oversampling, polyphony and model changes under ringing notes, with no
    // allocation (render() forbids it) and finite output.
    configureHost();
    auto device = makeDevice();
    render(*device);
    render(*device, { noteDiff(48, 100, 0), noteDiff(55, 100, 0), noteDiff(60, 100, 0), noteDiff(64, 100, 0) });
    for (const double oversampling : { 2.0, 1.0, 0.0, 2.0 })
    {
        render(*device, { paramDiff("oversampling", oversampling, 17), noteDiff(67, 90, 17) });
        for (int batch = 0; batch < 20; ++batch) render(*device);
    }
    render(*device, { paramDiff("polyphony", 0.0, 0) });
    for (int note = 40; note < 70; ++note) render(*device, { noteDiff(note, 100, note % 64) });
    render(*device, { paramDiff("polyphony", 2.0, 0), paramDiff("model", 3.0, 0) });
    for (int batch = 0; batch < 50; ++batch) render(*device);
    std::printf("  PASS oversampling/polyphony/model changes under ringing notes do not allocate\n");
}

// The contract's 0..1 -> physical mapping: every property reaches the engine
// with its documented scale, and each modulation CV and the mod wheel add to
// their knob. One CV diff per batch, so a CV diff alone must reload the engine.
void testParameterMapping()
{
    configureHost();
    auto device = makeDevice();
    render(*device);
    const maremba::EngineParameters& p = CMarembaTestAccess::engine(*device).GetParameters();
    auto near = [](double value, double expected) { return std::abs(value - expected) <= 1e-4; };

    render(*device, { paramDiff("strikeJitter", 0.25, 0), paramDiff("resonatorTune", 0.75, 0),
                      paramDiff("decay", 0.5, 0), paramDiff("stereoWidth", 0.75, 0), paramDiff("warmth", 0.25, 0),
                      paramDiff("compAttack", 0.5, 0), paramDiff("compRelease", 0.25, 0), paramDiff("detune", 0.3, 0),
                      paramDiff("closeLevel", 0.11, 0), paramDiff("farLevel", 0.22, 0), paramDiff("piezoLevel", 0.33, 0),
                      paramDiff("buzzAmount", 0.44, 0), paramDiff("artifacts", 0.55, 0), paramDiff("pitchGlide", 0.66, 0),
                      paramDiff("bodyBloom", 0.77, 0), paramDiff("preampDrive", 0.12, 0), paramDiff("compAmount", 0.34, 0),
                      paramDiff("masterTune", 0.75, 0), paramDiff("model", 2.0, 0), paramDiff("malletType", 3.0, 0),
                      paramDiff("velocityCurve", 3.0, 0), paramDiff("polyphony", 0.0, 0), paramDiff("oversampling", 1.0, 0) });
    assert(near(p.strikeJitter, 25.0));
    assert(near(p.resonatorTune, 25.0));
    assert(near(p.decay, 0.10 + 0.5 * 7.90));
    assert(near(p.stereoWidth, 1.5));
    assert(near(p.warmth, -0.5));
    assert(near(p.compAttack, 1.0 + 0.5 * 49.0));
    assert(near(p.compRelease, 20.0 + 0.25 * 480.0));
    assert(near(p.detune, 30.0));
    assert(near(p.tuneCents, 50.0));
    assert(near(p.closeLevel, 0.11) && near(p.farLevel, 0.22) && near(p.piezoLevel, 0.33));
    assert(near(p.buzzAmount, 0.44) && near(p.artifacts, 0.55) && near(p.pitchGlide, 0.66));
    assert(near(p.bodyBloom, 0.77) && near(p.preampDrive, 0.12) && near(p.compAmount, 0.34));
    assert(p.model == 2 && p.malletType == 3 && p.velocityCurve == 3 && p.polyphony == 0 && p.oversampling == 1);

    render(*device, { paramDiff("malletHardness", 0.2, 0), paramDiff("strikePosition", 0.3, 0),
                      paramDiff("resonatorCoupling", 0.4, 0), paramDiff("sympathetic", 0.5, 0), paramDiff("volume", 0.6, 0),
                      cvConnect("mallet_cv", true, 0), cvConnect("position_cv", true, 0), cvConnect("coupling_cv", true, 0),
                      cvConnect("volume_cv", true, 0), cvConnect("sympathetic_cv", true, 0) });
    render(*device, { cvDiff("mallet_cv", 0.1, 0) });
    assert(near(p.malletHardness, 0.3));
    render(*device, { cvDiff("position_cv", -0.2, 0) });
    assert(near(p.strikePosition, 0.1));
    render(*device, { cvDiff("coupling_cv", 0.3, 0) });
    assert(near(p.resonatorCoupling, 0.7));
    render(*device, { cvDiff("volume_cv", -0.1, 0) });
    assert(near(p.volume, 0.5));
    render(*device, { cvDiff("sympathetic_cv", 0.25, 0) });
    assert(near(p.sympathetic, 0.75));
    render(*device, { paramDiff("modWheel", 1.0, 0) });
    assert(near(p.malletHardness, 0.3 + 0.35));
    // Pulling the cable removes the CV term.
    render(*device, { cvConnect("mallet_cv", false, 0) });
    assert(near(p.malletHardness, 0.2 + 0.35));
    std::printf("  PASS every property, modulation CV and the mod wheel reach the engine as the contract maps them\n");
}

// Main L and R over 1 s of a chord struck on a fresh device with every output
// cabled, one property set and optionally one modulation CV plugged in.
struct Stereo
{
    std::vector<float> left;
    std::vector<float> right;
};

Stereo renderStrike(const char* parameter, double value, const char* cv, double cvValue, int velocity, int notes)
{
    configureHost();
    for (int index = 2; index < kOutputs; ++index) set(kOutputPaths[index], "connected", Kind::Boolean, 1.0);
    if (parameter != nullptr) setParam(parameter, value);
    if (cv != nullptr)
    {
        const std::string path = std::string("/cv_inputs/") + cv;
        set(path.c_str(), "connected", Kind::Boolean, 1.0);
        set(path.c_str(), "value", Kind::Number, cvValue);
    }
    auto device = makeDevice();
    render(*device);
    std::vector<TJBox_PropertyDiff> chord;
    for (int note = 0; note < notes; ++note) chord.push_back(noteDiff(48 + 3 * note, velocity, 0));
    Stereo out;
    for (int batch = 0; batch < batchesFor(1.0); ++batch)
    {
        const Capture c = render(*device, batch == 0 ? chord : std::vector<TJBox_PropertyDiff> {});
        out.left.insert(out.left.end(), c.audio[0].begin(), c.audio[0].end());
        out.right.insert(out.right.end(), c.audio[1].begin(), c.audio[1].end());
    }
    return out;
}

double maxDifference(const Stereo& a, const Stereo& b)
{
    double result = 0.0;
    for (std::size_t i = 0; i < a.left.size(); ++i)
    {
        result = std::max(result, static_cast<double>(std::abs(a.left[i] - b.left[i])));
        result = std::max(result, static_cast<double>(std::abs(a.right[i] - b.right[i])));
    }
    return result;
}

// MD-1: no control is dead. Each property (the performance controllers too)
// moved from its default to the far end of its range, and each modulation CV
// plugged in, must change the main output. strikePosition is symmetric about
// the middle, so "far end" is 1 when the default is below half the range,
// else 0 (step 0 or the last step for stepped properties).
void testEveryControlIsAudible()
{
    const Stereo base = renderStrike(nullptr, 0.0, nullptr, 0.0, 100, 1);
    // The engine is deterministic, so any difference below is the control's.
    assert(maxDifference(base, renderStrike(nullptr, 0.0, nullptr, 0.0, 100, 1)) == 0.0);

    int dead = 0;
    const char* weakest = "";
    double weakestDifference = std::numeric_limits<double>::infinity();
    auto check = [&](const char* control, double difference) {
        if (difference < weakestDifference)
        {
            weakestDifference = difference;
            weakest = control;
        }
        if (difference > 1e-4) return;
        std::printf("    DEAD %s (max |difference| %.2e)\n", control, difference);
        ++dead;
    };

    for (int index = 0; index < CMarembaTestAccess::parameterCount; ++index)
    {
        const char* name = CMarembaTestAccess::parameterName(index);
        const std::string key = name;
        const int steps = key == "model" || key == "malletType" || key == "velocityCurve" ? 4
            : key == "oversampling" || key == "polyphony" ? 3
            : 0;
        const double last = steps > 0 ? steps - 1.0 : 1.0;
        const double farEnd = CMarembaTestAccess::parameterDefault(index) < 0.5 * last ? last : 0.0;
        if (key == "velocityCurve")
        {
            // Near the middle of the range the curves are close to linear, so
            // compare the two outer curves at a medium velocity.
            check(name, maxDifference(renderStrike(name, 0.0, nullptr, 0.0, 64, 1),
                                      renderStrike(name, 2.0, nullptr, 0.0, 64, 1)));
        }
        else if (key == "polyphony")
        {
            // Only a chord larger than every voice limit can hear the limit.
            check(name, maxDifference(renderStrike(nullptr, 0.0, nullptr, 0.0, 100, 20),
                                      renderStrike(name, farEnd, nullptr, 0.0, 100, 20)));
        }
        else
        {
            check(name, maxDifference(base, renderStrike(name, farEnd, nullptr, 0.0, 100, 1)));
        }
    }
    for (const char* cv : { "mallet_cv", "position_cv", "coupling_cv", "volume_cv", "sympathetic_cv" })
    {
        const double value = std::strcmp(cv, "volume_cv") == 0 ? -0.5 : 0.5;
        check(cv, maxDifference(base, renderStrike(nullptr, 0.0, cv, value, 100, 1)));
    }
    assert(dead == 0);
    std::printf("  PASS every property and modulation CV changes the sound (weakest: %s, %.1e)\n",
                weakest, weakestDifference);
}

} // namespace

// --- JBox shim ---------------------------------------------------------------
TJBox_ObjectRef JBox_GetMotherboardObjectRef(const char* path) { return objectFor(path); }

TJBox_PropertyRef JBox_MakePropertyRef(TJBox_ObjectRef object, const char* key) { return propertyFor(object, key); }

TJBox_Value JBox_LoadMOMProperty(TJBox_PropertyRef property)
{
    assert(!constructing); // not allowed in CreateNativeObject
    assert(property > 0 && property < properties.size());
    return properties[property].value;
}

void JBox_StoreMOMProperty(TJBox_PropertyRef property, TJBox_Value value)
{
    assert(!constructing);
    assert(property > 0 && property < properties.size());
    assert(properties[property].key == "noteon"); // the only rt_owner property
    assert(decode(value).kind == Kind::Boolean);
    properties[property].value = value;
}

TJBox_Float64 JBox_GetNumber(TJBox_Value value)
{
    const auto decoded = decode(value);
    assert(decoded.kind == Kind::Number);
    return decoded.value;
}

TJBox_Bool JBox_GetBoolean(TJBox_Value value)
{
    const auto decoded = decode(value);
    assert(decoded.kind == Kind::Boolean);
    return decoded.value != 0.0;
}

TJBox_ValueType JBox_GetType(TJBox_Value value)
{
    switch (decode(value).kind)
    {
    case Kind::Number: return kJBox_Number;
    case Kind::Boolean: return kJBox_Boolean;
    default: return kJBox_DSPBuffer;
    }
}

TJBox_Value JBox_MakeBoolean(TJBox_Bool value) { return encode(Kind::Boolean, value != 0); }

TJBox_Float64 JBox_LoadMOMPropertyAsNumber(TJBox_ObjectRef object, TJBox_Tag tag)
{
    assert(!constructing);
    const auto& path = objects[object];
    if (path == "/environment" && tag == kJBox_EnvironmentMasterTune) return masterTune;
    if (path == "/environment" && tag == kJBox_EnvironmentSystemSampleRate) return sampleRate;
    if (path == "/transport" && tag == kJBox_TransportRequestResetAudio) return resetCounter;
    assert(false);
    return 0.0;
}

TJBox_Value JBox_LoadMOMPropertyByTag(TJBox_ObjectRef object, TJBox_Tag tag)
{
    assert(!constructing);
    if (objects[object] == "/transport" && tag == kJBox_TransportPlaying)
        return encode(Kind::Boolean, transportPlaying ? 1.0 : 0.0);
    assert(tag == kJBox_AudioOutputBuffer);
    return encode(Kind::Buffer, object);
}

void JBox_SetDSPBufferData(TJBox_Value value, TJBox_AudioFramePos first, TJBox_AudioFramePos last,
                           const TJBox_AudioSample audio[])
{
    assert(!constructing);
    assert(first == 0 && last == kFrames);
    const auto decoded = decode(value);
    assert(decoded.kind == Kind::Buffer);
    const int output = outputIndex(static_cast<TJBox_ObjectRef>(decoded.value));
    assert(!captured.wrote[static_cast<std::size_t>(output)]); // once per batch
    bool audible = false;
    for (int frame = 0; frame < kFrames; ++frame)
    {
        assert(std::isfinite(audio[frame]));
        audible = audible || std::abs(audio[frame]) >= kJBox_SilentThreshold;
    }
    assert(audible); // silent buffers are left unwritten
    std::copy(audio, audio + kFrames, captured.audio[static_cast<std::size_t>(output)].begin());
    captured.wrote[static_cast<std::size_t>(output)] = true;
}

#ifndef MAREMBA_WRAPPER_TEST_NO_MAIN
int main()
{
    std::printf("=== Maremba wrapper host contract (CMaremba::RenderBatch, %.0f Hz) ===\n", sampleRate);
    testConstructionAndFirstBatch();
    testSilentDeviceWritesNothing();
    testSampleAccurateNotes();
    testParameterBeforeNoteInSameFrame();
    testFirstBatchSnapshot();
    testGateEdgesReplay();
    testFirstBatchCVKeyAtFrameZero();
    testGateUnplug();
    testNoteCVUnplugged();
    testGateVelocityOne();
    testVelocityScales();
    testMasterTune();
    testPitchBendOnRingingNote();
    testMidiNoteOffRingsFreely();
    testTransportStopDamps();
    testReset();
    testResetClearsGateLatch();
    testFuzz();
    testMonoFold();
    testLamp();
    testParameterChangesMidNote();
    testParameterMapping();
    testEveryControlIsAudible();
    std::printf(">>> SUCCESS: wrapper host contract holds <<<\n");
    return 0;
}
#endif
