#include "Jukebox.h"
#include "YouKnow.h"

#include <cstring>

void* JBox_Export_CreateNativeObject(const char operation[],
                                     const TJBox_Value params[],
                                     TJBox_UInt32 count)
{
    if (std::strcmp(operation, "Instance") == 0)
    {
        JBOX_ASSERT(count == 1);
        if (count != 1 || JBox_GetType(params[0]) != kJBox_Number)
        {
            JBOX_ASSERT_MESSAGE(false,
                                "Instance expects a numeric sample rate");
            return nullptr;
        }
        return new CYouKnow(JBox_GetNumber(params[0]));
    }

    JBOX_ASSERT_MESSAGE(false, "Unknown native object operation");
    return nullptr;
}

void JBox_Export_RenderRealtime(void* privateState,
                                const TJBox_PropertyDiff propertyDiffs[],
                                TJBox_UInt32 diffCount)
{
    if (privateState != nullptr)
        static_cast<CYouKnow*>(privateState)->RenderBatch(propertyDiffs, diffCount);
}

void JBox_Export_Draw(const TJBox_DisplayArgs*) {}
void JBox_Export_Gesture(TJBox_GestureArgs*) {}
void JBox_Export_DisplaySetup(const TJBox_DisplayArgs*) {}
void JBox_Export_Notify(TJBox_NotifyArgs*) {}
