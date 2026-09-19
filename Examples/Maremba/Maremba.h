#pragma once

#include "Jukebox.h"
#include "DSP/MarembaEngine.h"

#include <array>
#include <cstdint>

class CMaremba {
public:
    explicit CMaremba(double sampleRate);
    void RenderBatch(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount);

    // Host sample rates outside what the engine was sized for (or a
    // nonfinite one) fall back to a supported rate.
    static double SanitizeSampleRate(double sampleRate);

private:
    friend struct CMarembaTestAccess;

    enum EParameter {
        kModel,
        kMalletType,
        kMalletHardness,
        kStrikePosition,
        kStrikeJitter,
        kResonatorTune,
        kResonatorCoupling,
        kDecay,
        kBuzzAmount,
        kArtifacts,
        kSympathetic,
        kPitchGlide,
        kBodyBloom,
        kCloseLevel,
        kFarLevel,
        kPiezoLevel,
        kStereoWidth,
        kPreampDrive,
        kWarmth,
        kCompAmount,
        kCompAttack,
        kCompRelease,
        kVolume,
        kOversampling,
        kVelocityCurve,
        kPolyphony,
        kMasterTune,
        kDetune,
        kModWheel,
        kPitchBend,
        kParameterCount
    };

    // The /custom_properties name of every EParameter, in the same order.
    static constexpr std::array<const char*, kParameterCount> kParameterNames {
        "model",
        "malletType",
        "malletHardness",
        "strikePosition",
        "strikeJitter",
        "resonatorTune",
        "resonatorCoupling",
        "decay",
        "buzzAmount",
        "artifacts",
        "sympathetic",
        "pitchGlide",
        "bodyBloom",
        "closeLevel",
        "farLevel",
        "piezoLevel",
        "stereoWidth",
        "preampDrive",
        "warmth",
        "compAmount",
        "compAttack",
        "compRelease",
        "volume",
        "oversampling",
        "velocityCurve",
        "polyphony",
        "masterTune",
        "detune",
        "modWheel",
        "pitchBend"
    };

    // Every property's motherboard_def.lua default, in EParameter order. A
    // nonfinite host value reads as this default. The performance controllers
    // use the SDK's rest positions. Tests/validate_extension.py checks every
    // entry against the Lua declaration named in its comment.
    static constexpr std::array<double, kParameterCount> kParameterDefaults {
        0.0,    // model
        1.0,    // malletType (Medium Cord / Natural Thumb)
        0.40,   // malletHardness
        0.50,   // strikePosition
        0.15,   // strikeJitter
        0.50,   // resonatorTune
        0.70,   // resonatorCoupling
        0.1139, // decay
        0.15,   // buzzAmount
        0.35,   // artifacts
        0.40,   // sympathetic
        0.30,   // pitchGlide
        0.50,   // bodyBloom
        0.85,   // closeLevel
        0.45,   // farLevel
        0.30,   // piezoLevel
        0.50,   // stereoWidth
        0.15,   // preampDrive
        0.55,   // warmth
        0.25,   // compAmount
        0.1837, // compAttack
        0.2083, // compRelease
        0.80,   // volume
        0.0,    // oversampling (2x)
        1.0,    // velocityCurve (Linear)
        1.0,    // polyphony (16)
        0.50,   // masterTune
        0.0,    // detune
        0.0,    // modWheel
        0.50    // pitchBend
    };

    enum ECVInput {
        kNoteCV,
        kGateCV,
        kMalletCV,
        kPositionCV,
        kCouplingCV,
        kVolumeCV,
        kSympatheticCV,
        kCVCount
    };

    enum EOutput {
        kOutLeft,
        kOutRight,
        kOutCloseLeft,
        kOutCloseRight,
        kOutFarLeft,
        kOutFarRight,
        kOutPiezo,
        kOutputCount
    };

    static constexpr int kBatchFrames = 64;

    struct CVInput {
        TJBox_ObjectRef object = kJBox_InvalidObjectRef;
        TJBox_PropertyRef valueRef = kJBox_InvalidPropertyRef;
        TJBox_PropertyRef connectedRef = kJBox_InvalidPropertyRef;
        double value = 0.0;
        bool connected = false;
    };

    struct AudioOutput {
        TJBox_ObjectRef object = kJBox_InvalidObjectRef;
        TJBox_PropertyRef connectedRef = kJBox_InvalidPropertyRef;
        bool connected = false;
    };

    void SnapshotProperties();
    bool ApplyPropertyDiff(const TJBox_PropertyDiff& diff, bool previous = false);
    double Number(EParameter parameter) const;
    float Unit(EParameter parameter) const;
    float Modulated(EParameter parameter, ECVInput input, double extra = 0.0) const;
    void LoadEngineParameters();
    int CurrentCVNote();
    void HandleCV();
    void StartMidiNote(int note, float velocity);
    void StopMidiNote(int note);
    bool ResetIfRequested();
    void HandleTransport();
    void RenderRange(int first, int last);
    void WriteOutputs();
    void StrikeLamp();
    void SetNoteLamp(bool on);

    std::array<AudioOutput, kOutputCount> fOutputs;
    TJBox_ObjectRef fEnvironment = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fTransport = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fNoteStates = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fCustomProperties = kJBox_InvalidObjectRef;
    TJBox_PropertyRef fNoteOnLampRef = kJBox_InvalidPropertyRef;

    std::array<TJBox_PropertyRef, kParameterCount> fProperties {};
    std::array<double, kParameterCount> fValues {};
    std::array<CVInput, kCVCount> fCVInputs {};
    // MIDI holds per key, so a stray note-off cannot release a pitch that a
    // same-frame note-on has just struck (see RenderBatch).
    std::array<std::uint16_t, 128> fMidiHeldCounts {};

    maremba::MarembaEngine fEngine;
    double fSampleRate = 44100.0;
    double fLastResetCounter = 0.0;
    double fReasonMasterTune = 0.0;

    // One batch of rendered audio, in EOutput order.
    float fBuffers[kOutputCount][kBatchFrames];
    bool fRendered = false;

    float fLampSecondsRemaining = 0.0f;
    bool fNoteLampOn = false;
    bool fParametersLoaded = false;
    bool fTransportPlaying = false;

    // CV keyboard: the pitch last read from a connected Note CV (60 until one
    // is), and the note the Gate CV currently holds.
    int fCVPitch = 60;
    int fCVHeldNote = 60;
    bool fCVGateOn = false;
};
