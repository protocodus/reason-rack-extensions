#include "Jukebox.h"
#include "Maremba.h"
#include <cstring>

void* JBox_Export_CreateNativeObject(const char iOperation[], const TJBox_Value iParams[], TJBox_UInt32 iCount) {
    if (std::strcmp(iOperation, "Instance") == 0) {
        double sampleRate = 44100.0;
        if (iCount >= 1) {
            sampleRate = JBox_GetNumber(iParams[0]);
        }
        return new CMaremba(sampleRate);
    }
    return nullptr;
}

void JBox_Export_RenderRealtime(void* privateState, const TJBox_PropertyDiff iPropertyDiffs[], TJBox_UInt32 iDiffCount) {
    if (privateState == nullptr) return;
    CMaremba* instance = reinterpret_cast<CMaremba*>(privateState);
    instance->RenderBatch(iPropertyDiffs, iDiffCount);
}

void JBox_Export_Draw(const TJBox_DisplayArgs* /*iArgs*/) {}
void JBox_Export_Gesture(TJBox_GestureArgs* /*iArgs*/) {}
void JBox_Export_DisplaySetup(const TJBox_DisplayArgs* /*iArgs*/) {}
void JBox_Export_Notify(TJBox_NotifyArgs*) {}
