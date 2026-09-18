#include "Maremba.h"
#include <algorithm>
#include <cmath>

namespace {
    inline double LoadNumberProperty(TJBox_PropertyRef ref, double defaultVal) {
        if (ref == kJBox_InvalidPropertyRef) return defaultVal;
        TJBox_Value val = JBox_LoadMOMProperty(ref);
        return JBox_GetNumber(val);
    }

    inline bool LoadBooleanProperty(TJBox_PropertyRef ref, bool defaultVal) {
        if (ref == kJBox_InvalidPropertyRef) return defaultVal;
        TJBox_Value val = JBox_LoadMOMProperty(ref);
        return JBox_GetBoolean(val);
    }
}

CMaremba::CMaremba(double sampleRate)
    : fEngine(sampleRate)
    , fSampleRate(sampleRate > 8000.0 ? sampleRate : 44100.0)
{
    fValues = kParameterDefaults;

    // Motherboard objects
    fAudioOutLeft = JBox_GetMotherboardObjectRef("/audio_outputs/left");
    fAudioOutRight = JBox_GetMotherboardObjectRef("/audio_outputs/right");
    fAudioOutCloseL = JBox_GetMotherboardObjectRef("/audio_outputs/close_left");
    fAudioOutCloseR = JBox_GetMotherboardObjectRef("/audio_outputs/close_right");
    fAudioOutFarL = JBox_GetMotherboardObjectRef("/audio_outputs/far_left");
    fAudioOutFarR = JBox_GetMotherboardObjectRef("/audio_outputs/far_right");
    fAudioOutPiezo = JBox_GetMotherboardObjectRef("/audio_outputs/piezo");

    fEnvironment = JBox_GetMotherboardObjectRef("/environment");
    fTransport = JBox_GetMotherboardObjectRef("/transport");
    fNoteStates = JBox_GetMotherboardObjectRef("/note_states");
    fCustomProperties = JBox_GetMotherboardObjectRef("/custom_properties");

    // Custom properties
    fProperties[kModel] = JBox_MakePropertyRef(fCustomProperties, "model");
    fProperties[kMalletType] = JBox_MakePropertyRef(fCustomProperties, "malletType");
    fProperties[kMalletHardness] = JBox_MakePropertyRef(fCustomProperties, "malletHardness");
    fProperties[kStrikePosition] = JBox_MakePropertyRef(fCustomProperties, "strikePosition");
    fProperties[kStrikeJitter] = JBox_MakePropertyRef(fCustomProperties, "strikeJitter");
    fProperties[kResonatorTune] = JBox_MakePropertyRef(fCustomProperties, "resonatorTune");
    fProperties[kResonatorCoupling] = JBox_MakePropertyRef(fCustomProperties, "resonatorCoupling");
    fProperties[kDecay] = JBox_MakePropertyRef(fCustomProperties, "decay");
    fProperties[kBuzzAmount] = JBox_MakePropertyRef(fCustomProperties, "buzzAmount");
    fProperties[kArtifacts] = JBox_MakePropertyRef(fCustomProperties, "artifacts");

    fProperties[kSympathetic] = JBox_MakePropertyRef(fCustomProperties, "sympathetic");
    fProperties[kPitchGlide] = JBox_MakePropertyRef(fCustomProperties, "pitchGlide");
    fProperties[kBodyBloom] = JBox_MakePropertyRef(fCustomProperties, "bodyBloom");
    fProperties[kRollSpeed] = JBox_MakePropertyRef(fCustomProperties, "rollSpeed");

    fProperties[kCloseLevel] = JBox_MakePropertyRef(fCustomProperties, "closeLevel");
    fProperties[kFarLevel] = JBox_MakePropertyRef(fCustomProperties, "farLevel");
    fProperties[kPiezoLevel] = JBox_MakePropertyRef(fCustomProperties, "piezoLevel");
    fProperties[kStereoWidth] = JBox_MakePropertyRef(fCustomProperties, "stereoWidth");

    fProperties[kPreampDrive] = JBox_MakePropertyRef(fCustomProperties, "preampDrive");
    fProperties[kWarmth] = JBox_MakePropertyRef(fCustomProperties, "warmth");
    fProperties[kCompAmount] = JBox_MakePropertyRef(fCustomProperties, "compAmount");
    fProperties[kCompAttack] = JBox_MakePropertyRef(fCustomProperties, "compAttack");
    fProperties[kCompRelease] = JBox_MakePropertyRef(fCustomProperties, "compRelease");

    fProperties[kVolume] = JBox_MakePropertyRef(fCustomProperties, "volume");
    fProperties[kOversampling] = JBox_MakePropertyRef(fCustomProperties, "oversampling");
    fProperties[kVelocityCurve] = JBox_MakePropertyRef(fCustomProperties, "velocityCurve");
    fProperties[kPolyphony] = JBox_MakePropertyRef(fCustomProperties, "polyphony");
    fProperties[kMasterTune] = JBox_MakePropertyRef(fCustomProperties, "masterTune");
    fProperties[kDetune] = JBox_MakePropertyRef(fCustomProperties, "detune");

    fProperties[kModWheel] = JBox_MakePropertyRef(fCustomProperties, "modWheel");
    fProperties[kPitchBend] = JBox_MakePropertyRef(fCustomProperties, "pitchBend");
    fProperties[kSustainPedal] = JBox_MakePropertyRef(fCustomProperties, "sustainPedal");

    fNoteOnLampRef = JBox_MakePropertyRef(fCustomProperties, "noteon");
    fActiveVoicesRef = JBox_MakePropertyRef(fCustomProperties, "active_voices");

    // CV inputs
    auto InitCV = [this](ECVInput idx, const char* path) {
        TJBox_ObjectRef obj = JBox_GetMotherboardObjectRef(path);
        fCVInputs[idx].object = obj;
        fCVInputs[idx].valueRef = JBox_MakePropertyRef(obj, "value");
        fCVInputs[idx].connectedRef = JBox_MakePropertyRef(obj, "connected");
        fCVInputs[idx].value = 0.0;
        fCVInputs[idx].connected = false;
    };

    InitCV(kNoteCV, "/cv_inputs/note_cv");
    InitCV(kGateCV, "/cv_inputs/gate_cv");
    InitCV(kMalletCV, "/cv_inputs/mallet_cv");
    InitCV(kPositionCV, "/cv_inputs/position_cv");
    InitCV(kCouplingCV, "/cv_inputs/coupling_cv");
    InitCV(kVolumeCV, "/cv_inputs/volume_cv");
    InitCV(kSympatheticCV, "/cv_inputs/sympathetic_cv");
    InitCV(kRollCV, "/cv_inputs/roll_cv");
}

void CMaremba::ResetIfRequested() {
    if (fTransport != kJBox_InvalidObjectRef) {
        TJBox_Float64 resetCounter = JBox_LoadMOMPropertyAsNumber(fTransport, kJBox_TransportRequestResetAudio);
        if (resetCounter != 0.0 && resetCounter != fLastResetCounter) {
            fEngine.Reset();
            fLastResetCounter = resetCounter;
        }
    }
}

void CMaremba::HandleNoteEvents(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount) {
    for (TJBox_UInt32 i = 0; i < diffCount; ++i) {
        if (propertyDiffs[i].fObjectRef == fNoteStates) {
            TJBox_Tag note = propertyDiffs[i].fPropertyTag;
            if (note <= 127) {
                double vel = JBox_GetNumber(propertyDiffs[i].fCurrentValue);
                if (vel > 0.0) {
                    fEngine.NoteOn(static_cast<int>(note), static_cast<float>(vel));
                    fLampSecondsRemaining = 0.25f;
                    if (!fLampOn) {
                        JBox_StoreMOMProperty(fNoteOnLampRef, JBox_MakeBoolean(true));
                        fLampOn = true;
                    }
                } else {
                    fEngine.NoteOff(static_cast<int>(note));
                }
            }
        }
    }
}

void CMaremba::HandleCVEvents() {
    for (int i = 0; i < kCVCount; ++i) {
        if (fCVInputs[i].connectedRef != kJBox_InvalidPropertyRef) {
            fCVInputs[i].connected = LoadBooleanProperty(fCVInputs[i].connectedRef, false);
            if (fCVInputs[i].connected) {
                fCVInputs[i].value = LoadNumberProperty(fCVInputs[i].valueRef, 0.0);
            } else {
                fCVInputs[i].value = 0.0;
            }
        }
    }

    if (fCVInputs[kGateCV].connected) {
        double gateVal = fCVInputs[kGateCV].value;
        bool gateActive = (gateVal > 0.1);
        int note = static_cast<int>(std::clamp(fCVInputs[kNoteCV].value * 127.0 + 0.5, 0.0, 127.0));

        if (gateActive && !fLastCVGateActive) {
            fEngine.NoteOn(note, static_cast<float>(gateVal));
            fLastCVNote = note;
            fLampSecondsRemaining = 0.25f;
            if (!fLampOn) {
                JBox_StoreMOMProperty(fNoteOnLampRef, JBox_MakeBoolean(true));
                fLampOn = true;
            }
        } else if (!gateActive && fLastCVGateActive) {
            fEngine.NoteOff(fLastCVNote);
        } else if (gateActive && note != fLastCVNote) {
            fEngine.NoteOff(fLastCVNote);
            fEngine.NoteOn(note, static_cast<float>(gateVal));
            fLastCVNote = note;
        }

        fLastCVGateActive = gateActive;
    }
}

void CMaremba::UpdateParameters() {
    for (int i = 0; i < kParameterCount; ++i) {
        if (fProperties[i] != kJBox_InvalidPropertyRef) {
            fValues[i] = LoadNumberProperty(fProperties[i], kParameterDefaults[i]);
        }
    }

    maremba::EngineParameters ep;
    ep.model = static_cast<int>(fValues[kModel]);
    ep.malletType = static_cast<int>(fValues[kMalletType]);

    // Apply CV modulations
    float malletMod = static_cast<float>(fValues[kMalletHardness]);
    if (fCVInputs[kMalletCV].connected) {
        malletMod += static_cast<float>(fCVInputs[kMalletCV].value);
    }
    // Mod wheel can modulate mallet hardness / attack brightness
    malletMod += static_cast<float>(fValues[kModWheel]) * 0.35f;
    ep.malletHardness = std::clamp(malletMod, 0.0f, 1.0f);

    float posMod = static_cast<float>(fValues[kStrikePosition]);
    if (fCVInputs[kPositionCV].connected) {
        posMod += static_cast<float>(fCVInputs[kPositionCV].value);
    }
    ep.strikePosition = std::clamp(posMod, 0.0f, 1.0f);
    ep.strikeJitter = static_cast<float>(fValues[kStrikeJitter]) * 100.0f;

    ep.resonatorTune = (static_cast<float>(fValues[kResonatorTune]) - 0.50f) * 100.0f;

    float coupMod = static_cast<float>(fValues[kResonatorCoupling]);
    if (fCVInputs[kCouplingCV].connected) {
        coupMod += static_cast<float>(fCVInputs[kCouplingCV].value);
    }
    ep.resonatorCoupling = std::clamp(coupMod, 0.0f, 1.0f);

    ep.decay = 0.10f + static_cast<float>(fValues[kDecay]) * 7.90f;
    ep.buzzAmount = static_cast<float>(fValues[kBuzzAmount]);
    ep.artifacts = static_cast<float>(fValues[kArtifacts]);

    // Premium phenomena
    float sympMod = static_cast<float>(fValues[kSympathetic]);
    if (fCVInputs[kSympatheticCV].connected) {
        sympMod += static_cast<float>(fCVInputs[kSympatheticCV].value);
    }
    ep.sympathetic = std::clamp(sympMod, 0.0f, 1.0f);

    ep.pitchGlide = static_cast<float>(fValues[kPitchGlide]);
    ep.bodyBloom = static_cast<float>(fValues[kBodyBloom]);

    float rollMod = static_cast<float>(fValues[kRollSpeed]) * 20.0f;
    if (fCVInputs[kRollCV].connected) {
        rollMod += static_cast<float>(fCVInputs[kRollCV].value) * 20.0f;
    }
    // If roll speed is dialed up, mod wheel speeds up the roll
    if (rollMod > 1.0f) {
        rollMod += static_cast<float>(fValues[kModWheel]) * 6.0f;
    }
    ep.rollSpeed = std::clamp(rollMod, 0.0f, 20.0f);

    ep.closeLevel = static_cast<float>(fValues[kCloseLevel]);
    ep.farLevel = static_cast<float>(fValues[kFarLevel]);
    ep.piezoLevel = static_cast<float>(fValues[kPiezoLevel]);
    ep.stereoWidth = static_cast<float>(fValues[kStereoWidth]) * 2.0f;

    ep.preampDrive = static_cast<float>(fValues[kPreampDrive]);
    ep.warmth = (static_cast<float>(fValues[kWarmth]) - 0.50f) * 2.0f;
    ep.compAmount = static_cast<float>(fValues[kCompAmount]);
    ep.compAttack = 1.0f + static_cast<float>(fValues[kCompAttack]) * 49.0f;
    ep.compRelease = 20.0f + static_cast<float>(fValues[kCompRelease]) * 480.0f;

    float volMod = static_cast<float>(fValues[kVolume]);
    if (fCVInputs[kVolumeCV].connected) {
        volMod += static_cast<float>(fCVInputs[kVolumeCV].value);
    }
    ep.volume = std::clamp(volMod, 0.0f, 1.0f);

    ep.oversampling = static_cast<int>(fValues[kOversampling]);
    ep.velocityCurve = static_cast<int>(fValues[kVelocityCurve]);
    ep.polyphony = static_cast<int>(fValues[kPolyphony]);

    float bendOffset = (static_cast<float>(fValues[kPitchBend]) - 0.50f) * (2.0f / 12.0f);
    ep.masterTune = static_cast<float>(fValues[kMasterTune]) + bendOffset;
    ep.detune = static_cast<float>(fValues[kDetune]) * 100.0f;
    ep.sustainPedalDown = (fValues[kSustainPedal] > 0.5f);

    fEngine.SetParameters(ep);
}

void CMaremba::RenderBatch(const TJBox_PropertyDiff propertyDiffs[], TJBox_UInt32 diffCount) {
    ResetIfRequested();
    HandleNoteEvents(propertyDiffs, diffCount);
    HandleCVEvents();
    UpdateParameters();

    if (fLampOn) {
        fLampSecondsRemaining -= 64.0f / static_cast<float>(fSampleRate);
        if (fLampSecondsRemaining <= 0.0f) {
            JBox_StoreMOMProperty(fNoteOnLampRef, JBox_MakeBoolean(false));
            fLampOn = false;
        }
    }

    constexpr int kFrames = 64;
    float mainL[kFrames], mainR[kFrames];
    float closeL[kFrames], closeR[kFrames];
    float farL[kFrames], farR[kFrames];
    float piezo[kFrames];

    fEngine.RenderBatch(mainL, mainR, closeL, closeR, farL, farR, piezo, kFrames);

    TJBox_Value outLeftVal = JBox_LoadMOMPropertyByTag(fAudioOutLeft, kJBox_AudioOutputBuffer);
    JBox_SetDSPBufferData(outLeftVal, 0, kFrames, mainL);

    TJBox_Value outRightVal = JBox_LoadMOMPropertyByTag(fAudioOutRight, kJBox_AudioOutputBuffer);
    JBox_SetDSPBufferData(outRightVal, 0, kFrames, mainR);

    if (fAudioOutCloseL != kJBox_InvalidObjectRef) {
        TJBox_Value v = JBox_LoadMOMPropertyByTag(fAudioOutCloseL, kJBox_AudioOutputBuffer);
        JBox_SetDSPBufferData(v, 0, kFrames, closeL);
    }
    if (fAudioOutCloseR != kJBox_InvalidObjectRef) {
        TJBox_Value v = JBox_LoadMOMPropertyByTag(fAudioOutCloseR, kJBox_AudioOutputBuffer);
        JBox_SetDSPBufferData(v, 0, kFrames, closeR);
    }
    if (fAudioOutFarL != kJBox_InvalidObjectRef) {
        TJBox_Value v = JBox_LoadMOMPropertyByTag(fAudioOutFarL, kJBox_AudioOutputBuffer);
        JBox_SetDSPBufferData(v, 0, kFrames, farL);
    }
    if (fAudioOutFarR != kJBox_InvalidObjectRef) {
        TJBox_Value v = JBox_LoadMOMPropertyByTag(fAudioOutFarR, kJBox_AudioOutputBuffer);
        JBox_SetDSPBufferData(v, 0, kFrames, farR);
    }
    if (fAudioOutPiezo != kJBox_InvalidObjectRef) {
        TJBox_Value v = JBox_LoadMOMPropertyByTag(fAudioOutPiezo, kJBox_AudioOutputBuffer);
        JBox_SetDSPBufferData(v, 0, kFrames, piezo);
    }

    JBox_StoreMOMProperty(fActiveVoicesRef, JBox_MakeNumber(fEngine.GetActiveVoiceCount()));
}
