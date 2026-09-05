#pragma once

#include "JukeboxTypes.h"

#include <cstddef>

constexpr std::size_t kBatchSize = 64;
constexpr int kProcessingLatencySamples = 41;
// Covers the measured host-rate output-coupling tail after a voice retires.
constexpr double kOutputTailSeconds = 0.20;
