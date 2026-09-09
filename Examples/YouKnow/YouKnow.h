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
    void AdvanceCalibrationGlide(int count);
    void HandleKeyModeReassert();
    void HandleCV();
    void StartMidiNote(int note, float velocity);
    void StopMidiNote(int note);
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
    // The engine combines MIDI and Gate CV into one keyboard. Keep MIDI's
    // ownership here so a stray MIDI off cannot release a CV-held key.
    std::array<std::uint16_t, 128> fMidiHeldCounts {};

    youknow::YouKnowEngine fEngine;
    double fSampleRate;
    float fPatchGainTarget;
    float fPatchGainSmoothed;
    float fPatchGainSmoothing;
    // Unit Character is automatable, and it is the one parameter whose change
    // rebuilds every voice card's analogue trims at once. Jumped across its
    // whole travel under a sounding note that rebuild is audible as a burst,
    // so the wrapper hands the engine a gliding value instead of the raw one.
    // Patch loads and resets still snap, so no stored sound is altered.
    youknow::EngineParameters fEngineParameters {};
    float fCalibrationTarget;
    float fCalibrationCurrent;
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
