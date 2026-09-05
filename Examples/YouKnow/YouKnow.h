#pragma once

#include "DSP/YouKnowEngine.h"
#include "Jukebox.h"

#include <array>

class CYouKnow
{
public:
    explicit CYouKnow(double sampleRate);
    void RenderBatch(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount);

private:
    friend struct CYouKnowTestAccess;

    enum EParameter
    {
        kVolume,
        kPresetGain,
        kBenderDco,
        kBenderVcf,
        kBenderLfo,
        kPortamento,
        kKeyMode,
        kLfoRate,
        kLfoDelay,
        kDcoLfo,
        kPwm,
        kPwmMode,
        kRange,
        kSaw,
        kPulse,
        kSub,
        kNoise,
        kHighPass,
        kCutoff,
        kResonance,
        kEnvPolarity,
        kVcfEnv,
        kVcfLfo,
        kKeyFollow,
        kVcaMode,
        kVcaLevel,
        kAttack,
        kDecay,
        kSustain,
        kRelease,
        kChorus,
        kTranspose,
        kMasterTune,
        kVelocity,
        kCalibration,
        kAging,
        kChorusNoise,
        kPolyphony,
        kQuality,
        kVcfTanhMode,
        kVcfFastEarlyMode,
        kVcfSolverMode,
        kPitchBend,
        kModWheel,
        kSustainPedal,
        kParameterCount
    };

    enum ECVInput
    {
        kNoteCVInput, kGateCVInput, kCutoffCVInput, kResonanceCVInput,
        kVolumeCVInput, kVcaLevelCVInput, kSubCVInput, kNoiseCVInput,
        kCVInputCount
    };

    struct CVInput
    {
        TJBox_ObjectRef object;
        TJBox_PropertyRef valueProperty;
        TJBox_PropertyRef connectedProperty;
        double value = 0.0;
        bool connected = false;
    };

    static double ParameterValue(EParameter parameter, TJBox_Value value);
    void SnapshotProperties();
    bool ApplyPropertyDiff(const TJBox_PropertyDiff& diff, bool previous = false);
    double Number(EParameter parameter) const;
    bool Boolean(EParameter parameter) const;
    float Modulated(EParameter parameter, ECVInput input, bool multiply) const;
    void LoadEngineParameters(double reasonMasterTune);
    void HandleKeyModeReassert();
    void HandleCV();
    bool ResetIfRequested();
    void RenderRange(TJBox_AudioSample left[], TJBox_AudioSample right[],
                     int first, int last, bool qualityReady);
    void SetNoteLamp(bool on);

    TJBox_ObjectRef fAudioOutLeft;
    TJBox_ObjectRef fAudioOutRight;
    TJBox_ObjectRef fEnvironment;
    TJBox_ObjectRef fTransport;
    TJBox_ObjectRef fNoteStates;
    TJBox_ObjectRef fCustomProperties;
    TJBox_PropertyRef fNoteOn;
    TJBox_PropertyRef fKeyModeReassert;
    std::array<TJBox_PropertyRef, kParameterCount> fProperties;
    std::array<double, kParameterCount> fValues {};
    std::array<CVInput, kCVInputCount> fCVInputs {};

    youknow::YouKnowEngine fEngine;
    double fSampleRate;
    float fPatchGainTarget;
    float fPatchGainSmoothed;
    float fPatchGainSmoothing;
    double fLastResetCounter;
    int fTailSamplesRemaining;
    int fLastCVNote;
    bool fCVActive;
    bool fNoteLampOn;
    bool fKeyModeReassertPressed = false;
    bool fLastKeyModeReassert;
    bool fInitialQualityApplied;
    bool fParametersLoaded;
    double fLastReasonMasterTune;
    int fRequestedOversamplingFactor;
};
