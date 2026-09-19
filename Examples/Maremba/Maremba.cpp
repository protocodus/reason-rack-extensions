#include "Maremba.h"

#include <algorithm>
#include <cmath>
#include <cstring>

namespace {
    double FiniteOr(double value, double fallback) {
        return std::isfinite(value) ? value : fallback;
    }

    // Round and clamp a stepped value in floating point before converting, so
    // no value can reach an undefined float-to-int conversion.
    int StepIndex(double value, int steps) {
        const double last = static_cast<double>(steps - 1);
        return static_cast<int>(std::floor(std::clamp(FiniteOr(value, 0.0), 0.0, last) + 0.5));
    }

    int EventFrame(const TJBox_PropertyDiff& diff) {
        // SDK 5 documents the legacy host fallback for indices above 63.
        return static_cast<int>(std::min<TJBox_UInt16>(diff.fAtFrameIndex, 63));
    }

    // A note state without a finite velocity carries no key press, so it reads
    // as a release, as a zero velocity does.
    float NoteVelocity(const TJBox_PropertyDiff& diff) {
        return static_cast<float>(std::clamp(FiniteOr(JBox_GetNumber(diff.fCurrentValue), 0.0), 0.0, 127.0));
    }

    bool IsSilentBuffer(const float* buffer, int count) {
        for (int i = 0; i < count; ++i) {
            if (std::abs(buffer[i]) >= kJBox_SilentThreshold) return false;
        }
        return true;
    }

    constexpr float kLampSeconds = 0.25f;          // Note On lamp pulse per strike
    constexpr double kReasonTuneLimitCents = 100.0; // Reason's global master tune range
    constexpr double kPitchBendRangeCents = 200.0;  // full wheel = +/-2 semitones
    constexpr double kModWheelHardness = 0.35;      // mod wheel adds up to this much mallet hardness
    // One cable on the main pair carries the mean of both channels (as YouKnow's mono jack).
    constexpr float kMonoFoldGain = 0.5f;

    const char* const kOutputPaths[] {
        "/audio_outputs/left", "/audio_outputs/right",
        "/audio_outputs/close_left", "/audio_outputs/close_right",
        "/audio_outputs/far_left", "/audio_outputs/far_right",
        "/audio_outputs/piezo",
    };

    const char* const kCVPaths[] {
        "/cv_inputs/note_cv", "/cv_inputs/gate_cv", "/cv_inputs/mallet_cv",
        "/cv_inputs/position_cv", "/cv_inputs/coupling_cv", "/cv_inputs/volume_cv",
        "/cv_inputs/sympathetic_cv",
    };
}

double CMaremba::SanitizeSampleRate(double sampleRate) {
    // The engine's delay lines are sized for 8x oversampling at 192 kHz.
    return std::isfinite(sampleRate) ? std::clamp(sampleRate, 22050.0, 192000.0) : 44100.0;
}

// CreateNativeObject may not touch the MOM: only object and property refs are
// made here. The first RenderBatch snapshots the MOM (see RenderBatch).
CMaremba::CMaremba(double sampleRate)
    : fEngine(SanitizeSampleRate(sampleRate))
    , fSampleRate(SanitizeSampleRate(sampleRate))
{
    static_assert(sizeof(kOutputPaths) / sizeof(kOutputPaths[0]) == kOutputCount, "one path per output");
    static_assert(sizeof(kCVPaths) / sizeof(kCVPaths[0]) == kCVCount, "one path per CV input");

    for (int i = 0; i < kOutputCount; ++i) {
        fOutputs[i].object = JBox_GetMotherboardObjectRef(kOutputPaths[i]);
        fOutputs[i].connectedRef = JBox_MakePropertyRef(fOutputs[i].object, "connected");
    }
    for (int i = 0; i < kCVCount; ++i) {
        fCVInputs[i].object = JBox_GetMotherboardObjectRef(kCVPaths[i]);
        fCVInputs[i].valueRef = JBox_MakePropertyRef(fCVInputs[i].object, "value");
        fCVInputs[i].connectedRef = JBox_MakePropertyRef(fCVInputs[i].object, "connected");
    }

    fEnvironment = JBox_GetMotherboardObjectRef("/environment");
    fTransport = JBox_GetMotherboardObjectRef("/transport");
    fNoteStates = JBox_GetMotherboardObjectRef("/note_states");
    fCustomProperties = JBox_GetMotherboardObjectRef("/custom_properties");
    for (int i = 0; i < kParameterCount; ++i) {
        fProperties[i] = JBox_MakePropertyRef(fCustomProperties, kParameterNames[i]);
    }
    fNoteOnLampRef = JBox_MakePropertyRef(fCustomProperties, "noteon");

    std::memset(fBuffers, 0, sizeof(fBuffers));

    // Start the engine from the declared defaults; the first batch replaces
    // them with the song's values before any note is struck.
    fValues = kParameterDefaults;
    LoadEngineParameters();
}

void CMaremba::SnapshotProperties() {
    for (int i = 0; i < kParameterCount; ++i) {
        fValues[i] = JBox_GetNumber(JBox_LoadMOMProperty(fProperties[i]));
    }
    for (auto& input : fCVInputs) {
        input.value = JBox_GetNumber(JBox_LoadMOMProperty(input.valueRef));
        input.connected = JBox_GetBoolean(JBox_LoadMOMProperty(input.connectedRef)) != 0;
    }
    for (auto& output : fOutputs) {
        output.connected = JBox_GetBoolean(JBox_LoadMOMProperty(output.connectedRef)) != 0;
    }
}

// Mirrors one diff into fValues / fCVInputs / fOutputs. Returns true when the
// engine parameters depend on the changed value.
bool CMaremba::ApplyPropertyDiff(const TJBox_PropertyDiff& diff, bool previous) {
    const TJBox_Value value = previous ? diff.fPreviousValue : diff.fCurrentValue;
    if (diff.fObjectRef == fCustomProperties) {
        for (int i = 0; i < kParameterCount; ++i) {
            if (diff.fPropertyRef == fProperties[i]) {
                fValues[i] = JBox_GetNumber(value);
                return true;
            }
        }
        return false;
    }
    for (int i = 0; i < kCVCount; ++i) {
        auto& input = fCVInputs[i];
        if (diff.fObjectRef != input.object) continue;
        if (diff.fPropertyRef == input.valueRef) {
            input.value = JBox_GetNumber(value);
        } else if (diff.fPropertyRef == input.connectedRef) {
            input.connected = JBox_GetBoolean(value) != 0;
        } else {
            return false;
        }
        return i >= kMalletCV;
    }
    for (auto& output : fOutputs) {
        if (diff.fObjectRef == output.object && diff.fPropertyRef == output.connectedRef) {
            output.connected = JBox_GetBoolean(value) != 0;
            return false;
        }
    }
    return false;
}

double CMaremba::Number(EParameter parameter) const {
    return FiniteOr(fValues[parameter], kParameterDefaults[parameter]);
}

// A normalised 0..1 control, clamped in double precision.
float CMaremba::Unit(EParameter parameter) const {
    return static_cast<float>(std::clamp(Number(parameter), 0.0, 1.0));
}

// Knob + CV (+ extra), clamped to 0..1. An unplugged or nonfinite CV adds nothing.
float CMaremba::Modulated(EParameter parameter, ECVInput input, double extra) const {
    const auto& cv = fCVInputs[input];
    const double amount = cv.connected ? FiniteOr(cv.value, 0.0) : 0.0;
    return static_cast<float>(std::clamp(Unit(parameter) + amount + extra, 0.0, 1.0));
}

void CMaremba::LoadEngineParameters() {
    maremba::EngineParameters p;
    p.model = StepIndex(Number(kModel), 4);
    p.malletType = StepIndex(Number(kMalletType), 4);
    p.malletHardness = Modulated(kMalletHardness, kMalletCV, kModWheelHardness * Unit(kModWheel));
    p.strikePosition = Modulated(kStrikePosition, kPositionCV);
    p.strikeJitter = Unit(kStrikeJitter) * 100.0f;
    p.resonatorTune = (Unit(kResonatorTune) - 0.5f) * 100.0f;
    p.resonatorCoupling = Modulated(kResonatorCoupling, kCouplingCV);
    p.decay = 0.10f + Unit(kDecay) * 7.90f;
    p.buzzAmount = Unit(kBuzzAmount);
    p.artifacts = Unit(kArtifacts);

    p.sympathetic = Modulated(kSympathetic, kSympatheticCV);
    p.pitchGlide = Unit(kPitchGlide);
    p.bodyBloom = Unit(kBodyBloom);

    p.closeLevel = Unit(kCloseLevel);
    p.farLevel = Unit(kFarLevel);
    p.piezoLevel = Unit(kPiezoLevel);
    p.stereoWidth = Unit(kStereoWidth) * 2.0f;

    p.preampDrive = Unit(kPreampDrive);
    p.warmth = (Unit(kWarmth) - 0.5f) * 2.0f;
    p.compAmount = Unit(kCompAmount);
    p.compAttack = 1.0f + Unit(kCompAttack) * 49.0f;
    p.compRelease = 20.0f + Unit(kCompRelease) * 480.0f;

    p.volume = Modulated(kVolume, kVolumeCV);
    p.oversampling = StepIndex(Number(kOversampling), 3);
    p.velocityCurve = StepIndex(Number(kVelocityCurve), 4);
    p.polyphony = StepIndex(Number(kPolyphony), 3);
    // Device Master Tune (+/-100 cents) plus Reason's global master tune.
    p.tuneCents = static_cast<float>((Unit(kMasterTune) - 0.5) * 200.0 + fReasonMasterTune);
    p.detune = Unit(kDetune) * 100.0f;

    fEngine.SetParameters(p);
    fEngine.SetPitchBendCents(static_cast<float>((Unit(kPitchBend) - 0.5) * 2.0 * kPitchBendRangeCents));
}

// The pitch of a connected Note CV, rounded in floating point. An unplugged
// (or nonfinite) Note CV keeps the last pitch, so gate-only use plays it and
// pulling the Note CV cable never re-strikes.
int CMaremba::CurrentCVNote() {
    const auto& input = fCVInputs[kNoteCV];
    if (input.connected && std::isfinite(input.value)) {
        fCVPitch = static_cast<int>(std::floor(std::clamp(input.value * 127.0, 0.0, 127.0) + 0.5));
    }
    return fCVPitch;
}

void CMaremba::HandleCV() {
    const auto& gate = fCVInputs[kGateCV];
    if (!gate.connected) {
        // Unplugging a high gate releases its note and clears the latch, so a
        // re-plugged high gate strikes again.
        if (fCVGateOn) {
            fEngine.NoteOff(fCVHeldNote);
            fCVGateOn = false;
        }
        return;
    }

    // Gate CV is velocity / 127: any velocity of 1 or more opens it.
    const double level = std::clamp(FiniteOr(gate.value, 0.0), 0.0, 1.0);
    const bool on = level * 127.0 >= 0.5;
    const int note = CurrentCVNote();

    if (fCVGateOn && on) {
        // Legato: a new pitch under a held gate strikes a new bar.
        if (note != fCVHeldNote) {
            fEngine.NoteOff(fCVHeldNote);
            fEngine.NoteOn(note, static_cast<float>(level));
            fCVHeldNote = note;
            StrikeLamp();
        }
        return;
    }
    if (fCVGateOn && !on) {
        fEngine.NoteOff(fCVHeldNote);
        fCVGateOn = false;
    }
    if (on && !fCVGateOn) {
        fEngine.NoteOn(note, static_cast<float>(level));
        fCVHeldNote = note;
        fCVGateOn = true;
        StrikeLamp();
    }
}

void CMaremba::StartMidiNote(int note, float velocity) {
    auto& held = fMidiHeldCounts[static_cast<std::size_t>(note)];
    if (held < 0xFFFF) ++held;
    fEngine.NoteOn(note, velocity);
    StrikeLamp();
}

void CMaremba::StopMidiNote(int note) {
    auto& held = fMidiHeldCounts[static_cast<std::size_t>(note)];
    if (held == 0) return;
    if (--held == 0) fEngine.NoteOff(note);
}

bool CMaremba::ResetIfRequested() {
    const double counter = JBox_LoadMOMPropertyAsNumber(fTransport, kJBox_TransportRequestResetAudio);
    // A nonfinite value is not a counter change; NaN would otherwise compare
    // unequal and reset the instrument on every batch.
    if (!std::isfinite(counter) || counter == 0.0 || counter == fLastResetCounter) return false;

    fEngine.Reset();
    fMidiHeldCounts.fill(0);
    fCVGateOn = false;
    fCVPitch = 60;
    fCVHeldNote = 60;
    fLastResetCounter = counter;
    fLampSecondsRemaining = 0.0f;
    SetNoteLamp(false);
    // The next steps re-read the whole MOM, as for a new instance.
    fParametersLoaded = false;
    return true;
}

// Note-off never damps (the bars ring freely), but when Reason's transport
// stops, every sounding bar gets the model's gentle hand damping.
void CMaremba::HandleTransport() {
    const TJBox_Value value = JBox_LoadMOMPropertyByTag(fTransport, kJBox_TransportPlaying);
    const TJBox_ValueType type = JBox_GetType(value);
    const bool playing = type == kJBox_Boolean ? JBox_GetBoolean(value) != 0
        : type == kJBox_Number ? FiniteOr(JBox_GetNumber(value), 0.0) != 0.0
        : false;
    if (fParametersLoaded && fTransportPlaying && !playing) {
        fEngine.DampAll();
    }
    fTransportPlaying = playing;
}

// Renders [first, last) of the batch. A silent engine is skipped and leaves
// its frames at zero; direct outputs without any cable are not computed.
void CMaremba::RenderRange(int first, int last) {
    const int count = last - first;
    if (count <= 0 || fEngine.IsSilent()) return;

    if (!fRendered) {
        std::memset(fBuffers, 0, sizeof(fBuffers));
        fRendered = true;
    }
    const bool close = fOutputs[kOutCloseLeft].connected || fOutputs[kOutCloseRight].connected;
    const bool far = fOutputs[kOutFarLeft].connected || fOutputs[kOutFarRight].connected;
    const bool piezo = fOutputs[kOutPiezo].connected;
    fEngine.RenderBatch(fBuffers[kOutLeft] + first, fBuffers[kOutRight] + first,
                        close ? fBuffers[kOutCloseLeft] + first : nullptr,
                        close ? fBuffers[kOutCloseRight] + first : nullptr,
                        far ? fBuffers[kOutFarLeft] + first : nullptr,
                        far ? fBuffers[kOutFarRight] + first : nullptr,
                        piezo ? fBuffers[kOutPiezo] + first : nullptr,
                        count);
}

void CMaremba::WriteOutputs() {
    // Last-resort guard: a nonfinite sample must never reach the host. Drop
    // the whole batch and start the engine over.
    for (const auto& buffer : fBuffers) {
        for (float sample : buffer) {
            if (!std::isfinite(sample)) {
                fEngine.Reset();
                return;
            }
        }
    }

    auto write = [this](int output, const float* buffer) {
        // An unwritten output is silent to Reason, so the chain after it can idle.
        if (IsSilentBuffer(buffer, kBatchFrames)) return;
        const TJBox_Value dsp = JBox_LoadMOMPropertyByTag(fOutputs[output].object, kJBox_AudioOutputBuffer);
        JBox_SetDSPBufferData(dsp, 0, kBatchFrames, buffer);
    };

    // One cable on the main pair carries both channels (the keyboard is
    // panned, so a single side would lose half of it).
    const bool leftConnected = fOutputs[kOutLeft].connected;
    const bool rightConnected = fOutputs[kOutRight].connected;
    if (leftConnected != rightConnected) {
        float* mono = fBuffers[kOutLeft];
        for (int i = 0; i < kBatchFrames; ++i) {
            mono[i] = kMonoFoldGain * (mono[i] + fBuffers[kOutRight][i]);
        }
        write(leftConnected ? kOutLeft : kOutRight, mono);
    } else {
        write(kOutLeft, fBuffers[kOutLeft]);
        write(kOutRight, fBuffers[kOutRight]);
    }

    for (int output = kOutCloseLeft; output < kOutputCount; ++output) {
        if (fOutputs[output].connected) write(output, fBuffers[output]);
    }
}

void CMaremba::StrikeLamp() {
    fLampSecondsRemaining = kLampSeconds;
    SetNoteLamp(true);
}

void CMaremba::SetNoteLamp(bool on) {
    if (on == fNoteLampOn) return;
    JBox_StoreMOMProperty(fNoteOnLampRef, JBox_MakeBoolean(on));
    fNoteLampOn = on;
}

void CMaremba::RenderBatch(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount) {
    ResetIfRequested();
    const bool firstBatch = !fParametersLoaded;
    // A first batch whose Note/Gate CV changes at frame 0 lets that frame's
    // replay set the gate (see below).
    bool cvKeyAtFrame0 = false;
    if (firstBatch) {
        // A re-created instance (e.g. after a sample-rate change) inherits the
        // previous instance's lamp value, so clear it unconditionally.
        JBox_StoreMOMProperty(fNoteOnLampRef, JBox_MakeBoolean(false));
        fNoteLampOn = false;
        fLampSecondsRemaining = 0.0f;

        // SDK 5 supplies final MOM values plus frame-ordered diffs. Undo the
        // nonzero-frame changes to recover the state at the start of the
        // batch; Note/Gate CV edges are undone at every frame, so each is
        // replayed exactly once below.
        SnapshotProperties();
        for (TJBox_UInt32 index = diffCount; index > 0; --index) {
            const auto& diff = propertyDiffs[index - 1];
            const bool cvKey = diff.fObjectRef == fCVInputs[kNoteCV].object
                || diff.fObjectRef == fCVInputs[kGateCV].object;
            if (cvKey && EventFrame(diff) == 0) cvKeyAtFrame0 = true;
            if (EventFrame(diff) > 0 || cvKey) {
                ApplyPropertyDiff(diff, true);
            }
        }
    }

    HandleTransport();

    // A nonfinite global tuning carries no offset; sanitise it before the
    // change test, which NaN would otherwise pass on every batch.
    const double reasonTune = std::clamp(
        FiniteOr(JBox_LoadMOMPropertyAsNumber(fEnvironment, kJBox_EnvironmentMasterTune), 0.0),
        -kReasonTuneLimitCents, kReasonTuneLimitCents);
    if (firstBatch || reasonTune != fReasonMasterTune) {
        fReasonMasterTune = reasonTune;
        LoadEngineParameters();
    }
    fParametersLoaded = true;
    if (cvKeyAtFrame0) {
        // Latch the pre-batch pitch only: striking the pre-batch state here
        // would sound a bar that frame 0 immediately re-pitches or releases,
        // and a released bar rings on. The frame-0 replay strikes instead.
        CurrentCVNote();
    } else {
        // Picks up a gate already high at the start of a first batch; otherwise a no-op.
        HandleCV();
    }

    fRendered = false;
    int renderedTo = 0;
    TJBox_UInt32 index = 0;
    while (index < diffCount) {
        const int frame = EventFrame(propertyDiffs[index]);
        RenderRange(renderedTo, frame);
        renderedTo = std::max(renderedTo, frame);
        TJBox_UInt32 end = index + 1;
        while (end < diffCount && EventFrame(propertyDiffs[end]) == frame) ++end;

        // 1. Automation, patch values and modulation CV at this frame form one
        //    control image: publish it before any note of the same frame (not
        //    once per batch: a strike keeps its frame's model and mallet).
        bool parametersChanged = false;
        for (TJBox_UInt32 item = index; item < end; ++item) {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef != fNoteStates
                && diff.fObjectRef != fCVInputs[kNoteCV].object
                && diff.fObjectRef != fCVInputs[kGateCV].object) {
                parametersChanged = ApplyPropertyDiff(diff) || parametersChanged;
            }
        }
        if (parametersChanged) LoadEngineParameters();

        // 2. Release the MIDI holds ending here. SDK 5 gives no tie-break
        //    within a frame, so an off for a key that is not held pairs with a
        //    same-frame on below (a zero-length note) instead of being lost.
        std::array<std::uint16_t, 128> remainingOffs {};
        for (TJBox_UInt32 item = index; item < end; ++item) {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef != fNoteStates || diff.fPropertyTag > 127 || NoteVelocity(diff) > 0.0f) continue;
            const auto note = static_cast<std::size_t>(diff.fPropertyTag);
            if (fMidiHeldCounts[note] != 0) {
                StopMidiNote(static_cast<int>(note));
            } else {
                ++remainingOffs[note];
            }
        }

        // 3. CV keyboard. Take the frame's pitch first, so Gate -> Note and
        //    Note -> Gate strike the same pitch, then replay every gate edge
        //    (an off/on pair in one frame re-strikes).
        bool hasGateEdges = false;
        for (TJBox_UInt32 item = index; item < end; ++item) {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef == fCVInputs[kNoteCV].object) {
                ApplyPropertyDiff(diff);
            } else if (diff.fObjectRef == fCVInputs[kGateCV].object) {
                hasGateEdges = true;
            }
        }
        bool handledPitch = false;
        for (TJBox_UInt32 item = index; item < end; ++item) {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef == fCVInputs[kNoteCV].object) {
                if (!hasGateEdges && !handledPitch) {
                    HandleCV();
                    handledPitch = true;
                }
            } else if (diff.fObjectRef == fCVInputs[kGateCV].object) {
                ApplyPropertyDiff(diff);
                HandleCV();
            }
        }

        // 4. MIDI strikes.
        for (TJBox_UInt32 item = index; item < end; ++item) {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef != fNoteStates || diff.fPropertyTag > 127) continue;
            const float velocity = NoteVelocity(diff);
            if (velocity <= 0.0f) continue;
            const auto note = static_cast<std::size_t>(diff.fPropertyTag);
            StartMidiNote(static_cast<int>(note), velocity / 127.0f);
            if (remainingOffs[note] != 0) {
                --remainingOffs[note];
                StopMidiNote(static_cast<int>(note));
            }
        }
        index = end;
    }
    RenderRange(renderedTo, kBatchFrames);

    if (fNoteLampOn) {
        fLampSecondsRemaining -= static_cast<float>(kBatchFrames / fSampleRate);
        if (fLampSecondsRemaining <= 0.0f) SetNoteLamp(false);
    }

    // Nothing rendered (a silent engine and no strike): leave every output
    // unwritten, which Reason treats as silence.
    if (fRendered) WriteOutputs();
}
