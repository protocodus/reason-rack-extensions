#pragma once

#include "Jukebox.h"
#include "DSP/MarembaEngine.h"

#include <array>
#include <cstdint>

class CMaremba {
public:
    explicit CMaremba(double sampleRate);
    void RenderBatch(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount);

private:
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
        kRollSpeed,
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
        kSustainPedal,
        kParameterCount
    };

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
        0.0,    // rollSpeed
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
        0.50,   // pitchBend
        0.0     // sustainPedal
    };

    enum ECVInput {
        kNoteCV,
        kGateCV,
        kMalletCV,
        kPositionCV,
        kCouplingCV,
        kVolumeCV,
        kSympatheticCV,
        kRollCV,
        kCVCount
    };

    struct CVState {
        TJBox_ObjectRef object = kJBox_InvalidObjectRef;
        TJBox_PropertyRef valueRef = kJBox_InvalidPropertyRef;
        TJBox_PropertyRef connectedRef = kJBox_InvalidPropertyRef;
        double value = 0.0;
        bool connected = false;
    };

    void HandleNoteEvents(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount);
    void HandleCVEvents();
    void UpdateParameters();
    void ResetIfRequested();

    TJBox_ObjectRef fAudioOutLeft = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fAudioOutRight = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fAudioOutCloseL = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fAudioOutCloseR = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fAudioOutFarL = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fAudioOutFarR = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fAudioOutPiezo = kJBox_InvalidObjectRef;

    TJBox_ObjectRef fEnvironment = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fTransport = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fNoteStates = kJBox_InvalidObjectRef;
    TJBox_ObjectRef fCustomProperties = kJBox_InvalidObjectRef;

    TJBox_PropertyRef fNoteOnLampRef = kJBox_InvalidPropertyRef;
    TJBox_PropertyRef fActiveVoicesRef = kJBox_InvalidPropertyRef;

    std::array<TJBox_PropertyRef, kParameterCount> fProperties;
    std::array<double, kParameterCount> fValues;
    std::array<CVState, kCVCount> fCVInputs;

    maremba::MarembaEngine fEngine;
    double fSampleRate = 44100.0;
    double fLastResetCounter = 0.0;
    float fLampSecondsRemaining = 0.0f;
    bool fLampOn = false;

    // CV note state tracking
    int fLastCVNote = 60;
    bool fLastCVGateActive = false;
};
