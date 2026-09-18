#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================================="
echo "   MAREMBA COMPREHENSIVE REASON VERIFICATION TEST SUITE   "
echo "=========================================================="

echo ""
echo "[Step 1/4] Running Extension Architecture & Declaration Validator..."
python3 "$SCRIPT_DIR/validate_extension.py"

echo ""
echo "[Step 2/4] Running Jukebox Patch & Preset Compliance Validator..."
python3 "$SCRIPT_DIR/validate_patches.py"

echo ""
echo "[Step 3/4] Compiling & Running Modal Synthesis & Physics DSP Engine Tests..."
clang++ -std=c++17 -O3 -Wall -Wextra -Werror \
    "$SCRIPT_DIR/test_dsp.cpp" \
    "$ROOT_DIR/DSP/MarembaEngine.cpp" \
    "$ROOT_DIR/DSP/MarembaVoice.cpp" \
    -o "$SCRIPT_DIR/test_dsp"
"$SCRIPT_DIR/test_dsp"

echo ""
echo "[Step 4/4] Compiling & Running Multi-Sample-Rate All-Patch Audio Render Test..."
clang++ -std=c++17 -O3 -Wall -Wextra -Werror \
    "$SCRIPT_DIR/AllPatchRenderTest.cpp" \
    "$ROOT_DIR/DSP/MarembaEngine.cpp" \
    "$ROOT_DIR/DSP/MarembaVoice.cpp" \
    -o "$SCRIPT_DIR/all_patch_render_test"
"$SCRIPT_DIR/all_patch_render_test"

echo ""
echo "=========================================================="
echo "  SUCCESS: ALL TEST SUITES PASSED! INSTRUMENT IS 100% OK  "
echo "=========================================================="
