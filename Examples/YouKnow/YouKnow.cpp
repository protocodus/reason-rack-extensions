#include "YouKnow.h"

#include "Constants.h"

#include <algorithm>
#include <cmath>

namespace
{
template <typename Enum>
Enum ClampedEnum(double value, int maximum)
{
    const int rounded = static_cast<int>(std::floor(value + 0.5));
    return static_cast<Enum>(std::clamp(rounded, 0, maximum));
}

int OversamplingFactor(double value)
{
    const int index = std::clamp(static_cast<int>(std::floor(value + 0.5)),
                                 0, 2);
    return youknow::YouKnowEngine::oversampleFactors[
        static_cast<std::size_t>(index)];
}

float PatchGain(double value)
{
    const double travel = std::isfinite(value)
                            ? std::clamp(value, 0.0, 1.0) : 0.5;
    return static_cast<float>(std::exp2((travel - 0.5) * 6.0));
}

int EventFrame(const TJBox_PropertyDiff& diff)
{
    // SDK 5 documents the legacy host fallback for indices above 63.
    return static_cast<int>(std::min<TJBox_UInt16>(
        diff.fAtFrameIndex, static_cast<TJBox_UInt16>(kBatchSize - 1)));
}

double FiniteCV(double value)
{
    return std::isfinite(value) ? value : 0.0;
}
}

CYouKnow::CYouKnow(double sampleRate)
    : fSampleRate(std::isfinite(sampleRate)
                      ? std::clamp(sampleRate,
                                   youknow::YouKnowEngine::minimumSupportedSampleRate,
                                   youknow::YouKnowEngine::maximumSupportedSampleRate)
                      : 48000.0),
      fPatchGainTarget(1.0f),
      fPatchGainSmoothed(1.0f),
      fPatchGainSmoothing(static_cast<float>(
          1.0 - std::exp(-1.0 / (0.005 * fSampleRate)))),
      fLastResetCounter(0.0),
      fTailSamplesRemaining(0),
      fLastCVNote(60),
      fCVActive(false),
      fNoteLampOn(false),
      fLastKeyModeReassert(false),
      fInitialQualityApplied(false),
      fParametersLoaded(false),
      fLastReasonMasterTune(0.0),
      fRequestedOversamplingFactor(1)
{
    fAudioOutLeft = JBox_GetMotherboardObjectRef("/audio_outputs/left");
    fAudioOutRight = JBox_GetMotherboardObjectRef("/audio_outputs/right");
    fEnvironment = JBox_GetMotherboardObjectRef("/environment");
    fTransport = JBox_GetMotherboardObjectRef("/transport");
    fNoteStates = JBox_GetMotherboardObjectRef("/note_states");

    const char* const cvPaths[] {
        "/cv_inputs/note_cv", "/cv_inputs/gate_cv",
        "/cv_inputs/cutoff_cv", "/cv_inputs/resonance_cv",
        "/cv_inputs/volume_cv", "/cv_inputs/vca_level_cv",
        "/cv_inputs/sub_cv", "/cv_inputs/noise_cv",
    };
    for (std::size_t index = 0; index < fCVInputs.size(); ++index)
    {
        auto& input = fCVInputs[index];
        input.object = JBox_GetMotherboardObjectRef(cvPaths[index]);
        input.valueProperty = JBox_MakePropertyRef(input.object, "value");
        input.connectedProperty = JBox_MakePropertyRef(input.object, "connected");
    }

    fCustomProperties = JBox_GetMotherboardObjectRef("/custom_properties");
#define PROPERTY(index, name) \
    fProperties[index] = JBox_MakePropertyRef(fCustomProperties, name)
    PROPERTY(kVolume, "volume");
    PROPERTY(kPresetGain, "presetGain");
    PROPERTY(kBenderDco, "benderDco");
    PROPERTY(kBenderVcf, "benderVcf");
    PROPERTY(kBenderLfo, "benderLfo");
    PROPERTY(kPortamento, "portamento");
    PROPERTY(kKeyMode, "keyMode");
    PROPERTY(kLfoRate, "lfoRate");
    PROPERTY(kLfoDelay, "lfoDelay");
    PROPERTY(kDcoLfo, "dcoLfo");
    PROPERTY(kPwm, "pwm");
    PROPERTY(kPwmMode, "pwmMode");
    PROPERTY(kRange, "range");
    PROPERTY(kSaw, "saw");
    PROPERTY(kPulse, "pulse");
    PROPERTY(kSub, "sub");
    PROPERTY(kNoise, "noise");
    PROPERTY(kHighPass, "highPass");
    PROPERTY(kCutoff, "cutoff");
    PROPERTY(kResonance, "resonance");
    PROPERTY(kEnvPolarity, "envPolarity");
    PROPERTY(kVcfEnv, "vcfEnv");
    PROPERTY(kVcfLfo, "vcfLfo");
    PROPERTY(kKeyFollow, "keyFollow");
    PROPERTY(kVcaMode, "vcaMode");
    PROPERTY(kVcaLevel, "vcaLevel");
    PROPERTY(kAttack, "attack");
    PROPERTY(kDecay, "decay");
    PROPERTY(kSustain, "sustain");
    PROPERTY(kRelease, "release");
    PROPERTY(kChorus, "chorus");
    PROPERTY(kTranspose, "transpose");
    PROPERTY(kMasterTune, "masterTune");
    PROPERTY(kVelocity, "velocity");
    PROPERTY(kCalibration, "calibration");
    PROPERTY(kAging, "aging");
    PROPERTY(kChorusNoise, "chorusNoise");
    PROPERTY(kPolyphony, "polyphony");
    PROPERTY(kQuality, "quality");
    PROPERTY(kVcfTanhMode, "vcfTanhMode");
    PROPERTY(kVcfFastEarlyMode, "vcfFastEarlyMode");
    PROPERTY(kVcfSolverMode, "vcfSolverMode");
    PROPERTY(kPitchBend, "pitchBend");
    PROPERTY(kModWheel, "modWheel");
    PROPERTY(kSustainPedal, "sustainPedal");
#undef PROPERTY
    fNoteOn = JBox_MakePropertyRef(fCustomProperties, "noteOn");
    fKeyModeReassert = JBox_MakePropertyRef(
        fCustomProperties, "keyModeReassertPress");

    fEngine.prepare(fSampleRate, static_cast<int>(kBatchSize),
                    OversamplingFactor(0.0));
}

void CYouKnow::HandleKeyModeReassert()
{
    const bool pressed = fKeyModeReassertPressed;
    if (pressed && !fLastKeyModeReassert)
        fEngine.reassertKeyMode();
    fLastKeyModeReassert = pressed;
}

double CYouKnow::ParameterValue(EParameter parameter, TJBox_Value value)
{
    return parameter == kSaw || parameter == kPulse
        ? (JBox_GetBoolean(value) != 0 ? 1.0 : 0.0) : JBox_GetNumber(value);
}

void CYouKnow::SnapshotProperties()
{
    for (std::size_t index = 0; index < fValues.size(); ++index)
        fValues[index] = ParameterValue(static_cast<EParameter>(index),
            JBox_LoadMOMProperty(fProperties[index]));
    for (auto& input : fCVInputs)
    {
        input.value = JBox_GetNumber(JBox_LoadMOMProperty(input.valueProperty));
        input.connected = JBox_GetBoolean(
            JBox_LoadMOMProperty(input.connectedProperty)) != 0;
    }
    fKeyModeReassertPressed = JBox_GetBoolean(
        JBox_LoadMOMProperty(fKeyModeReassert)) != 0;
}

bool CYouKnow::ApplyPropertyDiff(const TJBox_PropertyDiff& diff, bool previous)
{
    const auto value = previous ? diff.fPreviousValue : diff.fCurrentValue;
    if (diff.fObjectRef == fCustomProperties)
    {
        if (diff.fPropertyRef == fKeyModeReassert)
        {
            fKeyModeReassertPressed = JBox_GetBoolean(value) != 0;
            return false;
        }
        for (std::size_t index = 0; index < fProperties.size(); ++index)
            if (diff.fPropertyRef == fProperties[index])
            {
                fValues[index] = ParameterValue(static_cast<EParameter>(index), value);
                return true;
            }
    }
    for (std::size_t index = 0; index < fCVInputs.size(); ++index)
    {
        auto& input = fCVInputs[index];
        if (diff.fObjectRef != input.object)
            continue;
        if (diff.fPropertyRef == input.valueProperty)
            input.value = JBox_GetNumber(value);
        else if (diff.fPropertyRef == input.connectedProperty)
            input.connected = JBox_GetBoolean(value) != 0;
        else
            return false;
        return index >= kCutoffCVInput;
    }
    return false;
}

double CYouKnow::Number(EParameter parameter) const
{
    return fValues[parameter];
}

bool CYouKnow::Boolean(EParameter parameter) const
{
    return fValues[parameter] != 0.0;
}

float CYouKnow::Modulated(EParameter parameter, ECVInput input, bool multiply) const
{
    const auto& cv = fCVInputs[input];
    const double base = Number(parameter);
    if (!cv.connected)
        return static_cast<float>(base);
    const double amount = FiniteCV(cv.value);
    return static_cast<float>(std::clamp(
        multiply ? base * std::clamp(amount, 0.0, 1.0) : base + amount,
        0.0, 1.0));
}

void CYouKnow::LoadEngineParameters(double reasonMasterTune)
{
    using namespace youknow;
    EngineParameters parameters;

    parameters.volume = Modulated(kVolume, kVolumeCVInput, true);
    fPatchGainTarget = PatchGain(Number(kPresetGain));
    // A newly loaded patch may need much more attenuation than the previous
    // one. Never carry that stale, hotter makeup gain into the new circuit
    // state; downward changes take effect immediately, while upward changes
    // retain the click-suppressing five-millisecond glide below.
    if (!fParametersLoaded || fPatchGainSmoothed > fPatchGainTarget)
        fPatchGainSmoothed = fPatchGainTarget;
    parameters.benderDcoDepth = static_cast<float>(Number(kBenderDco));
    parameters.benderVcfDepth = static_cast<float>(Number(kBenderVcf));
    parameters.benderLfoDepth = static_cast<float>(Number(kBenderLfo));
    parameters.portamento = static_cast<float>(Number(kPortamento));
    parameters.keyMode = ClampedEnum<KeyMode>(Number(kKeyMode), 2);

    parameters.lfoRate = static_cast<float>(Number(kLfoRate));
    parameters.lfoDelay = static_cast<float>(Number(kLfoDelay));
    parameters.dcoLfoDepth = static_cast<float>(Number(kDcoLfo));
    parameters.pwmDepth = static_cast<float>(Number(kPwm));
    parameters.pwmSource = ClampedEnum<PwmSource>(Number(kPwmMode), 1);
    parameters.range = ClampedEnum<DcoRange>(Number(kRange), 2);
    parameters.sawEnabled = Boolean(kSaw);
    parameters.pulseEnabled = Boolean(kPulse);
    parameters.subLevel = Modulated(kSub, kSubCVInput, true);
    parameters.noiseLevel = Modulated(kNoise, kNoiseCVInput, true);

    parameters.highPass = ClampedEnum<HighPassMode>(Number(kHighPass), 3);
    parameters.cutoff = Modulated(kCutoff, kCutoffCVInput, false);
    parameters.resonance = Modulated(kResonance, kResonanceCVInput, false);
    parameters.envPolarity = ClampedEnum<EnvPolarity>(Number(kEnvPolarity), 1);
    parameters.envDepth = static_cast<float>(Number(kVcfEnv));
    parameters.vcfLfoDepth = static_cast<float>(Number(kVcfLfo));
    parameters.keyFollow = static_cast<float>(Number(kKeyFollow));

    parameters.vcaMode = ClampedEnum<VcaMode>(Number(kVcaMode), 1);
    parameters.vcaLevel = Modulated(kVcaLevel, kVcaLevelCVInput, true);
    parameters.attack = static_cast<float>(Number(kAttack));
    parameters.decay = static_cast<float>(Number(kDecay));
    parameters.sustain = static_cast<float>(Number(kSustain));
    parameters.release = static_cast<float>(Number(kRelease));
    parameters.chorus = ClampedEnum<ChorusMode>(Number(kChorus), 3);

    parameters.keyTranspose = std::clamp(static_cast<int>(Number(kTranspose)) - 12,
                                         -12, 12);
    parameters.masterTuneCents = static_cast<float>(
        reasonMasterTune + (Number(kMasterTune) * 100.0 - 50.0));
    parameters.velocityDepth = static_cast<float>(Number(kVelocity));
    parameters.calibration = static_cast<float>(Number(kCalibration) * 2.0);
    parameters.aging = static_cast<float>(Number(kAging));
    parameters.chorusNoise = static_cast<float>(Number(kChorusNoise));
    parameters.polyphony = std::clamp(static_cast<int>(Number(kPolyphony)) + 1,
                                      1, YouKnowEngine::maxVoices);
    parameters.vcfTanhMode = ClampedEnum<VcfTanhMode>(
        Number(kVcfTanhMode), 2);
    parameters.vcfFastEarlyMode = ClampedEnum<VcfFastEarlyMode>(
        Number(kVcfFastEarlyMode), 1);
    parameters.vcfSolverMode = ClampedEnum<VcfSolverMode>(
        Number(kVcfSolverMode), 2);
    fRequestedOversamplingFactor = OversamplingFactor(Number(kQuality));

    fEngine.setParameters(parameters);
    fEngine.setPitchBend(static_cast<float>(Number(kPitchBend) * 2.0 - 1.0));
    fEngine.setModWheel(static_cast<float>(Number(kModWheel)));
    fEngine.setSustainPedal(Number(kSustainPedal) >= 0.5);
}

void CYouKnow::HandleCV()
{
    const auto& gateInput = fCVInputs[kGateCVInput];
    const bool connected = gateInput.connected;
    if (!connected)
    {
        if (fCVActive)
            fEngine.noteOff(fLastCVNote);
        fCVActive = false;
        return;
    }

    const double gate = std::clamp(FiniteCV(gateInput.value), 0.0, 1.0);
    const int note = std::clamp(static_cast<int>(
        std::clamp(FiniteCV(fCVInputs[kNoteCVInput].value), 0.0, 1.0)
            * 127.0 + 0.1), 0, 127);
    const bool on = gate > 0.0;

    if (fCVActive && on && note != fLastCVNote)
    {
        if (!fEngine.retargetHeldNoteLegato(fLastCVNote, note))
        {
            // MIDI/CV overlap and a pending assigner rescan have no unique
            // voice to retarget. Preserve the existing balanced fallback.
            fEngine.noteOff(fLastCVNote);
            fEngine.noteOn(note, static_cast<float>(gate));
        }
        fLastCVNote = note;
        return;
    }

    if (fCVActive && !on)
    {
        fEngine.noteOff(fLastCVNote);
        fCVActive = false;
    }
    if (on && !fCVActive)
    {
        fEngine.noteOn(note, static_cast<float>(gate));
        fLastCVNote = note;
        fCVActive = true;
    }
}

bool CYouKnow::ResetIfRequested()
{
    const double counter = JBox_LoadMOMPropertyAsNumber(
        fTransport, kJBox_TransportRequestResetAudio);
    if (counter != 0.0 && counter != fLastResetCounter)
    {
        fEngine.reset();
        fTailSamplesRemaining = 0;
        fCVActive = false;
        fLastResetCounter = counter;
        SetNoteLamp(false);
        return true;
    }
    return false;
}

void CYouKnow::RenderRange(TJBox_AudioSample left[], TJBox_AudioSample right[],
                              int first, int last, bool qualityReady)
{
    const int count = last - first;
    if (count <= 0)
        return;

    const bool voicesActive = fEngine.getActiveVoiceCount() > 0;
    if (voicesActive || fTailSamplesRemaining > 0)
    {
        fEngine.process(left + first, right + first, count);
        if (fEngine.getActiveVoiceCount() > 0)
            fTailSamplesRemaining = static_cast<int>(
                fSampleRate * kOutputTailSeconds);
        else
            fTailSamplesRemaining = std::max(0, fTailSamplesRemaining - count);
    }

    // A live quality change and a Key Mode assigner rescan both need private
    // processing while no voice is active. Without the latter, an idle preset
    // switch can leave the next Note On held but unassigned forever because
    // Reason is correctly told that every skipped output buffer is silent.
    else if (!qualityReady || fEngine.hasPendingVoiceAssignment())
    {
        TJBox_AudioSample scratchLeft[kBatchSize] {};
        TJBox_AudioSample scratchRight[kBatchSize] {};
        fEngine.process(scratchLeft, scratchRight, count);
    }

    // Apply the patch trim inside the event interval so a timed patch change
    // cannot alter audio rendered before its notification. Keep upward makeup
    // smooth and apply downward attenuation at the exact change boundary.
    for (int sample = first; sample < last; ++sample)
    {
        fPatchGainSmoothed +=
            (fPatchGainTarget - fPatchGainSmoothed) * fPatchGainSmoothing;
        left[sample] *= fPatchGainSmoothed;
        right[sample] *= fPatchGainSmoothed;
    }
}

void CYouKnow::SetNoteLamp(bool on)
{
    if (on == fNoteLampOn)
        return;
    JBox_StoreMOMProperty(fNoteOn, JBox_MakeBoolean(on));
    fNoteLampOn = on;
}

void CYouKnow::RenderBatch(const TJBox_PropertyDiff propertyDiffs[],
                              TJBox_UInt32 diffCount)
{
    const bool resetRequested = ResetIfRequested();
    const bool needsSnapshot = !fParametersLoaded || resetRequested;
    if (needsSnapshot)
    {
        SnapshotProperties();
        // SDK 5 supplies final MOM values and frame-ordered diffs. On initial
        // restore/reset, undo nonzero-frame control changes to recover startup.
        // Gates and gestures also undo frame-zero edges, which must be replayed
        // exactly once rather than inferred from their final snapshot.
        // Cache numbers/bools only: TJBox_Value must not outlive this callback.
        for (TJBox_UInt32 index = diffCount; index > 0; --index)
        {
            const auto& diff = propertyDiffs[index - 1];
            if (EventFrame(diff) > 0
                || diff.fObjectRef == fCVInputs[kNoteCVInput].object
                || diff.fObjectRef == fCVInputs[kGateCVInput].object
                || (diff.fObjectRef == fCustomProperties
                    && diff.fPropertyRef == fKeyModeReassert))
                ApplyPropertyDiff(diff, true);
        }
    }

    if (!fInitialQualityApplied)
    {
        fRequestedOversamplingFactor = OversamplingFactor(Number(kQuality));
        fEngine.setInitialOversamplingFactor(fRequestedOversamplingFactor);
        fInitialQualityApplied = true;
    }

    const double reasonMasterTune = JBox_LoadMOMPropertyAsNumber(
        fEnvironment, kJBox_EnvironmentMasterTune);
    if (needsSnapshot || reasonMasterTune != fLastReasonMasterTune)
    {
        LoadEngineParameters(reasonMasterTune);
        if (resetRequested)
            fPatchGainSmoothed = fPatchGainTarget;
        fParametersLoaded = true;
        fLastReasonMasterTune = reasonMasterTune;
    }

    HandleKeyModeReassert();
    HandleCV();
    bool qualityReady = fEngine.setOversamplingFactor(fRequestedOversamplingFactor);
    TJBox_AudioSample left[kBatchSize] {};
    TJBox_AudioSample right[kBatchSize] {};

    int renderedTo = 0;
    TJBox_UInt32 index = 0;
    while (index < diffCount)
    {
        const int eventFrame = EventFrame(propertyDiffs[index]);
        RenderRange(left, right, renderedTo, eventFrame, qualityReady);
        renderedTo = eventFrame;
        TJBox_UInt32 end = index + 1;
        while (end < diffCount && EventFrame(propertyDiffs[end]) == eventFrame)
            ++end;

        // An automation value and its CV arriving together form one effective
        // control image. Publish it before accepting any notes at that frame.
        bool parametersChanged = false;
        for (TJBox_UInt32 item = index; item < end; ++item)
        {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef != fCVInputs[kNoteCVInput].object
                && diff.fObjectRef != fCVInputs[kGateCVInput].object
                && !(diff.fObjectRef == fCustomProperties
                     && diff.fPropertyRef == fKeyModeReassert))
                parametersChanged = ApplyPropertyDiff(diff) || parametersChanged;
        }
        if (parametersChanged)
            LoadEngineParameters(reasonMasterTune);
        qualityReady = fEngine.setOversamplingFactor(fRequestedOversamplingFactor);

        for (TJBox_UInt32 item = index; item < end; ++item)
        {
            const auto& diff = propertyDiffs[item];
            if (diff.fObjectRef == fCVInputs[kNoteCVInput].object
                || diff.fObjectRef == fCVInputs[kGateCVInput].object)
            {
                // Note/Gate edges are events, including same-frame retriggers.
                ApplyPropertyDiff(diff);
                HandleCV();
            }
            else if (diff.fObjectRef == fCustomProperties
                && diff.fPropertyRef == fKeyModeReassert)
            {
                // Preserve a press/release pair even at the same frame.
                fKeyModeReassertPressed = JBox_GetBoolean(diff.fCurrentValue) != 0;
                HandleKeyModeReassert();
            }
            else if (diff.fObjectRef == fNoteStates)
            {
                const int note = static_cast<int>(
                    std::min<TJBox_Tag>(diff.fPropertyTag, 127));
                const float velocity = static_cast<float>(std::clamp(
                    FiniteCV(JBox_GetNumber(diff.fCurrentValue)), 0.0, 127.0));
                if (velocity > 0.0f)
                    fEngine.noteOn(note, velocity / 127.0f);
                else
                    fEngine.noteOff(note);
            }
        }
        index = end;
    }
    RenderRange(left, right, renderedTo, static_cast<int>(kBatchSize), qualityReady);

    SetNoteLamp(fEngine.getActiveVoiceCount() > 0);

    bool audible = false;
    for (std::size_t sample = 0; sample < kBatchSize; ++sample)
    {
        if (std::abs(left[sample]) > kJBox_SilentThreshold
            || std::abs(right[sample]) > kJBox_SilentThreshold)
        {
            audible = true;
            break;
        }
    }
    if (!audible)
        return;

    const TJBox_Value leftOutput = JBox_LoadMOMPropertyByTag(
        fAudioOutLeft, kJBox_AudioOutputBuffer);
    const TJBox_Value rightOutput = JBox_LoadMOMPropertyByTag(
        fAudioOutRight, kJBox_AudioOutputBuffer);
    JBox_SetDSPBufferData(leftOutput, 0, static_cast<int>(kBatchSize), left);
    JBox_SetDSPBufferData(rightOutput, 0, static_cast<int>(kBatchSize), right);
}
