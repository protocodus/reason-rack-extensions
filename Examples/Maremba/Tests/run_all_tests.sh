#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SDK_DIR="${JUKEBOX_SDK_DIR:-$ROOT_DIR/../..}"
SDK_API_DIR="$(cd "$SDK_DIR/API" && pwd)"
DSP_SOURCES=("$ROOT_DIR"/DSP/*.cpp)
CXXFLAGS=(-std=c++17 -O3 -Wall -Wextra -Werror)

echo "=========================================================="
echo "   MAREMBA COMPREHENSIVE REASON VERIFICATION TEST SUITE   "
echo "=========================================================="

echo ""
echo "[Step 1/6] Running Extension Architecture & Declaration Validator..."
python3 "$SCRIPT_DIR/validate_extension.py"

echo ""
echo "[Step 2/6] Running Jukebox Patch & Preset Compliance Validator..."
python3 "$SCRIPT_DIR/validate_patches.py"

echo ""
echo "[Step 3/6] Running Panel Geometry & GUI Binding Validator..."
python3 "$SCRIPT_DIR/validate_panel_geometry.py"

echo ""
echo "[Step 4/6] Compiling & Running Modal Synthesis & Physics DSP Engine Tests..."
clang++ "${CXXFLAGS[@]}" \
    "$SCRIPT_DIR/test_dsp.cpp" \
    "${DSP_SOURCES[@]}" \
    -o "$SCRIPT_DIR/test_dsp"
"$SCRIPT_DIR/test_dsp"

echo ""
echo "[Step 5/6] Compiling & Running Rack Wrapper Host Contract (CMaremba through a JBox shim)..."
clang++ "${CXXFLAGS[@]}" -I"$SDK_API_DIR" \
    "$SCRIPT_DIR/WrapperHostTest.cpp" \
    "$ROOT_DIR/Maremba.cpp" \
    "${DSP_SOURCES[@]}" \
    -o "$SCRIPT_DIR/wrapper_host_test"
"$SCRIPT_DIR/wrapper_host_test"

echo ""
echo "[Step 6/6] Compiling & Running Multi-Sample-Rate All-Patch Render Test (through the wrapper)..."
clang++ "${CXXFLAGS[@]}" -I"$SDK_API_DIR" \
    "$SCRIPT_DIR/AllPatchRenderTest.cpp" \
    "$ROOT_DIR/Maremba.cpp" \
    "${DSP_SOURCES[@]}" \
    -o "$SCRIPT_DIR/all_patch_render_test"
"$SCRIPT_DIR/all_patch_render_test" "$ROOT_DIR/Resources/Public"

echo ""
echo "=========================================================="
echo "  SUCCESS: ALL TEST SUITES PASSED! INSTRUMENT IS 100% OK  "
echo "=========================================================="
